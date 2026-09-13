from __future__ import annotations

import pandas as pd

from src.market_data import download_yahoo_data
from src.diagnostics_signals import signal_diagnostics


def main() -> None:
    """
    Baseline-test för Trust Me Signal Diagnostics.

    Testfall:
    - Ticker: MU
    - Mode: Swing
    - Chart TF: 1D
    - Datum: 2026-08-21

    Steg 1:
    Verifiera Entry Modules mot Pine Signal Diagnostics.

    Ingen optimering görs här.
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

        # Mode
        is_swing=True,
        allow_long=True,
        allow_short=False,

        # Trend
        ema_fast_length=50,
        ema_slow_length=200,
        adx_length=14,
        adx_min_swing=18.0,
        adx_min_intraday=15.0,

        # Volatility
        atr_length=14,
        min_atr_pct_swing=1.0,
        min_atr_pct_intraday=0.3,
        use_candle_filter=True,
        max_candle_atr=2.0,

        # Momentum
        rsi_length=14,
        rsi_smooth_len=9,
        confluence_window_swing=5,
        confluence_window_intraday=8,

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
    # REFERENSDATUM
    # ========================================================

    timestamp = pd.Timestamp("2026-08-21")

    if timestamp not in diagnostics.index:
        raise KeyError(
            f"Hittade inte {timestamp} i signal diagnostic-datan."
        )

    row = diagnostics.loc[timestamp]

    # ========================================================
    # BASELINE
    # ========================================================

    print()
    print("#" * 70)
    print("TRUST ME — SIGNAL DIAGNOSTIC BASELINE")
    print("#" * 70)

    print(f"Ticker:    {ticker}")
    print("Mode:      Swing")
    print("Chart TF:  1D")
    print(f"Date:      {timestamp.date()}")

    # ========================================================
    # ENTRY MODULES
    # ========================================================

    print()
    print("=" * 70)
    print("ENTRY MODULE DIAGNOSTICS")
    print("=" * 70)

    print()
    print("--- LONG MODULES ---")

    print(
        f"Pullback Long:        "
        f"{bool(row['pullback_long'])}"
    )

    print(
        f"Breakout Long:        "
        f"{bool(row['breakout_long'])}"
    )

    print(
        f"Squeeze Long:         "
        f"{bool(row['squeeze_long'])}"
    )

    print(
        f"Mean Reversion Long:  "
        f"{bool(row['mean_rev_long'])}"
    )

    print()
    print("--- SHORT MODULES ---")

    print(
        f"Pullback Short:       "
        f"{bool(row['pullback_short'])}"
    )

    print(
        f"Breakout Short:       "
        f"{bool(row['breakout_short'])}"
    )

    print(
        f"Squeeze Short:        "
        f"{bool(row['squeeze_short'])}"
    )

    print(
        f"Mean Reversion Short: "
        f"{bool(row['mean_rev_short'])}"
    )

    # ========================================================
    # MODULE SUMMARY / SCORE
    # ========================================================

    print()
    print("=" * 70)
    print("MODULE SUMMARY / SCORE")
    print("=" * 70)

    print(
        f"Long Score:          "
        f"{int(row['long_score'])}"
    )

    print(
        f"Long Modules:        "
        f"{repr(row['long_module_text'])}"
    )

    print(
        f"Short Score:         "
        f"{int(row['short_score'])}"
    )

    print(
        f"Short Modules:       "
        f"{repr(row['short_module_text'])}"
    )

    print(
        f"Min Confluence:      "
        f"{int(row['min_confluence'])}"
    )

    # ========================================================
    # FINAL SIGNAL DIAGNOSTICS
    # ========================================================

    print()
    print("=" * 70)
    print("FINAL SIGNAL DIAGNOSTICS")
    print("=" * 70)

    # --------------------------------------------------------
    # SIGNAL INPUTS
    # --------------------------------------------------------

    print()
    print("--- SIGNAL INPUTS ---")

    print(
        f"Allow Long:           "
        f"{bool(row['allow_long'])}"
    )

    print(
        f"Allow Short:          "
        f"{bool(row['allow_short'])}"
    )

    print(
        f"Long Score:           "
        f"{int(row['long_score'])}"
    )

    print(
        f"Short Score:          "
        f"{int(row['short_score'])}"
    )

    print(
        f"Min Confluence:       "
        f"{int(row['min_confluence'])}"
    )

    print(
        f"Volatility OK:        "
        f"{bool(row['volatility_ok'])}"
    )

    print(
        f"Not Overextended:     "
        f"{bool(row['not_overextended'])}"
    )

    print(
        f"Session OK:           "
        f"{bool(row['session_ok'])}"
    )

    print(
        f"Confirmed Bar:        "
        f"{bool(row['is_confirmed'])}"
    )

    # --------------------------------------------------------
    # FINAL SIGNAL
    # --------------------------------------------------------

    print()
    print("--- FINAL SIGNAL ---")

    print(
        f"Long Signal:          "
        f"{bool(row['long_signal'])}"
    )

    print(
        f"Short Signal:         "
        f"{bool(row['short_signal'])}"
    )

    # ========================================================
    # FAILURE / NEAR-MISS DIAGNOSTICS
    # ========================================================

    print()
    print("=" * 70)
    print("FAILURE / NEAR-MISS DIAGNOSTICS")
    print("=" * 70)

    # --------------------------------------------------------
    # LONG
    # --------------------------------------------------------

    print()
    print("--- LONG FAILURE ---")

    print(
        f"Fail Direction:       "
        f"{bool(row['long_fail_direction'])}"
    )

    print(
        f"Fail Score:           "
        f"{bool(row['long_fail_score'])}"
    )

    print(
        f"Fail Volatility:      "
        f"{bool(row['long_fail_volatility'])}"
    )

    print(
        f"Fail Candle:          "
        f"{bool(row['long_fail_candle'])}"
    )

    print(
        f"Fail Session:         "
        f"{bool(row['long_fail_session'])}"
    )

    print(
        f"Fail Confirmed:       "
        f"{bool(row['long_fail_confirmed'])}"
    )

    print(
        f"Fail Count:           "
        f"{int(row['long_fail_count'])}"
    )

    print(
        f"Score Gap:            "
        f"{int(row['long_score_gap'])}"
    )

    print()
    print("--- LONG NEAR MISS ---")

    print(
        f"Near Miss:            "
        f"{bool(row['long_near_miss'])}"
    )

    print(
        f"Near Miss Direction:  "
        f"{bool(row['long_near_miss_direction'])}"
    )

    print(
        f"Near Miss Score:      "
        f"{bool(row['long_near_miss_score'])}"
    )

    print(
        f"Near Miss Volatility: "
        f"{bool(row['long_near_miss_volatility'])}"
    )

    print(
        f"Near Miss Candle:     "
        f"{bool(row['long_near_miss_candle'])}"
    )

    print(
        f"Near Miss Session:    "
        f"{bool(row['long_near_miss_session'])}"
    )

    print(
        f"Near Miss Confirmed:  "
        f"{bool(row['long_near_miss_confirmed'])}"
    )

    # --------------------------------------------------------
    # SHORT
    # --------------------------------------------------------

    print()
    print("--- SHORT FAILURE ---")

    print(
        f"Fail Direction:       "
        f"{bool(row['short_fail_direction'])}"
    )

    print(
        f"Fail Score:           "
        f"{bool(row['short_fail_score'])}"
    )

    print(
        f"Fail Volatility:      "
        f"{bool(row['short_fail_volatility'])}"
    )

    print(
        f"Fail Candle:          "
        f"{bool(row['short_fail_candle'])}"
    )

    print(
        f"Fail Session:         "
        f"{bool(row['short_fail_session'])}"
    )

    print(
        f"Fail Confirmed:       "
        f"{bool(row['short_fail_confirmed'])}"
    )

    print(
        f"Fail Count:           "
        f"{int(row['short_fail_count'])}"
    )

    print(
        f"Score Gap:            "
        f"{int(row['short_score_gap'])}"
    )

    print()
    print("--- SHORT NEAR MISS ---")

    print(
        f"Near Miss:            "
        f"{bool(row['short_near_miss'])}"
    )

    print(
        f"Near Miss Direction:  "
        f"{bool(row['short_near_miss_direction'])}"
    )

    print(
        f"Near Miss Score:      "
        f"{bool(row['short_near_miss_score'])}"
    )

    print(
        f"Near Miss Volatility: "
        f"{bool(row['short_near_miss_volatility'])}"
    )

    print(
        f"Near Miss Candle:     "
        f"{bool(row['short_near_miss_candle'])}"
    )

    print(
        f"Near Miss Session:    "
        f"{bool(row['short_near_miss_session'])}"
    )

    print(
        f"Near Miss Confirmed:  "
        f"{bool(row['short_near_miss_confirmed'])}"
    )

    # ========================================================
    # MODULE FAILURE BREAKDOWN - LONG
    # ========================================================

    print()
    print("=" * 70)
    print("MODULE FAILURE BREAKDOWN - LONG")
    print("=" * 70)

    # --------------------------------------------------------
    # PULLBACK LONG
    # --------------------------------------------------------

    print()
    print("--- PULLBACK LONG ---")

    print(
        f"Fail Trend:          "
        f"{bool(row['pb_long_fail_trend'])}"
    )

    print(
        f"Fail Slow EMA:       "
        f"{bool(row['pb_long_fail_slow_ema'])}"
    )

    print(
        f"Fail RSI:            "
        f"{bool(row['pb_long_fail_rsi'])}"
    )

    print(
        f"Fail Touch:          "
        f"{bool(row['pb_long_fail_touch'])}"
    )

    print(
        f"Fail Reclaim:        "
        f"{bool(row['pb_long_fail_reclaim'])}"
    )

    print(
        f"Fail Mask:           "
        f"{int(row['pb_long_fail_mask'])}"
    )

    # --------------------------------------------------------
    # BREAKOUT LONG
    # --------------------------------------------------------

    print()
    print("--- BREAKOUT LONG ---")

    print(
        f"Fail Trend:          "
        f"{bool(row['bo_long_fail_trend'])}"
    )

    print(
        f"Fail Price:          "
        f"{bool(row['bo_long_fail_price'])}"
    )

    print(
        f"Fail Volume:         "
        f"{bool(row['bo_long_fail_volume'])}"
    )

    print(
        f"Fail RSI:            "
        f"{bool(row['bo_long_fail_rsi'])}"
    )

    print(
        f"Fail Mask:           "
        f"{int(row['bo_long_fail_mask'])}"
    )

    # --------------------------------------------------------
    # SQUEEZE LONG
    # --------------------------------------------------------

    print()
    print("--- SQUEEZE LONG ---")

    print(
        f"Fail Trend:          "
        f"{bool(row['sq_long_fail_trend'])}"
    )

    print(
        f"Fail Recent:         "
        f"{bool(row['sq_long_fail_recent'])}"
    )

    print(
        f"Fail Release:        "
        f"{bool(row['sq_long_fail_release'])}"
    )

    print(
        f"Fail Price:          "
        f"{bool(row['sq_long_fail_price'])}"
    )

    print(
        f"Fail Mask:           "
        f"{int(row['sq_long_fail_mask'])}"
    )

    # --------------------------------------------------------
    # MEAN REVERSION LONG
    # --------------------------------------------------------

    print()
    print("--- MEAN REVERSION LONG ---")

    print(
        f"Fail Trend:          "
        f"{bool(row['mr_long_fail_trend'])}"
    )

    print(
        f"Fail Slow EMA:       "
        f"{bool(row['mr_long_fail_slow_ema'])}"
    )

    print(
        f"Fail Oversold:       "
        f"{bool(row['mr_long_fail_oversold'])}"
    )

    print(
        f"Fail RSI Cross:      "
        f"{bool(row['mr_long_fail_rsi_cross'])}"
    )

    print(
        f"Fail Candle:         "
        f"{bool(row['mr_long_fail_candle'])}"
    )

    print(
        f"Fail Mask:           "
        f"{int(row['mr_long_fail_mask'])}"
    )

    # ========================================================
    # MODULE FAILURE BREAKDOWN - SHORT
    # ========================================================

    print()
    print("=" * 70)
    print("MODULE FAILURE BREAKDOWN - SHORT")
    print("=" * 70)

    # --------------------------------------------------------
    # PULLBACK SHORT
    # --------------------------------------------------------

    print()
    print("--- PULLBACK SHORT ---")

    print(
        f"Fail Trend:          "
        f"{bool(row['pb_short_fail_trend'])}"
    )

    print(
        f"Fail Slow EMA:       "
        f"{bool(row['pb_short_fail_slow_ema'])}"
    )

    print(
        f"Fail RSI:            "
        f"{bool(row['pb_short_fail_rsi'])}"
    )

    print(
        f"Fail Touch:          "
        f"{bool(row['pb_short_fail_touch'])}"
    )

    print(
        f"Fail Reclaim:        "
        f"{bool(row['pb_short_fail_reclaim'])}"
    )

    print(
        f"Fail Mask:           "
        f"{int(row['pb_short_fail_mask'])}"
    )

    # --------------------------------------------------------
    # BREAKOUT SHORT
    # --------------------------------------------------------

    print()
    print("--- BREAKOUT SHORT ---")

    print(
        f"Fail Trend:          "
        f"{bool(row['bo_short_fail_trend'])}"
    )

    print(
        f"Fail Price:          "
        f"{bool(row['bo_short_fail_price'])}"
    )

    print(
        f"Fail Volume:         "
        f"{bool(row['bo_short_fail_volume'])}"
    )

    print(
        f"Fail RSI:            "
        f"{bool(row['bo_short_fail_rsi'])}"
    )

    print(
        f"Fail Mask:           "
        f"{int(row['bo_short_fail_mask'])}"
    )

    # --------------------------------------------------------
    # SQUEEZE SHORT
    # --------------------------------------------------------

    print()
    print("--- SQUEEZE SHORT ---")

    print(
        f"Fail Trend:          "
        f"{bool(row['sq_short_fail_trend'])}"
    )

    print(
        f"Fail Recent:         "
        f"{bool(row['sq_short_fail_recent'])}"
    )

    print(
        f"Fail Release:        "
        f"{bool(row['sq_short_fail_release'])}"
    )

    print(
        f"Fail Price:          "
        f"{bool(row['sq_short_fail_price'])}"
    )

    print(
        f"Fail Mask:           "
        f"{int(row['sq_short_fail_mask'])}"
    )

    # --------------------------------------------------------
    # MEAN REVERSION SHORT
    # --------------------------------------------------------

    print()
    print("--- MEAN REVERSION SHORT ---")

    print(
        f"Fail Trend:          "
        f"{bool(row['mr_short_fail_trend'])}"
    )

    print(
        f"Fail Slow EMA:       "
        f"{bool(row['mr_short_fail_slow_ema'])}"
    )

    print(
        f"Fail Overbought:     "
        f"{bool(row['mr_short_fail_overbought'])}"
    )

    print(
        f"Fail RSI Cross:      "
        f"{bool(row['mr_short_fail_rsi_cross'])}"
    )

    print(
        f"Fail Candle:         "
        f"{bool(row['mr_short_fail_candle'])}"
    )

    print(
        f"Fail Mask:           "
        f"{int(row['mr_short_fail_mask'])}"
    )

    # ========================================================
    # ENTRY DELAY / OPPORTUNITY ANALYSIS
    # ========================================================

    print()
    print("=" * 70)
    print("ENTRY DELAY / OPPORTUNITY ANALYSIS")
    print("=" * 70)

    # --------------------------------------------------------
    # LONG
    # --------------------------------------------------------

    print()
    print("--- LONG ---")

    print(
        f"Non-Score Ready:                  "
        f"{bool(row['long_non_score_ready'])}"
    )

    print(
        f"Waiting For Score:                "
        f"{bool(row['long_waiting_for_score'])}"
    )

    print(
        f"Score Wait Bars:                  "
        f"{int(row['long_score_wait_bars'])}"
    )

    print(
        f"Delay On Signal:                  "
        f"{row['long_delay_on_signal']}"
    )

    print(
        f"Near Miss Streak:                 "
        f"{int(row['long_near_miss_streak'])}"
    )

    print(
        f"Near Miss Streak Before Signal:   "
        f"{row['long_near_miss_streak_before_signal']}"
    )

    # --------------------------------------------------------
    # SHORT
    # --------------------------------------------------------

    print()
    print("--- SHORT ---")

    print(
        f"Non-Score Ready:                  "
        f"{bool(row['short_non_score_ready'])}"
    )

    print(
        f"Waiting For Score:                "
        f"{bool(row['short_waiting_for_score'])}"
    )

    print(
        f"Score Wait Bars:                  "
        f"{int(row['short_score_wait_bars'])}"
    )

    print(
        f"Delay On Signal:                  "
        f"{row['short_delay_on_signal']}"
    )

    print(
        f"Near Miss Streak:                 "
        f"{int(row['short_near_miss_streak'])}"
    )

    print(
        f"Near Miss Streak Before Signal:   "
        f"{row['short_near_miss_streak_before_signal']}"
    )

    # ========================================================
    # FINAL FILTER FAIL MASK
    # ========================================================

    print()
    print("=" * 70)
    print("FINAL FILTER FAIL MASK")
    print("=" * 70)

    print(
        f"Long Final Fail Mask:   "
        f"{int(row['long_final_fail_mask'])}"
    )

    print(
        f"Short Final Fail Mask:  "
        f"{int(row['short_final_fail_mask'])}"
    )

    # ========================================================
    # ACTIVE MODULE MASK
    # ========================================================

    print()
    print("=" * 70)
    print("ACTIVE MODULE MASK")
    print("=" * 70)

    print(
        f"Long Active Module Mask:   "
        f"{int(row['long_active_module_mask'])}"
    )

    print(
        f"Short Active Module Mask:  "
        f"{int(row['short_active_module_mask'])}"
    )

    # ========================================================
    # SANITY / REGRESSION ASSERTIONS
    # ========================================================
    #
    # Fast regression-baseline:
    #
    # Ticker:   MU
    # Mode:     Swing
    # Chart TF: 1D
    # Date:     2026-08-21
    #
    # Värdena nedan har verifierats mot Pine / TradingView.
    # Om ett assertion fallerar efter en framtida kodändring
    # vet vi att verifierad Signal Diagnostics-logik har ändrats.
    # ========================================================

    print()
    print("=" * 70)
    print("SANITY ASSERTIONS")
    print("=" * 70)

    # --------------------------------------------------------
    # ENTRY MODULES
    # --------------------------------------------------------

    assert bool(row["pullback_long"]) is False
    assert bool(row["breakout_long"]) is False
    assert bool(row["squeeze_long"]) is False
    assert bool(row["mean_rev_long"]) is False

    assert bool(row["pullback_short"]) is False
    assert bool(row["breakout_short"]) is False
    assert bool(row["squeeze_short"]) is False
    assert bool(row["mean_rev_short"]) is False

    print("Entry Modules                PASS")

    # --------------------------------------------------------
    # MODULE SUMMARY / SCORE
    # --------------------------------------------------------

    assert int(row["long_score"]) == 0
    assert int(row["short_score"]) == 0

    assert row["long_module_text"] == ""
    assert row["short_module_text"] == ""

    assert int(row["min_confluence"]) == 1

    print("Module Summary / Score       PASS")

    # --------------------------------------------------------
    # FINAL SIGNAL
    # --------------------------------------------------------

    assert bool(row["allow_long"]) is True
    assert bool(row["allow_short"]) is False

    assert bool(row["volatility_ok"]) is True
    assert bool(row["not_overextended"]) is True
    assert bool(row["session_ok"]) is True
    assert bool(row["is_confirmed"]) is True

    assert bool(row["long_signal"]) is False
    assert bool(row["short_signal"]) is False

    print("Final Signal                 PASS")

    # --------------------------------------------------------
    # FAILURE / NEAR-MISS
    # --------------------------------------------------------

    assert bool(row["long_fail_direction"]) is False
    assert bool(row["long_fail_score"]) is True
    assert bool(row["long_fail_volatility"]) is False
    assert bool(row["long_fail_candle"]) is False
    assert bool(row["long_fail_session"]) is False
    assert bool(row["long_fail_confirmed"]) is False

    assert int(row["long_fail_count"]) == 1
    assert int(row["long_score_gap"]) == 1

    assert bool(row["long_near_miss"]) is True
    assert bool(row["long_near_miss_direction"]) is False
    assert bool(row["long_near_miss_score"]) is True
    assert bool(row["long_near_miss_volatility"]) is False
    assert bool(row["long_near_miss_candle"]) is False
    assert bool(row["long_near_miss_session"]) is False
    assert bool(row["long_near_miss_confirmed"]) is False

    assert bool(row["short_fail_direction"]) is True
    assert bool(row["short_fail_score"]) is True
    assert bool(row["short_fail_volatility"]) is False
    assert bool(row["short_fail_candle"]) is False
    assert bool(row["short_fail_session"]) is False
    assert bool(row["short_fail_confirmed"]) is False

    assert int(row["short_fail_count"]) == 2
    assert int(row["short_score_gap"]) == 1

    assert bool(row["short_near_miss"]) is False
    assert bool(row["short_near_miss_direction"]) is False
    assert bool(row["short_near_miss_score"]) is False
    assert bool(row["short_near_miss_volatility"]) is False
    assert bool(row["short_near_miss_candle"]) is False
    assert bool(row["short_near_miss_session"]) is False
    assert bool(row["short_near_miss_confirmed"]) is False

    print("Failure / Near-Miss          PASS")

    # --------------------------------------------------------
    # MODULE FAILURE - LONG
    # --------------------------------------------------------

    assert int(row["pb_long_fail_mask"]) == 29
    assert int(row["bo_long_fail_mask"]) == 15
    assert int(row["sq_long_fail_mask"]) == 11
    assert int(row["mr_long_fail_mask"]) == 29

    print("Module Failure Long          PASS")

    # --------------------------------------------------------
    # MODULE FAILURE - SHORT
    # --------------------------------------------------------

    assert int(row["pb_short_fail_mask"]) == 23
    assert int(row["bo_short_fail_mask"]) == 15
    assert int(row["sq_short_fail_mask"]) == 11
    assert int(row["mr_short_fail_mask"]) == 15

    print("Module Failure Short         PASS")

    # --------------------------------------------------------
    # ENTRY DELAY / OPPORTUNITY
    # --------------------------------------------------------

    assert bool(row["long_non_score_ready"]) is True
    assert bool(row["short_non_score_ready"]) is False

    assert bool(row["long_waiting_for_score"]) is True
    assert bool(row["short_waiting_for_score"]) is False

    assert int(row["long_score_wait_bars"]) == 13
    assert int(row["short_score_wait_bars"]) == 0

    assert pd.isna(row["long_delay_on_signal"])
    assert pd.isna(row["short_delay_on_signal"])

    assert int(row["long_near_miss_streak"]) == 13
    assert int(row["short_near_miss_streak"]) == 0

    assert pd.isna(
        row["long_near_miss_streak_before_signal"]
    )

    assert pd.isna(
        row["short_near_miss_streak_before_signal"]
    )

    print("Entry Delay / Opportunity    PASS")

    # --------------------------------------------------------
    # FINAL FILTER FAIL MASK
    # --------------------------------------------------------

    assert int(row["long_final_fail_mask"]) == 2
    assert int(row["short_final_fail_mask"]) == 3

    print("Final Filter Fail Mask       PASS")

    # --------------------------------------------------------
    # ACTIVE MODULE MASK
    # --------------------------------------------------------

    assert int(row["long_active_module_mask"]) == 0
    assert int(row["short_active_module_mask"]) == 0

    print("Active Module Mask           PASS")

    # --------------------------------------------------------
    # REQUIRED VALUES
    # --------------------------------------------------------
    #
    # Viktiga diagnostikvärden får inte oväntat bli NaN.
    # Delay-fälten ovan är undantag eftersom NaN är korrekt
    # när ingen signal finns på aktuell bar.
    # --------------------------------------------------------

    required_values = [
        "long_score",
        "short_score",
        "min_confluence",
        "long_fail_count",
        "short_fail_count",
        "long_score_gap",
        "short_score_gap",
        "pb_long_fail_mask",
        "bo_long_fail_mask",
        "sq_long_fail_mask",
        "mr_long_fail_mask",
        "pb_short_fail_mask",
        "bo_short_fail_mask",
        "sq_short_fail_mask",
        "mr_short_fail_mask",
        "long_score_wait_bars",
        "short_score_wait_bars",
        "long_near_miss_streak",
        "short_near_miss_streak",
        "long_final_fail_mask",
        "short_final_fail_mask",
        "long_active_module_mask",
        "short_active_module_mask",
    ]

    for column in required_values:
        assert pd.notna(
            row[column]
        ), f"{column} är oväntat NaN"

    print("Required Values              PASS")

    # --------------------------------------------------------
    # ALL PASSED
    # --------------------------------------------------------

    print()
    print("ALL SIGNAL DIAGNOSTIC ASSERTIONS PASSED")

if __name__ == "__main__":
    main()