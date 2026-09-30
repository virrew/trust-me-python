"""Isolated Long research policies; production and frozen WR sources are immutable.

The small execution loop follows WR V1's ledger/trace convention and shares the
backtest's accounting/schema helpers. It is kept here to avoid invalidating the
source identity of completed WR sessions. No lifecycle/outcome engine is copied.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.backtest import (TRADE_SCHEMA, STATE_SCHEMA, RECONCILIATION_SCHEMA,
                         SwingBacktestResult, _validate, _table, _trade_row, _close)
from src.entry_research_analysis import cohorts, bin_numbers
from src.win_rate_research_analysis import pure_stream


def known_state(previous, *, age, entry, high, low, close):
    """Only call at a survived close. Strict new high; ties do not reset age."""
    old_mfe = previous.get('running_mfe', 0.)
    mfe = max(old_mfe, high / entry - 1)
    new = mfe > old_mfe
    peak_age = age if new else previous.get('last_high_age', 0)
    ret = close / entry - 1
    return dict(age=age, running_return=ret, running_mfe=mfe,
                running_mae=min(previous.get('running_mae', 0.), low / entry - 1),
                new_mfe_high=new, last_high_age=peak_age,
                bars_since_mfe_high=age-peak_age, giveback=mfe-ret,
                giveback_fraction=(mfe-ret)/mfe if mfe > 0 else np.nan,
                mfe_retention=ret/mfe if mfe > 0 else np.nan,
                close_relative_entry=ret, close_relative_peak=(1+ret)/(1+mfe)-1)


def policy_action(state, rule, entry, next_stop):
    """Return a next-bar stop and/or next-open market exit, never a same-bar fill."""
    if rule is None:
        return next_stop, False
    family = rule['family']
    if family not in ('giveback', 'stalled', 'adaptive'):
        raise ValueError('Unknown lifecycle policy')
    if state['running_mfe'] < rule['level']:
        return next_stop, False
    stalled = state['bars_since_mfe_high'] >= rule['stall_bars']
    if family == 'adaptive':
        if stalled:
            next_stop = max(next_stop, entry*(1+rule['lock_fraction']*state['running_mfe']))
        return next_stop, False
    trigger = state['giveback_fraction'] >= rule['giveback_fraction']
    return next_stop, bool(trigger and (family == 'giveback' or stalled))


def research_stream(diagnostics, module, entry_rule=None):
    """Reuse existing predicates. Relaxed rows keep their actual mask/score (0).

    A module-sole-blocker cohort is an experimental opportunity stream, never a
    Pure activation. No core, score, diagnostic or production mask is rewritten.
    """
    d = pure_stream(diagnostics, module)
    d['research_signal_source'] = 'PURE_APPROVED'
    if entry_rule:
        if entry_rule['family'] == 'relax_price' and module == 'breakout':
            c, _ = cohorts(diagnostics, module)
            added = c.single_blocker & c.sole_blocker.eq('bo_long_fail_price')
            d['long_signal'] |= added
            d.loc[added, 'research_signal_source'] = 'EXPERIMENTAL_SOLE_PRICE_BLOCKER'
        elif entry_rule['family'] == 'reject_bin':
            bins = bin_numbers(d[entry_rule['feature']], entry_rule['edges'])
            d['long_signal'] &= bins.ne(entry_rule['bin'])
        else:
            raise ValueError('Unsupported entry intervention')
    return d


def replay(diagnostics, settings, rule=None):
    """Causal full-stream replay including changed occupancy and subsequent fills."""
    _validate(diagnostics, settings['atr_multiplier'])
    if diagnostics.short_signal.fillna(False).any():
        raise ValueError('Strategy Improvement V1 is Long only')
    if rule is not None:
        if (rule['family'] not in ('giveback', 'stalled', 'adaptive')
                or not .01 <= rule['level'] <= .04
                or not 0 < rule['giveback_fraction'] < 1
                or rule['stall_bars'] not in (3, 5, 10)
                or rule['lock_fraction'] != .1):
            raise ValueError('Invalid finite lifecycle rule')
    trades, states, resolutions = [], [], []
    position = pending = None
    next_id = 1
    multiplier = settings['atr_multiplier']
    columns = ['open', 'high', 'low', 'close', 'atr', 'htf_ema_fast',
               'long_signal', 'long_active_module_mask', 'long_score']
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
            stop = entry-pending['atr']*multiplier
            position = dict(**pending, trade_id=next_id, entry_time=time, entry_price=entry,
                            atr_at_entry=pending['atr'], initial_stop=stop, active_stop=stop,
                            extreme=entry, bars_held=0, pending_reason=None, known={})
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
                state = known_state(p['known'], age=p['bars_held'], entry=p['entry_price'],
                                    high=bar.high, low=bar.low, close=bar.close)
                next_stop, market_exit = policy_action(state, rule, p['entry_price'], next_stop)
                trend = bool(settings['use_trend_exit'] and bar.close < bar.htf_ema_fast)
                reason = 'TREND_EXIT' if trend else 'RESEARCH_LIFECYCLE_EXIT' if market_exit else None
                p.update(extreme=after, active_stop=next_stop, pending_reason=reason, known=state)
            states.append(dict(trade_id=p['trade_id'], bar_time=time, direction='Long',
                               active_stop_at_bar_start=stop, extreme_before=extreme, stop_hit=hit,
                               trend_exit_triggered_at_close=trend, extreme_after=after,
                               active_stop_for_next_bar=next_stop))
            if hit:
                position = None
        if pd.notna(bar.long_signal) and bar.long_signal:
            resolution = ('IGNORED_POSITION_OPEN' if position is not None else
                          'NO_NEXT_BAR' if offset+1 == len(diagnostics) else
                          'INVALID_ENTRY_PREREQUISITE' if not np.isfinite(bar.atr) or bar.atr < 0 else None)
            resolutions.append(dict(signal_time=time, direction='Long',
                                    active_module_mask=int(bar.long_active_module_mask),
                                    module_score=int(bar.long_score),
                                    position_state_at_signal_close='Long' if position else 'FLAT',
                                    active_trade_id_at_signal_close=position['trade_id'] if position else pd.NA,
                                    resolution=resolution))
            if resolution is None:
                pending = dict(direction='Long', signal_time=time, signal_available_at='signal bar close',
                               atr=float(bar.atr), active_module_mask=int(bar.long_active_module_mask),
                               module_score=int(bar.long_score))
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
            r.update({k: t[k] for k in ('trade_id', 'entry_time', 'closed', 'censored_at_end')})
            r['resolution'] = 'FILLED' if t['closed'] else 'FILLED_BUT_CENSORED_AT_END'
    dtype = diagnostics.index.dtype
    return (SwingBacktestResult(_table(trades, TRADE_SCHEMA, dtype), _table(states, STATE_SCHEMA, dtype)),
            _table(resolutions, RECONCILIATION_SCHEMA, dtype))
