"""Deterministic, two-arm rule/configuration comparisons.

Each arm is independently replayed through the existing sequential research
engine.  This module reports observed differences; it never selects, ranks, or
combines variants.
"""
from __future__ import annotations

import json
from typing import Any, Mapping

import numpy as np
import pandas as pd

from src.strategy_evaluation import MODULE_BITS, evaluate_strategy


SUPPORTED_CONFIG = {"atr_multiplier", "use_locked_atr"}
EXECUTION_RESOLUTIONS = (
    "FILLED", "FILLED_BUT_CENSORED_AT_END", "IGNORED_POSITION_OPEN",
    "NO_NEXT_BAR", "CONFLICTING_SIGNAL", "INVALID_ENTRY_PREREQUISITE",
)
RISK_PERFORMANCE_SCHEMA = {
    "arm": "object", "group_type": "object", "direction": "object",
    "module": "object", "number_of_trades": "int64", "wins": "int64",
    "losses": "int64", "win_rate": "float64", "mean_return": "float64",
    "median_return": "float64", "average_win": "float64",
    "average_loss": "float64", "profit_factor": "float64",
    "expectancy": "float64", "mean_realized_R": "float64",
    "median_realized_R": "float64",
}
SIGNAL_EXECUTION_SCHEMA = {
    "arm": "object", "metric": "object", "count": "int64",
}
PAIRED_SCHEMA = {
    "signal_time": "datetime64[ns]", "direction": "object", "pair_status": "object",
    "resolution_a": "object", "resolution_b": "object", "trade_id_a": "Int64",
    "trade_id_b": "Int64", "exit_time_a": "datetime64[ns]",
    "exit_time_b": "datetime64[ns]", "exit_reason_a": "object",
    "exit_reason_b": "object", "return_a": "float64", "return_b": "float64",
    "realized_R_a": "float64", "realized_R_b": "float64",
    "bars_held_a": "Int64", "bars_held_b": "Int64",
    "lifecycle_mfe_a": "float64", "lifecycle_mfe_b": "float64",
    "delta_return": "float64", "delta_R": "float64",
}
METADATA_SCHEMA = {
    "experiment_id": "object", "experiment_name": "object",
    "baseline_config": "object", "variant_config": "object",
    "changed_parameter": "object", "baseline_value": "object",
    "variant_value": "object", "other_parameters_identical": "bool",
    "variant_behavior_change": "bool", "input_start": "datetime64[ns]",
    "input_end": "datetime64[ns]", "input_bars": "int64", "timezone": "object",
}


def _table(rows, schema, timestamp_dtype):
    if not rows:
        return pd.DataFrame({name: pd.Series(dtype=timestamp_dtype if dtype == "datetime64[ns]" else dtype)
                             for name, dtype in schema.items()})
    frame = pd.DataFrame(rows)
    for name, dtype in schema.items():
        target = timestamp_dtype if dtype == "datetime64[ns]" else dtype
        values = frame[name]
        if dtype == "float64":
            values = pd.to_numeric(values, errors="coerce")
        frame[name] = pd.Series(pd.array(values, dtype=target), index=frame.index)
    return frame[list(schema)]


def _validated_configs(baseline: Mapping[str, Any], variant: Mapping[str, Any]):
    a, b = dict(baseline), dict(variant)
    unknown = (set(a) | set(b)) - SUPPORTED_CONFIG
    if unknown:
        raise ValueError(f"unsupported A/B configuration: {sorted(unknown)}")
    # Defaults are part of provenance, so omitted and explicit values compare identically.
    a = {"atr_multiplier": 2.5, "use_locked_atr": False, **a}
    b = {"atr_multiplier": 2.5, "use_locked_atr": False, **b}
    changed = [key for key in sorted(a) if a[key] != b[key]]
    if len(changed) > 1:
        raise ValueError("variant must change at most one configuration parameter")
    return a, b, changed


def _risk_enriched(lifecycle: pd.DataFrame) -> pd.DataFrame:
    result = lifecycle.copy()
    risk = (result.entry_price - result.initial_stop).abs() / result.entry_price
    valid = np.isfinite(risk) & (risk > 0) & np.isfinite(result.entry_price) & (result.entry_price > 0)
    result["initial_risk_pct"] = risk.where(valid)
    result["realized_R"] = (result.return_pct / result.initial_risk_pct).where(
        result.closed & valid & np.isfinite(result.return_pct))
    result["mfe_R"] = (result.in_trade_mfe / result.initial_risk_pct).where(
        valid & np.isfinite(result.in_trade_mfe))
    return result


def _performance(arm: str, lifecycle: pd.DataFrame, base: pd.DataFrame):
    rows = []
    closed = lifecycle[lifecycle.closed.fillna(False)]
    for source in base.to_dict("records"):
        selected = closed
        if source["direction"] != "All":
            selected = selected[selected.direction == source["direction"]]
        if source["module"] != "All":
            selected = selected[(selected.active_module_mask.astype("int64")
                                 & MODULE_BITS[source["module"]]) != 0]
        values = selected.realized_R.dropna()
        rows.append({"arm": arm, **source, "mean_realized_R": float(values.mean()),
                     "median_realized_R": float(values.median())})
    return rows


def _signal_counts(arm, reconciliation):
    rows = [{"arm": arm, "metric": "TOTAL_FINAL_SIGNALS", "count": len(reconciliation)}]
    rows.extend({"arm": arm, "metric": status,
                 "count": int((reconciliation.resolution == status).sum())}
                for status in EXECUTION_RESOLUTIONS)
    return rows


def _paired(a, b, timestamp_dtype):
    ra = a["signal_fill_reconciliation"].set_index(["signal_time", "direction"], drop=False)
    rb = b["signal_fill_reconciliation"].set_index(["signal_time", "direction"], drop=False)
    la = a["ab_trade_lifecycle"].set_index(["signal_time", "direction"], drop=False)
    lb = b["ab_trade_lifecycle"].set_index(["signal_time", "direction"], drop=False)
    rows = []
    for key in ra.index.union(rb.index).unique():
        ar = ra.loc[key] if key in ra.index else None
        br = rb.loc[key] if key in rb.index else None
        # Signal provenance is unique per direction in the reconciliation contract.
        if isinstance(ar, pd.DataFrame) or isinstance(br, pd.DataFrame):
            raise ValueError("signal_time + direction provenance must be unique")
        af = ar is not None and str(ar.resolution).startswith("FILLED")
        bf = br is not None and str(br.resolution).startswith("FILLED")
        if af and bf:
            status = "MATCHED_SIGNAL"
        elif af:
            status = "A_ONLY_FILL"
        elif bf:
            status = "B_ONLY_FILL"
        else:
            status = "BOTH_SIGNAL_BUT_DIFFERENT_EXECUTION"
        at = la.loc[key] if af and key in la.index else None
        bt = lb.loc[key] if bf and key in lb.index else None
        def value(row, name):
            return row[name] if row is not None else pd.NA
        ret_a, ret_b = value(at, "return_pct"), value(bt, "return_pct")
        r_a, r_b = value(at, "realized_R"), value(bt, "realized_R")
        rows.append({
            "signal_time": key[0], "direction": key[1], "pair_status": status,
            "resolution_a": value(ar, "resolution"), "resolution_b": value(br, "resolution"),
            "trade_id_a": value(at, "trade_id"), "trade_id_b": value(bt, "trade_id"),
            "exit_time_a": value(at, "exit_time"), "exit_time_b": value(bt, "exit_time"),
            "exit_reason_a": value(at, "exit_reason"), "exit_reason_b": value(bt, "exit_reason"),
            "return_a": ret_a, "return_b": ret_b, "realized_R_a": r_a, "realized_R_b": r_b,
            "bars_held_a": value(at, "bars_held"), "bars_held_b": value(bt, "bars_held"),
            "lifecycle_mfe_a": value(at, "in_trade_mfe"),
            "lifecycle_mfe_b": value(bt, "in_trade_mfe"),
            "delta_return": (ret_b - ret_a if pd.notna(ret_a) and pd.notna(ret_b) else np.nan),
            "delta_R": (r_b - r_a if pd.notna(r_a) and pd.notna(r_b) else np.nan),
        })
    return _table(rows, PAIRED_SCHEMA, timestamp_dtype)


def run_ab_rule_test(
    diagnostics: pd.DataFrame, *, experiment_id: str, experiment_name: str,
    baseline_config: Mapping[str, Any] | None = None,
    variant_config: Mapping[str, Any] | None = None,
    excursion_horizon: int = 20,
) -> dict[str, pd.DataFrame]:
    """Replay A and B independently and return stable descriptive tables.

    Zero changed parameters is accepted as a deterministic equivalence/control
    run. A real variant may change exactly one supported execution parameter.
    """
    baseline, variant, changed = _validated_configs(baseline_config or {}, variant_config or {})
    original = diagnostics.copy(deep=True)
    arms = {}
    for label, config in (("A", baseline), ("B", variant)):
        result = evaluate_strategy(diagnostics, horizons=(excursion_horizon,),
                                   excursion_horizon=excursion_horizon, **config)
        result["ab_trade_lifecycle"] = _risk_enriched(result["trade_lifecycle"])
        arms[label] = result
    pd.testing.assert_frame_equal(diagnostics, original)
    timestamp_dtype = diagnostics.index.dtype
    perf_rows = (_performance("A", arms["A"]["ab_trade_lifecycle"], arms["A"]["trade_performance"])
                 + _performance("B", arms["B"]["ab_trade_lifecycle"], arms["B"]["trade_performance"]))
    changed_name = changed[0] if changed else "NONE_CONTROL_RUN"
    metadata = [{
        "experiment_id": experiment_id, "experiment_name": experiment_name,
        "baseline_config": json.dumps(baseline, sort_keys=True),
        "variant_config": json.dumps(variant, sort_keys=True),
        "changed_parameter": changed_name,
        "baseline_value": baseline.get(changed_name), "variant_value": variant.get(changed_name),
        "other_parameters_identical": True, "variant_behavior_change": bool(changed),
        "input_start": diagnostics.index[0] if len(diagnostics) else pd.NaT,
        "input_end": diagnostics.index[-1] if len(diagnostics) else pd.NaT,
        "input_bars": len(diagnostics), "timezone": str(diagnostics.index.tz),
    }]
    return {
        "experiment_metadata": _table(metadata, METADATA_SCHEMA, timestamp_dtype),
        "strategy_and_module_performance": _table(perf_rows, RISK_PERFORMANCE_SCHEMA, timestamp_dtype),
        "signal_execution": _table(_signal_counts("A", arms["A"]["signal_fill_reconciliation"])
                                   + _signal_counts("B", arms["B"]["signal_fill_reconciliation"]),
                                   SIGNAL_EXECUTION_SCHEMA, timestamp_dtype),
        "paired_signals": _paired(arms["A"], arms["B"], timestamp_dtype),
        "a_trade_lifecycle": arms["A"]["ab_trade_lifecycle"],
        "b_trade_lifecycle": arms["B"]["ab_trade_lifecycle"],
        "a_trade_stop_path": arms["A"]["trade_stop_path"],
        "b_trade_stop_path": arms["B"]["trade_stop_path"],
        "a_reconciliation": arms["A"]["signal_fill_reconciliation"],
        "b_reconciliation": arms["B"]["signal_fill_reconciliation"],
    }
