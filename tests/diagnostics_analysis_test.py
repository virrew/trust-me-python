from __future__ import annotations

import pandas as pd

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


if __name__ == "__main__":
    main()