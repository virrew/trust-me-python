"""Descriptive lifecycle mechanisms, separated causal states and future labels.

Returns and rates are fractions; holding ages are one-based observed rows.
All inference is historical and descriptive. No machine learning or production
rule selection is performed here.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.backtest import _table
from src.strategy_improvement_execution import known_state, policy_action
from src.win_rate_research_analysis import metrics, grouped_metrics, paired_effects, classify_losses

KEYS = ['module', 'symbol', 'signal_time']
STATE_SCHEMA = dict(trade_id='int64', bar_time='datetime64[ns]', age='int64',
    available_at='object', running_return='float64', running_mfe='float64',
    running_mae='float64', new_mfe_high='bool', last_high_age='int64',
    bars_since_mfe_high='int64', giveback='float64', giveback_fraction='float64',
    mfe_retention='float64', close_relative_entry='float64', close_relative_peak='float64',
    current_atr='float64', low_return='float64', active_stop='float64',
    stop_for_next_bar='float64', distance_to_active_stop='float64')
FUTURE_COLUMNS = KEYS + ['bar_time', 'age', 'outcome', 'partition', 'closed',
    'final_return', 'additional_mfe_lower', 'additional_mfe_upper',
    'remaining_holding_bars', 'bars_to_next_high', 'giveback_before_next_high',
    'new_high_next_3', 'new_high_next_5', 'new_high_next_10']


def causal_path(diagnostics, result):
    """Survived closes only. No exit-bar OHLC, completed trade label or final time."""
    rows = []
    for trade in result.trades.itertuples():
        if trade.direction != 'Long':
            raise ValueError('Lifecycle research supports Long only')
        previous = {}
        start = diagnostics.index.get_loc(trade.entry_time)
        trace = result.state[result.state.trade_id == trade.trade_id]
        for s in trace.itertuples():
            if s.stop_hit:
                continue
            b = diagnostics.loc[s.bar_time]
            age = diagnostics.index.get_loc(s.bar_time)-start+1
            previous = known_state(previous, age=age, entry=trade.entry_price,
                                   high=b.high, low=b.low, close=b.close)
            rows.append(dict(trade_id=trade.trade_id, bar_time=s.bar_time,
                available_at='survived bar close', **previous, current_atr=b.atr,
                low_return=b.low/trade.entry_price-1, active_stop=s.active_stop_at_bar_start,
                stop_for_next_bar=s.active_stop_for_next_bar,
                distance_to_active_stop=(b.close-s.active_stop_at_bar_start)/trade.entry_price))
    return _table(rows, STATE_SCHEMA, diagnostics.index.dtype)


def label_trades(trades, states):
    """Add retrospective labels without replacing authoritative lifecycle bounds."""
    t = trades.copy()
    t['outcome'] = np.select([~t.closed, t.return_pct > 0, t.return_pct < 0],
                             ['CENSORED', 'WINNER', 'LOSER'], default='ZERO')
    t['peak_age_exact'] = t.bars_to_mfe.astype(float)+1
    t['bars_peak_to_exit_exact'] = t.bars_held-t.peak_age_exact
    t['final_giveback_lower'] = t.in_trade_mfe_lower-t.return_pct
    t['final_giveback_upper'] = t.in_trade_mfe_upper-t.return_pct
    t['mfe_retention_exact'] = t.return_pct/t.in_trade_mfe.where(t.in_trade_mfe > 0)
    t['giveback_fraction_exact'] = 1-t.mfe_retention_exact
    t['magnitude_bucket'] = pd.cut(t.return_pct, [-np.inf, -.1, -.05, 0, .05, .1, np.inf],
        labels=['LOSS >10%', 'LOSS 5-10%', 'LOSS 0-5%', 'WIN 0-5%', 'WIN 5-10%', 'WIN >10%']).astype(str)
    t.loc[t.return_pct == 0, 'magnitude_bucket'] = 'ZERO'
    t.loc[~t.closed, 'magnitude_bucket'] = 'CENSORED'
    old = classify_losses(t)[KEYS+['category']].rename(columns={'category': 'wr_v1_taxonomy'})
    t = t.merge(old, on=KEYS, how='left', validate='one_to_one')
    stats = []
    for key, p in states.groupby(KEYS, sort=False):
        material = p[p.running_mfe >= .02]
        highs = p[p.new_mfe_high]
        stats.append(dict(zip(KEYS, key), max_stall=p.bars_since_mfe_high.max(),
            max_material_stall=material.bars_since_mfe_high.max(),
            max_material_giveback=material.giveback_fraction.max(),
            last_survived_high_age=highs.age.max(),
            new_high_count=len(highs), median_gap_between_highs=highs.age.diff().dropna().median()))
    cols = KEYS+['max_stall', 'max_material_stall', 'max_material_giveback',
                 'last_survived_high_age', 'new_high_count', 'median_gap_between_highs']
    statistics = pd.DataFrame(stats, columns=cols)
    for key in KEYS:
        statistics[key] = statistics[key].astype(t[key].dtype)
    for col in cols[len(KEYS):]:
        statistics[col] = statistics[col].astype(float)
    t = t.merge(statistics, on=KEYS, how='left', validate='one_to_one')
    t['mechanism'] = 'UNRESOLVED'
    losses = t.outcome == 'LOSER'
    t.loc[losses & (t.in_trade_mfe_upper < .005), 'mechanism'] = 'NEVER_WORKED'
    t.loc[losses & (t.wr_v1_taxonomy == 'IMMEDIATE_FAILURE'), 'mechanism'] = 'IMMEDIATE_FAILURE'
    t.loc[losses & (t.in_trade_mfe_lower >= .005) & (t.in_trade_mfe_upper < .02), 'mechanism'] = 'SMALL_PROFIT_GIVEBACK'
    t.loc[losses & (t.in_trade_mfe_lower >= .02), 'mechanism'] = 'MAJOR_GIVEBACK'
    t['post_peak_decay'] = losses & (t.in_trade_mfe_lower >= .02) & (t.bars_peak_to_exit_exact >= 5)
    t['stop_after_material_mfe'] = losses & (t.in_trade_mfe_lower >= .02) & t.exit_reason.isin(['ATR_STOP', 'TREND_AND_STOP_AT_OPEN'])
    t['entry_quality_problem'] = 'UNRESOLVED: path alone does not identify entry causation'
    # The low of the peak bar has unknown order. Measure strict subsequent bars.
    declines = []
    groups = {key: p for key, p in states.groupby(KEYS, sort=False)}
    for r in t.itertuples():
        p = groups.get((r.module, r.symbol, r.signal_time))
        lows = [] if p is None or pd.isna(r.peak_age_exact) else p.loc[p.age > r.peak_age_exact, 'low_return'].tolist()
        if r.closed and pd.notna(r.peak_age_exact):
            lows.append(r.return_pct)
        declines.append(max(0., r.in_trade_mfe-min(lows)) if lows else np.nan)
    t['post_peak_decline_known'] = declines
    return t


def future_labels(trades, states):
    """Separate future targets. Exit is a competing event, not a missing horizon.

    A stop-bar possible high is never counted as a definite next high. An unknown
    crossing remains NA; a censored unresolved horizon also remains NA. Temporary
    giveback uses completed bars strictly BEFORE the next high (unknown intrabar
    order on that high's bar is excluded).
    """
    rows = []
    lookup = trades.set_index(KEYS)
    for key, p in states.groupby(KEYS, sort=False):
        t = lookup.loc[key]
        p = p.sort_values('age')
        for s in p.itertuples():
            later = p[p.age > s.age]
            higher = later[later.running_mfe > s.running_mfe]
            next_age = int(higher.age.iloc[0]) if len(higher) else np.nan
            if np.isnan(next_age) and t.closed and t.in_trade_mfe_lower > s.running_mfe:
                next_age = int(t.bars_held)
            before = later[later.age < next_age] if np.isfinite(next_age) else later.iloc[:0]
            # Include the current close, known to be after this bar's high.
            lowest = min([s.running_return]+before.low_return.tolist())
            giveback = (s.running_mfe-lowest)/s.running_mfe if s.running_mfe > 0 and np.isfinite(next_age) else np.nan
            row = dict(zip(KEYS, key), bar_time=s.bar_time, age=s.age,
                outcome=t.outcome, partition=t.partition, closed=t.closed,
                final_return=t.return_pct,
                additional_mfe_lower=t.in_trade_mfe_lower-s.running_mfe if t.closed else np.nan,
                additional_mfe_upper=t.in_trade_mfe_upper-s.running_mfe if t.closed else np.nan,
                remaining_holding_bars=t.bars_held-s.age if t.closed else np.nan,
                bars_to_next_high=next_age-s.age, giveback_before_next_high=giveback)
            for n in (3, 5, 10):
                definite = np.isfinite(next_age) and next_age <= s.age+n
                ambiguous = (t.closed and t.bars_held <= s.age+n
                             and t.in_trade_mfe_upper > s.running_mfe
                             and not definite and not len(higher))
                observed = t.closed or p.age.max() >= s.age+n
                row[f'new_high_next_{n}'] = True if definite else pd.NA if ambiguous or not observed else False
            rows.append(row)
    result = pd.DataFrame(rows, columns=FUTURE_COLUMNS)
    for col in KEYS+['bar_time', 'age']:
        result[col] = result[col].astype(states[col].dtype)
    result['closed'] = result.closed.astype(bool)
    for col in ['final_return', 'additional_mfe_lower', 'additional_mfe_upper',
                'remaining_holding_bars', 'bars_to_next_high', 'giveback_before_next_high']:
        result[col] = result[col].astype(float)
    for n in (3, 5, 10):
        result[f'new_high_next_{n}'] = result[f'new_high_next_{n}'].astype('boolean')
    return result


def distributions(frame, fields, keys):
    rows = []
    for key, p in frame.groupby(keys, dropna=False, observed=True):
        key = key if isinstance(key, tuple) else (key,)
        for field in fields:
            v = pd.to_numeric(p[field], errors='coerce').dropna()
            rows.append(dict(zip(keys, key), field=field, total=len(p), observed=len(v),
                missing=len(p)-len(v), mean=v.mean(), q10=v.quantile(.1), q25=v.quantile(.25),
                median=v.dropna().median(), q75=v.quantile(.75), q90=v.quantile(.9)))
    return pd.DataFrame(rows, columns=keys+['field', 'total', 'observed', 'missing', 'mean', 'q10', 'q25', 'median', 'q75', 'q90'])


def threshold_analysis(trades, states, labels):
    joined = states.merge(labels, on=KEYS+['bar_time', 'age'], validate='one_to_one')
    raw = []
    for level in (.005, .01, .02, .03, .04):
        first = joined[joined.running_mfe >= level].groupby(KEYS, sort=False).head(1)
        keys_found = set(map(tuple, first[KEYS].itertuples(index=False, name=None)))
        for s in first.to_dict('records'):
            raw.append({**s, 'threshold': level, 'crossing': 'SURVIVED_CLOSE'})
        # A first known crossing at exit cannot trigger protection retroactively.
        for t in trades[trades.in_trade_mfe_lower >= level].to_dict('records'):
            if tuple(t[k] for k in KEYS) not in keys_found:
                raw.append({**{k: t[k] for k in KEYS}, 'threshold': level, 'age': t['bars_held'],
                    'outcome': t['outcome'], 'partition': t['partition'], 'closed': t['closed'],
                    'final_return': t['return_pct'], 'running_mfe': t['in_trade_mfe_lower'],
                    'additional_mfe_lower': 0., 'additional_mfe_upper': t['in_trade_mfe_upper']-t['in_trade_mfe_lower'],
                    'crossing': 'EXIT_ENDPOINT_ONLY'})
    raw_cols = list(joined.columns)+['threshold', 'crossing']
    raw = pd.DataFrame(raw, columns=raw_cols)
    summary = []
    for key, p in raw.groupby(['module', 'partition', 'threshold'], observed=True):
        closed = p[p.closed]
        t = trades[(trades.module == key[0]) & (trades.partition == key[1])]
        summary.append(dict(module=key[0], partition=key[1], threshold=key[2],
            reached_known=len(p), possibly_reached=int((t.in_trade_mfe_upper >= key[2]).sum()),
            censored=int((~p.closed).sum()), closed=len(closed),
            actionable_crossings=int((p.crossing == 'SURVIVED_CLOSE').sum()),
            final_win_rate=(closed.final_return > 0).mean(), probability_loss=(closed.final_return < 0).mean(),
            median_final_return=closed.final_return.dropna().median(),
            mean_additional_mfe=closed.additional_mfe_lower.mean(),
            median_remaining_upside_lower=closed.additional_mfe_lower.dropna().median(),
            median_remaining_upside_upper=closed.additional_mfe_upper.dropna().median(),
            median_bars_to_next_high=closed.bars_to_next_high.dropna().median(),
            next_high_observed=int(closed.bars_to_next_high.notna().sum()),
            median_giveback_before_next_high=closed.giveback_before_next_high.dropna().median()))
    cols = ['module', 'partition', 'threshold', 'reached_known', 'possibly_reached', 'censored', 'closed',
            'actionable_crossings', 'final_win_rate', 'probability_loss', 'median_final_return',
            'mean_additional_mfe', 'median_remaining_upside_lower', 'median_remaining_upside_upper',
            'median_bars_to_next_high', 'next_high_observed', 'median_giveback_before_next_high']
    return raw, pd.DataFrame(summary, columns=cols)


def state_curves(states, labels):
    f = states.merge(labels, on=KEYS+['bar_time', 'age'], validate='one_to_one')
    f['mfe_bin'] = pd.cut(f.running_mfe, [-np.inf, .005, .01, .02, .03, .04, np.inf], right=False).astype(str)
    f['stall_bin'] = pd.cut(f.bars_since_mfe_high, [-1, 0, 2, 4, 9, np.inf]).astype(str)
    f['giveback_bin'] = pd.cut(f.giveback_fraction, [-np.inf, .25, .5, .75, 1, np.inf], right=False).astype(str)
    rows = []
    keys = ['module', 'partition', 'mfe_bin', 'stall_bin', 'giveback_bin']
    for key, p in f.groupby(keys, dropna=False, observed=True):
        closed = p[p.closed]
        row = dict(zip(keys, key), state_rows=len(p), unique_trades=len(p[KEYS].drop_duplicates()),
            closed_rows=len(closed), winner_probability=(closed.final_return > 0).mean(),
            median_remaining_mfe_lower=closed.additional_mfe_lower.dropna().median())
        for n in (3, 5, 10):
            v = p[f'new_high_next_{n}']
            row.update({f'eligible_{n}': int(v.notna().sum()), f'probability_new_high_{n}': v.mean()})
        rows.append(row)
    cols = keys+['state_rows', 'unique_trades', 'closed_rows', 'winner_probability', 'median_remaining_mfe_lower']
    cols += [c for n in (3, 5, 10) for c in (f'eligible_{n}', f'probability_new_high_{n}')]
    return pd.DataFrame(rows, columns=cols)


def paired_comparison(a, b):
    pair = paired_effects(a, b)
    extras = ['in_trade_mfe_lower', 'in_trade_mfe_upper', 'mfe_retention_exact', 'mechanism']
    for side, f in [('a', a), ('b', b)]:
        pair = pair.merge(f[KEYS+extras].rename(columns={c: c+'_'+side for c in extras}),
                          on=KEYS, how='left', validate='one_to_one')
    matched = pair.matched_closed
    pair['return_delta'] = (pair.return_pct_b-pair.return_pct_a).where(matched)
    pair['winner_damaged'] = matched & (pair.return_pct_a > 0) & (pair.return_pct_b < pair.return_pct_a-1e-12)
    pair['winner_cut_25pct'] = matched & (pair.return_pct_a > 0) & (pair.return_pct_b < .75*pair.return_pct_a)
    pair['large_winner_truncated'] = pair.winner_cut_25pct & (pair.return_pct_a >= .1)
    pair['giveback_loser_rescued'] = pair.loser_to_win & pair.mechanism_a.isin(['SMALL_PROFIT_GIVEBACK', 'MAJOR_GIVEBACK'])
    return pair


def comparison_summary(a, b):
    pair = paired_comparison(a, b)
    matched = pair[pair.matched_closed]
    ma, mb = metrics(a), metrics(b)
    result = {**mb, **{'delta_'+k: mb[k]-ma[k] for k in ma}}
    for name in ['loser_to_win', 'loser_to_nonloss', 'winner_destroyed', 'winner_damaged',
                 'winner_cut_25pct', 'large_winner_truncated', 'giveback_loser_rescued']:
        result[name] = int(pair[name].sum())
    result.update(comparable_trades=len(matched), a_only_fills=int((pair._merge == 'left_only').sum()),
        b_only_fills=int((pair._merge == 'right_only').sum()), unmatched_or_censored=len(pair)-len(matched),
        baseline_losers=ma['losers'], baseline_winners=ma['winners'],
        matched_losers=int((matched.return_pct_a < 0).sum()), matched_winners=int((matched.return_pct_a > 0).sum()),
        matched_large_winners=int((matched.return_pct_a >= .1).sum()),
        removed_winners=int(((pair._merge == 'left_only') & (pair.return_pct_a > 0)).sum()),
        mean_mfe_captured=b.loc[b.closed, 'return_pct'].clip(lower=0).mean(),
        median_mfe_captured=b.loc[b.closed, 'return_pct'].clip(lower=0).dropna().median(),
        mean_mfe_retention=b.loc[b.closed, 'mfe_retention_exact'].mean(),
        median_mfe_retention=b.loc[b.closed, 'mfe_retention_exact'].dropna().median(),
        exact_mfe_retention_n=int(b.loc[b.closed, 'mfe_retention_exact'].notna().sum()))
    for name, numerator, denominator in [
        ('loser_rescue_rate_all', result['loser_to_win'], ma['losers']),
        ('loser_nonloss_rate_all', result['loser_to_nonloss'], ma['losers']),
        ('large_winner_truncation_rate', result['large_winner_truncated'], result['matched_large_winners']),
        ('giveback_rescue_rate', result['giveback_loser_rescued'], int(a.mechanism.isin(['MAJOR_GIVEBACK', 'SMALL_PROFIT_GIVEBACK']).sum()))]:
        result[name] = numerator/denominator if denominator else np.nan
    return result


def without_top(trades, n):
    closed = trades[trades.closed]
    return closed.drop(closed[closed.return_pct > 0].nlargest(n, 'return_pct').index)


def screen(a, b):
    """Preregistered multi-objective historical gate. No significance claim."""
    x, y = metrics(a), metrics(b)
    effects = comparison_summary(a, b)
    checks = dict(sample=min(x['trades'], y['trades']) >= 100,
        count=.7*x['trades'] <= y['trades'] <= 1.3*x['trades'],
        winners=y['winners'] >= x['winners'], losers=y['losers'] <= x['losers'],
        wr=y['win_rate'] >= x['win_rate']+.02,
        expectancy=y['expectancy'] > max(0., x['expectancy']),
        pf=y['profit_factor'] > max(1., x['profit_factor']),
        winner_size=y['mean_winner'] >= .9*x['mean_winner'] and y['median_winner'] >= .9*x['median_winner'],
        loser_size=y['mean_loser'] >= x['mean_loser'] and y['median_loser'] >= x['median_loser'],
        median=y['median_return'] >= x['median_return'],
        destruction=effects['winner_destroyed'] <= .1*effects['matched_winners'],
        large_winners=effects['large_winner_truncated'] <= .1*effects['matched_large_winners'])
    tail_a, tail_b = metrics(without_top(a, 5))['expectancy'], metrics(without_top(b, 5))['expectancy']
    checks['tail'] = tail_b > max(0., tail_a)
    agreement = {}
    for key, minimum in [('symbol', 10), ('year', 3)]:
        p = grouped_metrics(a, [key]).merge(grouped_metrics(b, [key]), on=key, suffixes=('_a', '_b'))
        p = p[(p.trades_a >= 5) & (p.trades_b >= 5)]
        rate = ((p.win_rate_b >= p.win_rate_a) & (p.expectancy_b >= p.expectancy_a)).mean()
        checks[key] = len(p) >= minimum and rate >= .6
        agreement.update({key+'_agreement': rate, key+'_eligible': len(p)})
    return dict(survived=all(checks.values()), failed_checks=','.join(k for k, v in checks.items() if not v),
                top5_removed_expectancy=tail_b, **agreement)


def preservation_estimates(trades, states, candidates):
    """Trigger exposure on original paths is diagnostic, never executable rescue."""
    rows = []
    paths = {k: p for k, p in states.groupby(KEYS, sort=False)}
    for c in candidates:
        rule = c.get('exit_rule')
        for t in trades[trades.module == c['module']].itertuples():
            key = (t.module, t.symbol, t.signal_time)
            p = paths.get(key)
            hit_age = np.nan
            if p is not None and rule:
                for s in p.to_dict('records'):
                    stop, exit_now = policy_action(s, rule, t.entry_price, s['stop_for_next_bar'])
                    if exit_now or stop > s['stop_for_next_bar']:
                        hit_age = s['age']
                        break
            rows.append(dict(module=t.module, symbol=t.symbol, signal_time=t.signal_time,
                scenario=c['id'], outcome=t.outcome, partition=t.partition,
                final_return=t.return_pct, large_winner=t.return_pct >= .1,
                exposed=bool(np.isfinite(hit_age)) if rule else pd.NA, first_exposure_age=hit_age,
                interpretation='Original-path trigger exposure only; stage 7 counts actual damage' if rule
                    else 'Entry occupancy effects require full replay; no lifecycle trigger exposure'))
    cols = KEYS+['scenario', 'outcome', 'partition', 'final_return', 'large_winner', 'exposed',
                'first_exposure_age', 'interpretation']
    result = pd.DataFrame(rows, columns=cols)
    result['exposed'] = result.exposed.astype('boolean')
    return result
