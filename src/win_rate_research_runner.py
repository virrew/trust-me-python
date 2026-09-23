"""Eight checkpointed Win Rate Research V1 stages on the frozen Exit V1 snapshot.

python -m src.win_rate_research_runner --all
python -m src.win_rate_research_runner --stage 1
python -m src.win_rate_research_runner --resume
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from src.backtest import run_swing_backtest_with_reconciliation, TRADE_SCHEMA
from src.trade_lifecycle import trade_lifecycle_diagnostics
from src.entry_research_analysis import bin_numbers, NUMERIC_FEATURES
from src.entry_research_runner import read_json, checkpoint, verify_marker, markdown
from src.exit_research_runner import (ROOT, UNIVERSE, DEFAULT_SESSION as SNAPSHOT,
    config, config_key, digest, save_json, store_frame, load_frame, atomic_bytes, now)
from src.win_rate_research_analysis import (MODULE_BITS, EXIT_RULES, THRESHOLDS, CATEGORIES,
    pure_stream, replay, metrics, grouped_metrics, path_observations, classify_losses,
    paired_effects, partition, screen, frontier_targets)

SESSION = 'WR-V1-20260923'
ENTRY = 'ENTRY-V1-20260923'
STAGES = ['stage_1_baseline','stage_2_loser_taxonomy','stage_3_winner_survival',
          'stage_4_exit_interventions','stage_5_entry_interventions','stage_6_wr_frontier',
          'stage_7_robustness','stage_8_final_matrix']
POLICIES = dict(meanrev=config(2.,False), pullback=config(1.5), breakout=config(), squeeze=config())
SOURCES = ['src/win_rate_research_analysis.py','src/win_rate_research_runner.py',
           'src/backtest.py','src/trade_lifecycle.py','src/entry_research_analysis.py',
           'src/entry_research_runner.py','src/exit_research_runner.py','src/exit_research_analysis.py',
           'src/trust_me_core.py','src/diagnostics_context.py','src/diagnostics_signals.py',
           'reference/RESEARCH_EXECUTION_CONTRACT.md','reference/trust_me_strategy.pine']


def checked_external(folder):
    record = read_json(folder/'completed.json')
    for name, sha in record['hashes'].items():
        if digest(folder/name) != sha:
            raise ValueError(f'External artifact checksum mismatch: {folder/name}')
    return record


class WinRateRunner:
    def __init__(self, root=ROOT, session=SESSION):
        import re
        if not re.fullmatch(r'[A-Za-z0-9-]+',session):
            raise ValueError('Invalid session name')
        self.root = Path(root)
        self.base = self.root/'results/win_rate_research'/session
        self.entry = self.root/'results/entry_research'/ENTRY
        self.snapshot = self.root/'results/research_data'/SNAPSHOT
        self.exitcache = self.root/'results/ab_tests/_exit_runner_cache'/SNAPSHOT
        manifest = read_json(self.snapshot/'manifest.json')
        if manifest['status'] != 'completed' or set(manifest['symbols']) != set(UNIVERSE):
            raise ValueError('Complete canonical snapshot required')
        snapshot_id = hashlib.sha256(json.dumps(manifest['symbols'],sort_keys=True).encode()).hexdigest()
        if snapshot_id != manifest['snapshot_id']:
            raise ValueError('Snapshot identity mismatch')
        inputs = [self.snapshot/'manifest.json', self.entry/'research_plan.json',
                  self.entry/'candidate_entry_hypotheses.csv', self.entry/'holdout_results.csv',
                  self.root/'results/research_registry.csv', self.root/'results/EXIT_POLICY_MATRIX_V1.md']
        for symbol, item in manifest['symbols'].items():
            for suffix,key in [('.csv','sha256'),('.schema.json','schema_sha256')]:
                path = self.snapshot/(symbol+suffix)
                if digest(path) != item[key]:
                    raise ValueError('Snapshot data corruption')
                inputs.append(path)
            folder = self.entry/f'cache/features/{symbol}'
            checked_external(folder)
            inputs.extend(folder.glob('*'))
        for module in MODULE_BITS:
            for stage in ['discovery','holdout']:
                folder = self.entry/module/stage
                checked_external(folder)
                inputs.extend(p for p in folder.iterdir() if p.is_file())
        checked_external(self.entry/'hypothesis_freeze')
        checked_external(self.entry/'published')
        for module in ['breakout','squeeze']:
            for marker in sorted((self.exitcache/module).glob('*/[A-Z]*/completed.json')):
                checked_external(marker.parent)
                inputs.extend(p for p in marker.parent.iterdir() if p.is_file())
        self.split = read_json(self.entry/'research_plan.json')['identity']['holdout_start']
        identity = dict(sources={p:digest(ROOT/p) for p in SOURCES},
            inputs={str(p.relative_to(self.root)):digest(p) for p in sorted(set(inputs)) if p.is_file()},
            runtime=dict(python=sys.version,pandas=pd.__version__,numpy=np.__version__),snapshot=snapshot_id)
        self.base.mkdir(parents=True,exist_ok=True)
        path = self.base/'research_plan.json'
        if path.exists():
            self.plan = read_json(path)
            if self.plan['identity'] != identity:
                raise ValueError('Inputs, source or runtime changed; refusing mixed research versions')
        else:
            entry_rules = {}
            # Reuse the exact Entry V1 discovery negative-20 enrichment family.
            # Selection happens before looking at realized trade outcomes.
            for module in MODULE_BITS:
                poor = load_frame(self.entry/module/'discovery/false_positives.csv')
                p = poor[(poor.outcome_view == 'negative_return_20') & (poor.eligible >= 30) & (poor.enrichment > 1)]
                p = p.sort_values(['enrichment','feature','bin'],ascending=[False,True,True]).head(3)
                edges = read_json(self.entry/module/'discovery/bin_edges.json')
                entry_rules[module] = [dict(id=f'skip_{r.feature}_{int(r.bin)}',feature=r.feature,
                    bin=int(r.bin),edges=edges[r.feature],source='Entry V1 discovery negative20; exploratory')
                    for r in p.itertuples()]
            self.plan = dict(version=1,created_at=now(),identity=identity,policies=POLICIES,
                split=self.split,exit_rules=EXIT_RULES,entry_rules=entry_rules,
                taxonomy=dict(priority=list(CATEGORIES),mfe_thresholds=list(THRESHOLDS),
                    giveback='known MFE >= .02',small='known MFE >= .005 and possible MFE < .02',
                    dead='possible lifetime MFE < .005; first 10 completed bars inside [-.01,.005)',
                    immediate='possible lifetime MFE < .005; known MAE <= -.02 within first 3 bars',
                    never='remaining possible lifetime MFE < .005',uncertain='bounds cross category boundary',
                    causation='Bad-entry-like paths are descriptive proxies, not causal attribution'),
                execution='Long pure streams; next-open entry/market exit; survived-close stop updates effective next bar; gap fills at open; zero return is not a winner; no costs',
                screen='Discovery closed before split only; >=100 trades, >=70% baseline count, WR +2pp, positive expectancy >=90% baseline, PF >1 and >=90% baseline, mean winner >=75%; >=10 symbols and >=3 years with >=5 trades per arm and >=60% WR/expectancy agreement; positive expectancy after top5 winners removed',
                combinations='At most one per module: highest discovery expectancy surviving exit and entry, tie by id. None if either family has no survivor.',
                status='ROBUST requires discovery and Entry Holdout screens plus no leave-one-year/symbol deterioration, and inconclusive-exit modules capped INCONCLUSIVE; not untouched OOS. Otherwise LOW SAMPLE / TAIL-SENSITIVE / FAILED CONFIRMATION / PROMISING / MIXED.',
                targets=[.5,.6,.7,.75],confirmation='No untouched confirmatory data available. Entry Holdout is already viewed and exit-used history.',
                behavior_change='NO',existing_strategy_behavior_changed='NO')
            save_json(path,self.plan)  # Pre-registration BEFORE any trade computation.
        self.identity = digest(path)
        self.state_path = self.base/'research_state.json'
        self.state = read_json(self.state_path) if self.state_path.exists() else dict(status='PENDING',stages={})
        self.diags = {}

    def diagnostics(self, symbol):
        if symbol not in self.diags:
            f = load_frame(self.entry/f'cache/features/{symbol}/features.csv')
            d = f.drop(columns=['observation_id','symbol','direction','available_at']).set_index('timestamp')
            prices = load_frame(self.snapshot/f'{symbol}.csv').set_index('timestamp')
            assert_frame_equal(d[list(prices.columns)], prices, check_freq=False)
            self.diags[symbol] = d
        return self.diags[symbol]

    def write(self, folder, name, frame):
        store_frame(folder/f'{name}.csv',frame)

    def read(self, stage, name):
        return load_frame(self.base/STAGES[stage-1]/f'{name}.csv')

    def run(self, stage=None):
        targets = [stage] if stage else range(1,9)
        for number in targets:
            name = STAGES[number-1]
            for before in STAGES[:number-1]:
                if not verify_marker(self.base/before,self.identity):
                    raise ValueError(f'Prerequisite incomplete: {before}; use --resume')
            try:
                result = checkpoint(self.base/name,self.identity,getattr(self,f'stage_{number}'))
                self.state['stages'][name] = dict(status='COMPLETED',checksum=digest(self.base/name/'completed.json'))
                self.state['status'] = 'COMPLETED' if len(self.state['stages']) == 8 else 'PARTIAL'
                self.state.pop('last_error',None)
                save_json(self.state_path,self.state)
                print(f'{name}: {result}',flush=True)
            except Exception as error:
                self.state['status'] = 'FAILED'
                self.state['last_error'] = dict(stage=name,error=str(error))
                save_json(self.state_path,self.state)
                raise
        if self.state['status'] == 'COMPLETED':
            source = self.base/STAGES[7]/'WIN_RATE_RESEARCH_MATRIX_V1.md'
            destination = self.base/source.name
            if destination.exists() and digest(destination) != digest(source):
                raise ValueError('Published matrix checksum mismatch')
            if not destination.exists():
                atomic_bytes(destination,source.read_bytes())
            for module in MODULE_BITS:
                source = self.base/STAGES[7]/f'{module}.md'
                destination = self.base/module/'report.md'
                if destination.exists() and digest(destination) != digest(source):
                    raise ValueError('Published module checksum mismatch')
                if not destination.exists():
                    atomic_bytes(destination,source.read_bytes())

    def stage_1(self, folder):
        raw, reconciliations, sensitivity, provenance = [], [], [], []
        for module, settings in POLICIES.items():
            for symbol in UNIVERSE:
                target = folder/'cache'/module/symbol
                def calculate(out, m=module,s=symbol,c=settings):
                    d = pure_stream(self.diagnostics(s),m)
                    cached = self.exitcache/m/config_key(c)/s
                    if (cached/'completed.json').exists():
                        meta = checked_external(cached)
                        if meta['settings'] != c or meta['symbol'] != s:
                            raise ValueError('Exit cache configuration mismatch')
                        life = load_frame(cached/'ab_trade_lifecycle.csv')
                        rec = load_frame(cached/'signal_fill_reconciliation.csv')
                        source = 'REUSED EXIT V1'
                    else:
                        original, rec = run_swing_backtest_with_reconciliation(d,**c)
                        life = trade_lifecycle_diagnostics(d,original)['trade_lifecycle']
                        source = 'NEW SNAPSHOT ALIGNMENT; prior historical experiment not rerun'
                    check, check_rec = replay(d,c)
                    assert_frame_equal(check.trades,life[list(TRADE_SCHEMA)],check_dtype=False)
                    assert_frame_equal(check_rec,rec,check_dtype=False)
                    enriched = path_observations(d,life)
                    enriched['regime'] = [f'ADX {"18-25" if d.loc[t,"htf_adx"] < 25 else "25-40" if d.loc[t,"htf_adx"] < 40 else "40+"}' for t in life.signal_time]
                    self.write(out,'trades',partition(enriched.assign(module=m,symbol=s),self.split))
                    self.write(out,'reconciliation',rec.assign(module=m,symbol=s))
                    save_json(out/'provenance.json',dict(source=source,settings=c,disabled_rule_equivalence=True))
                checkpoint(target,self.identity,calculate)
                raw.append(load_frame(target/'trades.csv'))
                reconciliations.append(load_frame(target/'reconciliation.csv'))
                provenance.append(dict(module=module,symbol=symbol,**read_json(target/'provenance.json')))
            print(f'Baseline {module}: 50 symbols verified',flush=True)
        for module in ['breakout','squeeze']:
            for config_folder in sorted((self.exitcache/module).iterdir()):
                if not config_folder.is_dir():
                    continue
                for symbol in UNIVERSE:
                    target = config_folder/symbol
                    checked_external(target)
                    frame = load_frame(target/'ab_trade_lifecycle.csv')
                    sensitivity.append(partition(frame.assign(module=module,symbol=symbol,
                        configuration=config_folder.name),self.split))
        trades = pd.concat(raw,ignore_index=True)
        self.write(folder,'trades',trades)
        self.write(folder,'reconciliation',pd.concat(reconciliations,ignore_index=True))
        self.write(folder,'provenance',pd.DataFrame(provenance).assign(settings=lambda f:f.settings.map(json.dumps)))
        for keys in [['module'],['module','year'],['module','symbol'],['module','regime'],
                     ['module','exit_reason'],['module','holding_bucket'],['module','partition']]:
            self.write(folder,'by_'+'_'.join(keys),grouped_metrics(trades,keys))
        sen = pd.concat(sensitivity,ignore_index=True)
        self.write(folder,'exit_sensitivity_trades',sen)
        self.write(folder,'exit_sensitivity',grouped_metrics(sen,['module','configuration']))
        self.write(folder,'exit_sensitivity_year_symbol',pd.concat([
            grouped_metrics(sen,['module','configuration',key]).assign(group_type=key)
            for key in ['year','symbol']],ignore_index=True))

    def stage_2(self, folder):
        losses = classify_losses(self.read(1,'trades'))
        self.write(folder,'losses',losses)
        rows, bounds = [], []
        for module in MODULE_BITS:
            part = losses[losses.module == module]
            for category in CATEGORIES:
                n = int((part.category == category).sum())
                rows.append(dict(module=module,category=category,count=n,total_losses=len(part),
                                 fraction=n/len(part) if len(part) else np.nan))
            for level in THRESHOLDS:
                bounds.append(dict(module=module,threshold=level,total_losses=len(part),
                    definitely_reached=int((part.in_trade_mfe_lower >= level).sum()),
                    possibly_reached=int((part.in_trade_mfe_upper >= level).sum()),
                    interpretation='Retrospective excursion ceiling, not executable rescue rate'))
        self.write(folder,'taxonomy',pd.DataFrame(rows))
        self.write(folder,'rescue_bounds',pd.DataFrame(bounds))

    def stage_3(self, folder):
        trades = self.read(1,'trades')
        winners = trades[trades.closed & (trades.return_pct > 0)]
        self.write(folder,'winners',winners)
        rows, quantiles = [], []
        features = ['in_trade_mfe_lower','in_trade_mfe_upper','in_trade_mae_lower','in_trade_mae_upper',
                    'mae_before_positive_close','first_positive_close_bar','bars_held'] + [
                    f'first_known_{v:.3f}' for v in (.01,.02,.03)]
        for module in MODULE_BITS:
            w = winners[winners.module == module]
            for level in (.01,.02,.03):
                rows.append(dict(module=module,adverse_threshold=-level,winners=len(w),
                    definitely_touched=int((w.in_trade_mae_upper <= -level).sum()),
                    possibly_touched=int((w.in_trade_mae_lower <= -level).sum()),
                    fraction_definite=(w.in_trade_mae_upper <= -level).mean(),
                    fraction_possible=(w.in_trade_mae_lower <= -level).mean()))
            for outcome, p in [('winner',w),('loser',trades[(trades.module == module)&(trades.return_pct < 0)])]:
                for feature in features:
                    values = p[feature].dropna()
                    quantiles.append(dict(module=module,outcome=outcome,feature=feature,total=len(p),
                        observed=len(values),not_observed=len(p)-len(values),mean=values.mean(),
                        q25=values.quantile(.25),median=values.median(),q75=values.quantile(.75),q90=values.quantile(.9)))
        self.write(folder,'stop_tolerance',pd.DataFrame(rows))
        self.write(folder,'distributions',pd.DataFrame(quantiles))

    def scenario(self, folder, module, name, exit_rule=None, entry_rule=None):
        chunks, reconciliations = [], []
        for symbol in UNIVERSE:
            target = folder/'cache'/module/name/symbol
            def calculate(out,s=symbol):
                d = pure_stream(self.diagnostics(s),module)
                if entry_rule:
                    bins = bin_numbers(d[entry_rule['feature']],entry_rule['edges'])
                    d['long_signal'] &= bins.ne(entry_rule['bin'])  # retain missing, never impute
                result, rec = replay(d,POLICIES[module],exit_rule)
                self.write(out,'trades',partition(result.trades.assign(module=module,symbol=s,scenario=name),self.split))
                self.write(out,'reconciliation',rec.assign(module=module,symbol=s,scenario=name))
            checkpoint(target,self.identity,calculate)
            chunks.append(load_frame(target/'trades.csv'))
            reconciliations.append(load_frame(target/'reconciliation.csv'))
        return pd.concat(chunks,ignore_index=True),pd.concat(reconciliations,ignore_index=True)

    def intervention_tables(self, folder, scenarios):
        baseline = self.read(1,'trades')
        trades, recs, pairs, screens = [], [], [], []
        for module,name,exit_rule,entry_rule in scenarios:
            b, rec = self.scenario(folder,module,name,exit_rule,entry_rule)
            a = baseline[baseline.module == module]
            pair = paired_effects(a,b).assign(scenario=name)
            result = screen(a[a.partition == 'IN-SAMPLE'],b[b.partition == 'IN-SAMPLE'])
            screens.append(dict(module=module,scenario=name,**result,
                discovery_expectancy=metrics(b[b.partition == 'IN-SAMPLE'])['expectancy']))
            trades.append(b); recs.append(rec); pairs.append(pair)
            print(f'{folder.name}: {module} {name}',flush=True)
        schema = baseline[list(TRADE_SCHEMA)+['module','symbol','partition','year','holding_bucket']].iloc[:0].assign(scenario=pd.Series(dtype=str))
        all_trades = pd.concat(trades,ignore_index=True) if trades else schema
        self.write(folder,'trades',all_trades)
        self.write(folder,'reconciliation',pd.concat(recs,ignore_index=True) if recs else self.read(1,'reconciliation').iloc[:0].assign(scenario=pd.Series(dtype=str)))
        self.write(folder,'pairs',pd.concat(pairs,ignore_index=True) if pairs else paired_effects(baseline.iloc[:0],baseline.iloc[:0]).assign(scenario=pd.Series(dtype=str)))
        self.write(folder,'screen',pd.DataFrame(screens,columns=['module','scenario','survived','failed_checks',
            'top5_removed_expectancy','symbol_agreement','year_agreement','discovery_expectancy']))
        summary = grouped_metrics(all_trades,['module','scenario'])
        if pairs:
            combined_pairs = pd.concat(pairs,ignore_index=True)
            effects = combined_pairs.groupby(['module','scenario'])[['loser_to_win','loser_to_nonloss','winner_destroyed']].sum().reset_index()
            summary = summary.merge(effects,on=['module','scenario'],validate='one_to_one')
        else:
            for col in ['loser_to_win','loser_to_nonloss','winner_destroyed']:
                summary[col] = pd.Series(dtype='int64')
        self.write(folder,'summary',summary)

    def stage_4(self, folder):
        self.intervention_tables(folder,[(m,r['id'],r,None) for m in MODULE_BITS for r in EXIT_RULES])

    def stage_5(self, folder):
        baseline = self.read(1,'trades')
        rows = []
        for module in MODULE_BITS:
            edges = read_json(self.entry/module/'discovery/bin_edges.json')
            part = baseline[baseline.module == module].copy()
            for feature in NUMERIC_FEATURES:
                if feature not in edges:
                    continue
                part['feature_value'] = [self.diagnostics(s).loc[t,feature] for s,t in zip(part.symbol,part.signal_time)]
                part['bin'] = bin_numbers(part.feature_value,edges[feature]).fillna(-1).astype(int)
                for keys in [['bin'],['bin','year'],['bin','symbol'],['bin','partition']]:
                    table = grouped_metrics(part,keys).assign(module=module,feature=feature,group_type='/'.join(keys))
                    rows.append(table)
        self.write(folder,'feature_bins',pd.concat(rows,ignore_index=True))
        self.intervention_tables(folder,[(m,r['id'],None,r) for m in MODULE_BITS for r in self.plan['entry_rules'][m]])

    def stage_6(self, folder):
        scenarios, selection = [], []
        for module in MODULE_BITS:
            chosen = []
            for stage in [4,5]:
                s = self.read(stage,'screen')
                s = s[(s.module == module)&s.survived].sort_values(['discovery_expectancy','scenario'],ascending=[False,True])
                chosen.append(s.scenario.iloc[0] if len(s) else None)
            selection.append(dict(module=module,exit=chosen[0],entry=chosen[1],
                status='COMBINE' if all(chosen) else 'NO COMBINATION: one or both families failed discovery screen'))
            if all(chosen):
                er = next(r for r in EXIT_RULES if r['id'] == chosen[0])
                en = next(r for r in self.plan['entry_rules'][module] if r['id'] == chosen[1])
                scenarios.append((module,'combined_'+chosen[0]+'_'+chosen[1],er,en))
        self.write(folder,'selection',pd.DataFrame(selection))
        self.intervention_tables(folder,scenarios)
        columns = list(self.read(4,'trades').columns)
        raw = pd.concat([self.read(1,'trades').assign(scenario='baseline')[columns]]+
                        [self.read(s,'trades') for s in [4,5,6]],ignore_index=True)
        self.write(folder,'frontier_trades',raw)
        summary = grouped_metrics(raw,['module','scenario'])
        base = summary[summary.scenario == 'baseline'].set_index('module')
        summary['fraction_trades_removed'] = [1-n/base.loc[m,'trades'] for m,n in zip(summary.module,summary.trades)]
        self.write(folder,'frontier',summary)

    def stage_7(self, folder):
        raw = self.read(6,'frontier_trades')
        summaries, tails, leaveouts = [], [], []
        for (module,scenario), b in raw.groupby(['module','scenario']):
            a = raw[(raw.module == module)&(raw.scenario == 'baseline')]
            discovery = screen(a[a.partition == 'IN-SAMPLE'],b[b.partition == 'IN-SAMPLE'])
            holdout = screen(a[a.partition.str.startswith('ENTRY')],b[b.partition.str.startswith('ENTRY')])
            # Full history leave-one-group sensitivity; no untouched OOS claim.
            all_leave = True
            for key in ['year','symbol']:
                for value in sorted(set(a[key]) | set(b[key])):
                    aa, bb = a[a[key] != value], b[b[key] != value]
                    ma, mb = metrics(aa), metrics(bb)
                    passed = mb['win_rate'] >= ma['win_rate'] and mb['expectancy'] >= .9*ma['expectancy'] and mb['expectancy'] > 0
                    all_leave &= passed
                    leaveouts.append(dict(module=module,scenario=scenario,group=key,removed=value,passed=passed,**mb))
            for n in [0,1,3,5]:
                closed = b[b.closed].copy()
                trimmed = closed.drop(closed[closed.return_pct > 0].nlargest(n,'return_pct').index)
                tails.append(dict(module=module,scenario=scenario,removed_top=n,**metrics(trimmed)))
            met = metrics(b)
            if met['trades'] < 100:
                status = 'LOW SAMPLE'
            elif not discovery['top5_removed_expectancy'] > 0:
                status = 'TAIL-SENSITIVE'
            elif discovery['survived'] and holdout['survived'] and all_leave:
                status = 'ROBUST'
            elif discovery['survived'] and not holdout['survived']:
                status = 'FAILED CONFIRMATION' if not holdout['failed_checks'].startswith('sample') else 'PROMISING'
            else:
                status = 'MIXED'
            if status == 'ROBUST' and module in ['breakout','squeeze']:
                status = 'INCONCLUSIVE'
            if scenario == 'baseline' and met['trades'] >= 100 and status != 'TAIL-SENSITIVE':
                status = 'INCONCLUSIVE'
            stability = {}
            for key in ['year','symbol']:
                groups = grouped_metrics(b,[key])
                eligible = groups[groups.trades >= 5]
                stability.update({key+'_eligible_groups':len(eligible),
                    key+'_wr_min':eligible.win_rate.min(),key+'_wr_max':eligible.win_rate.max(),
                    key+'_wr_std':eligible.win_rate.std(ddof=0)})
            summaries.append(dict(module=module,scenario=scenario,status=status,**met,**stability,
                discovery_survived=discovery['survived'],holdout_survived=holdout['survived'],
                discovery_failed=discovery['failed_checks'],holdout_failed=holdout['failed_checks'],
                leave_groups_passed=all_leave,untouched_confirmation=False))
        summary = pd.DataFrame(summaries)
        self.write(folder,'assessment',summary)
        self.write(folder,'tail_removal',pd.DataFrame(tails))
        self.write(folder,'leave_group_out',pd.DataFrame(leaveouts))
        for keys in [['module','scenario','year'],['module','scenario','symbol'],['module','scenario','partition']]:
            self.write(folder,'by_'+'_'.join(keys),grouped_metrics(raw,keys))
        self.write(folder,'targets',frontier_targets(summary))

    def stage_8(self, folder):
        self.final_report(folder)

    def final_report(self, folder):
        baseline = self.read(1,'by_module')
        taxonomy = self.read(2,'taxonomy')
        summary = self.read(7,'assessment')
        targets = self.read(7,'targets')
        frontier = self.read(6,'frontier')
        text = '# Win Rate Research Matrix V1\n\n'
        text += 'Behavior change: NO. Existing strategy behavior changed: NO. Research-only interventions; production code and authoritative references unchanged.\n\n'
        text += f'Frozen 50-symbol Daily snapshot `{SNAPSHOT}`. Pure Long modules, one position per symbol/module; pooled modules are not a portfolio or the broad strategy. Entry Holdout starts {self.split[:10]}; discovery excludes trades whose exits cross the boundary. ALL history was previously used by Exit V1; Entry Holdout has already been examined by Entry V1. **No untouched CONFIRMATORY DATA is available.**\n\n'
        text += 'The premise of approximately 40% WR must be checked against the cohort and exit policy. MeanRev uses provisional Dynamic ATR 2 / Trend OFF; Pullback Dynamic 1.5 / Trend ON; Breakout and Squeeze use unresolved reference Dynamic 2.5 / Trend ON. Their full existing predefined configuration sensitivity is retained. Returns are raw fractions with no costs, sizing or portfolio aggregation. Break-even is not a win.\n\n'
        text += markdown(baseline,list(baseline.columns))
        pooled = pd.DataFrame([metrics(self.read(1,'trades'))])
        self.write(folder,'pooled_baseline',pooled)
        text += '\nCross-module pooled independent research trades (NOT a portfolio or a deduplicated broad-strategy WR):\n\n'+markdown(pooled,list(pooled.columns))
        text += '\nLoss taxonomy (mutually exclusive, fractions of ALL losses; uncertainty retained):\n\n'+markdown(taxonomy,list(taxonomy.columns))
        text += '\nBad-entry-like is IMMEDIATE_FAILURE + NEVER_WORKED, a descriptive proxy, not a causal percentage. A failed path does not prove an entry defect. STOP_TIMING_OTHER is not assigned merely because a trade hit a stop. Uncertain stop-bar ordering prevents attributing some losses. DEAD_TRADE is a deliberately narrow, preregistered near-flat-first-10-bars definition.\n\n'
        matrix = []
        for module in MODULE_BITS:
            base = baseline[baseline.module == module].iloc[0]
            tax = taxonomy[taxonomy.module == module].set_index('category')
            part = summary[(summary.module == module)&(summary.scenario != 'baseline')]
            best = part.sort_values(['win_rate','scenario'],ascending=[False,True]).iloc[0] if len(part) else None
            robust = part[part.status == 'ROBUST']
            row = dict(module=module,baseline_wr=base.win_rate,baseline_trades=base.trades,
                bad_entry_like_fraction=tax.loc[['IMMEDIATE_FAILURE','NEVER_WORKED'],'fraction'].sum(),
                giveback_fraction=tax.loc[['GIVEBACK_LOSER','SMALL_PROFIT_GIVEBACK'],'fraction'].sum(),
                dead_fraction=tax.loc['DEAD_TRADE','fraction'],uncertain_fraction=tax.loc['UNCERTAIN_PATH','fraction'],
                largest_category=tax['count'].idxmax(),highest_observed_scenario=best.scenario if best is not None else 'none',
                highest_observed_wr=best.win_rate if best is not None else np.nan,
                trades=best.trades if best is not None else 0,pf=best.profit_factor if best is not None else np.nan,
                expectancy=best.expectancy if best is not None else np.nan,status=best.status if best is not None else 'INCONCLUSIVE',
                robust_supported_wr=robust.win_rate.max() if len(robust) else np.nan)
            matrix.append(row)
            detail = f'# {module}: Win Rate V1\n\n'+markdown(pd.DataFrame([row]),list(row))
            detail += '\nAll predefined scenarios, without selecting a production policy:\n\n'+markdown(summary[summary.module == module],['scenario','status','trades','win_rate','mean_winner','mean_loser','profit_factor','expectancy','year_wr_min','year_wr_max','year_wr_std','symbol_wr_std','discovery_failed','holdout_failed'])
            detail += '\nWinner stop tolerance (bounds, fractions):\n\n'+markdown(self.read(3,'stop_tolerance').query('module == @module'),list(self.read(3,'stop_tolerance').columns))
            atomic_bytes(folder/f'{module}.md',detail.encode())
        matrix = pd.DataFrame(matrix)
        self.write(folder,'matrix',matrix)
        self.write(folder,'frontier',frontier.merge(summary[['module','scenario','status']],on=['module','scenario'],validate='one_to_one'))
        self.write(folder,'targets',targets)
        text += '## Module matrix\n\n'+markdown(matrix,list(matrix.columns))
        text += '\n## WIN RATE FRONTIER\n\n'+markdown(frontier.merge(summary[['module','scenario','status']],on=['module','scenario']),['module','scenario','status','trades','fraction_trades_removed','win_rate','mean_winner','median_winner','mean_loser','median_loser','profit_factor','expectancy','median_return','worst_return','top5_share_gross_profit'])
        text += '\nHistorical stability (eligible groups have >=5 trades):\n\n'+markdown(summary,['module','scenario','year_eligible_groups','year_wr_min','year_wr_max','year_wr_std','symbol_eligible_groups','symbol_wr_min','symbol_wr_max','symbol_wr_std'])
        text += '\n## Targets under the fixed robustness constraints\n\n'+markdown(targets,list(targets.columns))
        text += '\n## Existing exit-policy uncertainty\n\n'+markdown(self.read(1,'exit_sensitivity'),['module','configuration','trades','win_rate','profit_factor','expectancy'])
        text += '\n## Explicit research answers\n\n'
        for module in MODULE_BITS:
            b = baseline[baseline.module == module].iloc[0]
            tax = taxonomy[taxonomy.module == module].set_index('category')
            rescue = self.read(2,'rescue_bounds').query('module == @module')
            p = summary[(summary.module == module)&(summary.scenario != 'baseline')]
            exits = self.read(4,'summary').query('module == @module')
            entries = self.read(5,'summary').query('module == @module')
            pairs = self.read(4,'pairs').query('module == @module')
            effects = pairs.groupby('scenario')[['loser_to_win','loser_to_nonloss','winner_destroyed']].sum()
            self.write(folder,f'{module}_paired_effects',effects.reset_index())
            text += f'### {module}\n\n'
            text += f'1. Current pure-cohort WR is {b.win_rate:.2%}: {int(b.winners)} wins, {int(b.losers)} losses, {int(b.ties)} ties from {int(b.trades)} closed trades. Mean winner {b.mean_winner:.2%}, mean loser {b.mean_loser:.2%}; this payoff asymmetry explains why WR alone is inadequate.\n'
            text += f'2. Largest observed loss category: {tax["count"].idxmax()}, {tax["fraction"].max():.2%} of losses.\n'
            bad = int(tax.loc[['IMMEDIATE_FAILURE','NEVER_WORKED'],'count'].sum())
            give = int(tax.loc[['GIVEBACK_LOSER','SMALL_PROFIT_GIVEBACK'],'count'].sum())
            text += f'3. {bad} bad-from-start-like versus {give} known-giveback losses; {int(tax.loc["UNCERTAIN_PATH","count"])} cannot be unambiguously categorized.\n'
            rr = rescue[rescue.threshold == .01].iloc[0]
            text += f'4. {int(rr.definitely_reached)}–{int(rr.possibly_reached)} of {int(rr.total_losses)} losses reached +1% before exit (retrospective bounds, not tradable rescue counts). Best actual matched loser-to-win rescue among fixed exits: {int(effects.loser_to_win.max())}; matched rescue and winner destruction for every rule are in the paired-effect table.\n'
            text += f'5. {bad} losses had <0.5% possible lifetime favorable excursion and look more like entry-selection candidates. This does not prove they require a different entry; random variation and execution also matter.\n'
            features = self.read(5,'feature_bins')
            fs = features[(features.module == module)&(features.group_type == 'bin')&(features.trades >= 30)&(features.bin != -1)]
            spreads = fs.groupby('feature').win_rate.agg(lambda x:x.max()-x.min()).sort_values(ascending=False)
            text += '6. Largest adequately sampled fixed-bin WR spreads: '+(', '.join(f'{k} ({v:.1%})' for k,v in spreads.head(3).items()) or 'none')+'. These are associations selected for description, not new tested filters; year/symbol/partition detail and frozen edges remain in CSVs.\n'
            if len(exits):
                ex = exits.sort_values(['win_rate','scenario'],ascending=[False,True]).iloc[0]
                text += f'7. Highest observed fixed-exit WR: {ex.scenario}, {ex.win_rate:.2%}, n={int(ex.trades)}, PF={ex.profit_factor:.3f}, expectancy={ex.expectancy:.2%}, mean winner={ex.mean_winner:.2%}. This is a descriptive maximum, not a recommendation.\n'
            if len(entries):
                en = entries.sort_values(['win_rate','scenario'],ascending=[False,True]).iloc[0]
                text += f'8. Highest observed predefined entry-skip WR: {en.scenario}, {en.win_rate:.2%}, n={int(en.trades)} ({1-en.trades/b.trades:.1%} fewer), PF={en.profit_factor:.3f}, expectancy={en.expectancy:.2%}.\n'
            else:
                text += '8. Entry V1 supplied no sufficiently sampled enriched region for the preregistered skip family; no entry threshold was invented.\n'
            selection = self.read(6,'selection').query('module == @module').iloc[0]
            text += f'9. Combined research: {selection.status}. No Cartesian search is allowed.\n'
            robust = p[p.status == 'ROBUST']
            text += f'10. Highest WR satisfying every predefined historical robustness gate: {robust.win_rate.max():.2%}.\n' if len(robust) else '10. No intervention satisfies every predefined historical robustness gate; a higher robust WR is not established.\n'
            high = p[p.win_rate >= .75]
            text += f'11. {len(high)} predefined scenarios reach 75% in pooled history; none should be interpreted without count, winner-size, tail and year/symbol gates. Failed checks are explicit in stage 7.\n'
            text += '12. Robust 75% is not supported by this finite study. This is not a mathematical impossibility result; searching until 75% appears would add selection bias and may remove most trades or truncate winners.\n'
            text += '13. Freeze any surviving hypothesis and test it on genuinely later, unseen bars, with costs and a stable universe. For unresolved modules, first resolve exit-policy uncertainty; do not deploy the descriptive maximum.\n\n'
        text += '## Interpretation and limits\n\n'
        text += 'Full-stream replays include changed position occupancy and subsequent fills; rescue/destruction pairs match symbol/module/signal_time only. One-sided fills and censored pairs are retained separately. A higher WR from break-even exits cannot count zero returns as wins. Stop threshold sensitivity is not an optimized tighter-stop policy. Winner time-to-threshold quantiles are conditional on known hits; not-hit/unknown counts are exported. MAE-before-positive uses completed bars before first positive close; intrabar ordering within that first-positive bar is unknown.\n\n'
        text += 'Stage 7 includes every year/symbol, leave-one-year/symbol-out and removal of top 1/3/5 positive trades. ROBUST would be a descriptive historical status only, not statistical significance or independent OOS confirmation. Present-day universe selection, correlated trades, multiple comparisons, shorter IPO histories and unmodeled transaction costs remain material. Historical Outcome labels were already produced by Entry V1 and are reused only to preregister entry hypotheses; they are never joined as decision features. No ML, parameter optimization or production strategy changes were made.\n'
        atomic_bytes(folder/'WIN_RATE_RESEARCH_MATRIX_V1.md',text.encode())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--all',action='store_true')
    group.add_argument('--resume',action='store_true')
    group.add_argument('--stage',type=int,choices=range(1,9))
    parser.add_argument('--session',default=SESSION)
    args = parser.parse_args()
    # Lock all WR sessions; no mutation of any source registry or old artifact.
    lock = ROOT/'results/win_rate_research/.runner.lock'
    lock.parent.mkdir(parents=True,exist_ok=True)
    with lock.open('a') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        runner = WinRateRunner(session=args.session)
        runner.run(args.stage)
        print(f'Win Rate Research: {runner.state["status"]} — {runner.base}',flush=True)


if __name__ == '__main__':
    main()
