from __future__ import annotations

import pandas as pd
# Deterministic pytest coverage; main() above remains the Yahoo sanity program.
import numpy as np
import pytest
from pandas.testing import assert_frame_equal
from src.diagnostics_analysis import (
    module_opportunity_events, opportunity_signal_conversion,
    opportunity_conversion_summary,
)



from src.market_data import download_yahoo_data
from src.diagnostics_signals import signal_diagnostics
from src.diagnostics_analysis import analyze_signals


# ============================================================
# PRINT HELPER
# ============================================================

def print_table(
    title: str,
    df: pd.DataFrame,
) -> None:
    """
    Skriver ut en DataFrame tydligt i terminalen.
    """

    print()
    print("=" * 80)
    print(title)
    print("=" * 80)

    if df.empty:
        print("No data.")
        return

    print(
        df.to_string(
            index=False,
        )
    )


# ============================================================
# MAIN TEST
# ============================================================

def main() -> None:
    """
    Historiskt analystest för Trust Me.

    Baseline:
    - Ticker: MU
    - Mode: Swing
    - Chart TF: 1D
    - Historik: 2 år

    Testet verifierar kedjan:

        Market Data
            ↓
        Signal Diagnostics
            ↓
        Analysis Engine
            ↓
        Descriptive Analysis
            ↓
        Consistency / Sanity Checks
    """

    ticker = "MU"

    # ========================================================
    # HÄMTA DATA
    # ========================================================

    data = download_yahoo_data(
        ticker,
        period="2y",
        interval="1d",
    )

    # ========================================================
    # BYGG SIGNAL DIAGNOSTICS
    # ========================================================

    diagnostics = signal_diagnostics(
        data,
        is_swing=True,
        allow_long=True,
        allow_short=False,

        # Trend
        ema_fast_length=50,
        ema_slow_length=200,
        adx_length=14,
        adx_min_swing=18.0,

        # Volatility
        atr_length=14,
        min_atr_pct_swing=1.0,
        use_candle_filter=True,
        max_candle_atr=2.0,

        # Momentum
        rsi_length=14,
        rsi_smooth_len=9,
        confluence_window_swing=5,

        # Volume
        use_volume_filter=True,
        volume_length_swing=20,
        volume_length_intraday=30,

        # Breakout
        breakout_lookback_swing=10,
        breakout_lookback_intraday=20,

        # Squeeze
        bb_length=20,
        bb_mult=2.0,
        squeeze_window_swing=3,
        squeeze_window_intraday=6,
    )

    # ========================================================
    # KÖR ANALYSIS ENGINE
    # ========================================================

    analysis = analyze_signals(
        diagnostics
    )

    for key in ("opportunity_signal_conversion", "opportunity_conversion_summary",
                "opportunity_conversion_by_blocker"):
        print_table(key.upper(), analysis[key])
    conversions = analysis["opportunity_signal_conversion"]
    assert len(conversions) == len(analysis["module_opportunity_events"])
    assert conversions.loc[conversions.converted.fillna(False), "bars_to_conversion"].between(1, 5).all()

    # ========================================================
    # HEADER
    # ========================================================

    print()
    print("#" * 80)
    print("TRUST ME — HISTORICAL DIAGNOSTIC ANALYSIS")
    print("#" * 80)

    print(f"Ticker:          {ticker}")
    print("Mode:            Swing")
    print("Chart TF:        1D")
    print(f"Downloaded bars:{len(data):>10}")
    print(f"Diagnostic bars:{len(diagnostics):>10}")

    if len(diagnostics) > 0:

        print(
            f"From:            "
            f"{diagnostics.index.min().date()}"
        )

        print(
            f"To:              "
            f"{diagnostics.index.max().date()}"
        )

    # ========================================================
    # SIGNAL FUNNEL
    # ========================================================

    print_table(
        "SIGNAL FUNNEL",
        analysis["signal_funnel"],
    )

    # ========================================================
    # FINAL FILTER BLOCKERS
    # ========================================================

    blockers = (
        analysis["final_filter_blockers"]
        .sort_values(
            by=[
                "direction",
                "count",
            ],
            ascending=[
                True,
                False,
            ],
        )
    )

    print_table(
        "FINAL FILTER BLOCKERS",
        blockers,
    )

    # ========================================================
    # FINAL FAILURE COMBINATIONS
    # ========================================================

    failure_combinations = (
        analysis["final_failure_combinations"]
        .sort_values(
            by=[
                "direction",
                "count",
            ],
            ascending=[
                True,
                False,
            ],
        )
    )

    print_table(
        "FINAL FAILURE COMBINATIONS",
        failure_combinations,
    )

    # ========================================================
    # NEAR-MISS SUMMARY
    # ========================================================

    print_table(
        "NEAR-MISS SUMMARY",
        analysis["near_miss_summary"],
    )

    # ========================================================
    # MODULE ACTIVATION SUMMARY
    # ========================================================

    module_activation = (
        analysis["module_activation_summary"]
        .sort_values(
            by=[
                "direction",
                "activation_count",
            ],
            ascending=[
                True,
                False,
            ],
        )
    )

    print_table(
        "MODULE ACTIVATION SUMMARY",
        module_activation,
    )

    # ========================================================
    # MODULE FAILURE ANALYSIS
    # ========================================================

    module_failures = (
        analysis["module_failure_analysis"]
        .sort_values(
            by=[
                "direction",
                "module",
                "fail_count",
            ],
            ascending=[
                True,
                True,
                False,
            ],
        )
    )

    print_table(
        "MODULE FAILURE ANALYSIS",
        module_failures,
    )

    # ========================================================
    # MODULE CONDITIONAL ANALYSIS
    # ========================================================

    conditional_analysis = (
        analysis["module_conditional_analysis"]
    )

    # --------------------------------------------------------
    # SEQUENTIAL FUNNEL
    # --------------------------------------------------------

    sequential_funnel = (
        conditional_analysis[
            conditional_analysis["analysis_type"]
            == "Sequential Funnel"
        ]
        .sort_values(
            by=[
                "direction",
                "module",
                "step",
            ],
            ascending=[
                True,
                True,
                True,
            ],
        )
    )

    print_table(
        "MODULE CONDITIONAL ANALYSIS - SEQUENTIAL FUNNEL",
        sequential_funnel,
    )

    # --------------------------------------------------------
    # SOLE BLOCKERS
    # --------------------------------------------------------

    sole_blockers = (
        conditional_analysis[
            conditional_analysis["analysis_type"]
            == "Sole Blocker"
        ]
        .sort_values(
            by=[
                "direction",
                "module",
                "count",
            ],
            ascending=[
                True,
                True,
                False,
            ],
        )
    )

    print_table(
        "MODULE CONDITIONAL ANALYSIS - SOLE BLOCKERS",
        sole_blockers,
    )

    # ========================================================
    # MODULE OPPORTUNITY EVENTS
    # ========================================================

    opportunity_events = (
        analysis["module_opportunity_events"]
        .sort_values(
            by=[
                "direction",
                "module",
                "event_start",
            ],
            ascending=[
                True,
                True,
                True,
            ],
        )
    )

    # --------------------------------------------------------
    # EVENT SUMMARY
    # --------------------------------------------------------
    #
    # Vi skriver inte ut varje event direkt eftersom det
    # snabbt kan bli väldigt många rader.
    #
    # Istället summerar vi per:
    # - direction
    # - module
    #
    # och visar:
    # - antal separata events
    # - totalt antal opportunity-bars
    # - genomsnittlig event-längd
    # - medianlängd
    # - längsta event
    # - hur många events där blockeraren ändrades
    # --------------------------------------------------------

    opportunity_event_summary = (
        opportunity_events
        .groupby(
            [
                "direction",
                "module",
            ],
            as_index=False,
        )
        .agg(
            event_count=(
                "duration_bars",
                "size",
            ),
            opportunity_bars=(
                "duration_bars",
                "sum",
            ),
            avg_duration_bars=(
                "duration_bars",
                "mean",
            ),
            median_duration_bars=(
                "duration_bars",
                "median",
            ),
            max_duration_bars=(
                "duration_bars",
                "max",
            ),
            blocker_changed_events=(
                "blocker_changed",
                "sum",
            ),
        )
    )

    print_table(
        "MODULE OPPORTUNITY EVENT SUMMARY",
        opportunity_event_summary,
    )

    # --------------------------------------------------------
    # LONGEST EVENTS
    # --------------------------------------------------------
    #
    # Visar de längsta opportunity-eventen.
    # Detta är mer användbart i terminalen än att skriva
    # ut samtliga events.
    # --------------------------------------------------------

    longest_events = (
        opportunity_events
        .sort_values(
            by="duration_bars",
            ascending=False,
        )
        .head(15)
        [
            [
                "direction",
                "module",
                "event_start",
                "event_end",
                "duration_bars",
                "dominant_blocker",
                "blocker_changed",
            ]
        ]
    )

    print_table(
        "LONGEST MODULE OPPORTUNITY EVENTS",
        longest_events,
    )

    # ========================================================
    # ANALYSIS SANITY CHECKS
    # ========================================================

    print()
    print("=" * 80)
    print("ANALYSIS SANITY CHECKS")
    print("=" * 80)

    # --------------------------------------------------------
    # MARKET DATA / DIAGNOSTICS
    # --------------------------------------------------------

    assert len(data) > 0
    assert len(diagnostics) > 0

    # --------------------------------------------------------
    # REQUIRED ANALYSES
    # --------------------------------------------------------

    required_analyses = [
        "signal_funnel",
        "final_filter_blockers",
        "final_failure_combinations",
        "near_miss_summary",
        "module_failure_analysis",
        "module_activation_summary",
        "module_conditional_analysis",
        "module_opportunity_events",
    ]

    for analysis_name in required_analyses:

        assert analysis_name in analysis, (
            f"Analysis saknas: {analysis_name}"
        )

        assert not analysis[analysis_name].empty, (
            f"Analysis är tom: {analysis_name}"
        )

    # --------------------------------------------------------
    # CONDITIONAL ANALYSIS STRUCTURE
    # --------------------------------------------------------

    assert not sequential_funnel.empty
    assert not sole_blockers.empty

    assert (
        sequential_funnel["analysis_type"]
        == "Sequential Funnel"
    ).all()

    assert (
        sole_blockers["analysis_type"]
        == "Sole Blocker"
    ).all()

    assert (
        sequential_funnel["count"] >= 0
    ).all()

    assert (
        sole_blockers["count"] >= 0
    ).all()

    assert (
        sole_blockers["opportunity_count"] >= 0
    ).all()

    assert (
        sole_blockers["count"]
        <= sole_blockers["opportunity_count"]
    ).all()

    # ========================================================
    # MODULE FUNNEL CONSISTENCY
    # ========================================================
    #
    # Sista steget i varje Sequential Funnel måste vara
    # exakt samma som modulens activation_count.
    #
    # Exempel:
    #
    # Breakout:
    #
    # Trend
    #   ↓
    # Price
    #   ↓
    # Volume
    #   ↓
    # RSI
    #   ↓
    # Final count
    #
    # måste motsvara:
    #
    # breakout_long / breakout_short activation count.
    # ========================================================

    modules = [
        "Pullback",
        "Breakout",
        "Squeeze",
        "Mean Reversion",
    ]

    directions = [
        "Long",
        "Short",
    ]

    for direction in directions:

        for module in modules:

            # ------------------------------------------------
            # HÄMTA FUNNEL
            # ------------------------------------------------

            module_funnel = sequential_funnel[
                (
                    sequential_funnel["direction"]
                    == direction
                )
                & (
                    sequential_funnel["module"]
                    == module
                )
            ].sort_values(
                "step"
            )

            assert not module_funnel.empty, (
                f"Sequential funnel saknas för "
                f"{direction} {module}"
            )

            # ------------------------------------------------
            # FINAL FUNNEL COUNT
            # ------------------------------------------------

            final_funnel_count = int(
                module_funnel.iloc[-1][
                    "count"
                ]
            )

            # ------------------------------------------------
            # MODULE ACTIVATION COUNT
            # ------------------------------------------------

            activation_row = module_activation[
                (
                    module_activation["direction"]
                    == direction
                )
                & (
                    module_activation["module"]
                    == module
                )
            ]

            assert len(activation_row) == 1, (
                f"Activation row saknas eller dupliceras för "
                f"{direction} {module}"
            )

            activation_count = int(
                activation_row.iloc[0][
                    "activation_count"
                ]
            )

            # ------------------------------------------------
            # CONSISTENCY ASSERTION
            # ------------------------------------------------

            assert (
                final_funnel_count
                == activation_count
            ), (
                f"{direction} {module}: "
                f"funnel={final_funnel_count}, "
                f"activation={activation_count}"
            )

    # ========================================================
    # FUNNEL MATHEMATICAL SANITY
    # ========================================================

    for (
        direction,
        module,
    ), group in sequential_funnel.groupby(
        [
            "direction",
            "module",
        ]
    ):

        group = group.sort_values(
            "step"
        )

        counts = (
            group["count"]
            .astype(int)
            .tolist()
        )

        # ----------------------------------------------------
        # FUNNEL FÅR ALDRIG ÖKA
        # ----------------------------------------------------
        #
        # När ytterligare krav läggs till kan antalet
        # kandidater endast:
        #
        # - minska
        # - vara oförändrat
        #
        # aldrig öka.
        # ----------------------------------------------------

        assert all(
            current <= previous
            for previous, current in zip(
                counts,
                counts[1:],
            )
        ), (
            f"Funnel ökar oväntat för "
            f"{direction} {module}: {counts}"
        )

        # ----------------------------------------------------
        # COUNT RANGE
        # ----------------------------------------------------

        assert all(
            0 <= count <= len(diagnostics)
            for count in counts
        ), (
            f"Ogiltigt funnel count för "
            f"{direction} {module}: {counts}"
        )

    # ========================================================
    # SOLE BLOCKER MATHEMATICAL SANITY
    # ========================================================

    # Sole blocker måste vara en delmängd av
    # opportunity-setet.

    assert (
        sole_blockers["count"]
        <= sole_blockers["opportunity_count"]
    ).all()

    # Conditional blocker rate måste alltid ligga
    # mellan 0 och 100 procent.

    assert (
        sole_blockers[
            "conditional_block_rate"
        ].between(
            0.0,
            100.0,
            inclusive="both",
        )
    ).all()

    # ========================================================
    # OPPORTUNITY EVENT SANITY
    # ========================================================

    assert not opportunity_events.empty

    assert (
        opportunity_events["duration_bars"]
        >= 1
    ).all()

    assert (
        opportunity_events["event_start"]
        <= opportunity_events["event_end"]
    ).all()

    assert (
        opportunity_events["unique_blocker_count"]
        >= 1
    ).all()

    # ========================================================
    # OPPORTUNITY BAR CONSISTENCY
    # ========================================================
    #
    # Detta är den viktigaste kontrollen.
    #
    # Conditional Analysis räknar Sole Blocker-bars
    # separat för varje requirement.
    #
    # Opportunity Events grupperar exakt samma bars till
    # sammanhängande events.
    #
    # Därför måste:
    #
    # SUM(Sole Blocker counts)
    #
    # vara exakt samma som:
    #
    # SUM(Event duration bars)
    #
    # för varje direction + module.
    # ========================================================

    modules = [
        "Pullback",
        "Breakout",
        "Squeeze",
        "Mean Reversion",
    ]

    directions = [
        "Long",
        "Short",
    ]

    for direction in directions:

        for module in modules:

            module_sole_blockers = sole_blockers[
                (
                    sole_blockers["direction"]
                    == direction
                )
                & (
                    sole_blockers["module"]
                    == module
                )
            ]

            expected_opportunity_bars = int(
                module_sole_blockers[
                    "count"
                ].sum()
            )

            module_events = opportunity_events[
                (
                    opportunity_events["direction"]
                    == direction
                )
                & (
                    opportunity_events["module"]
                    == module
                )
            ]

            actual_opportunity_bars = int(
                module_events[
                    "duration_bars"
                ].sum()
            )

            assert (
                actual_opportunity_bars
                == expected_opportunity_bars
            ), (
                f"{direction} {module}: "
                f"events={actual_opportunity_bars}, "
                f"sole_blockers={expected_opportunity_bars}"
            )

    # ========================================================
    # PASS OUTPUT
    # ========================================================

    print("Market data                 PASS")
    print("Signal diagnostics          PASS")
    print("Signal funnel               PASS")
    print("Final blocker analysis      PASS")
    print("Failure combinations        PASS")
    print("Near-miss analysis          PASS")
    print("Module failure analysis     PASS")
    print("Module activation summary   PASS")
    print("Module conditional analysis PASS")
    print("Module funnel consistency   PASS")
    print("Conditional mathematics     PASS")
    print("Opportunity event analysis  PASS")
    print("Opportunity event consistency PASS")

    print()
    print("ALL ANALYSIS SANITY CHECKS PASSED")



_TEST_MODULES = {
    "Pullback": ("pb", "pullback", ["trend", "slow_ema", "rsi", "touch", "reclaim"]),
    "Breakout": ("bo", "breakout", ["trend", "price", "volume", "rsi"]),
    "Squeeze": ("sq", "squeeze", ["trend", "recent", "release", "price"]),
    "Mean Reversion": ("mr", "mean_rev", ["trend", "slow_ema", "oversold", "rsi_cross", "candle"]),
}


def _diagnostic_fixture(n=12):
    index = pd.date_range("2026-08-20 15:00", periods=n, freq="45min",
                          tz="America/New_York")
    columns = {}
    for _, (prefix, activation, requirements) in _TEST_MODULES.items():
        for direction in ("long", "short"):
            for requirement in requirements:
                if direction == "short" and requirement == "oversold":
                    requirement = "overbought"
                columns[f"{prefix}_{direction}_fail_{requirement}"] = True
            columns[f"{activation}_{direction}"] = False
    columns.update(long_signal=False, short_signal=False)
    return pd.DataFrame(columns, index=index)


def _set_bar(df, module, direction, position, blockers):
    prefix, activation, _ = _TEST_MODULES[module]
    columns = [c for c in df if c.startswith(f"{prefix}_{direction}_fail_")]
    df.loc[df.index[position], columns] = False
    for blocker in blockers:
        df.loc[df.index[position], f"{prefix}_{direction}_fail_{blocker}"] = True
    df.loc[df.index[position], f"{activation}_{direction}"] = not blockers


@pytest.mark.parametrize("module", _TEST_MODULES)
@pytest.mark.parametrize("direction", ["long", "short"])
@pytest.mark.parametrize("delay", [1, 3, 5, 6, None])
def test_conversion_windows_and_module_specificity(module, direction, delay):
    df = _diagnostic_fixture()
    _set_bar(df, module, direction, 1, ["trend"])
    if delay is not None:
        _set_bar(df, module, direction, 1 + delay, [])
    # Other modules/direction and a final signal cannot substitute for this module.
    other_direction = "short" if direction == "long" else "long"
    df.loc[df.index[2], f"pullback_{other_direction}"] = True
    df[f"{direction}_signal"] = False
    original = df.copy(deep=True)
    result = opportunity_signal_conversion(df)
    row = result.iloc[0]
    assert len(result) == 1
    expected = delay is not None and delay <= 5
    assert bool(row.converted) == expected
    for h in (1, 3, 5):
        suffix = "bar" if h == 1 else "bars"
        assert bool(row[f"converted_within_{h}_{suffix}"]) == (expected and delay <= h)
    if expected:
        assert row.conversion_time == df.index[1 + delay]
        assert row.bars_to_conversion == delay
        assert row.conversion_bar_position == 1 + delay
        assert not row.final_signal_at_conversion
    else:
        assert pd.isna(row.conversion_time)
        assert pd.isna(row.bars_to_conversion)
    assert_frame_equal(df, original)
    if delay == 6:
        assert opportunity_signal_conversion(df, max_followup_bars=6).iloc[0].bars_to_conversion == 6


def test_censoring_open_event_and_cohort_denominators():
    df = _diagnostic_fixture(12)
    for position in (0, 6, 9, 11):
        _set_bar(df, "Pullback", "long", position, ["reclaim"])
    for position in (1, 10):
        _set_bar(df, "Pullback", "long", position, [])
    events = opportunity_signal_conversion(df)
    assert events.converted.tolist()[:3] == [True, True, True]
    assert pd.isna(events.converted.iloc[3])
    assert events.event_open_at_data_end.tolist() == [False, False, False, True]
    assert events.followup_complete.tolist() == [True, True, False, False]
    summary = opportunity_conversion_summary(events).iloc[0]
    assert summary.opportunity_events == 4
    assert summary.converted_events == 3
    assert summary.censored_events == 1
    assert summary.eligible_events == 2
    assert summary.conversion_rate == 100
    assert summary.conversion_rate_within_1 == pytest.approx(200 / 3)
    assert summary.mean_bars_to_conversion == 2
    assert summary.median_bars_to_conversion == 1
    # Remove late activation: partial horizons become unknown, full ones false.
    _set_bar(df, "Pullback", "long", 10, ["trend", "reclaim"])
    events = opportunity_signal_conversion(df)
    assert not events.iloc[1].converted
    assert pd.isna(events.iloc[2].converted)
    assert not events.iloc[2].converted_within_1_bar
    assert pd.isna(events.iloc[2].converted_within_3_bars)


def test_blocker_transitions_event_contract_and_shared_activation():
    df = _diagnostic_fixture()
    for pos, blocker in [(0, "price"), (1, "price"), (2, "volume"), (4, "volume")]:
        _set_bar(df, "Breakout", "short", pos, [blocker])
    _set_bar(df, "Breakout", "short", 5, [])
    df.loc[df.index[5], "short_signal"] = True
    events = opportunity_signal_conversion(df)
    assert events.duration_bars.tolist() == [3, 1]
    assert events.iloc[0].dominant_blocker == "Price"
    assert events.iloc[0].blocker_changed
    assert events.iloc[0].blocker_sequence == "Price -> Price -> Volume"
    assert events.iloc[0].blocker_transition_path == "Price -> Volume"
    assert events.bars_to_conversion.tolist() == [3, 1]
    assert events.final_signal_at_conversion.all()
    assert_frame_equal(events[list(module_opportunity_events(df).columns)], module_opportunity_events(df))
    grouped = opportunity_conversion_summary(events, by_blocker=True)
    assert len(grouped) == 2
    assert opportunity_conversion_summary(events, by_blocker=True, min_events=2).empty


def test_empty_schemas_and_invalid_inputs():
    df = _diagnostic_fixture()
    _set_bar(df, "Squeeze", "short", 1, ["recent"])
    populated = opportunity_signal_conversion(df)
    for empty_input in (_diagnostic_fixture(), df.iloc[:0]):
        empty = opportunity_signal_conversion(empty_input)
        assert empty.empty
        assert empty.dtypes.equals(populated.dtypes)
        assert module_opportunity_events(empty_input).dtypes.equals(module_opportunity_events(df).dtypes)
        summary = opportunity_conversion_summary(empty)
        assert len(summary) == 8
        assert summary.opportunity_events.sum() == 0
        assert summary.conversion_rate.isna().all()
        assert opportunity_conversion_summary(empty, by_blocker=True).dtypes.equals(
            opportunity_conversion_summary(populated, by_blocker=True).dtypes)
    for horizon in (0, 4, True, 5.5):
        with pytest.raises(ValueError):
            opportunity_signal_conversion(df, max_followup_bars=horizon)
    for invalid in (df.iloc[::-1], pd.concat([df, df.iloc[:1]]), df.reset_index(drop=True)):
        with pytest.raises(ValueError):
            opportunity_signal_conversion(invalid)
    df["squeeze_short"] = df.squeeze_short.astype("boolean")
    df.loc[df.index[2], "squeeze_short"] = pd.NA
    with pytest.raises(ValueError, match="nonmissing booleans"):
        opportunity_signal_conversion(df)


def _ohlcv_fixture():
    t = np.arange(300)
    close = 100 + 0.03 * t + 8 * np.sin(t / 9)
    return pd.DataFrame({"open": close + np.cos(t), "high": close + 2,
                         "low": close - 2, "close": close,
                         "volume": 1000 + 300 * np.sin(t / 3)},
                        index=pd.date_range("2025-01-01", periods=len(t), freq="D"))


@pytest.mark.filterwarnings("ignore:DataFrame is highly fragmented:pandas.errors.PerformanceWarning")
def test_full_pipeline_prefix_causality_and_existing_analysis_contracts():
    data = _ohlcv_fixture()
    full = signal_diagnostics(data, allow_short=True)
    prefix = signal_diagnostics(data.iloc[:240], allow_short=True)
    assert_frame_equal(full.iloc[:240], prefix)
    before = full.copy(deep=True)
    result = analyze_signals(full)
    assert_frame_equal(full, before)
    for direction in ("long", "short"):
        for module, (mask_prefix, activation, _) in _TEST_MODULES.items():
            assert (full[f"{mask_prefix}_{direction}_fail_mask"].eq(0)
                    == full[f"{activation}_{direction}"]).all()
            events = result["module_opportunity_events"]
            group = events[(events.direction == direction.title()) & (events.module == module)]
            conditional = result["module_conditional_analysis"]
            sole = conditional[(conditional.direction == direction.title()) &
                               (conditional.module == module) &
                               (conditional.analysis_type == "Sole Blocker")]
            assert group.duration_bars.sum() == sole["count"].sum()
    empty = analyze_signals(full.iloc[:0])
    for key in result:
        assert list(result[key].columns) == list(empty[key].columns)
    # Completed retrospective windows cannot change when future rows are appended.
    early = opportunity_signal_conversion(prefix)
    completed = early[early.followup_complete]
    later = result["opportunity_signal_conversion"]
    later = later.merge(completed[["direction", "module", "event_start"]],
                        on=["direction", "module", "event_start"], how="inner")
    assert_frame_equal(completed.reset_index(drop=True), later[completed.columns].reset_index(drop=True))


def test_partial_session_and_overnight_gap_count_observed_bars():
    df = _diagnostic_fixture(3)
    df.index = pd.DatetimeIndex([
        "2026-08-20 15:15", "2026-08-21 09:30", "2026-08-21 10:15",
    ], tz="America/New_York")
    _set_bar(df, "Squeeze", "long", 0, ["recent"])
    _set_bar(df, "Squeeze", "long", 1, [])
    partial = opportunity_signal_conversion(df.iloc[:1]).iloc[0]
    assert partial.event_open_at_data_end
    assert pd.isna(partial.converted)
    complete = opportunity_signal_conversion(df).iloc[0]
    assert complete.bars_to_conversion == 1
    assert complete.conversion_time == df.index[1]
    assert not complete.followup_complete
    assert complete.converted_within_5_bars


def test_unrelated_final_signal_does_not_convert_opportunity():
    df = _diagnostic_fixture()
    _set_bar(df, "Pullback", "long", 1, ["reclaim"])
    _set_bar(df, "Breakout", "long", 2, [])
    df.loc[df.index[2], "long_signal"] = True
    row = opportunity_signal_conversion(df).iloc[0]
    assert not row.converted
    assert pd.isna(row.final_signal_at_conversion)


if __name__ == "__main__":
    main()
