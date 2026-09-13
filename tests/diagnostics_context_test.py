from __future__ import annotations

import pandas as pd

from src.market_data import download_yahoo_data
from src.diagnostics_context import context_diagnostics


def main() -> None:
    """
    Första baseline-testet för Trust Me Context Diagnostics.

    Testfall:
    - Ticker: MU
    - Mode: Swing
    - Chart TF: 1D
    - Datum: 2026-08-21

    Syftet är INTE att optimera strategin.

    Syftet är att verifiera att Diagnostic Engine
    bygger rätt context ovanpå vår parity-verifierade Core.
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
    # BYGG CONTEXT DIAGNOSTICS
    # ========================================================

    diagnostics = context_diagnostics(
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
    # REFERENSDATUM
    # ========================================================

    timestamp = pd.Timestamp("2026-08-21")

    if timestamp not in diagnostics.index:
        raise KeyError(
            f"Hittade inte {timestamp} i diagnostic-datan."
        )

    row = diagnostics.loc[timestamp]

    # ========================================================
    # OUTPUT
    # ========================================================

    print()
    print("#" * 70)
    print("TRUST ME — CONTEXT DIAGNOSTIC BASELINE")
    print("#" * 70)

    print(f"Ticker:    {ticker}")
    print("Mode:      Swing")
    print("Chart TF:  1D")
    print(f"Date:      {timestamp.date()}")

    # --------------------------------------------------------
    # MODE / SESSION
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("MODE / SESSION")
    print("=" * 70)

    print(f"isSwing:          {bool(row['is_swing'])}")
    print(f"Allow Long:       {bool(row['allow_long'])}")
    print(f"Allow Short:      {bool(row['allow_short'])}")
    print(f"In Entry Session: {bool(row['in_entry_session'])}")
    print(f"In Full Session:  {bool(row['in_full_session'])}")
    print(f"Session OK:       {bool(row['session_ok'])}")

    # --------------------------------------------------------
    # TREND
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("TREND DIAGNOSTICS")
    print("=" * 70)

    print(
        f"EMA Fast:         "
        f"{row['htf_ema_fast']:.6f}"
    )

    print(
        f"EMA Slow:         "
        f"{row['htf_ema_slow']:.6f}"
    )

    print(
        f"ADX:              "
        f"{row['htf_adx']:.6f}"
    )

    print(
        f"ADX Min:          "
        f"{row['adx_min']:.6f}"
    )

    print(
        f"ADX OK:           "
        f"{bool(row['adx_ok'])}"
    )

    print(
        f"Uptrend:          "
        f"{bool(row['uptrend'])}"
    )

    print(
        f"Downtrend:        "
        f"{bool(row['downtrend'])}"
    )

    print()
    print("--- Diagnostic measurements ---")

    print(
        f"EMA Spread:       "
        f"{row['ema_spread']:.6f}"
    )

    print(
        f"EMA Spread %:     "
        f"{row['ema_spread_pct']:.6f}"
    )

    print(
        f"ADX Margin:       "
        f"{row['adx_margin']:.6f}"
    )

    # --------------------------------------------------------
    # VOLATILITY
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("VOLATILITY DIAGNOSTICS")
    print("=" * 70)

    print(
        f"ATR14:            "
        f"{row['atr']:.6f}"
    )

    print(
        f"ATR %:            "
        f"{row['atr_pct']:.6f}"
    )

    print(
        f"Min ATR %:        "
        f"{row['min_atr_pct']:.6f}"
    )

    print(
        f"Volatility OK:    "
        f"{bool(row['volatility_ok'])}"
    )

    print(
        f"Candle Range:     "
        f"{row['candle_range']:.6f}"
    )

    print(
        f"Max Candle ATR:   "
        f"{row['max_candle_atr']:.6f}"
    )

    print(
        f"Not Overextended: "
        f"{bool(row['not_overextended'])}"
    )

    print()
    print("--- Diagnostic measurements ---")

    print(
        f"ATR % Margin:     "
        f"{row['atr_pct_margin']:.6f}"
    )

    print(
        f"Candle Range ATR: "
        f"{row['candle_range_atr']:.6f}"
    )

    print(
        f"Candle ATR Margin:"
        f" {row['candle_atr_margin']:.6f}"
    )

    # --------------------------------------------------------
    # MOMENTUM
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("MOMENTUM DIAGNOSTICS")
    print("=" * 70)

    print(
        f"RSI:                       "
        f"{row['rsi']:.6f}"
    )

    print(
        f"RSI Avg:                   "
        f"{row['rsi_avg']:.6f}"
    )

    print(
        f"RSI Cross Up:              "
        f"{bool(row['rsi_cross_up'])}"
    )

    print(
        f"RSI Cross Down:            "
        f"{bool(row['rsi_cross_down'])}"
    )

    print(
        f"Bars Since RSI Up:         "
        f"{row['bars_since_rsi_up']}"
    )

    print(
        f"Bars Since RSI Down:       "
        f"{row['bars_since_rsi_down']}"
    )

    print(
        f"RSI Up Recent:             "
        f"{bool(row['rsi_up_recent'])}"
    )

    print(
        f"RSI Down Recent:           "
        f"{bool(row['rsi_down_recent'])}"
    )

    print(
        f"Bars Since Oversold:       "
        f"{row['bars_since_oversold']}"
    )

    print(
        f"Bars Since Overbought:     "
        f"{row['bars_since_overbought']}"
    )

    print(
        f"Was Oversold Recently:     "
        f"{bool(row['was_oversold_recently'])}"
    )

    print(
        f"Was Overbought Recently:   "
        f"{bool(row['was_overbought_recently'])}"
    )

    print(
        f"Confluence Window:         "
        f"{row['confluence_window']}"
    )

    print()
    print("--- Diagnostic measurements ---")

    print(
        f"RSI Distance From Avg:     "
        f"{row['rsi_distance_from_avg']:.6f}"
    )

    print(
        f"RSI Distance From 50:      "
        f"{row['rsi_distance_from_50']:.6f}"
    )

    print(
        f"RSI Distance From 30:      "
        f"{row['rsi_distance_from_30']:.6f}"
    )

    print(
        f"RSI Distance From 70:      "
        f"{row['rsi_distance_from_70']:.6f}"
    )

    # --------------------------------------------------------
    # VOLUME
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("VOLUME DIAGNOSTICS")
    print("=" * 70)

    print(
        f"Volume:                    "
        f"{row['volume']:.0f}"
    )

    print(
        f"Average Volume:            "
        f"{row['average_volume']:.6f}"
    )

    print(
        f"Volume Length:             "
        f"{int(row['volume_length'])}"
    )

    print(
        f"Use Volume Filter:         "
        f"{bool(row['use_volume_filter'])}"
    )

    print(
        f"Volume Strong:             "
        f"{bool(row['volume_strong'])}"
    )

    print()
    print("--- Diagnostic measurements ---")

    print(
        f"Volume Ratio:              "
        f"{row['volume_ratio']:.6f}"
    )

    print(
        f"Volume Margin:             "
        f"{row['volume_margin']:.6f}"
    )

    print(
        f"Volume Margin %:           "
        f"{row['volume_margin_pct']:.6f}"
    )

    # --------------------------------------------------------
    # BREAKOUT
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("BREAKOUT DIAGNOSTICS")
    print("=" * 70)

    print(
        f"Breakout Level:            "
        f"{row['breakout_level']:.6f}"
    )

    print(
        f"Breakdown Level:           "
        f"{row['breakdown_level']:.6f}"
    )

    print(
        f"Breakout Lookback:         "
        f"{int(row['breakout_lookback'])}"
    )

    print(
        f"Price Above Breakout:      "
        f"{bool(row['price_above_breakout'])}"
    )

    print(
        f"Price Below Breakdown:     "
        f"{bool(row['price_below_breakdown'])}"
    )

    print()
    print("--- Diagnostic measurements ---")

    print(
        f"Distance To Breakout:      "
        f"{row['distance_to_breakout']:.6f}"
    )

    print(
        f"Distance To Breakdown:     "
        f"{row['distance_to_breakdown']:.6f}"
    )

    print(
        f"Distance To Breakout ATR:  "
        f"{row['distance_to_breakout_atr']:.6f}"
    )

    print(
        f"Distance To Breakdown ATR: "
        f"{row['distance_to_breakdown_atr']:.6f}"
    )

    # --------------------------------------------------------
    # SQUEEZE
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("SQUEEZE DIAGNOSTICS")
    print("=" * 70)

    print(
        f"BB Length:                  "
        f"{int(row['bb_length'])}"
    )

    print(
        f"BB Mult:                    "
        f"{row['bb_mult']:.6f}"
    )

    print(
        f"BB Basis:                   "
        f"{row['bb_basis']:.6f}"
    )

    print(
        f"BB Dev:                     "
        f"{row['bb_dev']:.6f}"
    )

    print(
        f"BB Upper:                   "
        f"{row['bb_upper']:.6f}"
    )

    print(
        f"BB Lower:                   "
        f"{row['bb_lower']:.6f}"
    )

    print(
        f"BB Width:                   "
        f"{row['bb_width']:.6f}"
    )

    print(
        f"BB Width Avg:               "
        f"{row['bb_width_avg']:.6f}"
    )

    print(
        f"In Squeeze:                 "
        f"{bool(row['in_squeeze'])}"
    )

    print(
        f"Bars Since Squeeze:         "
        f"{row['bars_since_squeeze']}"
    )

    print(
        f"Squeeze Recent:             "
        f"{bool(row['squeeze_recent'])}"
    )

    print(
        f"Squeeze Window:             "
        f"{int(row['squeeze_window'])}"
    )

    print()
    print("--- Diagnostic measurements ---")

    print(
        f"Squeeze Threshold:          "
        f"{row['squeeze_threshold']:.6f}"
    )

    print(
        f"Distance To Squeeze:        "
        f"{row['distance_to_squeeze']:.6f}"
    )

    print(
        f"Distance To Squeeze %:      "
        f"{row['distance_to_squeeze_pct']:.6f}"
    )

    print(
        f"Distance To Upper Band ATR: "
        f"{row['distance_to_upper_band_atr']:.6f}"
    )

    print(
        f"Distance To Lower Band ATR: "
        f"{row['distance_to_lower_band_atr']:.6f}"
    )

    # ========================================================
    # SANITY ASSERTIONS
    # ========================================================

    print()
    print("=" * 70)
    print("SANITY ASSERTIONS")
    print("=" * 70)

    # --------------------------------------------------------
    # MODE / SESSION
    # --------------------------------------------------------

    assert bool(row["is_swing"]) is True
    assert bool(row["allow_long"]) is True
    assert bool(row["allow_short"]) is False
    assert bool(row["session_ok"]) is True

    print("Mode / Session       PASS")

    # --------------------------------------------------------
    # TREND
    # --------------------------------------------------------

    assert row["adx_min"] == 18.0

    assert row["adx_ok"] == (
        row["htf_adx"] > row["adx_min"]
    )

    assert row["uptrend"] == (
        (row["htf_ema_fast"] > row["htf_ema_slow"])
        and row["adx_ok"]
    )

    assert row["downtrend"] == (
        (row["htf_ema_fast"] < row["htf_ema_slow"])
        and row["adx_ok"]
    )

    assert abs(
        row["ema_spread"]
        - (
            row["htf_ema_fast"]
            - row["htf_ema_slow"]
        )
    ) < 1e-10

    assert abs(
        row["adx_margin"]
        - (
            row["htf_adx"]
            - row["adx_min"]
        )
    ) < 1e-10

    print("Trend                PASS")

    # --------------------------------------------------------
    # VOLATILITY
    # --------------------------------------------------------

    assert row["min_atr_pct"] == 1.0
    assert row["max_candle_atr"] == 2.0

    assert row["volatility_ok"] == (
        row["atr_pct"] >= row["min_atr_pct"]
    )

    assert row["not_overextended"] == (
        row["candle_range"]
        < row["atr"] * row["max_candle_atr"]
    )

    assert abs(
        row["atr_pct_margin"]
        - (
            row["atr_pct"]
            - row["min_atr_pct"]
        )
    ) < 1e-10

    assert abs(
        row["candle_range_atr"]
        - (
            row["candle_range"]
            / row["atr"]
        )
    ) < 1e-10

    print("Volatility           PASS")

    # --------------------------------------------------------
    # MOMENTUM
    # --------------------------------------------------------

    assert row["confluence_window"] == 5

    assert abs(
        row["rsi_distance_from_avg"]
        - (
            row["rsi"]
            - row["rsi_avg"]
        )
    ) < 1e-10

    assert abs(
        row["rsi_distance_from_50"]
        - (row["rsi"] - 50.0)
    ) < 1e-10

    assert abs(
        row["rsi_distance_from_30"]
        - (row["rsi"] - 30.0)
    ) < 1e-10

    assert abs(
        row["rsi_distance_from_70"]
        - (row["rsi"] - 70.0)
    ) < 1e-10

    print("Momentum             PASS")

    # --------------------------------------------------------
    # VOLUME
    # --------------------------------------------------------

    assert row["volume_length"] == 20
    assert bool(row["use_volume_filter"]) is True

    assert row["volume_strong"] == (
        row["volume"] > row["average_volume"]
    )

    assert abs(
        row["volume_ratio"]
        - (
            row["volume"]
            / row["average_volume"]
        )
    ) < 1e-10

    assert abs(
        row["volume_margin"]
        - (
            row["volume"]
            - row["average_volume"]
        )
    ) < 1e-10

    print("Volume               PASS")

    # --------------------------------------------------------
    # BREAKOUT
    # --------------------------------------------------------

    assert row["breakout_lookback"] == 10

    assert row["price_above_breakout"] == (
        row["close"] > row["breakout_level"]
    )

    assert row["price_below_breakdown"] == (
        row["close"] < row["breakdown_level"]
    )

    assert abs(
        row["distance_to_breakout"]
        - (
            row["breakout_level"]
            - row["close"]
        )
    ) < 1e-10

    assert abs(
        row["distance_to_breakdown"]
        - (
            row["close"]
            - row["breakdown_level"]
        )
    ) < 1e-10

    assert abs(
        row["distance_to_breakout_atr"]
        - (
            row["distance_to_breakout"]
            / row["atr"]
        )
    ) < 1e-10

    print("Breakout             PASS")

    # --------------------------------------------------------
    # SQUEEZE
    # --------------------------------------------------------

    assert row["bb_length"] == 20
    assert row["bb_mult"] == 2.0
    assert row["squeeze_window"] == 3

    assert abs(
        row["squeeze_threshold"]
        - (
            row["bb_width_avg"] * 0.7
        )
    ) < 1e-10

    assert abs(
        row["distance_to_squeeze"]
        - (
            row["bb_width"]
            - row["squeeze_threshold"]
        )
    ) < 1e-10

    assert abs(
        row["distance_to_squeeze_pct"]
        - (
            (
                row["bb_width"]
                / row["squeeze_threshold"]
                - 1.0
            )
            * 100.0
        )
    ) < 1e-10

    print("Squeeze              PASS")

    # --------------------------------------------------------
    # GLOBAL SANITY
    # --------------------------------------------------------

    required_values = [
        "htf_ema_fast",
        "htf_ema_slow",
        "htf_adx",
        "atr",
        "atr_pct",
        "rsi",
        "rsi_avg",
        "average_volume",
        "volume_ratio",
        "breakout_level",
        "breakdown_level",
        "bb_basis",
        "bb_width",
        "bb_width_avg",
        "squeeze_threshold",
    ]

    for column in required_values:
        assert pd.notna(row[column]), (
            f"{column} är NaN på baseline-baren."
        )

    print("Required values       PASS")

    print()
    print(
        "ALL CONTEXT DIAGNOSTIC ASSERTIONS PASSED"
    )


if __name__ == "__main__":
    main()