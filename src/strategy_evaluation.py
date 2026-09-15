"""Descriptive evaluation of Trust Me research trades and opportunities.

The layer composes existing diagnostics, historical outcomes, and the Swing
research backtest.  It does not alter signals, execution, or strategy rules.
Blocked opportunities have no fill or PnL; their forward price outcomes are
reported separately from realized trade returns.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from src.backtest import run_swing_backtest
from src.diagnostics_analysis import module_opportunity_events
from src.historical_outcomes import (
    DEFAULT_HORIZONS, OBSERVATION_SCHEMA, calculate_historical_outcomes,
)


MODULE_BITS = {"Pullback": 1, "Breakout": 2, "Squeeze": 4, "Mean Reversion": 8}

PERFORMANCE_SCHEMA = {
    "group_type": "object", "direction": "object", "module": "object",
    "number_of_trades": "int64", "wins": "int64", "losses": "int64",
    "win_rate": "float64", "mean_return": "float64",
    "median_return": "float64", "average_win": "float64",
    "average_loss": "float64", "profit_factor": "float64",
    "expectancy": "float64",
}

COMPARISON_SCHEMA = {
    "direction": "object", "module": "object", "evaluation_group": "object",
    "sample_size": "int64", "complete_samples": "int64",
    "censored_samples": "int64", "win_rate": "float64",
    "mean_forward_return": "float64", "median_forward_return": "float64",
    "mean_mfe": "float64", "median_mfe": "float64",
    "mean_mae": "float64", "median_mae": "float64",
    "profit_factor": "float64", "expectancy": "float64",
}

EXCURSION_SCHEMA = {
    "trade_id": "int64", "direction": "object", "module": "object",
    "signal_time": "datetime64[ns]", "entry_time": "datetime64[ns]",
    "exit_time": "datetime64[ns]", "closed": "bool",
    "realized_return": "float64", "mfe": "float64", "mae": "float64",
    "realized_to_mfe": "float64", "mfe_minus_realized": "float64",
}

EXCURSION_SUMMARY_SCHEMA = {
    "direction": "object", "module": "object", "sample_size": "int64",
    "mean_realized_return": "float64", "mean_mfe": "float64",
    "mean_mae": "float64", "mean_realized_to_mfe": "float64",
    "mean_mfe_minus_realized": "float64",
}


def _empty(schema: dict[str, str], timestamp_dtype="datetime64[ns]") -> pd.DataFrame:
    return pd.DataFrame({
        name: pd.Series(dtype=timestamp_dtype if dtype == "datetime64[ns]" else dtype)
        for name, dtype in schema.items()
    })


def _metrics(returns: pd.Series) -> dict[str, float | int]:
    values = returns.dropna().astype(float)
    wins, losses = values[values > 0], values[values < 0]
    gross_win, gross_loss = float(wins.sum()), float(-losses.sum())
    n = len(values)
    return {
        "number_of_trades": n, "wins": len(wins), "losses": len(losses),
        "win_rate": float(len(wins) / n) if n else np.nan,
        "mean_return": float(values.mean()), "median_return": float(values.median()),
        "average_win": float(wins.mean()), "average_loss": float(losses.mean()),
        "profit_factor": (gross_win / gross_loss if gross_loss else
                          np.inf if gross_win else np.nan),
        "expectancy": float(values.mean()),
    }


def trade_performance(trades: pd.DataFrame) -> pd.DataFrame:
    """Return total, direction, module, and direction/module trade metrics.

    Multi-module trades are attributed to every active module and therefore
    module rows must not be summed to obtain the total.
    """
    required = {"direction", "active_module_mask", "closed", "return_pct"}
    missing = required.difference(trades.columns)
    if missing:
        raise ValueError(f"trades missing columns: {sorted(missing)}")
    closed = trades[trades.closed.fillna(False)].copy()
    rows = []

    def add(group_type, direction, module, source):
        rows.append({"group_type": group_type, "direction": direction,
                     "module": module, **_metrics(source.return_pct)})

    add("Total", "All", "All", closed)
    for direction in ("Long", "Short"):
        add("Direction", direction, "All", closed[closed.direction == direction])
    for module, bit in MODULE_BITS.items():
        selected = closed[(closed.active_module_mask.astype("int64") & bit) != 0]
        add("Module", "All", module, selected)
        for direction in ("Long", "Short"):
            add("Direction / Module", direction, module,
                selected[selected.direction == direction])
    return pd.DataFrame(rows).astype(PERFORMANCE_SCHEMA)


def _evaluation_observations(diagnostics: pd.DataFrame) -> pd.DataFrame:
    opportunities = module_opportunity_events(diagnostics)
    rows = []
    for timestamp, bar in diagnostics.iterrows():
        for direction in ("Long", "Short"):
            prefix = direction.lower()
            if bool(pd.notna(bar[f"{prefix}_signal"]) and bar[f"{prefix}_signal"]):
                mask = int(bar[f"{prefix}_active_module_mask"])
                for module, bit in MODULE_BITS.items():
                    if mask & bit:
                        rows.append({
                            "sample_type": "Approved Signal", "direction": direction,
                            "module": module, "dominant_blocker": pd.NA,
                            "event_start": pd.NaT, "event_end": pd.NaT,
                            "duration_bars": pd.NA, "blocker_changed": pd.NA,
                            "unique_blocker_count": pd.NA, "converted": pd.NA,
                            "bars_to_conversion": pd.NA, "anchor_time": timestamp,
                            "anchor_price": float(bar.close),
                            "available_at": "anchor bar close",
                        })
    for event in opportunities.to_dict("records"):
        timestamp = event["event_end"]
        rows.append({
            "sample_type": "Blocked Opportunity", "direction": event["direction"],
            "module": event["module"], "dominant_blocker": event["dominant_blocker"],
            "event_start": event["event_start"], "event_end": timestamp,
            "duration_bars": event["duration_bars"],
            "blocker_changed": event["blocker_changed"],
            "unique_blocker_count": event["unique_blocker_count"],
            "converted": pd.NA, "bars_to_conversion": pd.NA,
            "anchor_time": timestamp, "anchor_price": float(diagnostics.at[timestamp, "close"]),
            "available_at": "anchor bar close",
        })
    if not rows:
        return _empty(OBSERVATION_SCHEMA, diagnostics.index.dtype)
    result = pd.DataFrame(rows)
    for column, dtype in OBSERVATION_SCHEMA.items():
        result[column] = pd.Series(result[column], dtype=(
            diagnostics.index.dtype if dtype == "datetime64[ns]" else dtype))
    return result[list(OBSERVATION_SCHEMA)]


def approved_vs_blocked_evaluation(outcomes: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Compare post-anchor paths; blocked rows are never presented as trades."""
    needed = {f"complete_{horizon}", f"forward_return_{horizon}",
              f"mfe_{horizon}", f"mae_{horizon}"}
    missing = needed.difference(outcomes.columns)
    if missing:
        raise ValueError(f"outcomes missing horizon columns: {sorted(missing)}")
    rows = []
    keys = ["direction", "module", "sample_type"]
    for key, group in outcomes.groupby(keys, sort=True, dropna=False):
        complete = group[f"complete_{horizon}"].fillna(False)
        returns = group.loc[complete, f"forward_return_{horizon}"].astype(float)
        stats = _metrics(returns)
        rows.append({
            "direction": key[0], "module": key[1], "evaluation_group": key[2],
            "sample_size": len(group), "complete_samples": int(complete.sum()),
            "censored_samples": int((~complete).sum()), "win_rate": stats["win_rate"],
            "mean_forward_return": stats["mean_return"],
            "median_forward_return": stats["median_return"],
            "mean_mfe": float(group.loc[complete, f"mfe_{horizon}"].mean()),
            "median_mfe": float(group.loc[complete, f"mfe_{horizon}"].median()),
            "mean_mae": float(group.loc[complete, f"mae_{horizon}"].mean()),
            "median_mae": float(group.loc[complete, f"mae_{horizon}"].median()),
            "profit_factor": stats["profit_factor"], "expectancy": stats["expectancy"],
        })
    return (_empty(COMPARISON_SCHEMA) if not rows
            else pd.DataFrame(rows).astype(COMPARISON_SCHEMA))


def excursion_vs_realized(trades: pd.DataFrame, outcomes: pd.DataFrame,
                          horizon: int, timestamp_dtype) -> pd.DataFrame:
    """Match filled trades to approved-signal excursions at signal close."""
    approved = outcomes[outcomes.sample_type == "Approved Signal"]
    rows = []
    for trade in trades.to_dict("records"):
        matches = approved[(approved.direction == trade["direction"])
                           & (approved.anchor_time == trade["signal_time"])]
        for outcome in matches.to_dict("records"):
            realized = float(trade["return_pct"]) if trade["closed"] else np.nan
            mfe = float(outcome[f"mfe_{horizon}"])
            rows.append({
                "trade_id": trade["trade_id"], "direction": trade["direction"],
                "module": outcome["module"], "signal_time": trade["signal_time"],
                "entry_time": trade["entry_time"], "exit_time": trade["exit_time"],
                "closed": trade["closed"], "realized_return": realized,
                "mfe": mfe, "mae": float(outcome[f"mae_{horizon}"]),
                "realized_to_mfe": (realized / mfe if np.isfinite(realized) and mfe > 0 else np.nan),
                "mfe_minus_realized": (mfe - realized if np.isfinite(realized) else np.nan),
            })
    if not rows:
        return _empty(EXCURSION_SCHEMA, timestamp_dtype)
    result = pd.DataFrame(rows)
    for column, dtype in EXCURSION_SCHEMA.items():
        result[column] = pd.Series(result[column], dtype=(
            timestamp_dtype if dtype == "datetime64[ns]" else dtype))
    return result[list(EXCURSION_SCHEMA)]


def excursion_summary(comparison: pd.DataFrame) -> pd.DataFrame:
    rows = []
    eligible = comparison[comparison.closed & comparison.realized_return.notna()
                          & comparison.mfe.notna() & comparison.mae.notna()]
    for key, group in eligible.groupby(["direction", "module"], sort=True):
        rows.append({"direction": key[0], "module": key[1], "sample_size": len(group),
                     "mean_realized_return": float(group.realized_return.mean()),
                     "mean_mfe": float(group.mfe.mean()), "mean_mae": float(group.mae.mean()),
                     "mean_realized_to_mfe": float(group.realized_to_mfe.mean()),
                     "mean_mfe_minus_realized": float(group.mfe_minus_realized.mean())})
    return (_empty(EXCURSION_SUMMARY_SCHEMA) if not rows
            else pd.DataFrame(rows).astype(EXCURSION_SUMMARY_SCHEMA))


def evaluate_strategy(diagnostics: pd.DataFrame, *,
                      horizons: Sequence[int] = DEFAULT_HORIZONS,
                      excursion_horizon: int = 20, **backtest_kwargs) -> dict[str, pd.DataFrame]:
    """Run Strategy Evaluation over one diagnostics dataset.

    Signal/opportunity paths become known only after ``excursion_horizon``
    subsequent closed bars.  They are retrospective evaluation outputs and
    must not be used as features at the signal or opportunity anchor.
    """
    horizons = tuple(horizons)
    if excursion_horizon not in horizons:
        raise ValueError("excursion_horizon must be included in horizons")
    backtest = run_swing_backtest(diagnostics, **backtest_kwargs)
    observations = _evaluation_observations(diagnostics)
    outcomes = calculate_historical_outcomes(
        diagnostics, observations, horizons=horizons,
        path_horizon=max(horizons), target_stops=())
    comparison = excursion_vs_realized(
        backtest.trades, outcomes, excursion_horizon, diagnostics.index.dtype)
    return {
        "trade_performance": trade_performance(backtest.trades),
        "approved_vs_blocked": approved_vs_blocked_evaluation(outcomes, excursion_horizon),
        "excursion_vs_realized": comparison,
        "excursion_summary": excursion_summary(comparison),
        "trades": backtest.trades,
        "evaluation_outcomes": outcomes,
    }
