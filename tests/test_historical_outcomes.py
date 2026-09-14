import numpy as np
import pandas as pd
import pytest

from src.historical_outcomes import (
    OBSERVATION_SCHEMA, analyze_historical_outcomes, approved_vs_blocked,
    build_outcome_observations, calculate_historical_outcomes, outcome_summary,
)


def diagnostics(periods=25, tz="UTC"):
    index = pd.date_range("2026-01-01", periods=periods, tz=tz)
    close = np.full(periods, 100.0)
    frame = pd.DataFrame({"open": close, "high": close + 1,
                          "low": close - 1, "close": close,
                          "volume": 1}, index=index)
    for prefix in ("pullback", "breakout", "squeeze", "mean_rev"):
        for direction in ("long", "short"):
            frame[f"{prefix}_{direction}"] = False
    return frame


def observation(df, position=0, direction="Long", sample_type="Module Activation"):
    row = {name: pd.NA for name in OBSERVATION_SCHEMA}
    row.update({"sample_type": sample_type, "direction": direction,
                "module": "Breakout", "anchor_time": df.index[position],
                "anchor_price": float(df.close.iloc[position]),
                "available_at": "anchor bar close"})
    return pd.DataFrame([row])


def test_long_and_short_returns_mfe_mae_and_all_horizons():
    df = diagnostics()
    df.loc[df.index[1:], "close"] = np.arange(101, 125)
    df.loc[df.index[1:], "high"] = df.close.iloc[1:] + 2
    df.loc[df.index[1:], "low"] = df.close.iloc[1:] - 3
    long = calculate_historical_outcomes(df, observation(df, direction="Long"))
    short = calculate_historical_outcomes(df, observation(df, direction="Short"))
    for horizon in (1, 3, 5, 10, 20):
        assert long.at[0, f"forward_return_{horizon}"] == pytest.approx(horizon / 100)
        assert short.at[0, f"forward_return_{horizon}"] == pytest.approx(-horizon / 100)
        assert long.at[0, f"mfe_{horizon}"] == pytest.approx((horizon + 2) / 100)
        assert long.at[0, f"mae_{horizon}"] == pytest.approx(-0.02)
        assert short.at[0, f"mfe_{horizon}"] == pytest.approx(0.02)
        assert short.at[0, f"mae_{horizon}"] == pytest.approx(-(horizon + 2) / 100)


def test_censoring_and_anchor_high_low_are_never_used():
    df = diagnostics(3)
    df.loc[df.index[0], ["high", "low"]] = [1000, 1]
    df.loc[df.index[1], ["high", "low", "close"]] = [104, 98, 102]
    result = calculate_historical_outcomes(df, observation(df), horizons=(1, 3))
    assert result.at[0, "mfe_1"] == pytest.approx(.04)
    assert result.at[0, "mae_1"] == pytest.approx(-.02)
    assert pd.isna(result.at[0, "forward_return_3"])
    assert not result.at[0, "complete_3"]


@pytest.mark.parametrize("highs,lows,status,target_bar,stop_bar", [
    ([101, 104, 101], [99, 99, 97], "TARGET_BEFORE_STOP", 2, 3),
    ([101, 104, 101], [97, 99, 99], "STOP_BEFORE_TARGET", 2, 1),
    ([104, 101, 101], [97, 99, 99], "AMBIGUOUS", 1, 1),
    ([101, 101, 101], [99, 99, 99], "NEITHER", None, None),
])
def test_target_stop_paths(highs, lows, status, target_bar, stop_bar):
    df = diagnostics(4)
    df.loc[df.index[1:], "high"] = highs
    df.loc[df.index[1:], "low"] = lows
    result = calculate_historical_outcomes(
        df, observation(df), horizons=(1,), target_stops=((.03, .02),), path_horizon=3)
    key = "target_3_stop_2"
    assert result.at[0, f"{key}_path_status"] == status
    value = result.at[0, f"{key}_bars_to_target"]
    assert (pd.isna(value) if target_bar is None else value == target_bar)
    value = result.at[0, f"{key}_bars_to_stop"]
    assert (pd.isna(value) if stop_bar is None else value == stop_bar)
    if status == "AMBIGUOUS":
        assert result.at[0, f"{key}_target_hit"]
        assert result.at[0, f"{key}_stop_hit"]
        assert pd.isna(result.at[0, f"{key}_target_before_stop"])
        assert pd.isna(result.at[0, f"{key}_stop_before_target"])

        assert pd.isna(
        result.at[0, f"{key}_target_before_stop"]
    )
        assert pd.isna(
        result.at[0, f"{key}_stop_before_target"]
    )

def test_ambiguous_path_is_excluded_from_target_before_stop_rate():
    df = diagnostics(7)

    observations = pd.concat(
        [
            observation(df, position=0),
            observation(df, position=3),
        ],
        ignore_index=True,
    )

    # --------------------------------------------------------
    # Observation 1:
    # Target träffas före stop.
    # --------------------------------------------------------

    df.loc[
        df.index[1],
        ["high", "low"],
    ] = [104, 99]

    # --------------------------------------------------------
    # Observation 2:
    # Target och stop träffas på samma bar.
    # Ska klassas AMBIGUOUS.
    # --------------------------------------------------------

    df.loc[
        df.index[4],
        ["high", "low"],
    ] = [104, 97]

    outcomes = calculate_historical_outcomes(
        df,
        observations,
        horizons=(1,),
        target_stops=((0.03, 0.02),),
        path_horizon=1,
    )

    summary = outcome_summary(
        outcomes
    )

    key = "target_3_stop_2"

    # Endast den observation där ordningen faktiskt är känd
    # får ingå i denominatorn.
    assert (
        summary.at[
            0,
            f"{key}_eligible_samples",
        ]
        == 1
    )

    assert (
        summary.at[
            0,
            f"{key}_target_before_stop_rate",
        ]
        == pytest.approx(1.0)
    )

def test_unresolved_partial_target_path_is_censored_not_failure():
    df = diagnostics(2)
    result = calculate_historical_outcomes(df, observation(df), horizons=(1,),
                                           target_stops=((.03, .02),), path_horizon=3)
    assert result.at[0, "target_3_stop_2_path_status"] == "CENSORED"
    assert pd.isna(result.at[0, "target_3_stop_2_neither"])


def test_ambiguous_and_censored_paths_are_excluded_from_summary_rate():
    df = diagnostics(5)
    observations = pd.concat([observation(df, 0), observation(df, 1),
                              observation(df, 3)], ignore_index=True)
    # Anchor 0 reaches target on bar 1. Anchor 1 reaches target and stop on bar
    # 2. Anchor 3 has an unresolved, incomplete two-bar path.
    df.loc[df.index[1], ["high", "low"]] = [104, 99]
    df.loc[df.index[2], ["high", "low"]] = [104, 97]
    outcomes = calculate_historical_outcomes(
        df, observations, horizons=(1,), target_stops=((.03, .02),),
        path_horizon=2,
    )
    assert outcomes["target_3_stop_2_path_status"].tolist() == [
        "TARGET_BEFORE_STOP", "AMBIGUOUS", "CENSORED",
    ]
    summary = outcome_summary(outcomes).iloc[0]
    assert summary.target_3_stop_2_eligible_samples == 1
    assert summary.target_3_stop_2_target_before_stop_rate == 1.0


def test_module_activation_and_opportunity_metadata_and_timezone():
    df = diagnostics()
    df.loc[df.index[2], "breakout_long"] = True
    events = pd.DataFrame([{
        "direction": "Short", "module": "Breakout", "event_start": df.index[4],
        "event_end": df.index[5], "duration_bars": 2, "dominant_blocker": "Volume",
        "blocker_changed": False, "unique_blocker_count": 1,
        "blocker_sequence": "Volume", "converted": True, "bars_to_conversion": 2,
    }])
    observations = build_outcome_observations(df, events)
    activation = observations[observations.sample_type == "Module Activation"].iloc[0]
    opportunity = observations[observations.sample_type == "Opportunity Event"].iloc[0]
    assert activation.anchor_time == df.index[2]
    assert opportunity.anchor_time == opportunity.event_end == df.index[5]
    assert opportunity.dominant_blocker == "Volume"
    assert opportunity.converted and opportunity.bars_to_conversion == 2
    assert observations.anchor_time.dtype == df.index.dtype
    assert (observations.available_at == "anchor bar close").all()


def test_empty_schemas_summaries_and_approved_vs_blocked():
    df = diagnostics(0)
    observations = build_outcome_observations(df, pd.DataFrame(columns=[
        "direction", "module", "event_start", "event_end", "duration_bars",
        "dominant_blocker", "blocker_changed", "unique_blocker_count"]))
    assert list(observations) == list(OBSERVATION_SCHEMA)
    outcomes = calculate_historical_outcomes(df, observations)
    assert len(outcomes) == 0 and "forward_return_20" in outcomes
    assert len(outcome_summary(outcomes)) == 0
    assert len(outcome_summary(outcomes, by_blocker=True)) == 0
    assert len(approved_vs_blocked(outcomes)) == 0


def test_aggregate_views_keep_small_blocker_groups_and_sample_sizes():
    df = diagnostics()
    df.loc[df.index[0], "breakout_long"] = True
    events = pd.DataFrame([{
        "direction": "Long", "module": "Breakout", "event_start": df.index[1],
        "event_end": df.index[1], "duration_bars": 1, "dominant_blocker": "Volume",
        "blocker_changed": False, "unique_blocker_count": 1,
        "blocker_sequence": "Volume",
    }])
    result = analyze_historical_outcomes(df, events)
    assert result["outcome_summary"].sample_size.tolist() == [1, 1]
    blocker = result["outcomes_by_blocker"]
    assert len(blocker) == 1 and blocker.iloc[0].sample_size == 1
    comparison = result["approved_vs_blocked"]
    assert set(comparison.comparison_group) == {"Full Breakout", "Volume sole blocker"}
