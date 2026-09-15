"""Retrospective diagnostics of actual research holding periods.

No OHLC path is reconstructed. Intrabar stop bars contribute known open/fill
endpoints and possible full-bar extremes as bounds, never as exact excursions.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.backtest import TRADE_SCHEMA, STATE_SCHEMA, SwingBacktestResult, _table


LIFECYCLE_SCHEMA = {
    **TRADE_SCHEMA,
    "observed_through": "datetime64[ns]",
    "exit_timing": "object", "exit_stop_source": "object",
    "intrabar_exit_uncertain": "bool", "excursion_data_valid": "bool",
    "in_trade_mfe": "float64", "in_trade_mae": "float64",
    "in_trade_mfe_lower": "float64", "in_trade_mfe_upper": "float64",
    "in_trade_mae_lower": "float64", "in_trade_mae_upper": "float64",
    "mfe_bar": "datetime64[ns]", "bars_to_mfe": "Int64",
    "realized_to_in_trade_mfe": "float64",
    "in_trade_mfe_minus_realized": "float64",
    "post_exit_horizon": "int64", "post_exit_window_complete": "bool",
    "post_exit_observed_bars": "int64",
    "post_exit_mfe_from_entry": "float64",
}

STOP_PATH_SCHEMA = {
    **STATE_SCHEMA,
    "stop_source_at_bar_start": "object", "stop_moved_at_close": "bool",
    "exit_at_open": "bool",
}


def trade_lifecycle_diagnostics(
    diagnostics: pd.DataFrame, backtest: SwingBacktestResult, *,
    post_exit_horizon: int = 20,
) -> dict[str, pd.DataFrame]:
    """Consume the ledger and trace from the SAME dataset/backtest invocation.

    Excursions include zero at entry, full surviving bars, and exit price.
    MFE is nonnegative and MAE nonpositive; returns are fractions, not percent
    points. Point estimates exist only when lower == upper. Censored values
    describe the observed holding period only, not the eventual lifetime.

    Post-exit MFE uses actual entry as reference over the remainder of the
    signal-anchored horizon. An intrabar exit's remaining bar is excluded;
    an open exit's bar is included. NA means no eligible bars/incomplete data.
    """
    if isinstance(post_exit_horizon, bool) or not isinstance(post_exit_horizon, int) or post_exit_horizon < 1:
        raise ValueError("post_exit_horizon must be a positive integer")
    rows, paths = [], []
    index = diagnostics.index
    for trade in backtest.trades.to_dict("records"):
        start = index.get_loc(trade["entry_time"])
        end = index.get_loc(trade["exit_time"]) if trade["closed"] else len(index) - 1
        trace = backtest.state[backtest.state.trade_id == trade["trade_id"]]
        states = {row["bar_time"]: row for row in trace.to_dict("records")}
        sign = 1 if trade["direction"] == "Long" else -1
        entry = trade["entry_price"]
        known = [(0.0, start)]
        possible = [0.0]
        valid = bool(np.isfinite(entry) and entry > 0)
        uncertain = False
        timing = "CENSORED"
        exit_source = None
        for offset in range(start, end + 1):
            time = index[offset]
            bar = diagnostics.iloc[offset]
            state = states.get(time)
            exiting = trade["closed"] and offset == end
            # Trend fills have no row in the original state trace.
            if state is None:
                previous = states[index[offset - 1]]
                state = {
                    "trade_id": trade["trade_id"], "bar_time": time,
                    "direction": trade["direction"],
                    "active_stop_at_bar_start": previous["active_stop_for_next_bar"],
                    "extreme_before": previous["extreme_after"],
                    "stop_hit": trade["exit_reason"] == "TREND_AND_STOP_AT_OPEN",
                    "trend_exit_triggered_at_close": False,
                    "extreme_after": previous["extreme_after"],
                    "active_stop_for_next_bar": np.nan,
                }
            stop = state["active_stop_at_bar_start"]
            source = "INITIAL_STOP" if stop == trade["initial_stop"] else "TRAILING_STOP"
            gap = (bar.open <= stop if sign == 1 else bar.open >= stop)
            at_open = bool(exiting and (trade["exit_reason"] != "ATR_STOP" or gap))
            paths.append({
                **state, "stop_source_at_bar_start": source,
                "stop_moved_at_close": bool(
                    pd.notna(state["active_stop_for_next_bar"])
                    and state["active_stop_for_next_bar"] != stop),
                "exit_at_open": at_open,
            })
            if exiting:
                timing = "OPEN" if at_open else "INTRABAR_STOP"
                uncertain = not at_open
                if trade["exit_reason"] in ("ATR_STOP", "TREND_AND_STOP_AT_OPEN"):
                    exit_source = source
            prices = [bar.open]
            if exiting:
                prices.append(trade["exit_price"])
            if not exiting:
                prices.extend([bar.high, bar.low, bar.close])
            # Validate only information used by the excursion calculation.
            potential_prices = prices + ([bar.high, bar.low] if uncertain else [])
            valid = valid and bool(np.isfinite(potential_prices).all())
            if valid:
                known.extend((sign * (float(price) / entry - 1), offset) for price in prices)
                possible.extend(sign * (float(price) / entry - 1) for price in potential_prices)

        mfe_lo = max(value for value, _ in known) if valid else np.nan
        mae_hi = min(value for value, _ in known) if valid else np.nan
        mfe_hi = max(possible) if valid else np.nan
        mae_lo = min(possible) if valid else np.nan
        mfe = mfe_lo if mfe_lo == mfe_hi else np.nan
        mae = mae_lo if mae_lo == mae_hi else np.nan
        mfe_position = next((pos for value, pos in known if value == mfe), None)
        realized = trade["return_pct"]
        anchor = index.get_loc(trade["signal_time"])
        horizon_end = anchor + post_exit_horizon
        complete = horizon_end < len(index)
        post_start = end + (0 if timing == "OPEN" else 1)
        post = diagnostics.iloc[post_start:min(horizon_end + 1, len(index))] if trade["closed"] else diagnostics.iloc[:0]
        post_mfe = np.nan
        if complete and len(post) and valid:
            values = post.high if sign == 1 else post.low
            if np.isfinite(values).all():
                post_mfe = max(0.0, float((sign * (values / entry - 1)).max()))
        rows.append({
            **trade, "observed_through": index[end], "exit_timing": timing,
            "exit_stop_source": exit_source, "intrabar_exit_uncertain": uncertain,
            "excursion_data_valid": valid,
            "in_trade_mfe": mfe, "in_trade_mae": mae,
            "in_trade_mfe_lower": mfe_lo, "in_trade_mfe_upper": mfe_hi,
            "in_trade_mae_lower": mae_lo, "in_trade_mae_upper": mae_hi,
            "mfe_bar": index[mfe_position] if mfe_position is not None else pd.NaT,
            "bars_to_mfe": mfe_position - start if mfe_position is not None else pd.NA,
            "realized_to_in_trade_mfe": realized / mfe if mfe > 0 else np.nan,
            "in_trade_mfe_minus_realized": mfe - realized,
            "post_exit_horizon": post_exit_horizon,
            "post_exit_window_complete": complete,
            "post_exit_observed_bars": len(post),
            "post_exit_mfe_from_entry": post_mfe,
        })
    return {
        "trade_lifecycle": _table(rows, LIFECYCLE_SCHEMA, index.dtype),
        "trade_stop_path": _table(paths, STOP_PATH_SCHEMA, index.dtype),
    }
