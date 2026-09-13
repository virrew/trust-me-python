from __future__ import annotations

import pandas as pd


# ============================================================
# HELPERS
# ============================================================

def _count_true(series: pd.Series) -> int:
    """
    Räknar antal True-värden i en boolesk Series.
    NaN behandlas som False.
    """
    return int(
        series
        .fillna(False)
        .astype(bool)
        .sum()
    )


def _rate(
    count: int,
    denominator: int,
) -> float:
    """
    Returnerar andel i procent.

    Exempel:
    25 av 100 -> 25.0
    """
    if denominator == 0:
        return 0.0

    return (count / denominator) * 100.0


# ============================================================
# SIGNAL FUNNEL
# ============================================================

def signal_funnel(
    diagnostics: pd.DataFrame,
) -> pd.DataFrame:
    """
    Bygger en deskriptiv funnel för Long och Short.

    Syftet är att svara på frågor som:

    - Hur ofta är riktningen tillåten?
    - Hur ofta är alla non-score-filter redo?
    - Hur ofta finns minst en aktiv entry-modul?
    - Hur ofta uppstår slutlig signal?
    - Hur ofta väntar strategin endast på score?
    - Hur ofta är situationen en near miss?

    Funktionen ändrar INTE strategilogiken.
    Den analyserar redan beräknad Signal Diagnostics-data.
    """

    total_bars = len(diagnostics)

    rows: list[dict[str, object]] = []

    # --------------------------------------------------------
    # LONG
    # --------------------------------------------------------

    long_direction_allowed = _count_true(
        diagnostics["allow_long"]
    )

    long_non_score_ready = _count_true(
        diagnostics["long_non_score_ready"]
    )

    long_module_active = int(
        (
            diagnostics["long_score"] > 0
        ).sum()
    )

    long_score_ready = int(
        (
            diagnostics["long_score"]
            >= diagnostics["min_confluence"]
        ).sum()
    )

    long_waiting_for_score = _count_true(
        diagnostics["long_waiting_for_score"]
    )

    long_near_miss = _count_true(
        diagnostics["long_near_miss"]
    )

    long_signal = _count_true(
        diagnostics["long_signal"]
    )

    long_values = [
        ("Total Bars", total_bars),
        (
            "Direction Allowed",
            long_direction_allowed,
        ),
        (
            "Non-Score Ready",
            long_non_score_ready,
        ),
        (
            "Any Module Active",
            long_module_active,
        ),
        (
            "Score Requirement Met",
            long_score_ready,
        ),
        (
            "Waiting For Score",
            long_waiting_for_score,
        ),
        (
            "Near Miss",
            long_near_miss,
        ),
        (
            "Final Signal",
            long_signal,
        ),
    ]

    for metric, count in long_values:
        rows.append(
            {
                "direction": "Long",
                "metric": metric,
                "count": count,
                "pct_of_all_bars": _rate(
                    count,
                    total_bars,
                ),
            }
        )

    # --------------------------------------------------------
    # SHORT
    # --------------------------------------------------------

    short_direction_allowed = _count_true(
        diagnostics["allow_short"]
    )

    short_non_score_ready = _count_true(
        diagnostics["short_non_score_ready"]
    )

    short_module_active = int(
        (
            diagnostics["short_score"] > 0
        ).sum()
    )

    short_score_ready = int(
        (
            diagnostics["short_score"]
            >= diagnostics["min_confluence"]
        ).sum()
    )

    short_waiting_for_score = _count_true(
        diagnostics["short_waiting_for_score"]
    )

    short_near_miss = _count_true(
        diagnostics["short_near_miss"]
    )

    short_signal = _count_true(
        diagnostics["short_signal"]
    )

    short_values = [
        ("Total Bars", total_bars),
        (
            "Direction Allowed",
            short_direction_allowed,
        ),
        (
            "Non-Score Ready",
            short_non_score_ready,
        ),
        (
            "Any Module Active",
            short_module_active,
        ),
        (
            "Score Requirement Met",
            short_score_ready,
        ),
        (
            "Waiting For Score",
            short_waiting_for_score,
        ),
        (
            "Near Miss",
            short_near_miss,
        ),
        (
            "Final Signal",
            short_signal,
        ),
    ]

    for metric, count in short_values:
        rows.append(
            {
                "direction": "Short",
                "metric": metric,
                "count": count,
                "pct_of_all_bars": _rate(
                    count,
                    total_bars,
                ),
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# FINAL FILTER BLOCKER ANALYSIS
# ============================================================

def final_filter_blockers(
    diagnostics: pd.DataFrame,
) -> pd.DataFrame:
    """
    Räknar hur ofta varje slutfilter fallerar.

    Viktigt:
    En bar kan ha FLERA blockerare samtidigt.

    Därför summerar inte procentsatserna nödvändigtvis
    till 100 %.

    Detta är avsiktligt och gör att vi kan identifiera
    vilka final filters som oftast begränsar strategin.
    """

    total_bars = len(diagnostics)

    blocker_columns = {
        "Direction": (
            "long_fail_direction",
            "short_fail_direction",
        ),
        "Score": (
            "long_fail_score",
            "short_fail_score",
        ),
        "Volatility": (
            "long_fail_volatility",
            "short_fail_volatility",
        ),
        "Candle": (
            "long_fail_candle",
            "short_fail_candle",
        ),
        "Session": (
            "long_fail_session",
            "short_fail_session",
        ),
        "Confirmed": (
            "long_fail_confirmed",
            "short_fail_confirmed",
        ),
    }

    rows: list[dict[str, object]] = []

    for blocker, (
        long_column,
        short_column,
    ) in blocker_columns.items():

        long_count = _count_true(
            diagnostics[long_column]
        )

        short_count = _count_true(
            diagnostics[short_column]
        )

        rows.append(
            {
                "direction": "Long",
                "blocker": blocker,
                "count": long_count,
                "pct_of_all_bars": _rate(
                    long_count,
                    total_bars,
                ),
            }
        )

        rows.append(
            {
                "direction": "Short",
                "blocker": blocker,
                "count": short_count,
                "pct_of_all_bars": _rate(
                    short_count,
                    total_bars,
                ),
            }
        )

    result = pd.DataFrame(rows)

    return result


# ============================================================
# FINAL FAILURE COMBINATIONS
# ============================================================

def final_failure_combinations(
    diagnostics: pd.DataFrame,
) -> pd.DataFrame:
    """
    Analyserar vilka kombinationer av final-filter failures
    som är vanligast.

    Vi använder long_final_fail_mask och
    short_final_fail_mask som redan verifierats mot Pine.

    Exempel:

    mask 2:
        Score

    mask 3:
        Direction + Score

    mask 6:
        Score + Volatility

    Detta gör det möjligt att senare svara på:

    "Vilken kombination av regler blockerar flest setups?"
    """

    rows: list[dict[str, object]] = []

    for direction, column in [
        (
            "Long",
            "long_final_fail_mask",
        ),
        (
            "Short",
            "short_final_fail_mask",
        ),
    ]:

        counts = (
            diagnostics[column]
            .value_counts(dropna=False)
            .sort_values(ascending=False)
        )

        total = len(diagnostics)

        for mask, count in counts.items():

            rows.append(
                {
                    "direction": direction,
                    "fail_mask": int(mask),
                    "count": int(count),
                    "pct_of_all_bars": _rate(
                        int(count),
                        total,
                    ),
                }
            )

    return pd.DataFrame(rows)


# ============================================================
# NEAR-MISS SUMMARY
# ============================================================

def near_miss_summary(
    diagnostics: pd.DataFrame,
) -> pd.DataFrame:
    """
    Sammanfattar Near-Miss-beteendet.

    Vi mäter bland annat:

    - antal near misses
    - hur ofta respektive final filter var enda blockeraren
    - genomsnittlig streak
    - median streak
    - maximal streak

    Detta är början på analysen av hur "nära"
    strategin ofta befinner sig en signal.
    """

    rows: list[dict[str, object]] = []

    near_miss_reasons = {
        "Direction": "direction",
        "Score": "score",
        "Volatility": "volatility",
        "Candle": "candle",
        "Session": "session",
        "Confirmed": "confirmed",
    }

    for direction_lower, direction_name in [
        ("long", "Long"),
        ("short", "Short"),
    ]:

        near_miss_column = (
            f"{direction_lower}_near_miss"
        )

        streak_column = (
            f"{direction_lower}_near_miss_streak"
        )

        total_near_misses = _count_true(
            diagnostics[near_miss_column]
        )

        rows.append(
            {
                "direction": direction_name,
                "metric": "Total Near Misses",
                "value": float(total_near_misses),
            }
        )

        # ----------------------------------------------------
        # NEAR-MISS REASONS
        # ----------------------------------------------------

        for label, suffix in near_miss_reasons.items():

            column = (
                f"{direction_lower}_near_miss_{suffix}"
            )

            count = _count_true(
                diagnostics[column]
            )

            rows.append(
                {
                    "direction": direction_name,
                    "metric": (
                        f"Near Miss - {label}"
                    ),
                    "value": float(count),
                }
            )

        # ----------------------------------------------------
        # STREAK STATISTICS
        # ----------------------------------------------------
        #
        # Vi tittar endast på bars där streak > 0.
        # ----------------------------------------------------

        streaks = diagnostics.loc[
            diagnostics[streak_column] > 0,
            streak_column,
        ]

        if len(streaks) > 0:

            average_streak = float(
                streaks.mean()
            )

            median_streak = float(
                streaks.median()
            )

            max_streak = float(
                streaks.max()
            )

        else:
            average_streak = 0.0
            median_streak = 0.0
            max_streak = 0.0

        rows.extend(
            [
                {
                    "direction": direction_name,
                    "metric": "Average Near-Miss Streak",
                    "value": average_streak,
                },
                {
                    "direction": direction_name,
                    "metric": "Median Near-Miss Streak",
                    "value": median_streak,
                },
                {
                    "direction": direction_name,
                    "metric": "Max Near-Miss Streak",
                    "value": max_streak,
                },
            ]
        )

    return pd.DataFrame(rows)

# ============================================================
# MODULE FAILURE ANALYSIS
# ============================================================

def module_failure_analysis(
    diagnostics: pd.DataFrame,
) -> pd.DataFrame:
    """
    Analyserar varför respektive entry-modul inte aktiveras.

    För varje modul och riktning räknar vi:
    - hur många bars varje krav fallerar
    - hur stor andel av samtliga bars det motsvarar

    Flera krav kan fallera på samma bar.
    Procentsatserna behöver därför inte summera till 100 %.
    """

    total_bars = len(diagnostics)

    rows: list[dict[str, object]] = []

    # --------------------------------------------------------
    # MODULE DEFINITIONS
    # --------------------------------------------------------

    module_definitions = {
        "Pullback": {
            "Long": {
                "Trend": "pb_long_fail_trend",
                "Slow EMA": "pb_long_fail_slow_ema",
                "RSI": "pb_long_fail_rsi",
                "Touch": "pb_long_fail_touch",
                "Reclaim": "pb_long_fail_reclaim",
            },
            "Short": {
                "Trend": "pb_short_fail_trend",
                "Slow EMA": "pb_short_fail_slow_ema",
                "RSI": "pb_short_fail_rsi",
                "Touch": "pb_short_fail_touch",
                "Reclaim": "pb_short_fail_reclaim",
            },
        },

        "Breakout": {
            "Long": {
                "Trend": "bo_long_fail_trend",
                "Price": "bo_long_fail_price",
                "Volume": "bo_long_fail_volume",
                "RSI": "bo_long_fail_rsi",
            },
            "Short": {
                "Trend": "bo_short_fail_trend",
                "Price": "bo_short_fail_price",
                "Volume": "bo_short_fail_volume",
                "RSI": "bo_short_fail_rsi",
            },
        },

        "Squeeze": {
            "Long": {
                "Trend": "sq_long_fail_trend",
                "Recent Squeeze": "sq_long_fail_recent",
                "Release": "sq_long_fail_release",
                "Price": "sq_long_fail_price",
            },
            "Short": {
                "Trend": "sq_short_fail_trend",
                "Recent Squeeze": "sq_short_fail_recent",
                "Release": "sq_short_fail_release",
                "Price": "sq_short_fail_price",
            },
        },

        "Mean Reversion": {
            "Long": {
                "Trend": "mr_long_fail_trend",
                "Slow EMA": "mr_long_fail_slow_ema",
                "Oversold": "mr_long_fail_oversold",
                "RSI Cross": "mr_long_fail_rsi_cross",
                "Candle": "mr_long_fail_candle",
            },
            "Short": {
                "Trend": "mr_short_fail_trend",
                "Slow EMA": "mr_short_fail_slow_ema",
                "Overbought": "mr_short_fail_overbought",
                "RSI Cross": "mr_short_fail_rsi_cross",
                "Candle": "mr_short_fail_candle",
            },
        },
    }

    # --------------------------------------------------------
    # COUNT FAILURES
    # --------------------------------------------------------

    for module, directions in module_definitions.items():
        for direction, failures in directions.items():
            for requirement, column in failures.items():

                count = _count_true(
                    diagnostics[column]
                )

                rows.append(
                    {
                        "direction": direction,
                        "module": module,
                        "requirement": requirement,
                        "fail_count": count,
                        "fail_pct_all_bars": _rate(
                            count,
                            total_bars,
                        ),
                    }
                )

    return pd.DataFrame(rows)


# ============================================================
# MODULE ACTIVATION SUMMARY
# ============================================================

def module_activation_summary(
    diagnostics: pd.DataFrame,
) -> pd.DataFrame:
    """
    Räknar hur ofta varje färdig entry-modul
    faktiskt aktiveras.

    Failure Analysis:
        Varför aktiverades modulen inte?

    Activation Summary:
        Hur ofta lyckades alla modulkrav samtidigt?
    """

    total_bars = len(diagnostics)

    module_columns = {
        "Pullback": (
            "pullback_long",
            "pullback_short",
        ),
        "Breakout": (
            "breakout_long",
            "breakout_short",
        ),
        "Squeeze": (
            "squeeze_long",
            "squeeze_short",
        ),
        "Mean Reversion": (
            "mean_rev_long",
            "mean_rev_short",
        ),
    }

    rows: list[dict[str, object]] = []

    for module, (
        long_column,
        short_column,
    ) in module_columns.items():

        for direction, column in [
            ("Long", long_column),
            ("Short", short_column),
        ]:

            count = _count_true(
                diagnostics[column]
            )

            rows.append(
                {
                    "direction": direction,
                    "module": module,
                    "activation_count": count,
                    "activation_pct_all_bars": _rate(
                        count,
                        total_bars,
                    ),
                }
            )

    return pd.DataFrame(rows)

# ============================================================
# MODULE CONDITIONAL ANALYSIS
# ============================================================

def module_conditional_analysis(
    diagnostics: pd.DataFrame,
) -> pd.DataFrame:
    """
    Djupanalys av entry-modulernas krav.

    För varje modul och riktning mäter vi två saker:

    1. Sequential Funnel
       Hur många bars överlever kraven steg för steg?

    2. Sole Blocker
       Hur ofta är ett specifikt krav det ENDA kravet
       som fallerar medan alla andra krav i modulen passerar?

    Sole Blocker är särskilt viktigt eftersom det identifierar
    riktiga module-level near misses.

    Exempel:
        Trend     = PASS
        Price     = PASS
        Volume    = FAIL
        RSI       = PASS

    Då är Volume ensam blockerare för Breakout-modulen.
    """

    total_bars = len(diagnostics)

    rows: list[dict[str, object]] = []

    # --------------------------------------------------------
    # MODULE DEFINITIONS
    # --------------------------------------------------------
    #
    # Ordningen här används också som ordning i
    # Sequential Funnel.
    # --------------------------------------------------------

    module_definitions = {
        "Pullback": {
            "Long": [
                ("Trend", "pb_long_fail_trend"),
                ("Slow EMA", "pb_long_fail_slow_ema"),
                ("RSI", "pb_long_fail_rsi"),
                ("Touch", "pb_long_fail_touch"),
                ("Reclaim", "pb_long_fail_reclaim"),
            ],
            "Short": [
                ("Trend", "pb_short_fail_trend"),
                ("Slow EMA", "pb_short_fail_slow_ema"),
                ("RSI", "pb_short_fail_rsi"),
                ("Touch", "pb_short_fail_touch"),
                ("Reclaim", "pb_short_fail_reclaim"),
            ],
        },

        "Breakout": {
            "Long": [
                ("Trend", "bo_long_fail_trend"),
                ("Price", "bo_long_fail_price"),
                ("Volume", "bo_long_fail_volume"),
                ("RSI", "bo_long_fail_rsi"),
            ],
            "Short": [
                ("Trend", "bo_short_fail_trend"),
                ("Price", "bo_short_fail_price"),
                ("Volume", "bo_short_fail_volume"),
                ("RSI", "bo_short_fail_rsi"),
            ],
        },

        "Squeeze": {
            "Long": [
                ("Trend", "sq_long_fail_trend"),
                ("Recent Squeeze", "sq_long_fail_recent"),
                ("Release", "sq_long_fail_release"),
                ("Price", "sq_long_fail_price"),
            ],
            "Short": [
                ("Trend", "sq_short_fail_trend"),
                ("Recent Squeeze", "sq_short_fail_recent"),
                ("Release", "sq_short_fail_release"),
                ("Price", "sq_short_fail_price"),
            ],
        },

        "Mean Reversion": {
            "Long": [
                ("Trend", "mr_long_fail_trend"),
                ("Slow EMA", "mr_long_fail_slow_ema"),
                ("Oversold", "mr_long_fail_oversold"),
                ("RSI Cross", "mr_long_fail_rsi_cross"),
                ("Candle", "mr_long_fail_candle"),
            ],
            "Short": [
                ("Trend", "mr_short_fail_trend"),
                ("Slow EMA", "mr_short_fail_slow_ema"),
                ("Overbought", "mr_short_fail_overbought"),
                ("RSI Cross", "mr_short_fail_rsi_cross"),
                ("Candle", "mr_short_fail_candle"),
            ],
        },
    }

    # ========================================================
    # ANALYZE EACH MODULE
    # ========================================================

    for module, directions in module_definitions.items():

        for direction, requirements in directions.items():

            # ------------------------------------------------
            # PASS SERIES
            # ------------------------------------------------
            #
            # Failure-kolumnerna är True när kravet FAILAR.
            # Därför inverterar vi dem för att få PASS.
            # ------------------------------------------------

            pass_series: dict[str, pd.Series] = {}

            for requirement, fail_column in requirements:

                fail = (
                    diagnostics[fail_column]
                    .fillna(False)
                    .astype(bool)
                )

                pass_series[requirement] = ~fail

            # ------------------------------------------------
            # SEQUENTIAL FUNNEL
            # ------------------------------------------------

            cumulative_pass = pd.Series(
                True,
                index=diagnostics.index,
                dtype=bool,
            )

            previous_count = total_bars

            for step, (
                requirement,
                _,
            ) in enumerate(
                requirements,
                start=1,
            ):

                cumulative_pass = (
                    cumulative_pass
                    & pass_series[requirement]
                )

                pass_count = int(
                    cumulative_pass.sum()
                )

                dropped_at_step = (
                    previous_count
                    - pass_count
                )

                rows.append(
                    {
                        "direction": direction,
                        "module": module,
                        "analysis_type": "Sequential Funnel",
                        "step": step,
                        "requirement": requirement,
                        "count": pass_count,
                        "pct_of_all_bars": _rate(
                            pass_count,
                            total_bars,
                        ),
                        "dropped_at_step": dropped_at_step,
                        "drop_pct_previous_step": _rate(
                            dropped_at_step,
                            previous_count,
                        ),
                    }
                )

                previous_count = pass_count

            # ------------------------------------------------
            # SOLE BLOCKER ANALYSIS
            # ------------------------------------------------
            #
            # Ett krav är Sole Blocker när:
            #
            # - just det kravet FAILAR
            # - ALLA andra krav PASSERAR
            #
            # Detta är vår riktiga module-level near miss.
            # ------------------------------------------------

            for requirement, fail_column in requirements:

                target_fail = (
                    diagnostics[fail_column]
                    .fillna(False)
                    .astype(bool)
                )

                all_others_pass = pd.Series(
                    True,
                    index=diagnostics.index,
                    dtype=bool,
                )

                for (
                    other_requirement,
                    _,
                ) in requirements:

                    if (
                        other_requirement
                        == requirement
                    ):
                        continue

                    all_others_pass = (
                        all_others_pass
                        & pass_series[
                            other_requirement
                        ]
                    )

                sole_blocker = (
                    target_fail
                    & all_others_pass
                )

                sole_blocker_count = int(
                    sole_blocker.sum()
                )

                # --------------------------------------------
                # OPPORTUNITY SET
                # --------------------------------------------
                #
                # Hur många bars hade alla ANDRA krav redo?
                #
                # Detta är nämnaren som är mest intressant
                # för conditional blocker rate.
                # --------------------------------------------

                opportunity_count = int(
                    all_others_pass.sum()
                )

                rows.append(
                    {
                        "direction": direction,
                        "module": module,
                        "analysis_type": "Sole Blocker",
                        "step": pd.NA,
                        "requirement": requirement,
                        "count": sole_blocker_count,
                        "pct_of_all_bars": _rate(
                            sole_blocker_count,
                            total_bars,
                        ),
                        "dropped_at_step": pd.NA,
                        "drop_pct_previous_step": pd.NA,
                        "opportunity_count": opportunity_count,
                        "conditional_block_rate": _rate(
                            sole_blocker_count,
                            opportunity_count,
                        ),
                    }
                )

    return pd.DataFrame(rows)

# ============================================================
# MODULE OPPORTUNITY EVENTS
# ============================================================

def module_opportunity_events(
    diagnostics: pd.DataFrame,
) -> pd.DataFrame:
    """
    Identifierar sammanhängande module-level opportunity events.

    En opportunity-bar definieras här som:

        exakt ETT modulkrav fallerar

    medan alla övriga krav i samma modul passerar.

    Detta motsvarar vår tidigare Sole Blocker-logik, men här
    arbetar vi på tidsserien istället för att bara summera counts.

    Sammanhängande opportunity-bars för samma:
    - direction
    - module

    grupperas till ett event.

    Ett event kan därför svara på:
    - när setupen började
    - när setupen slutade
    - hur många bars den varade
    - vilka sole blockers som förekom
    - om blockeraren ändrades under eventet
    """

    rows: list[dict[str, object]] = []

    module_definitions = {
        "Pullback": {
            "Long": [
                ("Trend", "pb_long_fail_trend"),
                ("Slow EMA", "pb_long_fail_slow_ema"),
                ("RSI", "pb_long_fail_rsi"),
                ("Touch", "pb_long_fail_touch"),
                ("Reclaim", "pb_long_fail_reclaim"),
            ],
            "Short": [
                ("Trend", "pb_short_fail_trend"),
                ("Slow EMA", "pb_short_fail_slow_ema"),
                ("RSI", "pb_short_fail_rsi"),
                ("Touch", "pb_short_fail_touch"),
                ("Reclaim", "pb_short_fail_reclaim"),
            ],
        },

        "Breakout": {
            "Long": [
                ("Trend", "bo_long_fail_trend"),
                ("Price", "bo_long_fail_price"),
                ("Volume", "bo_long_fail_volume"),
                ("RSI", "bo_long_fail_rsi"),
            ],
            "Short": [
                ("Trend", "bo_short_fail_trend"),
                ("Price", "bo_short_fail_price"),
                ("Volume", "bo_short_fail_volume"),
                ("RSI", "bo_short_fail_rsi"),
            ],
        },

        "Squeeze": {
            "Long": [
                ("Trend", "sq_long_fail_trend"),
                ("Recent Squeeze", "sq_long_fail_recent"),
                ("Release", "sq_long_fail_release"),
                ("Price", "sq_long_fail_price"),
            ],
            "Short": [
                ("Trend", "sq_short_fail_trend"),
                ("Recent Squeeze", "sq_short_fail_recent"),
                ("Release", "sq_short_fail_release"),
                ("Price", "sq_short_fail_price"),
            ],
        },

        "Mean Reversion": {
            "Long": [
                ("Trend", "mr_long_fail_trend"),
                ("Slow EMA", "mr_long_fail_slow_ema"),
                ("Oversold", "mr_long_fail_oversold"),
                ("RSI Cross", "mr_long_fail_rsi_cross"),
                ("Candle", "mr_long_fail_candle"),
            ],
            "Short": [
                ("Trend", "mr_short_fail_trend"),
                ("Slow EMA", "mr_short_fail_slow_ema"),
                ("Overbought", "mr_short_fail_overbought"),
                ("RSI Cross", "mr_short_fail_rsi_cross"),
                ("Candle", "mr_short_fail_candle"),
            ],
        },
    }

    # ========================================================
    # ANALYZE EACH MODULE / DIRECTION
    # ========================================================

    for module, directions in module_definitions.items():

        for direction, requirements in directions.items():

            # ------------------------------------------------
            # BUILD FAILURE MATRIX
            # ------------------------------------------------

            failure_matrix = pd.DataFrame(
                index=diagnostics.index
            )

            for requirement, fail_column in requirements:

                failure_matrix[requirement] = (
                    diagnostics[fail_column]
                    .fillna(False)
                    .astype(bool)
                )

            # ------------------------------------------------
            # EXACTLY ONE FAILURE
            # ------------------------------------------------

            fail_count = failure_matrix.sum(
                axis=1
            )

            opportunity = (
                fail_count == 1
            )

            # Vilket krav är sole blocker på varje bar?
            sole_blocker = pd.Series(
                pd.NA,
                index=diagnostics.index,
                dtype="object",
            )

            for requirement in failure_matrix.columns:

                mask = (
                    opportunity
                    & failure_matrix[requirement]
                )

                sole_blocker.loc[mask] = requirement

            # ------------------------------------------------
            # GROUP CONSECUTIVE OPPORTUNITY BARS
            # ------------------------------------------------

            event_id = (
                opportunity.ne(
                    opportunity.shift(
                        fill_value=False
                    )
                )
                .cumsum()
            )

            opportunity_ids = event_id[
                opportunity
            ].unique()

            for local_event_id in opportunity_ids:

                event_mask = (
                    opportunity
                    & (event_id == local_event_id)
                )

                event_index = diagnostics.index[
                    event_mask
                ]

                if len(event_index) == 0:
                    continue

                blockers = (
                    sole_blocker.loc[event_mask]
                    .dropna()
                    .astype(str)
                )

                blocker_sequence = blockers.tolist()

                unique_blockers = list(
                    dict.fromkeys(
                        blocker_sequence
                    )
                )

                # --------------------------------------------
                # DOMINANT BLOCKER
                # --------------------------------------------

                if blockers.empty:
                    dominant_blocker = pd.NA
                else:
                    dominant_blocker = (
                        blockers
                        .value_counts()
                        .idxmax()
                    )

                # --------------------------------------------
                # EVENT ROW
                # --------------------------------------------

                rows.append(
                    {
                        "direction": direction,
                        "module": module,
                        "event_start": event_index[0],
                        "event_end": event_index[-1],
                        "duration_bars": len(event_index),
                        "dominant_blocker": dominant_blocker,
                        "blocker_changed": (
                            len(unique_blockers) > 1
                        ),
                        "unique_blocker_count": (
                            len(unique_blockers)
                        ),
                        "blocker_sequence": (
                            " -> ".join(
                                blocker_sequence
                            )
                        ),
                    }
                )

    return pd.DataFrame(rows)

# ============================================================
# FULL SIGNAL ANALYSIS
# ============================================================

def analyze_signals(
    diagnostics: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """
    Kör första kompletta deskriptiva analyslagret
    ovanpå Signal Diagnostics.

    Returnerar separata tabeller så att framtida kod kan:

    - skriva terminalrapporter
    - exportera CSV / Excel
    - jämföra tickers
    - jämföra timeframes
    - mata Outcome Engine
    - bygga scanner/ranking
    """

    return {
        "signal_funnel": signal_funnel(
            diagnostics
        ),
        "final_filter_blockers": final_filter_blockers(
            diagnostics
        ),
        "final_failure_combinations": (
            final_failure_combinations(
                diagnostics
            )
        ),
        "near_miss_summary": near_miss_summary(
            diagnostics
        ),
        "module_failure_analysis": (
            module_failure_analysis(
                diagnostics
            )
        ),
        "module_activation_summary": (
            module_activation_summary(
                diagnostics
            )
        ),
        "module_conditional_analysis": (
            module_conditional_analysis(
                diagnostics
            )
        ),
        "module_opportunity_events": (
            module_opportunity_events(
                diagnostics
            )
        ),
    }