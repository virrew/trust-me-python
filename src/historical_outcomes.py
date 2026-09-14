"""Retrospective price outcomes for diagnostic observations.

This module is an analysis layer, not a trade or exit simulator.  Every anchor
is available_at = anchor bar close and every outcome uses subsequent rows only.
The anchor close is an analytical reference price, never an assumed fill.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

import numpy as np
import pandas as pd

from src.diagnostics_analysis import MODULE_ACTIVATION_COLUMNS, module_opportunity_events


DEFAULT_HORIZONS = (1, 3, 5, 10, 20)
DEFAULT_TARGET_STOPS = ((0.03, 0.02), (0.05, 0.03))

OBSERVATION_SCHEMA = {
    "sample_type": "object", "direction": "object", "module": "object",
    "dominant_blocker": "object", "event_start": "datetime64[ns]",
    "event_end": "datetime64[ns]", "duration_bars": "Int64",
    "blocker_changed": "boolean", "unique_blocker_count": "Int64",
    "converted": "boolean", "bars_to_conversion": "Int64",
    "anchor_time": "datetime64[ns]", "anchor_price": "float64",
    "available_at": "object",
}


def _validate_config(horizons, target_stops, path_horizon):
    horizons = tuple(horizons)
    if (not horizons or any(type(h) is not int or h < 1 for h in horizons)
            or len(set(horizons)) != len(horizons)):
        raise ValueError("horizons must be unique positive integers")
    pairs = tuple(tuple(pair) for pair in target_stops)
    if any(len(pair) != 2 or pair[0] <= 0 or pair[1] <= 0 for pair in pairs):
        raise ValueError("target_stops must contain positive (target, stop) pairs")
    path_horizon = max(horizons) if path_horizon is None else path_horizon
    if type(path_horizon) is not int or path_horizon < 1:
        raise ValueError("path_horizon must be a positive integer")
    return horizons, pairs, path_horizon


def _validate_diagnostics(df):
    index = df.index
    if (not isinstance(index, pd.DatetimeIndex) or index.hasnans
            or not index.is_unique or not index.is_monotonic_increasing):
        raise ValueError("diagnostics requires a unique increasing DatetimeIndex")
    for column in ("high", "low", "close"):
        if column not in df or not pd.api.types.is_numeric_dtype(df[column]):
            raise ValueError(f"{column} must be a numeric column")


def _pair_key(target, stop):
    def part(value):
        return f"{value * 100:g}".replace(".", "p")
    return f"target_{part(target)}_stop_{part(stop)}"


def _empty_table(schema, timestamp_dtype):
    columns = {}
    for name, dtype in schema.items():
        if dtype == "datetime64[ns]":
            dtype = timestamp_dtype
        columns[name] = pd.Series(dtype=dtype)
    return pd.DataFrame(columns)


def build_outcome_observations(
    diagnostics: pd.DataFrame, opportunities: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build activation and opportunity anchors without calculating outcomes.

    Opportunity metadata is accepted from ``opportunity_signal_conversion`` as
    well as ``module_opportunity_events``.  Optional conversion fields remain
    nullable when the supplied event table does not contain them.
    """
    _validate_diagnostics(diagnostics)
    for direction in ("long", "short"):
        for prefix in MODULE_ACTIVATION_COLUMNS.values():
            column = f"{prefix}_{direction}"
            if column not in diagnostics:
                raise ValueError(f"missing activation column: {column}")
    opportunities = (module_opportunity_events(diagnostics)
                     if opportunities is None else opportunities)
    rows = []
    for module, prefix in MODULE_ACTIVATION_COLUMNS.items():
        for label, direction in (("Long", "long"), ("Short", "short")):
            active = diagnostics[f"{prefix}_{direction}"].fillna(False).astype(bool)
            for timestamp in diagnostics.index[active]:
                rows.append({
                    "sample_type": "Module Activation", "direction": label,
                    "module": module, "dominant_blocker": pd.NA,
                    "event_start": pd.NaT, "event_end": pd.NaT,
                    "duration_bars": pd.NA, "blocker_changed": pd.NA,
                    "unique_blocker_count": pd.NA, "converted": pd.NA,
                    "bars_to_conversion": pd.NA, "anchor_time": timestamp,
                    "anchor_price": float(diagnostics.at[timestamp, "close"]),
                    "available_at": "anchor bar close",
                })
    required = {"direction", "module", "event_start", "event_end",
                "duration_bars", "dominant_blocker", "blocker_changed",
                "unique_blocker_count"}
    missing = required.difference(opportunities.columns)
    if missing:
        raise ValueError(f"opportunities missing columns: {sorted(missing)}")
    for event in opportunities.to_dict("records"):
        timestamp = event["event_end"]
        if timestamp not in diagnostics.index:
            raise ValueError("every event_end must exist in diagnostics.index")
        rows.append({
            "sample_type": "Opportunity Event", "direction": event["direction"],
            "module": event["module"], "dominant_blocker": event["dominant_blocker"],
            "event_start": event["event_start"], "event_end": timestamp,
            "duration_bars": event["duration_bars"],
            "blocker_changed": event["blocker_changed"],
            "unique_blocker_count": event["unique_blocker_count"],
            "converted": event.get("converted", pd.NA),
            "bars_to_conversion": event.get("bars_to_conversion", pd.NA),
            "anchor_time": timestamp,
            "anchor_price": float(diagnostics.at[timestamp, "close"]),
            "available_at": "anchor bar close",
        })
    if not rows:
        return _empty_table(OBSERVATION_SCHEMA, diagnostics.index.dtype)
    result = pd.DataFrame(rows)
    for column, dtype in OBSERVATION_SCHEMA.items():
        if dtype == "datetime64[ns]":
            dtype = diagnostics.index.dtype
        result[column] = pd.Series(result[column], dtype=dtype)
    return result[list(OBSERVATION_SCHEMA)]


def _outcome_schema(horizons, pairs):
    schema = dict(OBSERVATION_SCHEMA)
    for horizon in horizons:
        schema.update({
            f"forward_return_{horizon}": "float64",
            f"mfe_{horizon}": "float64", f"mae_{horizon}": "float64",
            f"complete_{horizon}": "boolean",
        })
    schema.update({"path_horizon": "int64", "path_complete": "boolean"})
    for target, stop in pairs:
        key = _pair_key(target, stop)
        schema.update({
            f"{key}_target_hit": "boolean", f"{key}_stop_hit": "boolean",
            f"{key}_target_before_stop": "boolean",
            f"{key}_stop_before_target": "boolean",
            f"{key}_neither": "boolean", f"{key}_bars_to_target": "Int64",
            f"{key}_bars_to_stop": "Int64", f"{key}_path_status": "object",
        })
    return schema


def calculate_historical_outcomes(
    diagnostics: pd.DataFrame, observations: pd.DataFrame | None = None, *,
    horizons: Sequence[int] = DEFAULT_HORIZONS,
    target_stops: Iterable[tuple[float, float]] = DEFAULT_TARGET_STOPS,
    path_horizon: int | None = None,
) -> pd.DataFrame:
    """Calculate direction-adjusted outcomes strictly after each anchor bar."""
    _validate_diagnostics(diagnostics)
    horizons, pairs, path_horizon = _validate_config(
        horizons, target_stops, path_horizon)
    observations = (build_outcome_observations(diagnostics)
                    if observations is None else observations.copy())
    missing = set(OBSERVATION_SCHEMA).difference(observations.columns)
    if missing:
        raise ValueError(f"observations missing columns: {sorted(missing)}")
    schema = _outcome_schema(horizons, pairs)
    rows = []
    for observation in observations.to_dict("records"):
        anchor = diagnostics.index.get_loc(observation["anchor_time"])
        sign = 1 if observation["direction"] == "Long" else -1
        price = float(observation["anchor_price"])
        row = dict(observation)
        for horizon in horizons:
            complete = len(diagnostics) - anchor - 1 >= horizon
            row[f"complete_{horizon}"] = complete
            if complete:
                future = diagnostics.iloc[anchor + 1:anchor + horizon + 1]
                row[f"forward_return_{horizon}"] = sign * (
                    float(future.close.iloc[-1]) / price - 1)
                favorable = ((future.high / price - 1) if sign == 1
                             else (1 - future.low / price))
                adverse = ((future.low / price - 1) if sign == 1
                           else (1 - future.high / price))
                row[f"mfe_{horizon}"] = float(favorable.max())
                row[f"mae_{horizon}"] = float(adverse.min())
            else:
                row[f"forward_return_{horizon}"] = np.nan
                row[f"mfe_{horizon}"] = np.nan
                row[f"mae_{horizon}"] = np.nan
        observed = min(path_horizon, len(diagnostics) - anchor - 1)
        future = diagnostics.iloc[anchor + 1:anchor + observed + 1]
        complete = observed == path_horizon
        row.update({"path_horizon": path_horizon, "path_complete": complete})
        for target, stop in pairs:
            key = _pair_key(target, stop)
            favorable = ((future.high / price - 1) if sign == 1
                         else (1 - future.low / price))
            adverse = ((future.low / price - 1) if sign == 1
                       else (1 - future.high / price))
            target_hits = np.flatnonzero((favorable >= target).to_numpy()) + 1
            stop_hits = np.flatnonzero((adverse <= -stop).to_numpy()) + 1
            target_bar = int(target_hits[0]) if len(target_hits) else None
            stop_bar = int(stop_hits[0]) if len(stop_hits) else None
            if target_bar is not None and stop_bar is not None:
                status = ("AMBIGUOUS" if target_bar == stop_bar else
                          "TARGET_BEFORE_STOP" if target_bar < stop_bar else
                          "STOP_BEFORE_TARGET")
            elif target_bar is not None:
                status = "TARGET_BEFORE_STOP"
            elif stop_bar is not None:
                status = "STOP_BEFORE_TARGET"
            else:
                status = "NEITHER" if complete else "CENSORED"
            known_no_target = complete or target_bar is not None
            known_no_stop = complete or stop_bar is not None
            order_known = status not in {"AMBIGUOUS", "CENSORED"}
            row.update({
                f"{key}_target_hit": True if target_bar else (False if known_no_target else pd.NA),
                f"{key}_stop_hit": True if stop_bar else (False if known_no_stop else pd.NA),
                f"{key}_target_before_stop": (status == "TARGET_BEFORE_STOP"
                                                if order_known else pd.NA),
                f"{key}_stop_before_target": (status == "STOP_BEFORE_TARGET"
                                                if order_known else pd.NA),
                f"{key}_neither": (status == "NEITHER" if status != "CENSORED" else pd.NA),
                f"{key}_bars_to_target": target_bar,
                f"{key}_bars_to_stop": stop_bar, f"{key}_path_status": status,
            })
        rows.append(row)
            is_resolved_order = status not in {
    "CENSORED",
    "AMBIGUOUS",
}

    row.update({
    f"{key}_target_hit": (
        True
        if target_bar is not None
        else (False if known_no_target else pd.NA)
    ),
    f"{key}_stop_hit": (
        True
        if stop_bar is not None
        else (False if known_no_stop else pd.NA)
    ),
    f"{key}_target_before_stop": (
        status == "TARGET_BEFORE_STOP"
        if is_resolved_order
        else pd.NA
    ),
    f"{key}_stop_before_target": (
        status == "STOP_BEFORE_TARGET"
        if is_resolved_order
        else pd.NA
    ),
    f"{key}_neither": (
        status == "NEITHER"
        if status != "CENSORED"
        else pd.NA
    ),
    f"{key}_bars_to_target": target_bar,
    f"{key}_bars_to_stop": stop_bar,
    f"{key}_path_status": status,
})
    rows.append(row)
    if not rows:
        return _empty_table(schema, diagnostics.index.dtype)
    result = pd.DataFrame(rows)
    for column, dtype in schema.items():
        if dtype == "datetime64[ns]":
            dtype = diagnostics.index.dtype
        result[column] = pd.Series(result[column], dtype=dtype)
    return result[list(schema)]


def outcome_summary(outcomes: pd.DataFrame, *, by_blocker: bool = False) -> pd.DataFrame:
    """Aggregate observed outcomes; no group is removed for small sample size."""
    keys = ["direction", "module", "sample_type"]
    if by_blocker:
        keys.append("dominant_blocker")
        source = outcomes[outcomes.sample_type == "Opportunity Event"]
    else:
        source = outcomes
    horizons = [int(c.removeprefix("forward_return_")) for c in outcomes
                if c.startswith("forward_return_")]
    pair_keys = [c.removesuffix("_path_status") for c in outcomes
                 if c.endswith("_path_status")]
    schema = {key: "object" for key in keys}
    schema["sample_size"] = "int64"
    for h in horizons:
        schema.update({f"complete_samples_{h}": "int64",
                       f"censored_count_{h}": "int64"})
        for metric in ("forward_return", "mfe", "mae"):
            schema[f"mean_{metric}_{h}"] = "float64"
            schema[f"median_{metric}_{h}"] = "float64"
    for key in pair_keys:
        schema[f"{key}_eligible_samples"] = "int64"
        schema[f"{key}_target_before_stop_rate"] = "float64"
    rows = []
    for group_key, group in source.groupby(keys, sort=True, dropna=False):
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        row = dict(zip(keys, group_key)); row["sample_size"] = len(group)
        for h in horizons:
            complete = group[f"complete_{h}"].fillna(False)
            row[f"complete_samples_{h}"] = int(complete.sum())
            row[f"censored_count_{h}"] = int((~complete).sum())
            for metric in ("forward_return", "mfe", "mae"):
                values = group.loc[complete, f"{metric}_{h}"]
                row[f"mean_{metric}_{h}"] = float(values.mean())
                row[f"median_{metric}_{h}"] = float(values.median())
        for key in pair_keys:
            eligible = group[f"{key}_path_status"].isin({
                "TARGET_BEFORE_STOP", "STOP_BEFORE_TARGET", "NEITHER",
            })
                "TARGET_BEFORE_STOP",
                "STOP_BEFORE_TARGET",
                "NEITHER",
})
            n = int(eligible.sum())
            row[f"{key}_eligible_samples"] = n
            row[f"{key}_target_before_stop_rate"] = (
                float(group.loc[eligible, f"{key}_target_before_stop"].mean())
                if n else np.nan)
        rows.append(row)
    return (_empty_table(schema, outcomes.anchor_time.dtype) if not rows
            else pd.DataFrame(rows).astype(schema))


def approved_vs_blocked(outcomes: pd.DataFrame) -> pd.DataFrame:
    """Compare full module activations with each dominant sole blocker."""
    labeled = outcomes.copy()
    labeled["sample_type"] = np.where(
        labeled.sample_type == "Module Activation", "Full " + labeled.module,
        labeled.dominant_blocker.astype("string") + " sole blocker")
    return outcome_summary(labeled).rename(columns={"sample_type": "comparison_group"})


def analyze_historical_outcomes(
    diagnostics: pd.DataFrame, opportunities: pd.DataFrame | None = None, **kwargs,
) -> dict[str, pd.DataFrame]:
    """Run the outcome layer and its three outcome-aware diagnostic views."""
    observations = build_outcome_observations(diagnostics, opportunities)
    outcomes = calculate_historical_outcomes(diagnostics, observations, **kwargs)
    return {"historical_outcomes": outcomes,
            "outcome_summary": outcome_summary(outcomes),
            "outcomes_by_blocker": outcome_summary(outcomes, by_blocker=True),
            "approved_vs_blocked": approved_vs_blocked(outcomes)}
