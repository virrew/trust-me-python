"""Causal, deterministic execution model for Trust Me Swing research.

This module consumes final signal diagnostics; it does not recreate entry or
indicator logic.  Its fills are an explicit research convention, not an
emulation of TradingView's broker emulator.
"""

from __future__ import annotations

from typing import NamedTuple

import numpy as np
import pandas as pd


TRADE_SCHEMA = {
    "trade_id": "int64",
    "direction": "object",
    "signal_time": "datetime64[ns]",
    "signal_available_at": "object",
    "entry_time": "datetime64[ns]",
    "entry_price": "float64",
    "atr_at_entry": "float64",
    "initial_stop": "float64",
    "active_module_mask": "int64",
    "module_score": "int64",
    "exit_time": "datetime64[ns]",
    "exit_price": "float64",
    "exit_reason": "object",
    "bars_held": "int64",
    "closed": "bool",
    "censored_at_end": "bool",
    "return_pct": "float64",
}

STATE_SCHEMA = {
    "trade_id": "int64",
    "bar_time": "datetime64[ns]",
    "direction": "object",
    "active_stop_at_bar_start": "float64",
    "extreme_before": "float64",
    "stop_hit": "bool",
    "trend_exit_triggered_at_close": "bool",
    "extreme_after": "float64",
    "active_stop_for_next_bar": "float64",
}

SUMMARY_SCHEMA = {
    "number_of_trades": "int64", "wins": "int64", "losses": "int64",
    "win_rate": "float64", "mean_return": "float64",
    "median_return": "float64", "average_win": "float64",
    "average_loss": "float64", "profit_factor": "float64",
    "expectancy": "float64",
}


class SwingBacktestResult(NamedTuple):
    """Stable pair of the trade ledger and per-active-bar state trace."""

    trades: pd.DataFrame
    state: pd.DataFrame


def _empty(schema: dict[str, str], timestamp_dtype) -> pd.DataFrame:
    return pd.DataFrame({
        name: pd.Series(dtype=timestamp_dtype if dtype == "datetime64[ns]" else dtype)
        for name, dtype in schema.items()
    })


def _table(rows, schema, timestamp_dtype):
    if not rows:
        return _empty(schema, timestamp_dtype)
    result = pd.DataFrame(rows)
    for name, dtype in schema.items():
        target = timestamp_dtype if dtype == "datetime64[ns]" else dtype
        result[name] = pd.Series(pd.array(result[name], dtype=target), index=result.index)
    return result[list(schema)]


def _validate(diagnostics: pd.DataFrame, atr_multiplier: float) -> None:
    if not isinstance(diagnostics.index, pd.DatetimeIndex):
        raise ValueError("diagnostics requires a DatetimeIndex")
    if not diagnostics.index.is_unique or not diagnostics.index.is_monotonic_increasing:
        raise ValueError("diagnostics requires a unique increasing DatetimeIndex")
    required = {"open", "high", "low", "close", "atr", "htf_ema_fast",
                "long_signal", "short_signal", "long_active_module_mask",
                "short_active_module_mask", "long_score", "short_score"}
    missing = required.difference(diagnostics.columns)
    if missing:
        raise ValueError(f"diagnostics missing columns: {sorted(missing)}")
    for column in ("open", "high", "low", "close", "atr", "htf_ema_fast"):
        if not pd.api.types.is_numeric_dtype(diagnostics[column]):
            raise ValueError(f"{column} must be numeric")
    if not np.isfinite(atr_multiplier) or atr_multiplier <= 0:
        raise ValueError("atr_multiplier must be positive and finite")


def run_swing_backtest(
    diagnostics: pd.DataFrame, *, atr_multiplier: float = 2.5,
    use_locked_atr: bool = False,
) -> SwingBacktestResult:
    """Simulate one-at-a-time Swing trades from final diagnostic signals.

    A signal is known at its bar close and fills at the following open. ATR on
    the signal bar sets the initial stop.  A surviving bar's completed OHLC and
    (for dynamic mode) ATR can only set the stop for the following bar.
    """
    _validate(diagnostics, atr_multiplier)
    timestamp_dtype = diagnostics.index.dtype
    trades, states = [], []
    position = None
    pending_entry = None
    next_trade_id = 1

    for offset, (bar_time, bar) in enumerate(diagnostics.iterrows()):
        # A trend decision made at the preceding close exits at this open.
        if position is not None and position["trend_pending"]:
            gap_stop = ((position["direction"] == "Long" and
                         bar.open <= position["active_stop"]) or
                        (position["direction"] == "Short" and
                         bar.open >= position["active_stop"]))
            reason = "TREND_AND_STOP_AT_OPEN" if gap_stop else "TREND_EXIT"
            position["bars_held"] += 1
            _close(position, bar_time, float(bar.open), reason, trades)
            position = None

        # Only signals observed while flat can be pending entries.
        if position is None and pending_entry is not None:
            direction = pending_entry["direction"]
            entry_price = float(bar.open)
            atr_entry = pending_entry["atr"]
            stop = (entry_price - atr_entry * atr_multiplier if direction == "Long"
                    else entry_price + atr_entry * atr_multiplier)
            position = {
                **pending_entry, "trade_id": next_trade_id,
                "entry_time": bar_time, "entry_price": entry_price,
                "atr_at_entry": atr_entry, "initial_stop": stop,
                "active_stop": stop, "extreme": entry_price,
                "entry_offset": offset, "bars_held": 0, "trend_pending": False,
            }
            next_trade_id += 1
        pending_entry = None

        if position is not None:
            position["bars_held"] += 1
            direction = position["direction"]
            stop = position["active_stop"]
            extreme_before = position["extreme"]
            gap = ((direction == "Long" and bar.open <= stop) or
                   (direction == "Short" and bar.open >= stop))
            touched = ((direction == "Long" and bar.low <= stop) or
                       (direction == "Short" and bar.high >= stop))
            stop_hit = bool(gap or touched)
            trend = False
            extreme_after = extreme_before
            next_stop = np.nan
            if stop_hit:
                exit_price = float(bar.open) if gap else float(stop)
                _close(position, bar_time, exit_price, "ATR_STOP", trades)
            else:
                extreme_after = (max(extreme_before, float(bar.high)) if direction == "Long"
                                 else min(extreme_before, float(bar.low)))
                atr_for_stop = position["atr_at_entry"] if use_locked_atr else float(bar.atr)
                if np.isfinite(atr_for_stop):
                    candidate = (extreme_after - atr_for_stop * atr_multiplier
                                 if direction == "Long" else
                                 extreme_after + atr_for_stop * atr_multiplier)
                    next_stop = (max(stop, candidate) if direction == "Long"
                                 else min(stop, candidate))
                else:
                    next_stop = stop
                trend = bool((direction == "Long" and bar.close < bar.htf_ema_fast) or
                             (direction == "Short" and bar.close > bar.htf_ema_fast))
                position["extreme"] = extreme_after
                position["active_stop"] = next_stop
                position["trend_pending"] = trend
            states.append({
                "trade_id": position["trade_id"], "bar_time": bar_time,
                "direction": direction, "active_stop_at_bar_start": stop,
                "extreme_before": extreme_before, "stop_hit": stop_hit,
                "trend_exit_triggered_at_close": trend,
                "extreme_after": extreme_after,
                "active_stop_for_next_bar": next_stop,
            })
            if stop_hit:
                position = None

        # A bar's final signals are inspected only after all bar processing.
        if position is None and offset + 1 < len(diagnostics):
            long_signal = bool(pd.notna(bar.long_signal) and bar.long_signal)
            short_signal = bool(pd.notna(bar.short_signal) and bar.short_signal)
            if long_signal != short_signal:
                direction = "Long" if long_signal else "Short"
                atr_value = float(bar.atr)
                if np.isfinite(atr_value) and atr_value >= 0:
                    prefix = direction.lower()
                    pending_entry = {
                        "direction": direction, "signal_time": bar_time,
                        "signal_available_at": "signal bar close", "atr": atr_value,
                        "active_module_mask": int(bar[f"{prefix}_active_module_mask"]),
                        "module_score": int(bar[f"{prefix}_score"]),
                    }

    if position is not None:
        row = _trade_row(position)
        row.update({"exit_time": pd.NaT, "exit_price": np.nan,
                    "exit_reason": "CENSORED_AT_END", "closed": False,
                    "censored_at_end": True, "return_pct": np.nan})
        trades.append(row)
    return SwingBacktestResult(_table(trades, TRADE_SCHEMA, timestamp_dtype),
                               _table(states, STATE_SCHEMA, timestamp_dtype))


def _trade_row(position):
    return {name: position[name] for name in (
        "trade_id", "direction", "signal_time", "signal_available_at",
        "entry_time", "entry_price", "atr_at_entry", "initial_stop",
        "active_module_mask", "module_score", "bars_held")}


def _close(position, time, price, reason, trades):
    sign = 1 if position["direction"] == "Long" else -1
    row = _trade_row(position)
    row.update({"exit_time": time, "exit_price": price, "exit_reason": reason,
                "closed": True, "censored_at_end": False,
                "return_pct": sign * (price / position["entry_price"] - 1)})
    trades.append(row)


def summarize_trades(trades: pd.DataFrame) -> pd.DataFrame:
    """Return one-row performance statistics for closed trades only."""
    missing = {"closed", "return_pct"}.difference(trades.columns)
    if missing:
        raise ValueError(f"trades missing columns: {sorted(missing)}")
    returns = trades.loc[trades["closed"].fillna(False), "return_pct"].dropna().astype(float)
    wins, losses = returns[returns > 0], returns[returns < 0]
    gross_win, gross_loss = float(wins.sum()), float(-losses.sum())
    n = len(returns)
    profit_factor = (gross_win / gross_loss if gross_loss > 0 else
                     np.inf if gross_win > 0 else np.nan)
    row = {
        "number_of_trades": n, "wins": len(wins), "losses": len(losses),
        "win_rate": float(len(wins) / n) if n else np.nan,
        "mean_return": float(returns.mean()), "median_return": float(returns.median()),
        "average_win": float(wins.mean()), "average_loss": float(losses.mean()),
        "profit_factor": profit_factor, "expectancy": float(returns.mean()),
    }
    return pd.DataFrame([row]).astype(SUMMARY_SCHEMA)
