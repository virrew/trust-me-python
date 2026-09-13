from __future__ import annotations

import pandas as pd

from src.trust_me_core import (
    trend_context,
    volatility_context,
    momentum_context,
    volume_context,
    breakout_context,
    squeeze_context,
)

def context_diagnostics(
    data: pd.DataFrame,
    *,
    is_swing: bool = True,
    allow_long: bool = True,
    allow_short: bool = False,
    ema_fast_length: int = 50,
    ema_slow_length: int = 200,
    adx_length: int = 14,
    adx_min_swing: float = 18.0,
    adx_min_intraday: float = 15.0,
    atr_length: int = 14,
    min_atr_pct_swing: float = 1.0,
    min_atr_pct_intraday: float = 0.3,
    use_candle_filter: bool = True,
    max_candle_atr: float = 2.0,
    rsi_length: int = 14,
    rsi_smooth_len: int = 9,
    confluence_window_swing: int = 5,
    confluence_window_intraday: int = 8,
    use_volume_filter: bool = True,
    volume_length_swing: int = 20,
    volume_length_intraday: int = 30,

    # Breakout
    breakout_lookback_swing: int = 10,
    breakout_lookback_intraday: int = 20,

    # Squeeze
    bb_length: int = 20,
    bb_mult: float = 2.0,
    squeeze_window_swing: int = 3,
    squeeze_window_intraday: int = 6,
    in_entry_session: pd.Series | None = None,
    in_full_session: pd.Series | None = None,
) -> pd.DataFrame:
    """
    Bygger Trust Me Context Diagnostics.

    Version 1 innehåller:
    - Market Data
    - Mode
    - Session
    - Trend
    - Volatility
    - Momentum
    - Volume
    - Breakout
    - Squeeze

    Funktionen ändrar INTE Trust Me-logiken.
    Den observerar och lagrar vad strategin ser
    på varje bar.

    Core-värden hämtas från den parity-verifierade
    Trust Me Core-motorn.

    Diagnostic-lagret kompletterar dessa med
    kontinuerliga mått som beskriver hur långt
    varje bar befinner sig från strategins
    olika gränser och villkor.
    """

    if data.empty:
        raise ValueError("data får inte vara tom.")

    required_columns = {
        "open",
        "high",
        "low",
        "close",
        "volume",
    }

    missing_columns = required_columns.difference(
        data.columns
    )

    if missing_columns:
        raise ValueError(
            "Data saknar kolumner: "
            + ", ".join(sorted(missing_columns))
        )

    result = pd.DataFrame(
        index=data.index
    )

    # ========================================================
    # MARKET DATA
    # ========================================================

    result["open"] = data["open"]
    result["high"] = data["high"]
    result["low"] = data["low"]
    result["close"] = data["close"]
    result["volume"] = data["volume"]

    # ========================================================
    # MODE
    # ========================================================

    result["is_swing"] = is_swing
    result["allow_long"] = allow_long
    result["allow_short"] = allow_short

    # ========================================================
    # SESSION
    # ========================================================

    if in_entry_session is None:
        in_entry_session = pd.Series(
            True,
            index=data.index,
            dtype=bool,
        )
    else:
        in_entry_session = (
            in_entry_session
            .reindex(data.index)
            .fillna(False)
            .astype(bool)
        )

    if in_full_session is None:
        in_full_session = pd.Series(
            True,
            index=data.index,
            dtype=bool,
        )
    else:
        in_full_session = (
            in_full_session
            .reindex(data.index)
            .fillna(False)
            .astype(bool)
        )

    result["in_entry_session"] = in_entry_session
    result["in_full_session"] = in_full_session

    # Pine:
    # sessionOk = isSwing or inEntrySession

    if is_swing:
        result["session_ok"] = True
    else:
        result["session_ok"] = (
            result["in_entry_session"]
        )

    # ========================================================
    # TREND CONTEXT
    # ========================================================

    trend = trend_context(
        data,
        ema_fast_length=ema_fast_length,
        ema_slow_length=ema_slow_length,
        adx_length=adx_length,
    )

    result["htf_ema_fast"] = trend["ema_fast"]
    result["htf_ema_slow"] = trend["ema_slow"]
    result["htf_adx"] = trend["adx"]

    adx_min = (
        adx_min_swing
        if is_swing
        else adx_min_intraday
    )

    result["adx_min"] = adx_min

    result["adx_ok"] = (
        result["htf_adx"] > result["adx_min"]
    )

    result["uptrend"] = (
        (result["htf_ema_fast"] > result["htf_ema_slow"])
        & result["adx_ok"]
    )

    result["downtrend"] = (
        (result["htf_ema_fast"] < result["htf_ema_slow"])
        & result["adx_ok"]
    )

    # Diagnostiska mått.
    #
    # Dessa ändrar INTE strategins beslut.
    # De mäter hur långt från gränserna vi befinner oss.

    result["ema_spread"] = (
        result["htf_ema_fast"]
        - result["htf_ema_slow"]
    )

    result["ema_spread_pct"] = (
        (
        result["ema_spread"]
        / result["htf_ema_slow"]
        )
        * 100
    ).where(
        result["htf_ema_slow"] != 0
    )

    result["adx_margin"] = (
        result["htf_adx"]
        - result["adx_min"]
    )

    # ========================================================
    # VOLATILITY CONTEXT
    # ========================================================

    min_atr_pct = (
        min_atr_pct_swing
        if is_swing
        else min_atr_pct_intraday
    )

    volatility = volatility_context(
        data,
        atr_length=atr_length,
        min_atr_pct=min_atr_pct,
        use_candle_filter=use_candle_filter,
        max_candle_atr=max_candle_atr,
    )

    result["atr"] = volatility["atr"]
    result["atr_pct"] = volatility["atr_pct"]
    result["min_atr_pct"] = min_atr_pct

    result["volatility_ok"] = (
        volatility["volatility_ok"]
    )

    result["candle_range"] = (
        volatility["candle_range"]
    )

    result["max_candle_atr"] = max_candle_atr

    result["not_overextended"] = (
        volatility["not_overextended"]
    )

    # Hur långt över/under ATR%-gränsen ligger baren?
    result["atr_pct_margin"] = (
        result["atr_pct"]
        - result["min_atr_pct"]
    )

    # Candle range uttryckt i ATR.
    result["candle_range_atr"] = (
        result["candle_range"]
        / result["atr"]
    ).where(
        result["atr"] > 0
    )

    # Hur mycket utrymme återstår innan
    # candle-filtret underkänner baren?
    result["candle_atr_margin"] = (
        result["max_candle_atr"]
        - result["candle_range_atr"]
    )


    # ========================================================
    # MOMENTUM CONTEXT
    # ========================================================

    confluence_window = (
        confluence_window_swing
        if is_swing
        else confluence_window_intraday
    )

    momentum = momentum_context(
        data,
        rsi_length=rsi_length,
        rsi_smooth_len=rsi_smooth_len,
        confluence_window=confluence_window,
    )

    # --------------------------------------------------------
    # Core-värden
    # --------------------------------------------------------

    result["rsi"] = momentum["rsi"]
    result["rsi_avg"] = momentum["rsi_avg"]

    result["rsi_cross_up"] = (
        momentum["rsi_cross_up"]
    )

    result["rsi_cross_down"] = (
        momentum["rsi_cross_down"]
    )

    result["bars_since_rsi_up"] = (
        momentum["bars_since_rsi_up"]
    )

    result["bars_since_rsi_down"] = (
        momentum["bars_since_rsi_down"]
    )

    result["rsi_up_recent"] = (
        momentum["rsi_up_recent"]
    )

    result["rsi_down_recent"] = (
        momentum["rsi_down_recent"]
    )

    result["bars_since_oversold"] = (
        momentum["bars_since_oversold"]
    )

    result["bars_since_overbought"] = (
        momentum["bars_since_overbought"]
    )

    result["was_oversold_recently"] = (
        momentum["was_oversold_recently"]
    )

    result["was_overbought_recently"] = (
        momentum["was_overbought_recently"]
    )

    result["confluence_window"] = (
        confluence_window
    )

    # --------------------------------------------------------
    # Diagnostic measurements
    # --------------------------------------------------------

    # Pine Context Diagnostic:
    #
    # rsiDistanceFromAvg = rsiValue - rsiAvg

    result["rsi_distance_from_avg"] = (
        result["rsi"]
        - result["rsi_avg"]
    )

    # Extra diagnostiska mått.
    #
    # Avstånd till klassiska RSI-nivåer.
    # Positivt/negativt värde visar på vilken
    # sida om nivån aktuell RSI befinner sig.

    result["rsi_distance_from_50"] = (
        result["rsi"] - 50.0
    )

    result["rsi_distance_from_30"] = (
        result["rsi"] - 30.0
    )

    result["rsi_distance_from_70"] = (
        result["rsi"] - 70.0
    )

    # ========================================================
    # VOLUME CONTEXT
    # ========================================================

    volume_length = (
        volume_length_swing
        if is_swing
        else volume_length_intraday
    )

    volume_result = volume_context(
        data,
        volume_length=volume_length,
        use_volume_filter=use_volume_filter,
    )

    # --------------------------------------------------------
    # Core-värden
    # --------------------------------------------------------

    result["average_volume"] = (
        volume_result["average_volume"]
    )

    result["volume_strong"] = (
        volume_result["volume_strong"]
    )

    result["volume_length"] = volume_length

    result["use_volume_filter"] = (
        use_volume_filter
    )

    # --------------------------------------------------------
    # Diagnostic measurements
    # --------------------------------------------------------

    # Samma diagnostic som i Pine Context Diagnostic:
    #
    # volumeRatio =
    #     averageVolume > 0
    #         ? volume / averageVolume
    #         : na

    result["volume_ratio"] = (
        result["volume"]
        / result["average_volume"]
    ).where(
        result["average_volume"] > 0
    )

    # Absolut skillnad mellan aktuell volym
    # och volymens glidande medelvärde.
    #
    # Positivt = över snittet.
    # Negativt = under snittet.

    result["volume_margin"] = (
        result["volume"]
        - result["average_volume"]
    )

    # Samma skillnad uttryckt procentuellt.
    #
    # Exempel:
    # +20 = volymen ligger 20 % över snittet.
    # -20 = volymen ligger 20 % under snittet.

    result["volume_margin_pct"] = (
        (
            result["volume"]
            - result["average_volume"]
        )
        / result["average_volume"]
        * 100
    ).where(
        result["average_volume"] > 0
    )

    # ========================================================
    # BREAKOUT CONTEXT
    # ========================================================

    breakout_lookback = (
        breakout_lookback_swing
        if is_swing
        else breakout_lookback_intraday
    )

    breakout_result = breakout_context(
        data,
        breakout_lookback=breakout_lookback,
    )

    # --------------------------------------------------------
    # Core-värden
    # --------------------------------------------------------

    result["breakout_level"] = (
        breakout_result["breakout_level"]
    )

    result["breakdown_level"] = (
        breakout_result["breakdown_level"]
    )

    result["breakout_lookback"] = (
        breakout_lookback
    )

    # --------------------------------------------------------
    # Diagnostic measurements — Pine-facit
    # --------------------------------------------------------

    # Pine:
    # distanceToBreakout = breakoutLevel - close

    result["distance_to_breakout"] = (
        result["breakout_level"]
        - result["close"]
    )

    # Pine:
    # distanceToBreakdown = close - breakdownLevel

    result["distance_to_breakdown"] = (
        result["close"]
        - result["breakdown_level"]
    )

    # Pine:
    # distanceToBreakoutAtr =
    #     atrValueRaw > 0
    #         ? distanceToBreakout / atrValueRaw
    #         : na

    result["distance_to_breakout_atr"] = (
        result["distance_to_breakout"]
        / result["atr"]
    ).where(
        result["atr"] > 0
    )

    # Pine:
    # distanceToBreakdownAtr =
    #     atrValueRaw > 0
    #         ? distanceToBreakdown / atrValueRaw
    #         : na

    result["distance_to_breakdown_atr"] = (
        result["distance_to_breakdown"]
        / result["atr"]
    ).where(
        result["atr"] > 0
    )

    # Pine:
    # priceAboveBreakout = close > breakoutLevel

    result["price_above_breakout"] = (
        result["close"]
        > result["breakout_level"]
    )

    # Pine:
    # priceBelowBreakdown = close < breakdownLevel

    result["price_below_breakdown"] = (
        result["close"]
        < result["breakdown_level"]
    )

    # ========================================================
    # SQUEEZE CONTEXT
    # ========================================================

    squeeze_window = (
        squeeze_window_swing
        if is_swing
        else squeeze_window_intraday
    )

    squeeze_result = squeeze_context(
        data,
        bb_length=bb_length,
        bb_mult=bb_mult,
        squeeze_window=squeeze_window,
    )

    # --------------------------------------------------------
    # Core-värden
    # --------------------------------------------------------

    result["bb_basis"] = (
        squeeze_result["bb_basis"]
    )

    result["bb_dev"] = (
        squeeze_result["bb_dev"]
    )

    result["bb_upper"] = (
        squeeze_result["bb_upper"]
    )

    result["bb_lower"] = (
        squeeze_result["bb_lower"]
    )

    result["bb_width"] = (
        squeeze_result["bb_width"]
    )

    result["bb_width_avg"] = (
        squeeze_result["bb_width_avg"]
    )

    result["in_squeeze"] = (
        squeeze_result["in_squeeze"]
    )

    result["bars_since_squeeze"] = (
        squeeze_result["bars_since_squeeze"]
    )

    result["squeeze_recent"] = (
        squeeze_result["squeeze_recent"]
    )

    result["squeeze_window"] = (
        squeeze_window
    )

    result["bb_length"] = (
        bb_length
    )

    result["bb_mult"] = (
        bb_mult
    )

    # --------------------------------------------------------
    # Diagnostic measurements — Pine-facit
    # --------------------------------------------------------

    # Pine:
    # squeezeThreshold = bbWidthAvg * 0.7

    result["squeeze_threshold"] = (
        result["bb_width_avg"] * 0.7
    )

    # Pine:
    # distanceToSqueeze =
    #     bbWidth - squeezeThreshold

    result["distance_to_squeeze"] = (
        result["bb_width"]
        - result["squeeze_threshold"]
    )

    # Pine:
    # distanceToSqueezePct =
    #     squeezeThreshold != 0
    #         ? (bbWidth / squeezeThreshold - 1) * 100
    #         : na

    result["distance_to_squeeze_pct"] = (
        (
            result["bb_width"]
            / result["squeeze_threshold"]
            - 1.0
        )
        * 100.0
    ).where(
        result["squeeze_threshold"] != 0
    )

    # Pine:
    # distanceToUpperBandAtr =
    #     atrValueRaw > 0
    #         ? (bbUpper - close) / atrValueRaw
    #         : na

    result["distance_to_upper_band_atr"] = (
        (
            result["bb_upper"]
            - result["close"]
        )
        / result["atr"]
    ).where(
        result["atr"] > 0
    )

    # Pine:
    # distanceToLowerBandAtr =
    #     atrValueRaw > 0
    #         ? (close - bbLower) / atrValueRaw
    #         : na

    result["distance_to_lower_band_atr"] = (
        (
            result["close"]
            - result["bb_lower"]
        )
        / result["atr"]
    ).where(
        result["atr"] > 0
    )

    return result