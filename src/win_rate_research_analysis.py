"""Research-only trade path diagnostics and finite causal Long exit experiments.

No production function is changed. Rates/returns are fractions, bars are rows.
Excursion uncertainty is preserved; retrospective paths are never entry features.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.backtest import (
    TRADE_SCHEMA, STATE_SCHEMA, RECONCILIATION_SCHEMA, SwingBacktestResult,
    _validate, _table, _trade_row, _close,
)

MODULE_BITS = dict(meanrev=8, pullback=1, breakout=2, squeeze=4)
CATEGORIES = ('GIVEBACK_LOSER', 'SMALL_PROFIT_GIVEBACK', 'DEAD_TRADE',
              'IMMEDIATE_FAILURE', 'NEVER_WORKED', 'STOP_TIMING_OTHER', 'UNCERTAIN_PATH')
THRESHOLDS = (.005, .01, .02, .03, .04)
EXIT_RULES = [dict(id=f'{family}_{int(level*100)}', family=family, level=level)
              for family in ('breakeven', 'lock25') for level in (.01, .02, .03, .04)] + [
    dict(id=f'time_{bars}', family='time', bars=bars) for bars in (5, 10, 15)] + [
    dict(id='early_3', family='early', bars=3)]


def pure_stream(diagnostics, module):
    expected = sum(diagnostics[c].astype(int)*b for c, b in zip(
        ('pullback_long', 'breakout_long', 'squeeze_long', 'mean_rev_long'), (1, 2, 4, 8)))
    if not expected.equals(diagnostics.long_active_module_mask.astype(int)):
        raise ValueError('Module mask disagreement')
    result = diagnostics.copy()
    result['long_signal'] = result.long_signal & (result.long_active_module_mask == MODULE_BITS[module])
    result['short_signal'] = False
    return result


def replay(diagnostics, settings, rule=None):
    """Isolated Long research replay, with full position/re-entry effects.

    Original ledger/state contract. Disabled-rule equivalence is checked against
    production. Research market exits use next open. Protective stops use ONLY
    survived bars, update at close, and are active on the following bar.
    """
    _validate(diagnostics, settings['atr_multiplier'])
    if diagnostics.short_signal.fillna(False).any():
        raise ValueError('Win Rate V1 is Long only')
    if rule is not None and rule not in EXIT_RULES:
        raise ValueError('Unregistered intervention')
    trades, states, resolutions = [], [], []
    position = pending = None
    next_id = 1
    multiplier = settings['atr_multiplier']
    columns = ['open','high','low','close','atr','htf_ema_fast','long_signal',
               'long_active_module_mask','long_score']
    for offset, bar in enumerate(diagnostics[columns].itertuples()):
        time = bar.Index
        if position is not None and position['pending_reason']:
            reason = position['pending_reason']
            if reason == 'TREND_EXIT' and bar.open <= position['active_stop']:
                reason = 'TREND_AND_STOP_AT_OPEN'
            position['bars_held'] += 1
            _close(position, time, float(bar.open), reason, trades)
            position = None
        if position is None and pending is not None:
            entry = float(bar.open)
            stop = entry - pending['atr']*multiplier
            position = dict(**pending, trade_id=next_id, entry_time=time,
                entry_price=entry, atr_at_entry=pending['atr'], initial_stop=stop,
                active_stop=stop, extreme=entry, bars_held=0, pending_reason=None, mae=0.)
            next_id += 1
        pending = None
        if position is not None:
            p = position
            p['bars_held'] += 1
            stop, extreme = p['active_stop'], p['extreme']
            hit = bar.open <= stop or bar.low <= stop
            trend, next_stop, after = False, np.nan, extreme
            if hit:
                _close(p, time, float(bar.open) if bar.open <= stop else stop, 'ATR_STOP', trades)
            else:
                after = max(extreme, float(bar.high))
                atr = p['atr_at_entry'] if settings['use_locked_atr'] else float(bar.atr)
                next_stop = max(stop, after-atr*multiplier) if np.isfinite(atr) else stop
                mfe = after/p['entry_price']-1
                p['mae'] = min(p['mae'], bar.low/p['entry_price']-1)
                trend = bool(settings['use_trend_exit'] and bar.close < bar.htf_ema_fast)
                pending_reason = 'TREND_EXIT' if trend else None
                if rule:
                    if rule['family'] in ('breakeven', 'lock25') and mfe >= rule['level']:
                        lock = 0. if rule['family'] == 'breakeven' else .25*mfe
                        next_stop = max(next_stop, p['entry_price']*(1+lock))
                    if rule['family'] in ('time', 'early') and p['bars_held'] == rule['bars']:
                        failing = mfe < .005
                        if rule['family'] == 'early':
                            failing = failing and p['mae'] <= -.02 and bar.close < p['entry_price']
                        if failing and pending_reason is None:
                            pending_reason = 'RESEARCH_TIME_EXIT'
                p.update(extreme=after, active_stop=next_stop, pending_reason=pending_reason)
            states.append(dict(trade_id=p['trade_id'], bar_time=time, direction='Long',
                active_stop_at_bar_start=stop, extreme_before=extreme, stop_hit=hit,
                trend_exit_triggered_at_close=trend, extreme_after=after,
                active_stop_for_next_bar=next_stop))
            if hit:
                position = None
        active = bool(pd.notna(bar.long_signal) and bar.long_signal)
        if active:
            resolution = ('IGNORED_POSITION_OPEN' if position is not None else
                          'NO_NEXT_BAR' if offset+1 == len(diagnostics) else
                          'INVALID_ENTRY_PREREQUISITE' if not np.isfinite(bar.atr) or bar.atr < 0 else None)
            resolutions.append(dict(signal_time=time, direction='Long',
                active_module_mask=int(bar.long_active_module_mask), module_score=int(bar.long_score),
                position_state_at_signal_close='Long' if position is not None else 'FLAT',
                active_trade_id_at_signal_close=position['trade_id'] if position else pd.NA,
                resolution=resolution))
            if resolution is None:
                pending = dict(direction='Long', signal_time=time, signal_available_at='signal bar close',
                    atr=float(bar.atr), active_module_mask=int(bar.long_active_module_mask), module_score=int(bar.long_score))
    if position is not None:
        row = _trade_row(position)
        row.update(exit_time=pd.NaT, exit_price=np.nan, exit_reason='CENSORED_AT_END',
                   closed=False, censored_at_end=True, return_pct=np.nan)
        trades.append(row)
    fills = {t['signal_time']: t for t in trades}
    for r in resolutions:
        t = fills.get(r['signal_time'])
        r.update(trade_id=pd.NA, entry_time=pd.NaT, closed=pd.NA, censored_at_end=pd.NA)
        if t:
            r.update({k:t[k] for k in ('trade_id', 'entry_time', 'closed', 'censored_at_end')})
            r['resolution'] = 'FILLED' if t['closed'] else 'FILLED_BUT_CENSORED_AT_END'
    dtype = diagnostics.index.dtype
    return (SwingBacktestResult(_table(trades, TRADE_SCHEMA, dtype), _table(states, STATE_SCHEMA, dtype)),
            _table(resolutions, RECONCILIATION_SCHEMA, dtype))


def metrics(trades):
    closed = trades.loc[trades.closed.fillna(False)]
    r = closed.return_pct.dropna()
    w, l = r[r > 0], r[r < 0]
    gross_loss = -l.sum()
    return dict(trades=len(r), censored=int((~trades.closed).sum()), winners=len(w), losers=len(l),
        ties=int((r == 0).sum()), win_rate=len(w)/len(r) if len(r) else np.nan,
        mean_winner=w.mean(), median_winner=w.median(), mean_loser=l.mean(), median_loser=l.median(),
        average_return=r.mean(), median_return=r.median(), expectancy=r.mean(),
        profit_factor=w.sum()/gross_loss if gross_loss > 0 else np.inf if w.sum() > 0 else np.nan,
        average_holding=closed.bars_held.mean(), median_holding=closed.bars_held.median(),
        worst_return=r.min(), p05_return=r.quantile(.05),
        expected_shortfall05=r[r <= r.quantile(.05)].mean(),
        top5_share_gross_profit=w.nlargest(5).sum()/w.sum() if w.sum() else np.nan)


def grouped_metrics(trades, keys):
    rows = []
    for values, part in trades.groupby(keys, dropna=False, observed=True):
        values = values if isinstance(values, tuple) else (values,)
        rows.append(dict(zip(keys, values), **metrics(part)))
    return pd.DataFrame(rows, columns=[*keys, *metrics(trades.iloc[:0])])


def path_observations(diagnostics, lifecycle):
    """Bounded threshold timing; one-based holding bars; no exit-bar future close.

    'mae_before_positive' uses completed bars BEFORE the first positive close,
    excluding that bar's intraday ordering. Full winner MAE is separately retained.
    """
    rows = []
    for t in lifecycle.itertuples():
        start = diagnostics.index.get_loc(t.entry_time)
        end = diagnostics.index.get_loc(t.exit_time) if t.closed else len(diagnostics)-1
        mfe_lo = mfe_hi = 0.
        mae_lo = mae_hi = 0.
        early_mae = early_mfe_upper = 0.
        first_positive = np.nan
        pre_positive_mae = 0.
        hits_known, hits_possible = {}, {}
        flat10 = end-start+1 >= 10
        for j in range(start, end+1):
            b = diagnostics.iloc[j]
            age = j-start+1
            exiting = t.closed and j == end
            known = [float(b.open)/t.entry_price-1]
            possible = list(known)
            full = not exiting
            if exiting:
                known.append(t.exit_price/t.entry_price-1)
                possible = list(known)
                if t.exit_timing == 'INTRABAR_STOP':
                    possible += [b.high/t.entry_price-1, b.low/t.entry_price-1]
            else:
                known += [b.high/t.entry_price-1, b.low/t.entry_price-1, b.close/t.entry_price-1]
                possible = list(known)
            mfe_lo, mfe_hi = max(mfe_lo, max(known)), max(mfe_hi, max(possible))
            mae_hi, mae_lo = min(mae_hi, min(known)), min(mae_lo, min(possible))
            if age <= 3:
                early_mae = min(early_mae, min(known))
                early_mfe_upper = max(early_mfe_upper, max(possible))
            if age <= 10 and (not full or min(known) < -.01 or max(known) >= .005):
                flat10 = False
            if full and np.isnan(first_positive):
                if b.close > t.entry_price:
                    first_positive = age
                else:
                    pre_positive_mae = min(pre_positive_mae, min(known))
            for level in THRESHOLDS:
                if mfe_lo >= level and level not in hits_known:
                    hits_known[level] = age
                if mfe_hi >= level and level not in hits_possible:
                    hits_possible[level] = age
        row = dict(trade_id=t.trade_id, early_mae_known=early_mae, early_mfe_upper=early_mfe_upper,
            first_positive_close_bar=first_positive, mae_before_positive_close=pre_positive_mae,
            flat_first10=flat10)
        for level in THRESHOLDS:
            tag = f'{level:.3f}'
            row[f'first_known_{tag}'] = hits_known.get(level, np.nan)
            row[f'first_possible_{tag}'] = hits_possible.get(level, np.nan)
        rows.append(row)
    cols = ['trade_id','early_mae_known','early_mfe_upper','first_positive_close_bar',
            'mae_before_positive_close','flat_first10'] + [f'{kind}_{level:.3f}' for level in THRESHOLDS
            for kind in ('first_known','first_possible')]
    return lifecycle.merge(pd.DataFrame(rows, columns=cols), on='trade_id', validate='one_to_one')


def classify_losses(trades):
    result = trades.loc[trades.closed & (trades.return_pct < 0)].copy()
    def category(t):
        lo, hi = t.in_trade_mfe_lower, t.in_trade_mfe_upper
        if not np.isfinite(lo) or not np.isfinite(hi):
            return 'UNCERTAIN_PATH'
        if lo >= .02:
            return 'GIVEBACK_LOSER'
        if hi >= .02:
            return 'UNCERTAIN_PATH'
        if lo >= .005:
            return 'SMALL_PROFIT_GIVEBACK'
        if hi >= .005:
            return 'UNCERTAIN_PATH'
        if t.flat_first10:
            return 'DEAD_TRADE'
        if t.early_mae_known <= -.02 and t.early_mfe_upper < .005:
            return 'IMMEDIATE_FAILURE'
        if hi < .005:
            return 'NEVER_WORKED'
        return 'STOP_TIMING_OTHER'
    result['category'] = [category(t) for t in result.itertuples()]
    return result


def paired_effects(a, b):
    """Match actual signal provenance, never trade ordering after exit changes."""
    keys = ['module', 'symbol', 'signal_time']
    cols = keys+['closed','return_pct']
    pair = a[cols].merge(b[cols], on=keys, how='outer', suffixes=('_a','_b'), indicator=True,
                         validate='one_to_one')
    both = (pair._merge == 'both') & pair.closed_a.astype('boolean').fillna(False) & pair.closed_b.astype('boolean').fillna(False)
    pair['matched_closed'] = both
    pair['loser_to_win'] = both & (pair.return_pct_a < 0) & (pair.return_pct_b > 0)
    pair['loser_to_nonloss'] = both & (pair.return_pct_a < 0) & (pair.return_pct_b >= 0)
    pair['winner_destroyed'] = both & (pair.return_pct_a > 0) & (pair.return_pct_b <= 0)
    return pair


def partition(trades, split):
    """Purge boundary-crossing outcomes from discovery selection."""
    split = pd.Timestamp(split)
    out = trades.copy()
    out['partition'] = np.where(out.signal_time >= split, 'ENTRY HOLDOUT / EXIT-USED HISTORY',
        np.where(out.closed & (out.exit_time < split), 'IN-SAMPLE', 'BOUNDARY / CENSORED'))
    out['year'] = out.signal_time.dt.year
    out['holding_bucket'] = pd.cut(out.bars_held, [0, 3, 5, 10, 15, np.inf],
                                  labels=['1-3','4-5','6-10','11-15','16+']).astype(str)
    return out


def screen(a, b):
    """Fixed descriptive screen, not significance or untouched confirmation."""
    x, y = metrics(a), metrics(b)
    checks = dict(sample=y['trades'] >= 100, count=y['trades'] >= .7*x['trades'],
        wr=y['win_rate'] >= x['win_rate']+.02,
        expectancy=y['expectancy'] > 0 and y['expectancy'] >= .9*x['expectancy'],
        pf=y['profit_factor'] > 1 and y['profit_factor'] >= .9*x['profit_factor'],
        winner_size=y['mean_winner'] >= .75*x['mean_winner'])
    agreements = {}
    for key, minimum in [('symbol', 10), ('year', 3)]:
        aa, bb = grouped_metrics(a, [key]), grouped_metrics(b, [key])
        p = aa.merge(bb, on=key, suffixes=('_a','_b'))
        p = p[(p.trades_a >= 5) & (p.trades_b >= 5)]
        agreement = ((p.win_rate_b >= p.win_rate_a) & (p.expectancy_b >= .9*p.expectancy_a)).mean()
        checks[key] = len(p) >= minimum and agreement >= .6
        agreements[key+'_agreement'] = agreement
    r = b.loc[b.closed, 'return_pct'].dropna()
    tail = r.drop(r[r > 0].nlargest(5).index).mean()
    checks['tail'] = tail > 0
    return dict(survived=all(checks.values()), failed_checks=','.join(k for k,v in checks.items() if not v),
                top5_removed_expectancy=tail, **agreements)


def frontier_targets(summary, targets=(.5,.6,.7,.75)):
    rows = []
    for module in MODULE_BITS:
        part = summary[summary.module == module]
        for target in targets:
            reached = part[part.win_rate >= target]
            robust = reached[reached.status == 'ROBUST']
            leader = robust.sort_values(['expectancy','scenario'], ascending=[False,True]).head(1)
            rows.append(dict(module=module,target=target,any_predefined_reached=bool(len(reached)),
                robust_reached=bool(len(robust)),scenario=leader.scenario.iloc[0] if len(leader) else 'UNSUPPORTED',
                trades=int(leader.trades.iloc[0]) if len(leader) else 0,
                expectancy=leader.expectancy.iloc[0] if len(leader) else np.nan,
                profit_factor=leader.profit_factor.iloc[0] if len(leader) else np.nan))
    return pd.DataFrame(rows)
