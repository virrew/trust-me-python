from __future__ import annotations

import pandas as pd

from src.market_data import (
    download_yahoo_data,
    resample_regular_session,
    map_daily_context_to_intraday,
)

from src.trust_me_core import (
    trend_context,
    trend_regime_context,
    volatility_context,
    momentum_context,
    volume_context,
    breakout_context,
    squeeze_context,
    pullback_context,
    session_entry_context,
)


# ============================================================
# TRUST ME v2.0 — SWING DEFAULTS
# ============================================================

EMA_FAST_LENGTH = 50
EMA_SLOW_LENGTH = 200
ADX_LENGTH = 14
ADX_MIN_SWING = 18.0

ATR_LENGTH = 14
MIN_ATR_PCT_SWING = 1.0
USE_CANDLE_FILTER = True
MAX_CANDLE_ATR = 2.0

RSI_LENGTH = 14
RSI_SMOOTH_LENGTH = 9
CONFLUENCE_WINDOW_SWING = 5

USE_VOLUME_FILTER = True
VOLUME_LENGTH_SWING = 20

BREAKOUT_LOOKBACK_SWING = 10

BB_LENGTH = 20
BB_MULT = 2.0
SQUEEZE_WINDOW_SWING = 3

SWING_PARITY_DATE = "2026-08-21"


# ============================================================
# GENERIC HELPERS
# ============================================================

def compare_bar(
    python_bar: pd.Series,
    tradingview: dict[str, float],
) -> pd.DataFrame:
    """
    Jämför en Python/Yahoo-bar med TradingView OHLC.
    """

    rows = []

    for field in ["open", "high", "low", "close"]:
        py_value = float(python_bar[field])
        tv_value = float(tradingview[field])

        difference = py_value - tv_value
        abs_difference = abs(difference)

        difference_pct = (
            abs_difference / tv_value * 100
            if tv_value != 0
            else 0.0
        )

        rows.append(
            {
                "field": field,
                "tradingview": tv_value,
                "python": py_value,
                "difference": difference,
                "abs_difference": abs_difference,
                "difference_pct": difference_pct,
            }
        )

    return pd.DataFrame(rows)


def compare_bars(
    python_data: pd.DataFrame,
    tradingview_bars: dict[pd.Timestamp, dict[str, float]],
) -> pd.DataFrame:
    """
    Jämför flera TradingView-bars mot Python/Yahoo.
    """

    comparisons = []

    for timestamp, tv_bar in tradingview_bars.items():
        if timestamp not in python_data.index:
            raise KeyError(
                f"Hittade inte bar {timestamp} i Python-datan."
            )

        python_bar = python_data.loc[timestamp]

        comparison = compare_bar(
            python_bar,
            tv_bar,
        )

        comparison["timestamp"] = timestamp
        comparisons.append(comparison)

    result = pd.concat(
        comparisons,
        ignore_index=True,
    )

    return result[
        [
            "timestamp",
            "field",
            "tradingview",
            "python",
            "difference",
            "abs_difference",
            "difference_pct",
        ]
    ]


def print_summary(
    comparison: pd.DataFrame,
) -> None:
    """
    Skriver sammanfattande OHLC-parity-statistik.
    """

    print()
    print("=" * 70)
    print("PARITY SUMMARY")
    print("=" * 70)

    print(
        "Bars compared:",
        comparison["timestamp"].nunique(),
    )

    print(
        "Values compared:",
        len(comparison),
    )

    print(
        "Mean absolute difference:",
        round(
            comparison["abs_difference"].mean(),
            6,
        ),
    )

    print(
        "Max absolute difference:",
        round(
            comparison["abs_difference"].max(),
            6,
        ),
    )

    print(
        "Mean difference %:",
        round(
            comparison["difference_pct"].mean(),
            6,
        ),
        "%",
    )

    print(
        "Max difference %:",
        round(
            comparison["difference_pct"].max(),
            6,
        ),
        "%",
    )


def timestamp_for_date(
    df: pd.DataFrame,
    date_string: str,
) -> pd.Timestamp:
    """
    Hämtar faktisk timestamp i DataFrame för ett kalenderdatum.

    Praktiskt eftersom Yahoo Daily kan vara timezone-aware.
    """

    target_date = pd.Timestamp(date_string).date()

    matches = df.index[
        df.index.date == target_date
    ]

    if len(matches) == 0:
        raise KeyError(
            f"Hittade inget datum {date_string} i datan."
        )

    return matches[0]


# ============================================================
# 45M DATA-FEED PARITY
#
# Detta behålls som regressionstest för Yahoo -> 45m.
# Det är INTE vår huvudsakliga Swing-strategiparity.
# ============================================================

def print_45m_feed_parity(
    data_45m: pd.DataFrame,
) -> None:
    """
    Verifierar våra tidigare 45m-bars mot TradingView.
    """

    tradingview_bars = {
        pd.Timestamp(
            "2026-08-21 11:00",
            tz="America/New_York",
        ): {
            "open": 963.20,
            "high": 972.39,
            "low": 961.50,
            "close": 970.60,
        },

        pd.Timestamp(
            "2026-08-21 11:45",
            tz="America/New_York",
        ): {
            "open": 970.51,
            "high": 972.33,
            "low": 960.04,
            "close": 965.93,
        },
    }

    comparison = compare_bars(
        data_45m,
        tradingview_bars,
    )

    print()
    print("=" * 70)
    print("TRUST ME — 45M DATA-FEED PARITY")
    print("=" * 70)

    print("Ticker:    MU")
    print("Timeframe: 45m")
    print("Mode:      Feed/aggregation diagnostic")
    print()

    print(
        comparison.to_string(
            index=False,
            float_format=lambda x: f"{x:.6f}",
        )
    )

    print_summary(
        comparison,
    )


# ============================================================
# 45M HTF REGRESSION CHECK
#
# Vi behåller även detta eftersom det redan verifierats mot Pine.
# ============================================================

def print_45m_htf_regression(
    ticker: str,
    intraday_data: pd.DataFrame,
    timestamp: pd.Timestamp,
) -> None:
    """
    Tidigare verifierad HTF-mappning:
    Daily trend-context -> 45m.
    """

    daily_data = download_yahoo_data(
        ticker,
        period="2y",
        interval="1d",
    )

    daily_trend = trend_context(
        daily_data,
        ema_fast_length=EMA_FAST_LENGTH,
        ema_slow_length=EMA_SLOW_LENGTH,
        adx_length=ADX_LENGTH,
    )

    mapped_trend = map_daily_context_to_intraday(
        intraday_data,
        daily_trend,
    )

    if timestamp not in mapped_trend.index:
        raise KeyError(
            f"Hittade inte {timestamp} i HTF-datan."
        )

    row = mapped_trend.loc[timestamp]

    print()
    print("=" * 70)
    print("TRUST ME — 45M HTF REGRESSION")
    print("=" * 70)

    print(f"Timestamp: {timestamp}")
    print()

    print(
        f"Python HTF EMA50:  "
        f"{row['ema_fast']:.6f}"
    )

    print(
        f"Python HTF EMA200: "
        f"{row['ema_slow']:.6f}"
    )

    print(
        f"Python HTF ADX14:  "
        f"{row['adx']:.6f}"
    )


# ============================================================
# SWING TREND CONTEXT
# ============================================================

def print_swing_trend_values(
    daily_data: pd.DataFrame,
    timestamp: pd.Timestamp,
) -> pd.DataFrame:
    """
    Trust Me v2.0 Swing:
    EMA50, EMA200, ADX14 och trend regime med ADX > 18.
    """

    trend = trend_context(
        daily_data,
        ema_fast_length=EMA_FAST_LENGTH,
        ema_slow_length=EMA_SLOW_LENGTH,
        adx_length=ADX_LENGTH,
    )

    regime = trend_regime_context(
        ema_fast=trend["ema_fast"],
        ema_slow=trend["ema_slow"],
        adx=trend["adx"],
        adx_min=ADX_MIN_SWING,
    )

    row = trend.loc[timestamp]
    regime_row = regime.loc[timestamp]

    print()
    print("=" * 70)
    print("TRUST ME — SWING TREND PARITY")
    print("=" * 70)

    print(f"Timestamp: {timestamp}")
    print("Mode:      Swing")
    print("Chart TF:  1D")
    print("Trend TF:  1D")
    print()

    print(
        f"Python EMA50:       "
        f"{row['ema_fast']:.6f}"
    )

    print(
        f"Python EMA200:      "
        f"{row['ema_slow']:.6f}"
    )

    print(
        f"Python ADX14:       "
        f"{row['adx']:.6f}"
    )

    print(
        f"Python ADX > 18:    "
        f"{bool(row['adx'] > ADX_MIN_SWING)}"
    )

    print(
        f"Python Uptrend:     "
        f"{bool(regime_row['uptrend'])}"
    )

    print(
        f"Python Downtrend:   "
        f"{bool(regime_row['downtrend'])}"
    )

    return trend


# ============================================================
# SWING VOLATILITY CONTEXT
# ============================================================

def print_swing_volatility_values(
    daily_data: pd.DataFrame,
    timestamp: pd.Timestamp,
) -> None:
    """
    Swing-parametrar:
    ATR14
    min ATR% = 1.0
    candle filter = True
    max candle = 2.0 ATR
    """

    volatility = volatility_context(
        daily_data,
        atr_length=ATR_LENGTH,
        min_atr_pct=MIN_ATR_PCT_SWING,
        use_candle_filter=USE_CANDLE_FILTER,
        max_candle_atr=MAX_CANDLE_ATR,
    )

    row = volatility.loc[timestamp]

    print()
    print("=" * 70)
    print("TRUST ME — SWING VOLATILITY PARITY")
    print("=" * 70)

    print(f"Timestamp: {timestamp}")
    print()

    print(
        f"Python ATR14:             "
        f"{row['atr']:.6f}"
    )

    print(
        f"Python ATR %:             "
        f"{row['atr_pct']:.6f}"
    )

    print(
        f"Python Min ATR %:         "
        f"{MIN_ATR_PCT_SWING:.1f}"
    )

    print(
        f"Python Volatility OK:     "
        f"{bool(row['volatility_ok'])}"
    )

    print(
        f"Python Candle Range:      "
        f"{row['candle_range']:.6f}"
    )

    print(
        f"Python Not Overextended:  "
        f"{bool(row['not_overextended'])}"
    )


# ============================================================
# SWING MOMENTUM CONTEXT
# ============================================================

def print_swing_momentum_values(
    daily_data: pd.DataFrame,
    timestamp: pd.Timestamp,
) -> None:
    """
    Swing-parametrar:
    RSI14
    RSI SMA9
    confluence window = 5
    """

    momentum = momentum_context(
        daily_data,
        rsi_length=RSI_LENGTH,
        rsi_smooth_len=RSI_SMOOTH_LENGTH,
        confluence_window=CONFLUENCE_WINDOW_SWING,
    )

    row = momentum.loc[timestamp]

    print()
    print("=" * 70)
    print("TRUST ME — SWING MOMENTUM PARITY")
    print("=" * 70)

    print(f"Timestamp: {timestamp}")
    print()

    print(
        f"Python RSI:                       "
        f"{row['rsi']:.6f}"
    )

    print(
        f"Python RSI Avg:                   "
        f"{row['rsi_avg']:.6f}"
    )

    print(
        f"Python RSI Cross Up:              "
        f"{bool(row['rsi_cross_up'])}"
    )

    print(
        f"Python RSI Cross Down:            "
        f"{bool(row['rsi_cross_down'])}"
    )

    print(
        f"Python Bars Since RSI Up:         "
        f"{row['bars_since_rsi_up']}"
    )

    print(
        f"Python Bars Since RSI Down:       "
        f"{row['bars_since_rsi_down']}"
    )

    print(
        f"Python RSI Up Recent:             "
        f"{bool(row['rsi_up_recent'])}"
    )

    print(
        f"Python RSI Down Recent:           "
        f"{bool(row['rsi_down_recent'])}"
    )

    print(
        f"Python Bars Since Oversold:       "
        f"{row['bars_since_oversold']}"
    )

    print(
        f"Python Bars Since Overbought:     "
        f"{row['bars_since_overbought']}"
    )

    print(
        f"Python Was Oversold Recently:     "
        f"{bool(row['was_oversold_recently'])}"
    )

    print(
        f"Python Was Overbought Recently:   "
        f"{bool(row['was_overbought_recently'])}"
    )


# ============================================================
# SWING VOLUME CONTEXT
# ============================================================

def print_swing_volume_values(
    daily_data: pd.DataFrame,
    timestamp: pd.Timestamp,
) -> None:
    """
    Swing volume:
    volume SMA20.
    """

    volume_result = volume_context(
        daily_data,
        volume_length=VOLUME_LENGTH_SWING,
        use_volume_filter=USE_VOLUME_FILTER,
    )

    row = volume_result.loc[timestamp]
    raw_volume = daily_data.loc[timestamp, "volume"]

    print()
    print("=" * 70)
    print("TRUST ME — SWING VOLUME PARITY")
    print("=" * 70)

    print(f"Timestamp: {timestamp}")
    print()

    print(
        f"Python Volume:          "
        f"{float(raw_volume):.0f}"
    )

    print(
        f"Python Average Volume:  "
        f"{row['average_volume']:.6f}"
    )

    print(
        f"Python Volume Strong:   "
        f"{bool(row['volume_strong'])}"
    )


# ============================================================
# SWING BREAKOUT CONTEXT
# ============================================================

def print_swing_breakout_values(
    daily_data: pd.DataFrame,
    timestamp: pd.Timestamp,
) -> None:
    """
    Swing breakout lookback = 10.
    """

    breakout_result = breakout_context(
        daily_data,
        breakout_lookback=BREAKOUT_LOOKBACK_SWING,
    )

    row = breakout_result.loc[timestamp]
    close_value = float(
        daily_data.loc[timestamp, "close"]
    )

    print()
    print("=" * 70)
    print("TRUST ME — SWING BREAKOUT PARITY")
    print("=" * 70)

    print(f"Timestamp: {timestamp}")
    print()

    print(
        f"Python Close:            "
        f"{close_value:.6f}"
    )

    print(
        f"Python Breakout Level:   "
        f"{row['breakout_level']:.6f}"
    )

    print(
        f"Python Breakdown Level:  "
        f"{row['breakdown_level']:.6f}"
    )

    print(
        f"Python Above Breakout:   "
        f"{close_value > row['breakout_level']}"
    )

    print(
        f"Python Below Breakdown:  "
        f"{close_value < row['breakdown_level']}"
    )


# ============================================================
# SWING SQUEEZE CONTEXT
# ============================================================

def print_swing_squeeze_values(
    daily_data: pd.DataFrame,
    timestamp: pd.Timestamp,
) -> None:
    """
    Swing:
    BB20
    2 std
    squeeze window = 3
    """

    squeeze_result = squeeze_context(
        daily_data,
        bb_length=BB_LENGTH,
        bb_mult=BB_MULT,
        squeeze_window=SQUEEZE_WINDOW_SWING,
    )

    row = squeeze_result.loc[timestamp]

    print()
    print("=" * 70)
    print("TRUST ME — SWING SQUEEZE PARITY")
    print("=" * 70)

    print(f"Timestamp: {timestamp}")
    print()

    print(
        f"Python BB Basis:           "
        f"{row['bb_basis']:.6f}"
    )

    print(
        f"Python BB Dev:             "
        f"{row['bb_dev']:.6f}"
    )

    print(
        f"Python BB Upper:           "
        f"{row['bb_upper']:.6f}"
    )

    print(
        f"Python BB Lower:           "
        f"{row['bb_lower']:.6f}"
    )

    print(
        f"Python BB Width:           "
        f"{row['bb_width']:.6f}"
    )

    print(
        f"Python BB Width Avg:       "
        f"{row['bb_width_avg']:.6f}"
    )

    print(
        f"Python In Squeeze:         "
        f"{bool(row['in_squeeze'])}"
    )

    print(
        f"Python Bars Since Squeeze: "
        f"{row['bars_since_squeeze']}"
    )

    print(
        f"Python Squeeze Recent:     "
        f"{bool(row['squeeze_recent'])}"
    )


# ============================================================
# SWING PULLBACK CONTEXT
# ============================================================

def print_swing_pullback_values(
    daily_data: pd.DataFrame,
    trend: pd.DataFrame,
    timestamp: pd.Timestamp,
) -> None:
    """
    På 1D Swing-chart är trendTF också 1D.

    Pullback använder därför Daily EMA50 direkt.
    """

    htf_ema_fast = trend["ema_fast"]

    pullback_result = pullback_context(
        daily_data,
        htf_ema_fast=htf_ema_fast,
    )

    row = pullback_result.loc[timestamp]

    print()
    print("=" * 70)
    print("TRUST ME — SWING PULLBACK PARITY")
    print("=" * 70)

    print(f"Timestamp: {timestamp}")
    print()

    print(
        f"Python HTF EMA Fast:       "
        f"{htf_ema_fast.loc[timestamp]:.6f}"
    )

    print(
        f"Python Touched EMA Long:   "
        f"{bool(row['touched_ema_long'])}"
    )

    print(
        f"Python Reclaimed Long:     "
        f"{bool(row['reclaimed_long'])}"
    )

    print(
        f"Python Touched EMA Short:  "
        f"{bool(row['touched_ema_short'])}"
    )

    print(
        f"Python Reclaimed Short:    "
        f"{bool(row['reclaimed_short'])}"
    )


# ============================================================
# SWING SESSION CONTEXT
# ============================================================

def print_swing_session_values(
    daily_data: pd.DataFrame,
    timestamp: pd.Timestamp,
) -> None:
    """
    Trust Me v2.0:
        sessionOk = isSwing or inEntrySession

    Eftersom isSwing=True ska sessionOk alltid vara True.
    """

    in_entry_session = pd.Series(
        False,
        index=daily_data.index,
        dtype=bool,
    )

    session_ok = session_entry_context(
        is_swing=True,
        in_entry_session=in_entry_session,
    )

    print()
    print("=" * 70)
    print("TRUST ME — SWING SESSION PARITY")
    print("=" * 70)

    print(f"Timestamp: {timestamp}")
    print()
    print("Python isSwing:    True")

    print(
        f"Python Session OK: "
        f"{bool(session_ok.loc[timestamp])}"
    )


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    ticker = "MU"

    # ========================================================
    # 1. BEHÅLL VÅR VERIFIERADE 45M DATA-PARITY
    # ========================================================

    raw_intraday = download_yahoo_data(
        ticker,
        period="60d",
        interval="15m",
    )

    data_45m = resample_regular_session(
        raw_intraday,
        timeframe_minutes=45,
    )

    print_45m_feed_parity(
        data_45m,
    )

    old_parity_timestamp = pd.Timestamp(
        "2026-08-21 11:00",
        tz="America/New_York",
    )

    print_45m_htf_regression(
        ticker=ticker,
        intraday_data=data_45m,
        timestamp=old_parity_timestamp,
    )

    # ========================================================
    # 2. HUVUD-PARITY: TRUST ME SWING PÅ DAILY
    # ========================================================

    daily_data = download_yahoo_data(
        ticker,
        period="2y",
        interval="1d",
    )

    swing_timestamp = timestamp_for_date(
        daily_data,
        SWING_PARITY_DATE,
    )

    print()
    print("#" * 70)
    print("TRUST ME v2.0 — SWING PARITY BASELINE")
    print("#" * 70)

    print(f"Ticker:    {ticker}")
    print("Mode:      Swing")
    print("Chart TF:  1D")
    print(f"Date:      {SWING_PARITY_DATE}")

    trend = print_swing_trend_values(
        daily_data,
        swing_timestamp,
    )

    print_swing_volatility_values(
        daily_data,
        swing_timestamp,
    )

    print_swing_momentum_values(
        daily_data,
        swing_timestamp,
    )

    print_swing_volume_values(
        daily_data,
        swing_timestamp,
    )

    print_swing_breakout_values(
        daily_data,
        swing_timestamp,
    )

    print_swing_squeeze_values(
        daily_data,
        swing_timestamp,
    )

    print_swing_pullback_values(
        daily_data,
        trend,
        swing_timestamp,
    )

    print_swing_session_values(
        daily_data,
        swing_timestamp,
    )


if __name__ == "__main__":
    main()