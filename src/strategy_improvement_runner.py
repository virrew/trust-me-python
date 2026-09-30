"""Eleven resumable Strategy Improvement / Trade Lifecycle Research V1 stages.

python -m src.strategy_improvement_runner --resume
python -m src.strategy_improvement_runner --stage 0
"""
from __future__ import annotations

import argparse
import fcntl
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from src.backtest import TRADE_SCHEMA
from src.trade_lifecycle import trade_lifecycle_diagnostics
from src.entry_research_analysis import NUMERIC_FEATURES, bin_numbers, feature_manifest
from src.entry_research_runner import checkpoint, verify_marker, read_json, markdown
from src.exit_research_runner import ROOT, UNIVERSE, digest, save_json, store_frame, load_frame, atomic_bytes, now
from src.win_rate_research_runner import WinRateRunner, POLICIES, STAGES as WR_STAGES, SNAPSHOT
from src.win_rate_research_analysis import MODULE_BITS, grouped_metrics, metrics, partition, path_observations
from src.strategy_improvement_execution import replay, research_stream
from src.strategy_improvement_analysis import (KEYS, causal_path, label_trades, future_labels,
    distributions, threshold_analysis, state_curves, paired_comparison, comparison_summary,
    screen, without_top, preservation_estimates)

SESSION = 'SI-V1-20260930'
STAGES = ['stage_0_audit', 'stage_1_lifecycle_dataset', 'stage_2_entry_filter_diagnosis',
          'stage_3_mfe_path', 'stage_4_loser_mechanisms', 'stage_5_winner_preservation',
          'stage_6_candidates', 'stage_7_isolated_replay', 'stage_8_combined_candidates',
          'stage_9_robustness', 'stage_10_final']
NEW_SOURCES = ['src/strategy_improvement_runner.py', 'src/strategy_improvement_analysis.py',
               'src/strategy_improvement_execution.py']
CAUTION = 'ALL CURRENT HISTORY HAS ALREADY BEEN TOUCHED BY PREVIOUS RESEARCH. No untouched OOS or confirmatory data.'


def combine_frames(frames):
    nonempty = [f for f in frames if len(f)]
    return pd.concat(nonempty, ignore_index=True) if nonempty else frames[0].iloc[:0].copy()


def freeze_json(path, payload):
    """Write once, compare on retry, checksum even before stage completion."""
    path = Path(path)
    checksum = path.with_suffix('.sha256')
    if path.exists():
        if read_json(path) != payload:
            raise ValueError('Frozen candidate definitions changed')
        if checksum.exists() and checksum.read_text().strip() != digest(path):
            raise ValueError('Candidate checksum mismatch')
    else:
        if checksum.exists():
            raise ValueError('Frozen candidate file missing')
        save_json(path, payload)
    if not checksum.exists():
        atomic_bytes(checksum, (digest(path)+'\n').encode())
    return digest(path)


def read_frozen(path):
    path = Path(path)
    if path.with_suffix('.sha256').read_text().strip() != digest(path):
        raise ValueError('Candidate checksum mismatch')
    return read_json(path)


class StrategyImprovementRunner:
    def __init__(self, root=ROOT, session=SESSION):
        if not re.fullmatch(r'[A-Za-z0-9-]+', session):
            raise ValueError('Invalid session name')
        self.root = Path(root)
        # Read-only use of the established input validator and feature cache.
        self.prior = WinRateRunner(root=root)
        self.entry, self.split = self.prior.entry, self.prior.split
        self.diagnostics = self.prior.diagnostics
        self.base = self.root/'results/strategy_improvement'/session
        self.base.mkdir(parents=True, exist_ok=True)
        prior_markers = {}
        for name in WR_STAGES:
            folder = self.prior.base/name
            if not verify_marker(folder, self.prior.identity):
                raise ValueError('Completed WR V1 required: '+name)
            prior_markers[name] = digest(folder/'completed.json')
        git_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=self.root, text=True).strip()
        identity = dict(snapshot=self.prior.plan['identity']['snapshot'],
            previous_plan=self.prior.identity, previous_stages=prior_markers,
            sources={s: digest(ROOT/s) for s in NEW_SOURCES},
            runtime=dict(python=sys.version, pandas=pd.__version__, numpy=np.__version__),
            git_commit=git_commit)
        path = self.base/'research_plan.json'
        if path.exists():
            self.plan = read_json(path)
            if self.plan['identity'] != identity:
                raise ValueError('Input/source/runtime identity changed; refusing mixed study')
        else:
            self.plan = dict(version=1, created_at=now(), identity=identity, snapshot=SNAPSHOT,
                modules=MODULE_BITS, policies=POLICIES, holdout_start=self.split,
                discovery='signal and closed exit before holdout; crossing/censored trades excluded from selection',
                holdout='signal >= boundary; full historical indicator warm-up retained',
                confirmation=CAUTION, behavior_change='NO', existing_strategy_behavior_changed='NO',
                finite_plan=dict(max_lifecycle_per_module=3, max_rejection_per_module=1,
                    max_relaxation=1, max_combination_per_module=1,
                    selection='Only stage 1-5 IN-SAMPLE rows; no post-replay threshold edits',
                    lifecycle='Require >=20 discovery material-giveback losers and >=20 winners. Activation is smallest of 1/2/3/4% >= median loser known MFE, capped at 4%. Winner-path q75 material giveback rounded up to .50/.65/.80 (cap .80); stall q75 rounded up to 3/5/10 (cap 10). Three families: close giveback, stalled giveback, 10% running-MFE lock after stall. Quantiles use winners after the selected activation level.',
                    rejection='Only WR V1 previously frozen Entry V1 regions; >=30 discovery trades inside and outside, negative inside expectancy, lower WR/PF/MFE or worse MAE, >=60% lower-expectancy agreement across >=5 symbols and >=2 years with >=5 trades/arm. At most one by lowest inside expectancy, then id.',
                    relaxation='Only replicated bo_long_fail_price strict sole blocker; all other independent gates pass, no other active modules. Original mask/score remain unchanged; synthetic signal is explicitly experimental.',
                    early_failure='No new early-failure family without a previously replicated decision-time pattern; descriptive failures alone are insufficient',
                    combination='Only independently discovery-screened families; highest discovery expectancy then id in each family; at most one entry+exit per module'),
                screen=dict(min_trades=100, count_ratio=[.7, 1.3], wr_delta=.02,
                    expectancy='positive and strictly above baseline', pf='>1 and strictly above baseline',
                    winners='count >= baseline; mean and median >=90% baseline',
                    losers='count <= baseline; mean and median loss no larger', median_trade='>=baseline',
                    winner_destruction='<=10% matched winners', large_winner_truncation='<=10% of matched >=10% winners lose >25% of return',
                    tail='expectancy after removing top5 positive trades > max(0, baseline same exclusion)',
                    agreement='>=60% WR and expectancy nondecrease in >=10 symbols and >=3 years, >=5 trades/arm/group'),
                execution='Long only, next open entries/market exits, survived-close stop updates effective next bar, stops before current high, gap at open, trend priority; no costs/sizing/portfolio',
                availability='Entry panel at signal close; causal path only at survived close; final/forward labels in separate files; no imputation',
                peak_timing='Existing zero-based bars_to_mfe retained; new peak_age_exact is one-based; uncertainty remains NA',
                statistical_limits='Correlated/overlapping trades, reused historical universe, multiple comparisons, no causal identification, no significance or TradingView parity')
            save_json(path, self.plan)
        self.identity = digest(path)
        self.state_path = self.base/'research_state.json'
        self.state = dict(status='PENDING', stages={})

    def write(self, folder, name, frame):
        store_frame(Path(folder)/f'{name}.csv', frame)

    def read(self, stage, name):
        return load_frame(self.base/STAGES[stage]/f'{name}.csv')

    def run(self, stage=None):
        targets = range(11) if stage is None else [stage]
        # Completion markers, not a possibly interrupted state write, are authoritative.
        completed = {}
        try:
            for name in STAGES:
                if verify_marker(self.base/name, self.identity):
                    completed[name] = dict(status='COMPLETED', checksum=digest(self.base/name/'completed.json'))
        except Exception as exc:
            self.state = dict(status='FAILED', stages=completed, last_error=dict(stage='verification', error=str(exc)))
            save_json(self.state_path, self.state)
            raise
        self.state = dict(status='PARTIAL' if completed else 'PENDING', stages=completed)
        for n in targets:
            name = STAGES[n]
            for before in STAGES[:n]:
                if before not in self.state['stages']:
                    raise ValueError(f'Prerequisite incomplete: {before}; use --resume')
            try:
                result = checkpoint(self.base/name, self.identity, getattr(self, f'stage_{n}'))
                if not verify_marker(self.base/name, self.identity):
                    raise ValueError('Stage checksum verification failed')
                self.state['stages'][name] = dict(status='COMPLETED', checksum=digest(self.base/name/'completed.json'))
                self.state['status'] = 'COMPLETED' if len(self.state['stages']) == 11 else 'PARTIAL'
                self.state['next_stage'] = next((i for i, s in enumerate(STAGES) if s not in self.state['stages']), None)
                self.state.pop('last_error', None)
                save_json(self.state_path, self.state)
                print(f'{name}: {result}', flush=True)
            except Exception as exc:
                self.state.update(status='FAILED', last_error=dict(stage=name, error=str(exc)))
                save_json(self.state_path, self.state)
                raise
        if self.state['status'] == 'COMPLETED':
            self.publish()

    def publish(self):
        pairs = [(self.base/STAGES[10]/'STRATEGY_IMPROVEMENT_MATRIX_V1.md', self.base/'STRATEGY_IMPROVEMENT_MATRIX_V1.md')]
        pairs += [(self.base/STAGES[10]/f'{m}.md', self.base/m/'report.md') for m in MODULE_BITS]
        pairs += [(self.base/STAGES[6]/f'candidate_strategy_improvements.{ext}', self.base/f'candidate_strategy_improvements.{ext}') for ext in ['json', 'sha256']]
        for source, dest in pairs:
            if dest.exists() and digest(dest) != digest(source):
                raise ValueError('Published artifact checksum mismatch: '+str(dest))
            if not dest.exists():
                atomic_bytes(dest, source.read_bytes())

    def stage_0(self, folder):
        inputs = self.prior.plan['identity']['inputs']
        self.write(folder, 'input_identity', pd.DataFrame([dict(path=p, sha256=s) for p, s in inputs.items()]))
        self.write(folder, 'baseline_verified', self.prior.read(1, 'by_module'))
        self.write(folder, 'prior_taxonomy', self.prior.read(2, 'taxonomy'))
        self.write(folder, 'prior_exit_interventions', self.prior.read(4, 'summary'))
        self.write(folder, 'prior_winner_tolerance', self.prior.read(3, 'stop_tolerance'))
        h = pd.read_csv(self.entry/'holdout_results.csv', float_precision='round_trip')
        self.write(folder, 'entry_evidence', h)
        audit = [dict(topic='Win rates', result='Verified from checked WR baseline', source='stage_1_baseline/by_module.csv'),
            dict(topic='Giveback losers', result='Verified from checked WR taxonomy', source='stage_2_loser_taxonomy/taxonomy.csv'),
            dict(topic='Aggressive profit locking / break-even', result='No prior scenario passed every historical screen; inspect full payoff tradeoff', source='stage_7_robustness/assessment.csv'),
            dict(topic='Winner adverse excursions', result='Verified bounded stop-touch counts', source='stage_3_winner_survival/stop_tolerance.csv'),
            dict(topic='Entry price blocker', result='Only fully replicated filter; observational, not realized execution benefit', source='Entry V1 holdout_results.csv'),
            dict(topic='Exit policy', result='Breakout/Squeeze INCONCLUSIVE; MeanRev PROVISIONAL and low sample', source='EXIT_POLICY_MATRIX_V1.md'),
            dict(topic='Causality', result='Next-open research semantics differ deliberately from Pine broker emulator', source='reference/RESEARCH_EXECUTION_CONTRACT.md')]
        self.write(folder, 'summary', pd.DataFrame(audit))
        atomic_bytes(folder/'summary.md', (markdown(pd.DataFrame(audit), ['topic', 'result', 'source'])+'\n'+CAUTION).encode())

    def stage_1(self, folder):
        baseline = self.prior.read(1, 'trades')
        all_states, all_features, checks = [], [], []
        for module in MODULE_BITS:
            for symbol in UNIVERSE:
                target = folder/'cache'/module/symbol
                def calculate(out, m=module, s=symbol):
                    d = self.diagnostics(s)
                    stream = research_stream(d, m)
                    result, _ = replay(stream, POLICIES[m])
                    old = baseline[(baseline.module == m) & (baseline.symbol == s)]
                    assert_frame_equal(result.trades.reset_index(drop=True), old[list(TRADE_SCHEMA)].reset_index(drop=True), check_dtype=False)
                    paths = causal_path(d, result).merge(result.trades[['trade_id', 'signal_time']], on='trade_id', validate='many_to_one')
                    self.write(out, 'states', paths.assign(module=m, symbol=s))
                    feature_manifest(d, ROOT)  # Reject any accidental future/unknown feature.
                    features = d.loc[result.trades.signal_time].rename_axis('signal_time').reset_index()
                    self.write(out, 'features', features.assign(module=m, symbol=s, available_at='signal bar close'))
                checkpoint(target, self.identity, calculate)
                all_states.append(load_frame(target/'states.csv'))
                all_features.append(load_frame(target/'features.csv'))
                checks.append(dict(module=module, symbol=symbol, baseline_ledger_equal=True))
            print(f'Canonical paths: {module}, 50 symbols', flush=True)
        states, features = pd.concat(all_states, ignore_index=True), pd.concat(all_features, ignore_index=True)
        trades = label_trades(baseline, states)
        self.write(folder, 'decision_time_entry_features', features)
        self.write(folder, 'decision_time_states', states)
        self.write(folder, 'retrospective_trade_labels', trades)
        self.write(folder, 'future_state_labels', future_labels(trades, states))
        prefixed = features.rename(columns={c: 'entry__'+c for c in features if c not in KEYS})
        self.write(folder, 'canonical_trades_RETROSPECTIVE', trades.merge(prefixed, on=KEYS, validate='one_to_one'))
        self.write(folder, 'baseline_equivalence', pd.DataFrame(checks))
        self.write(folder, 'summary', grouped_metrics(trades, ['module', 'partition']))
        manifest = [dict(file='decision_time_entry_features.csv', role='features', available_at='signal bar close'),
                    dict(file='decision_time_states.csv', role='features', available_at='survived bar close'),
                    dict(file='retrospective_trade_labels.csv', role='labels', available_at='exit bar close / censored observed end'),
                    dict(file='future_state_labels.csv', role='labels', available_at='future horizon/exit, never state time'),
                    dict(file='canonical_trades_RETROSPECTIVE.csv', role='joined retrospective export; NOT feature input', available_at='after exit')]
        self.write(folder, 'availability_manifest', pd.DataFrame(manifest))

    def stage_2(self, folder):
        trades, features = self.read(1, 'retrospective_trade_labels'), self.read(1, 'decision_time_entry_features')
        joined = trades.merge(features[KEYS+list(NUMERIC_FEATURES)], on=KEYS, validate='one_to_one')
        bins_raw, bin_summary, filters, filter_status, blocked = [], [], [], [], []
        holdout = pd.read_csv(self.entry/'holdout_results.csv', float_precision='round_trip')
        for module in MODULE_BITS:
            edges = read_json(self.entry/module/'discovery/bin_edges.json')
            part = joined[joined.module == module]
            for feature, edge in edges.items():
                p = part.copy()
                p['feature'], p['bin'] = feature, bin_numbers(p[feature], edge).fillna(-1).astype(int)
                cols = KEYS+['feature', 'bin', 'partition', 'year', 'closed', 'return_pct', 'bars_held',
                            'in_trade_mfe_lower', 'in_trade_mae_upper', 'mechanism']
                bins_raw.append(p[cols])
                for key in ['partition', 'year', 'symbol']:
                    for values, g in p.groupby(['bin', key], observed=True):
                        closed = g[g.closed]
                        bin_summary.append(dict(module=module, feature=feature, bin=values[0], group_type=key,
                            group=str(values[1]), **metrics(g), median_mfe=closed.in_trade_mfe_lower.dropna().median(),
                            median_mae=closed.in_trade_mae_upper.dropna().median(),
                            immediate_failure_rate=(closed.mechanism == 'IMMEDIATE_FAILURE').mean(),
                            giveback_loss_rate=closed.mechanism.isin(['MAJOR_GIVEBACK', 'SMALL_PROFIT_GIVEBACK']).mean()))
            for period in ['discovery', 'holdout']:
                table = load_frame(self.entry/module/period/'filter_summary.csv')
                filters.append(table.assign(module=module, period=period))
                # Reuse the Historical Outcome Engine's complete label outputs.
                b = load_frame(self.entry/module/period/'false_negatives.csv')
                keep = [c for c in b if c in ['observation_id', 'symbol', 'timestamp', 'sole_blocker']
                        or c.startswith(('forward_return_', 'mfe_', 'mae_', 'complete_', 'target_', 'label_end_'))]
                blocked.append(b[keep].assign(module=module, period=period))
            discovery = filters[-2]
            for r in discovery.itertuples():
                h = holdout[(holdout.module == module) & (holdout.feature == r.filter) & (holdout.kind == 'filter')]
                status = r.research_label
                replication = h.iloc[0]['final_status'] if len(h) else 'INCONCLUSIVE'
                if replication == 'FAILED HOLDOUT':
                    status = 'FAILED HOLDOUT'
                elif replication == 'LOW SAMPLE':
                    status = 'LOW SAMPLE'
                elif status == 'POTENTIALLY TOO STRICT' and replication != 'REPLICATED':
                    status = 'MIXED'
                filter_status.append(dict(module=module, filter=r.filter, classification=status,
                    entry_v1_discovery=r.research_label, entry_v1_holdout=replication,
                    approved_trade_count=int(part.closed.sum()),
                    false_positive_interpretation='Passing rule alone cannot distinguish allowed weak regions; see frozen feature bins',
                    false_negative_interpretation='Sole blocker observational forward outcomes; not realized trades'))
        self.write(folder, 'approved_trade_bins', pd.concat(bins_raw, ignore_index=True))
        self.write(folder, 'accepted_region_metrics', pd.DataFrame(bin_summary))
        self.write(folder, 'filter_contrasts', pd.concat(filters, ignore_index=True))
        self.write(folder, 'blocked_opportunity_outcomes', pd.concat(blocked, ignore_index=True))
        # Attribute descriptive allowed regions to the rule's measured inputs.
        # This linkage explains passing rules; it never recreates their predicates.
        links = {'trend': ['htf_adx', 'ema_spread_pct'], 'slow_ema': ['ema_spread_pct'],
            'rsi': ['rsi', 'rsi_distance_from_avg', 'bars_since_rsi_up'],
            'rsi_cross': ['rsi', 'rsi_distance_from_avg'], 'oversold': ['bars_since_oversold'],
            'volume': ['volume_ratio'], 'volatility': ['atr_pct'], 'candle': ['candle_range_atr'],
            'recent': ['bars_since_squeeze'], 'release': ['distance_to_squeeze_pct'],
            'touch': ['ema_spread_pct', 'candle_range_atr'], 'reclaim': ['ema_spread_pct']}
        allowed = pd.DataFrame(bin_summary)
        linked_rows = []
        for row in filter_status:
            suffix = row['filter'].split('_fail_', 1)[1]
            features_for_rule = links.get(suffix, [])
            if suffix == 'price':
                features_for_rule = ['distance_to_breakout_atr' if row['module'] == 'breakout' else 'distance_to_upper_band_atr']
            r = allowed[(allowed.module == row['module']) & allowed.feature.isin(features_for_rule)]
            linked_rows.append(r.assign(filter=row['filter']))
            d = r[(r.group_type == 'partition') & (r.group == 'IN-SAMPLE') & (r.bin >= 0)]
            base = metrics(trades[(trades.module == row['module']) & (trades.partition == 'IN-SAMPLE')])
            weak = d[(d.trades >= 30) & (d.expectancy < 0) & (d.win_rate < base['win_rate'])]
            row['false_positive_classification'] = 'POTENTIALLY TOO LOOSE' if len(weak) else 'LOW SAMPLE' if base['trades'] < 30 else 'INCONCLUSIVE'
            row['accepted_weak_regions'] = '; '.join(f'{x.feature} bin {int(x.bin)}' for x in weak.itertuples())
            row['false_positive_interpretation'] = 'Discovery association within passing rule inputs; year/symbol rows exported; not causal support for removing the rule'
        self.write(folder, 'filter_allowed_regions', pd.concat(linked_rows, ignore_index=True))
        for module in MODULE_BITS:
            filter_status.append(dict(module=module, filter='long_fail_score', classification='INCONCLUSIVE',
                entry_v1_discovery='DERIVED REQUIREMENT', entry_v1_holdout='NOT INDEPENDENTLY ABLATABLE',
                approved_trade_count=int(trades[(trades.module == module)].closed.sum()),
                false_positive_classification='INCONCLUSIVE', accepted_weak_regions='',
                false_positive_interpretation='Current min_confluence=1 is derived from module activations; no independent accepted variation',
                false_negative_interpretation='Module sole blockers account for derived score without double counting'))
        self.write(folder, 'summary', pd.DataFrame(filter_status))

    def stage_3(self, folder):
        trades, states, labels = (self.read(1, n) for n in ['retrospective_trade_labels', 'decision_time_states', 'future_state_labels'])
        raw, summary = threshold_analysis(trades, states, labels)
        self.write(folder, 'first_threshold_crossings', raw)
        self.write(folder, 'summary', summary)
        self.write(folder, 'state_curves', state_curves(states, labels))
        fields = ['in_trade_mfe_lower', 'in_trade_mfe_upper', 'in_trade_mae_lower', 'in_trade_mae_upper',
                  'peak_age_exact', 'bars_peak_to_exit_exact', 'final_giveback_lower', 'final_giveback_upper',
                  'mfe_retention_exact', 'giveback_fraction_exact', 'max_stall', 'last_survived_high_age',
                  'median_gap_between_highs', 'post_peak_decline_known']
        self.write(folder, 'distributions', distributions(trades, fields, ['module', 'partition', 'outcome']))

    def stage_4(self, folder):
        trades = self.read(1, 'retrospective_trade_labels')
        losses = trades[trades.outcome == 'LOSER']
        self.write(folder, 'losses', losses)
        self.write(folder, 'taxonomy', losses.groupby(['module', 'partition', 'mechanism'], observed=True).size().rename('count').reset_index())
        rows = []
        for key, p in losses.groupby(['module', 'partition'], observed=True):
            rows.append(dict(module=key[0], partition=key[1], losses=len(p),
                bad_from_start=int((p.in_trade_mfe_upper < .005).sum()),
                worked_then_failed=int((p.in_trade_mfe_lower >= .005).sum()),
                material_first=int((p.in_trade_mfe_lower >= .02).sum()),
                ambiguous=int(((p.in_trade_mfe_lower < .005) & (p.in_trade_mfe_upper >= .005)).sum()),
                bad_from_start_share=(p.in_trade_mfe_upper < .005).mean(),
                worked_then_failed_share=(p.in_trade_mfe_lower >= .005).mean(),
                material_first_share=(p.in_trade_mfe_lower >= .02).mean(),
                median_mfe=p.in_trade_mfe_lower.dropna().median(), median_peak_age=p.peak_age_exact.dropna().median(),
                median_bars_peak_exit=p.bars_peak_to_exit_exact.dropna().median(),
                median_giveback=p.final_giveback_lower.dropna().median(),
                post_peak_decay=int(p.post_peak_decay.sum()), stop_after_material=int(p.stop_after_material_mfe.sum())))
        self.write(folder, 'summary', pd.DataFrame(rows))
        reach = []
        for module, p in losses.groupby('module'):
            for v in (.005, .01, .02, .03, .04):
                reach.append(dict(module=module, threshold=v, total=len(p),
                    never_reached_definite=int((p.in_trade_mfe_upper < v).sum()),
                    never_reached_possible=int((p.in_trade_mfe_lower < v).sum()),
                    never_share_lower=(p.in_trade_mfe_upper < v).mean(), never_share_upper=(p.in_trade_mfe_lower < v).mean()))
        self.write(folder, 'never_reached_bounds', pd.DataFrame(reach))
        features = self.read(1, 'decision_time_entry_features')
        f = losses.merge(features[KEYS+list(NUMERIC_FEATURES)], on=KEYS, validate='one_to_one')
        self.write(folder, 'entry_feature_mechanisms', distributions(f, NUMERIC_FEATURES, ['module', 'partition', 'mechanism']))

    def stage_5(self, folder):
        winners = self.read(1, 'retrospective_trade_labels').query('outcome == "WINNER"').copy()
        winners['large_winner'] = winners.return_pct >= .1
        self.write(folder, 'winners', winners)
        fields = ['in_trade_mae_lower', 'in_trade_mae_upper', 'mae_before_positive_close',
                  'first_positive_close_bar', 'max_material_giveback', 'max_material_stall',
                  'last_survived_high_age', 'new_high_count', 'peak_age_exact', 'bars_held',
                  'mfe_retention_exact', 'final_giveback_lower']
        self.write(folder, 'summary', distributions(winners, fields, ['module', 'partition', 'large_winner']))
        # Existing interventions are context, never retuned or reselected here.
        self.write(folder, 'prior_winner_destruction', self.prior.read(4, 'pairs'))
        self.write(folder, 'prior_intervention_summary', self.prior.read(4, 'summary'))

    def stage_6(self, folder):
        trades = self.read(1, 'retrospective_trade_labels')
        states = self.read(1, 'decision_time_states')
        discovery = trades[trades.partition == 'IN-SAMPLE']
        bins = self.read(2, 'approved_trade_bins')
        candidates, decisions, region_evidence = [], [], []
        for module in MODULE_BITS:
            p = discovery[discovery.module == module]
            w, l = p[p.outcome == 'WINNER'], p[p.outcome == 'LOSER']
            material = l[l.in_trade_mfe_lower >= .02]
            if len(w) >= 20 and len(material) >= 20:
                level = next((v for v in (.01, .02, .03, .04) if v >= l.in_trade_mfe_lower.dropna().median()), .04)
                wp = states.merge(w[KEYS], on=KEYS, validate='many_to_one')
                wp = wp[wp.running_mfe >= level]
                peaks = wp.groupby(KEYS)[['giveback_fraction', 'bars_since_mfe_high']].max()
                if len(peaks) >= 20:
                    give = float(peaks.giveback_fraction.quantile(.75))
                    stale = float(peaks.bars_since_mfe_high.quantile(.75))
                    gb = next((v for v in (.5, .65, .8) if v >= give), .8)
                    stall = next((v for v in (3, 5, 10) if v >= stale), 10)
                    for family in ['giveback', 'stalled', 'adaptive']:
                        rule = dict(family=family, level=level, giveback_fraction=gb, stall_bars=stall, lock_fraction=.1)
                        candidates.append(dict(module=module, id=family, family='lifecycle', exit_rule=rule, entry_rule=None,
                            evidence=dict(discovery_winners=len(w), material_losers=len(material),
                                winner_paths=len(peaks), winner_giveback_q75=give, winner_stall_q75=stale,
                                quantile_capped=give > .8 or stale > 10)))
                    decisions.append(dict(module=module, family='lifecycle', status='THREE FROZEN CANDIDATES',
                        reason=f'Discovery only: level={level}, giveback={gb}, stall={stall}; winner tolerance caps are explicit'))
                else:
                    decisions.append(dict(module=module, family='lifecycle', status='LOW SAMPLE', reason='Fewer than 20 discovery winners reached selected activation'))
            else:
                decisions.append(dict(module=module, family='lifecycle', status='LOW SAMPLE', reason='Requires 20 discovery winners and 20 material-giveback losers'))
            eligible = []
            for rule in self.prior.plan['entry_rules'][module]:
                b = bins[(bins.module == module) & (bins.feature == rule['feature']) & (bins.partition == 'IN-SAMPLE')]
                inside, outside = b[b.bin == rule['bin']], b[b.bin != rule['bin']]
                x, y = metrics(inside), metrics(outside)
                checks = dict(sample=min(x['trades'], y['trades']) >= 30,
                    negative=x['expectancy'] < 0, wr=x['win_rate'] < y['win_rate'],
                    path=(inside.in_trade_mfe_lower.dropna().median() < outside.in_trade_mfe_lower.dropna().median()
                          or inside.in_trade_mae_upper.dropna().median() < outside.in_trade_mae_upper.dropna().median()))
                agreement = {}
                for key, minimum in [('symbol', 5), ('year', 2)]:
                    pairs = grouped_metrics(inside, [key]).merge(grouped_metrics(outside, [key]), on=key, suffixes=('_inside', '_outside'))
                    pairs = pairs[(pairs.trades_inside >= 5) & (pairs.trades_outside >= 5)]
                    rate = (pairs.expectancy_inside < pairs.expectancy_outside).mean()
                    checks[key] = len(pairs) >= minimum and rate >= .6
                    agreement[key+'_agreement'] = rate
                passed = all(checks.values())
                region_evidence.append(dict(module=module, candidate=rule['id'], feature=rule['feature'], bin=rule['bin'],
                    discovery_inside=x['trades'], discovery_outside=y['trades'], inside_expectancy=x['expectancy'],
                    outside_expectancy=y['expectancy'], passed=passed, failed_checks=','.join(k for k, v in checks.items() if not v), **agreement))
                if passed:
                    eligible.append((x['expectancy'], rule['id'], rule))
            if eligible:
                rule = sorted(eligible, key=lambda x: (x[0], x[1]))[0][2]
                candidates.append(dict(module=module, id=rule['id'], family='entry', exit_rule=None,
                    entry_rule=dict(**rule, family='reject_bin'), evidence='Repeated weak region in frozen Entry V1 bins, discovery trades only'))
            decisions.append(dict(module=module, family='entry_rejection', status='ONE FROZEN CANDIDATE' if eligible else 'INCONCLUSIVE',
                reason='Existing WR finite regions only; no further threshold search'))
            decisions.append(dict(module=module, family='early_failure', status='INCONCLUSIVE',
                reason='No replicated contemporaneous early-failure pattern; taxonomy alone does not authorize a new rule'))
        h = self.read(0, 'entry_evidence')
        replicated = h[(h.module == 'breakout') & (h.feature == 'bo_long_fail_price') & (h.final_status == 'REPLICATED')]
        if len(replicated):
            candidates.append(dict(module='breakout', id='relax_price', family='entry', exit_rule=None,
                entry_rule=dict(family='relax_price'), evidence='Entry V1 fixed 10-bar hypothesis REPLICATED; experimental strict sole blocker, not a Pure activation'))
        decisions.append(dict(module='breakout', family='entry_relaxation', status='ONE FROZEN CANDIDATE' if len(replicated) else 'INCONCLUSIVE', reason='No invented price threshold; test full removal in the strict sole-blocker envelope'))
        payload = dict(version=1, plan_sha256=self.identity,
            discovery_only=True, prior_holdout_already_seen=True, candidates=candidates,
            selection_inputs={f'{stage}/{name}': digest(self.base/STAGES[stage]/f'{name}.csv') for stage, name in [
                (1, 'retrospective_trade_labels'), (1, 'decision_time_states'), (2, 'approved_trade_bins'),
                (3, 'summary'), (4, 'summary'), (5, 'summary')]})
        freeze_json(folder/'candidate_strategy_improvements.json', payload)
        self.write(folder, 'summary', pd.DataFrame(decisions))
        cols = ['module', 'candidate', 'feature', 'bin', 'discovery_inside', 'discovery_outside',
                'inside_expectancy', 'outside_expectancy', 'passed', 'failed_checks', 'symbol_agreement', 'year_agreement']
        self.write(folder, 'entry_region_evidence', pd.DataFrame(region_evidence, columns=cols))
        self.write(folder, 'candidate_rules', pd.DataFrame([dict(module=c['module'], scenario=c['id'], family=c['family'], definition=json.dumps(c, sort_keys=True)) for c in candidates], columns=['module', 'scenario', 'family', 'definition']))
        self.write(folder, 'winner_exposure_estimates', preservation_estimates(trades, states, candidates))

    def scenario(self, folder, candidate):
        module, name = candidate['module'], candidate['id']
        raw, recs = [], []
        for symbol in UNIVERSE:
            target = folder/'cache'/module/name/symbol
            def calculate(out, s=symbol):
                d = research_stream(self.diagnostics(s), module, candidate['entry_rule'])
                result, rec = replay(d, POLICIES[module], candidate['exit_rule'])
                life = trade_lifecycle_diagnostics(d, result)['trade_lifecycle']
                enriched = path_observations(d, life)
                enriched['regime'] = [f'ADX {"18-25" if d.loc[t, "htf_adx"] < 25 else "25-40" if d.loc[t, "htf_adx"] < 40 else "40+"}' for t in life.signal_time]
                enriched['research_signal_source'] = [d.loc[t, 'research_signal_source'] for t in life.signal_time]
                trades = partition(enriched.assign(module=module, symbol=s, scenario=name), self.split)
                states = causal_path(d, result).merge(result.trades[['trade_id', 'signal_time']], on='trade_id', validate='many_to_one').assign(module=module, symbol=s)
                self.write(out, 'trades', label_trades(trades, states))
                self.write(out, 'states', states)
                self.write(out, 'reconciliation', rec.assign(module=module, symbol=s, scenario=name))
            checkpoint(target, self.identity, calculate)
            raw.append(load_frame(target/'trades.csv'))
            recs.append(load_frame(target/'reconciliation.csv'))
        return pd.concat(raw, ignore_index=True), pd.concat(recs, ignore_index=True)

    def evaluate(self, folder, candidates):
        baseline = self.read(1, 'retrospective_trade_labels')
        raw, recs, pairs, summaries, screens, tails = [], [], [], [], [], []
        for candidate in candidates:
            module, name = candidate['module'], candidate['id']
            b, rec = self.scenario(folder, candidate)
            a = baseline[baseline.module == module]
            raw.append(b); recs.append(rec)
            pair = paired_comparison(a, b).assign(scenario=name)
            pairs.append(pair)
            summaries.append(dict(module=module, scenario=name, family=candidate['family'], **comparison_summary(a, b)))
            for partition_name, aa, bb in [
                ('DISCOVERY', a[a.partition == 'IN-SAMPLE'], b[b.partition == 'IN-SAMPLE']),
                ('ENTRY HOLDOUT', a[a.partition.str.startswith('ENTRY')], b[b.partition.str.startswith('ENTRY')])]:
                screens.append(dict(module=module, scenario=name, family=candidate['family'], period=partition_name,
                    expectancy=metrics(bb)['expectancy'], **screen(aa, bb)))
            for n in (0, 1, 3, 5):
                for arm, t in [('baseline', a), ('candidate', b)]:
                    tails.append(dict(module=module, scenario=name, arm=arm, removed_top=n, **metrics(without_top(t, n))))
            print(f'{folder.name}: {module}/{name} complete', flush=True)
        empty = baseline.iloc[:0].assign(scenario=pd.Series(dtype=str), research_signal_source=pd.Series(dtype=str))
        self.write(folder, 'trades', pd.concat(raw, ignore_index=True) if raw else empty)
        empty_rec = self.prior.read(1, 'reconciliation').iloc[:0].assign(scenario=pd.Series(dtype=str))
        self.write(folder, 'reconciliation', pd.concat(recs, ignore_index=True) if recs else empty_rec)
        self.write(folder, 'pairs', pd.concat(pairs, ignore_index=True) if pairs else paired_comparison(baseline.iloc[:0], baseline.iloc[:0]).assign(scenario=pd.Series(dtype=str)))
        summary_cols = ['module', 'scenario', 'family']+list(comparison_summary(baseline.iloc[:0], baseline.iloc[:0]))
        self.write(folder, 'summary', pd.DataFrame(summaries, columns=summary_cols))
        screen_cols = ['module', 'scenario', 'family', 'period', 'expectancy']+list(screen(baseline.iloc[:0], baseline.iloc[:0]))
        self.write(folder, 'screen', pd.DataFrame(screens, columns=screen_cols))
        self.write(folder, 'tail_removal', pd.DataFrame(tails, columns=['module', 'scenario', 'arm', 'removed_top']+list(metrics(baseline.iloc[:0]))))

    def stage_7(self, folder):
        payload = read_frozen(self.base/STAGES[6]/'candidate_strategy_improvements.json')
        self.evaluate(folder, payload['candidates'])

    def stage_8(self, folder):
        payload = read_frozen(self.base/STAGES[6]/'candidate_strategy_improvements.json')
        screens = self.read(7, 'screen')
        screens = screens[(screens.period == 'DISCOVERY') & screens.survived]
        combinations, decisions = [], []
        for module in MODULE_BITS:
            chosen = []
            for family in ['entry', 'lifecycle']:
                group = screens[(screens.module == module) & (screens.family == family)]
                group = group.sort_values(['expectancy', 'scenario'], ascending=[False, True])
                chosen.append(group.scenario.iloc[0] if len(group) else None)
            decisions.append(dict(module=module, entry=chosen[0], lifecycle=chosen[1],
                status='COMBINE' if all(chosen) else 'NO COMBINATION: independent discovery screen failed'))
            if all(chosen):
                en = next(c for c in payload['candidates'] if c['module'] == module and c['id'] == chosen[0])
                ex = next(c for c in payload['candidates'] if c['module'] == module and c['id'] == chosen[1])
                combinations.append(dict(module=module, id='combined_'+chosen[0]+'_'+chosen[1], family='combined',
                    entry_rule=en['entry_rule'], exit_rule=ex['exit_rule']))
        freeze_json(folder/'combined_candidates.json', dict(candidates=combinations, isolated_sha256=digest(self.base/STAGES[6]/'candidate_strategy_improvements.json')))
        self.write(folder, 'selection', pd.DataFrame(decisions))
        self.evaluate(folder, combinations)

    def stage_9(self, folder):
        base = self.read(1, 'retrospective_trade_labels').assign(scenario='baseline')
        raw = combine_frames([base, self.read(7, 'trades'), self.read(8, 'trades')])
        summaries = combine_frames([self.read(7, 'summary'), self.read(8, 'summary')])
        screens = combine_frames([self.read(7, 'screen'), self.read(8, 'screen')])
        leave, assessment = [], []
        for r in summaries.itertuples():
            a = base[base.module == r.module]
            b = raw[(raw.module == r.module) & (raw.scenario == r.scenario)]
            sensitivity = {}
            for key in ['year', 'symbol']:
                flags = []
                for value in sorted(set(a[key]) | set(b[key])):
                    aa, bb = a[a[key] != value], b[b[key] != value]
                    x, y = metrics(aa), metrics(bb)
                    passed = (y['expectancy'] > max(0., x['expectancy']) and y['profit_factor'] > max(1., x['profit_factor'])
                              and y['mean_winner'] >= .9*x['mean_winner'] and y['win_rate'] >= x['win_rate'])
                    flags.append(passed)
                    leave.append(dict(module=r.module, scenario=r.scenario, group=key, removed=str(value),
                        passed=passed, delta_expectancy=y['expectancy']-x['expectancy'],
                        delta_pf=y['profit_factor']-x['profit_factor'], delta_wr=y['win_rate']-x['win_rate'], **y))
                sensitivity[key] = all(flags)
            ss = screens[(screens.module == r.module) & (screens.scenario == r.scenario)]
            d, h = ss[ss.period == 'DISCOVERY'].iloc[0], ss[ss.period == 'ENTRY HOLDOUT'].iloc[0]
            if r.trades < 100:
                status = 'LOW SAMPLE'
            elif not d.top5_removed_expectancy > 0:
                status = 'TAIL-SENSITIVE'
            elif not d.survived:
                status = 'FAILED' if r.delta_expectancy <= 0 and r.delta_profit_factor <= 0 else 'MIXED'
            elif not sensitivity['year']:
                status = 'YEAR-SENSITIVE'
            elif not sensitivity['symbol']:
                status = 'SYMBOL-SENSITIVE'
            elif h.survived:
                status = 'INCONCLUSIVE' if r.module in ['breakout', 'squeeze'] else 'ROBUST HISTORICALLY'
            else:
                status = 'PROMISING' if 'sample' in h.failed_checks else 'MIXED'
            assessment.append(dict(module=r.module, scenario=r.scenario, status=status,
                discovery_survived=d.survived, holdout_survived=h.survived,
                discovery_failed=d.failed_checks, holdout_failed=h.failed_checks,
                year_stable=sensitivity['year'], symbol_stable=sensitivity['symbol'],
                symbol_agreement=d.symbol_agreement, year_agreement=d.year_agreement,
                untouched_oos=False))
        self.write(folder, 'summary', pd.DataFrame(assessment, columns=['module', 'scenario', 'status',
            'discovery_survived', 'holdout_survived', 'discovery_failed', 'holdout_failed',
            'year_stable', 'symbol_stable', 'symbol_agreement', 'year_agreement', 'untouched_oos']))
        self.write(folder, 'leave_group_out', pd.DataFrame(leave, columns=['module', 'scenario', 'group', 'removed', 'passed', 'delta_expectancy', 'delta_pf', 'delta_wr']+list(metrics(base.iloc[:0]))))
        for key in ['year', 'symbol', 'regime', 'partition']:
            self.write(folder, 'by_'+key, grouped_metrics(raw, ['module', 'scenario', key]))
        self.write(folder, 'all_scenarios', raw)
        self.write(folder, 'tail_removal', combine_frames([self.read(7, 'tail_removal'), self.read(8, 'tail_removal')]))

    def stage_10(self, folder):
        trades = self.read(1, 'retrospective_trade_labels')
        baseline = grouped_metrics(trades, ['module'])
        comparison = combine_frames([self.read(7, 'summary'), self.read(8, 'summary')])
        comparison = comparison.merge(self.read(9, 'summary'), on=['module', 'scenario'], validate='one_to_one')
        discovery = self.read(7, 'screen').query('period == "DISCOVERY"')
        selection = self.read(8, 'selection').set_index('module')
        filters = self.read(2, 'summary')
        regional = self.read(6, 'entry_region_evidence')
        thresholds = self.read(3, 'summary')
        self.write(folder, 'candidate_comparisons', comparison)
        matrix, answers = [], []
        intro = '# Strategy Improvement / Trade Lifecycle Research V1\n\n'
        intro += 'Behavior change: NO. Existing strategy behavior changed: NO. Existing production functions, defaults, references and earlier research artifacts are unchanged. Alternative behavior exists only in explicitly isolated research arms.\n\n'
        intro += f'Git commit studied: `{self.plan["identity"]["git_commit"]}`. Frozen snapshot: `{SNAPSHOT}` (`{self.plan["identity"]["snapshot"]}`). '
        intro += f'{len(trades)} lifecycle trades, {int(trades.closed.sum())} closed, {int((~trades.closed).sum())} censored. 50 symbols, Long only, independent module streams; this is not a combined portfolio.\n\n'
        intro += f'**{CAUTION}** Discovery is strictly closed before {self.split[:10]}; boundary-crossing outcomes cannot select candidates. Entry Holdout begins at that boundary. Earlier Entry/Exit/WR studies used the history, including holdout.\n\n'
        intro += 'Reference exits: MeanRev Dynamic ATR 2 / Trend OFF (PROVISIONAL), Pullback Dynamic 1.5 / Trend ON (RESEARCH BASELINE), Breakout and Squeeze Dynamic 2.5 / Trend ON (INCONCLUSIVE). No transaction costs, sizing or portfolio effects. All returns and rates in CSVs/tables are fractions; peak ages are one-based holding bars. Exact-peak summaries exclude intrabar-ambiguous peaks and export their missing counts.\n\n'
        sections = []
        for module in MODULE_BITS:
            p = trades[trades.module == module]
            w, l = p[p.outcome == 'WINNER'], p[p.outcome == 'LOSER']
            b = baseline[baseline.module == module].iloc[0]
            c = comparison[comparison.module == module]
            d = discovery[discovery.module == module]
            leaders = {}
            for family in ['entry', 'lifecycle']:
                g = d[d.family == family].sort_values(['expectancy', 'scenario'], ascending=[False, True])
                leaders[family] = g.scenario.iloc[0] if len(g) else None
            best_name = leaders['lifecycle'] or leaders['entry']
            best = c[c.scenario == best_name].iloc[0] if best_name else None
            mechanism = l.mechanism.value_counts().idxmax() if len(l) else 'NO LOSSES'
            bad = int((l.in_trade_mfe_upper < .005).sum())
            worked = int((l.in_trade_mfe_lower >= .005).sum())
            material = int((l.in_trade_mfe_lower >= .02).sum())
            row = dict(module=module, lifecycle_trades=len(p), closed=int(b.trades), winners=len(w), losers=len(l),
                win_rate=b.win_rate, profit_factor=b.profit_factor, expectancy=b.expectancy,
                main_loss_mechanism=mechanism, bad_from_start=bad, worked_then_failed=worked,
                material_first=material, bad_share=bad/len(l) if len(l) else np.nan,
                worked_share=worked/len(l) if len(l) else np.nan,
                median_loser_mfe=l.in_trade_mfe_lower.dropna().median(), median_winner_mfe=w.in_trade_mfe_lower.dropna().median(),
                winner_peak_age=w.peak_age_exact.dropna().median(), loser_peak_age=l.peak_age_exact.dropna().median(),
                winner_peak_to_exit=w.bars_peak_to_exit_exact.dropna().median(), loser_peak_to_exit=l.bars_peak_to_exit_exact.dropna().median(),
                winner_giveback=w.final_giveback_lower.dropna().median(), loser_giveback=l.final_giveback_lower.dropna().median(),
                best_entry_by_discovery=leaders['entry'] or 'NONE', best_lifecycle_by_discovery=leaders['lifecycle'] or 'NONE',
                combined=selection.loc[module, 'status'], status=best.status if best is not None else 'LOW SAMPLE / NO CANDIDATE')
            matrix.append(row)
            issue = filters[(filters.module == module) & (filters.classification == 'POTENTIALLY TOO STRICT')]
            loose = regional[(regional.module == module) & regional.passed]
            answer_text = [
                ('What currently causes most losses?', f'Largest descriptive category: {mechanism}; this is a path description, not an identified cause.'),
                ('What fraction of losers never worked?', f'{bad}/{len(l)} ({row["bad_share"]:.1%}) never reached even a possible +0.5%.'),
                ('What fraction became materially profitable first?', f'{material}/{len(l)} ({material/len(l):.1%}) definitely reached +2%; {worked}/{len(l)} ({row["worked_share"]:.1%}) reached +0.5%.'),
                ('Typical loser MFE?', f'Median known lower bound {row["median_loser_mfe"]:.2%}; upper bounds remain in raw labels.'),
                ('Typical winner MFE?', f'Median known lower bound {row["median_winner_mfe"]:.2%}.'),
                ('Typical winner MFE peak?', f'Exact median holding bar {row["winner_peak_age"]:.1f}; {int(w.peak_age_exact.isna().sum())} of {len(w)} peaks ambiguous.'),
                ('Typical loser MFE peak?', f'Exact median holding bar {row["loser_peak_age"]:.1f}; {int(l.peak_age_exact.isna().sum())} of {len(l)} peaks ambiguous.'),
                ('Typical winner giveback?', f'Median surrendered return {row["winner_giveback"]:.2%}; median exact-MFE fraction {w.giveback_fraction_exact.dropna().median():.1%}.'),
                ('Typical loser giveback?', f'Median surrendered return {row["loser_giveback"]:.2%}; median exact-MFE fraction {l.giveback_fraction_exact.dropna().median():.1%}.'),
                ('How much positive excursion is surrendered?', f'Across closed independent trades: mean known MFE minus realized return {p.loc[p.closed,"final_giveback_lower"].mean():.2%}; this is not capturable portfolio profit.'),
                ('Which entry filters appear too strict?', ', '.join(issue['filter']) or 'None with fully replicated strictness evidence.'),
                ('Which accepted regions appear too loose?', ', '.join(loose.candidate) or 'No previously frozen region passed the repeated weak-lifecycle discovery screen; unconfirmed associations remain in stage 2.'),
                ('Best isolated entry intervention?', (leaders['entry'] or 'NONE')+' by discovery expectancy only; this ranking is descriptive and never a production recommendation.'),
                ('Best lifecycle intervention?', (leaders['lifecycle'] or 'NONE')+' by discovery expectancy only; all tested candidates and failed gates are shown below.'),
                ('How many losers did the displayed lifecycle candidate rescue?', f'{int(best.loser_to_win)} to winners, {int(best.loser_to_nonloss)} to non-loss; denominator {int(best.matched_losers)} matched historical losers; all-baseline rescue rate {best.loser_rescue_rate_all:.1%}.' if best is not None else 'No candidate: insufficient discovery mechanism sample.'),
                ('How many winners did it damage?', f'{int(best.winner_damaged)} earned less, {int(best.winner_destroyed)} became non-winners, {int(best.large_winner_truncated)} large winners lost >25% of return. {int(best.removed_winners)} original winners lost their fill.' if best is not None else 'No new intervention tested.'),
                ('Effect on WR?', f'{b.win_rate:.2%} → {best.win_rate:.2%} ({best.delta_win_rate*100:+.2f} percentage points).' if best is not None else 'No proposed change.'),
                ('Effect on PF?', f'{b.profit_factor:.3f} → {best.profit_factor:.3f} ({best.delta_profit_factor:+.3f}).' if best is not None else 'No proposed change.'),
                ('Effect on expectancy?', f'{b.expectancy:.2%} → {best.expectancy:.2%} ({best.delta_expectancy:+.2%}).' if best is not None else 'No proposed change.'),
                ('Effect on mean / median winner?', f'{b.mean_winner:.2%}/{b.median_winner:.2%} → {best.mean_winner:.2%}/{best.median_winner:.2%}.' if best is not None else f'Baseline {b.mean_winner:.2%}/{b.median_winner:.2%}.'),
                ('Effect on mean / median loser?', f'{b.mean_loser:.2%}/{b.median_loser:.2%} → {best.mean_loser:.2%}/{best.median_loser:.2%}.' if best is not None else f'Baseline {b.mean_loser:.2%}/{b.median_loser:.2%}.'),
                ('Effect on median trade?', f'{b.median_return:.2%} → {best.median_return:.2%} ({best.delta_median_return:+.2%}).' if best is not None else f'Baseline {b.median_return:.2%}.'),
                ('Effect on tail dependence?', f'Top-five winners share gross profit: {b.top5_share_gross_profit:.1%} → {best.top5_share_gross_profit:.1%}; status {best.status}. Exact top-1/3/5 deletion results are in stage 9.' if best is not None else 'Small sample; prior interventions did not clear all gates.'),
                ('Is a combined Strategy V2 candidate justified?', str(selection.loc[module, 'status'])),
                ('What remains unresolved?', 'Causal entry vs management attribution, cost sensitivity, unseen-data replication, intrabar order, and regime stability. '+('Exit-policy uncertainty remains INCONCLUSIVE.' if module in ['breakout', 'squeeze'] else 'MeanRev sample remains limited.' if module == 'meanrev' else 'No untested lifecycle threshold is promoted.'))]
            text = f'## {module}\n\n'
            text += '\n'.join(f'{i}. **{question}** {answer}' for i, (question, answer) in enumerate(answer_text, 1))+'\n\n'
            for i, (question, answer) in enumerate(answer_text, 1):
                answers.append(dict(module=module, number=i, question=question, answer=answer))
            cols = ['scenario', 'status', 'trades', 'win_rate', 'profit_factor', 'expectancy', 'median_return',
                    'mean_winner', 'median_winner', 'mean_loser', 'median_loser', 'loser_to_win', 'winner_damaged',
                    'winner_destroyed', 'large_winner_truncated', 'a_only_fills', 'b_only_fills']
            text += 'All isolated/combined scenarios; ranking never overrides the frozen screen:\n\n'+markdown(c, cols)+'\n'
            text += 'Threshold crossings by chronological period (conditional outcomes; not executable rescue probabilities):\n\n'
            text += markdown(thresholds[thresholds.module == module], ['partition', 'threshold', 'closed', 'final_win_rate',
                'probability_loss', 'median_final_return', 'median_remaining_upside_lower', 'median_bars_to_next_high', 'median_giveback_before_next_high'])
            atomic_bytes(folder/f'{module}.md', (intro+text).encode())
            sections.append(text)
        matrix = pd.DataFrame(matrix)
        self.write(folder, 'summary', matrix)
        self.write(folder, 'module_answers', pd.DataFrame(answers))
        cross = self.cross_module_answers(trades, comparison, matrix)
        self.write(folder, 'research_answers', pd.DataFrame(cross, columns=['question', 'answer']))
        final = intro+'## Baseline\n\n'+markdown(baseline, ['module', 'trades', 'winners', 'losers', 'win_rate', 'profit_factor', 'expectancy', 'mean_winner', 'mean_loser'])
        final += '\n## Main research questions\n\n'+'\n\n'.join(f'**{q}**\n\n{a}' for q, a in cross)+'\n\n'
        final += '\n'.join(sections)
        final += '\n## Interpretation and recovery\n\n'
        final += 'State-curve rows are dependent bar observations, with unique-trade counts and eligible denominators. Exit is a competing event for the next-high horizon; unknown stop-bar ordering and unresolved censoring stay missing. Threshold crossing on an exit endpoint cannot trigger protection retroactively. More MFE is not a causal treatment and cannot guarantee a durable winner. Original-path trigger exposure is separate from actual replay rescue and damage. All scenarios replay their full signal streams, so changed occupancy and re-entry affect counts; pairing uses module/symbol/signal time, never ledger order.\n\n'
        final += 'The price-relaxation arm adds strict sole-price-blocker opportunities while retaining original diagnostic masks/scores (normally zero); these are experimental entries, not Pure activations. None of the prior broad-entry or observational conclusions is upgraded to execution evidence without its explicit replay table. No randomized intervention, economic significance, costs, untouched OOS, ML, scanner, or production Strategy V2 is claimed.\n\n'
        final += 'Every stage has CSV/schema outputs, a hashed completion marker and atomic research state. The plan pins source/runtime/snapshot/prior-artifact identity. Corruption fails closed; valid completed stages are reused. Resume: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m src.strategy_improvement_runner --resume`.\n'
        atomic_bytes(folder/'STRATEGY_IMPROVEMENT_MATRIX_V1.md', final.encode())

    def cross_module_answers(self, trades, comparison, matrix):
        winners = trades[trades.outcome == 'WINNER']
        losses = trades[trades.outcome == 'LOSER']
        large = winners[winners.return_pct >= .1]
        material = losses[losses.in_trade_mfe_lower >= .02]
        eligible = comparison[comparison.discovery_survived & comparison.holdout_survived]
        both = comparison[(comparison.delta_expectancy > 0) & (comparison.delta_profit_factor > 0)]
        name_list = lambda f: ', '.join(f.module+'/'+f.scenario) if len(f) else 'none'
        return [
            ('Why is current win rate low?', f'{len(losses)} closed losses versus {len(winners)} wins; {int((losses.in_trade_mfe_lower >= .005).sum())} losses first achieved known +0.5% and {len(material)} achieved +2%. Loose return retention and noisy entries both contribute descriptively; expectancy also depends on the larger winners.'),
            ('Poor entries or poor lifecycle management?', f'Only {int((losses.in_trade_mfe_upper < .005).sum())}/{len(losses)} losers definitely never reached +0.5%. Worked-then-failed paths dominate, but this does not prove an exit fix can rescue them without harming winners. Intrabar ambiguity and selection prevent causal attribution.'),
            ('Which current filters block historically good opportunities?', 'bo_long_fail_price is the sole fully replicated Entry V1 strictness hypothesis. Forward returns were observational. Its isolated realized replay, original-mask provenance, occupancy changes and failed/passed gates appear in the Breakout section.'),
            ('Which filters fail to exclude bad opportunities?', 'Passing rules cannot establish causal false positives. Stage 2 reports every current filter and frozen accepted bin; stage 6 applies the preregistered repeated-weak-region screen. No arbitrary new feature bins or early-failure filter were invented.'),
            ('How much MFE makes a winner durable?', 'No guaranteed threshold. Stage 3 gives +0.5/1/2/3/4% first-crossing win/loss probabilities, remaining MFE bounds and missing counts separately by module/period. Even +4% can precede a loss; final MFE never enters a decision feature.'),
            ('When does a runner resemble a future giveback loser?', 'The empirical state curves stratify known running MFE, close giveback and time since a strict new high. Repeated rows are dependent. Candidate boundaries came only from discovery winner tolerance and loser MFE, then were frozen before replay; there is no universally demonstrated decay boundary.'),
            ('How much MFE can safely be given back?', f'No safety guarantee. Large (>=10%) winners have median maximum close giveback after +2% MFE of {large.max_material_giveback.dropna().median():.1%}, q75 {large.max_material_giveback.quantile(.75):.1%}; missing={int(large.max_material_giveback.isna().sum())}. A tight fractional lock can interrupt normal winners; actual truncation counts determine acceptance.'),
            ('How long do winners create new highs?', f'Median last survived strict high is holding bar {winners.last_survived_high_age.dropna().median():.1f}; median total holding {winners.bars_held.dropna().median():.1f}; large-winner last high median {large.last_survived_high_age.dropna().median():.1f}. Exact peak timing and gaps between highs are exported per module and period.'),
            ('How long do material giveback losers stall before failing?', f'Median exact peak-to-exit interval {material.bars_peak_to_exit_exact.dropna().median():.1f} bars; {int(material.bars_peak_to_exit_exact.isna().sum())}/{len(material)} exact timings unavailable. A stalled state is not by itself a causal failure signal.'),
            ('What fraction of losses can be rescued without excessive winner destruction?', 'No fraction is established beyond the finite causal replays. Each scenario exports matched and all-baseline loser denominators, winner damage/destruction, large-winner truncation and one-sided fills. Scenarios passing both chronological multi-objective screens: '+name_list(eligible)+'.'),
            ('Can WR rise without collapsing winner size?', 'Compare actual deltas and the >=90% mean/median winner preservation screen, not just WR. Passing both complete screens: '+name_list(eligible)+'. Previously aggressive lock25 remains a caution, not an adopted policy.'),
            ('Can PF and expectancy improve together?', 'Observed full-history increases in both: '+name_list(both)+'. This is descriptive; discovery, tail, year/symbol, count and holdout failures remain binding.'),
            ('Can median trade improve?', 'Observed positive median-trade changes: '+name_list(comparison[comparison.delta_median_return > 0])+'. The same winner-preservation and robustness requirements apply.'),
            ('Which module has the clearest improvement opportunity?', 'Breakout has the clearest replicated entry-filter hypothesis and many material giveback losses. That identifies a research mechanism, not a supported production change; its exit policy is still unresolved. Candidate-specific evidence is enumerated without picking a full-history winner.'),
            ('Which module should remain mostly unchanged?', f'MeanRev: only {int(trades.loc[trades.module == "meanrev", "closed"].sum())} closed reference trades and a provisional exit policy. Other modules also retain their current production behavior regardless of isolated research results.'),
            ('Is there enough evidence for a combined Strategy V2?', '; '.join(f'{r.module}: {r.combined}' for r in matrix.itertuples())+'. No combination is constructed when either independent family fails.'),
            ('Exact next research step?', 'Keep these candidate definitions and hashes fixed. First resolve the documented Breakout/Squeeze reference-exit uncertainty under a preregistered cost-aware protocol; then evaluate any surviving fixed hypothesis on genuinely later unseen bars with a prospectively fixed universe. Collect more MeanRev observations. Do not retune on this snapshot, deploy a descriptive maximum, train ML or start another phase automatically.')]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--all', action='store_true')
    group.add_argument('--resume', action='store_true')
    group.add_argument('--stage', type=int, choices=range(11))
    parser.add_argument('--session', default=SESSION)
    args = parser.parse_args()
    lock = ROOT/'results/strategy_improvement/.runner.lock'
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        runner = StrategyImprovementRunner(session=args.session)
        runner.run(args.stage)
        print(f'Strategy Improvement: {runner.state["status"]} — {runner.base}', flush=True)


if __name__ == '__main__':
    main()
