from __future__ import annotations

import pandas as pd

from src.diagnostics_context import context_diagnostics

from src.trust_me_core import (
    pullback_context,
    entry_modules_context,
    module_summary_context,
    entry_signal_context,
)


def signal_diagnostics(
    df: pd.DataFrame,
    *,
    is_swing: bool = True,
    allow_long: bool = True,
    allow_short: bool = False,

    # Trend
    ema_fast_length: int = 50,
    ema_slow_length: int = 200,
    adx_length: int = 14,
    adx_min_swing: float = 18.0,
    adx_min_intraday: float = 15.0,

    # Volatility
    atr_length: int = 14,
    min_atr_pct_swing: float = 1.0,
    min_atr_pct_intraday: float = 0.3,
    use_candle_filter: bool = True,
    max_candle_atr: float = 2.0,

    # Momentum
    rsi_length: int = 14,
    rsi_smooth_len: int = 9,
    confluence_window_swing: int = 5,
    confluence_window_intraday: int = 8,

    # Volume
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
) -> pd.DataFrame:
    """
    Bygger Trust Me Signal Diagnostics.

    Version 1, steg 1:
    - återanvänder Context Diagnostics
    - beräknar Pullback Context
    - beräknar Entry Modules

    Entry Modules:
    - Pullback Long / Short
    - Breakout Long / Short
    - Squeeze Long / Short
    - Mean Reversion Long / Short

    Funktionen ändrar INTE Trust Me-strategins
    signal- eller entrylogik.
    """

    # ========================================================
    # CONTEXT
    # ========================================================

    result = context_diagnostics(
        df,
        is_swing=is_swing,
        allow_long=allow_long,
        allow_short=allow_short,

        # Trend
        ema_fast_length=ema_fast_length,
        ema_slow_length=ema_slow_length,
        adx_length=adx_length,
        adx_min_swing=adx_min_swing,
        adx_min_intraday=adx_min_intraday,

        # Volatility
        atr_length=atr_length,
        min_atr_pct_swing=min_atr_pct_swing,
        min_atr_pct_intraday=min_atr_pct_intraday,
        use_candle_filter=use_candle_filter,
        max_candle_atr=max_candle_atr,

        # Momentum
        rsi_length=rsi_length,
        rsi_smooth_len=rsi_smooth_len,
        confluence_window_swing=confluence_window_swing,
        confluence_window_intraday=confluence_window_intraday,

        # Volume
        use_volume_filter=use_volume_filter,
        volume_length_swing=volume_length_swing,
        volume_length_intraday=volume_length_intraday,

        # Breakout
        breakout_lookback_swing=breakout_lookback_swing,
        breakout_lookback_intraday=breakout_lookback_intraday,

        # Squeeze
        bb_length=bb_length,
        bb_mult=bb_mult,
        squeeze_window_swing=squeeze_window_swing,
        squeeze_window_intraday=squeeze_window_intraday,
    )

    # ========================================================
    # PULLBACK CONTEXT
    # ========================================================

    pullback = pullback_context(
        df,
        result["htf_ema_fast"],
    )

    result["touched_ema_long"] = (
        pullback["touched_ema_long"]
    )

    result["reclaimed_long"] = (
        pullback["reclaimed_long"]
    )

    result["touched_ema_short"] = (
        pullback["touched_ema_short"]
    )

    result["reclaimed_short"] = (
        pullback["reclaimed_short"]
    )

    # ========================================================
    # ENTRY MODULES
    # ========================================================

    modules = entry_modules_context(
        df=df,

        uptrend=result["uptrend"],
        downtrend=result["downtrend"],
        htf_ema_slow=result["htf_ema_slow"],

        rsi_up_recent=result["rsi_up_recent"],
        rsi_down_recent=result["rsi_down_recent"],

        touched_ema_long=result["touched_ema_long"],
        reclaimed_long=result["reclaimed_long"],
        touched_ema_short=result["touched_ema_short"],
        reclaimed_short=result["reclaimed_short"],

        breakout_level=result["breakout_level"],
        breakdown_level=result["breakdown_level"],

        volume_strong=result["volume_strong"],

        squeeze_recent=result["squeeze_recent"],
        in_squeeze=result["in_squeeze"],
        bb_upper=result["bb_upper"],
        bb_lower=result["bb_lower"],

        was_oversold_recently=result["was_oversold_recently"],
        was_overbought_recently=result["was_overbought_recently"],

        rsi_cross_up=result["rsi_cross_up"],
        rsi_cross_down=result["rsi_cross_down"],
    )

    # ========================================================
    # ENTRY MODULE OUTPUT
    # ========================================================

    result["pullback_long"] = modules["pullback_long"]
    result["breakout_long"] = modules["breakout_long"]
    result["squeeze_long"] = modules["squeeze_long"]
    result["mean_rev_long"] = modules["mean_rev_long"]

    result["pullback_short"] = modules["pullback_short"]
    result["breakout_short"] = modules["breakout_short"]
    result["squeeze_short"] = modules["squeeze_short"]
    result["mean_rev_short"] = modules["mean_rev_short"]

    # ========================================================
    # MODULE SUMMARY / SCORE
    # ========================================================

    module_summary = module_summary_context(
        pullback_long=result["pullback_long"],
        breakout_long=result["breakout_long"],
        squeeze_long=result["squeeze_long"],
        mean_rev_long=result["mean_rev_long"],

        pullback_short=result["pullback_short"],
        breakout_short=result["breakout_short"],
        squeeze_short=result["squeeze_short"],
        mean_rev_short=result["mean_rev_short"],
    )

    # ========================================================
    # MODULE SUMMARY OUTPUT
    # ========================================================

    result["long_score"] = (
        module_summary["long_score"]
    )

    result["long_module_text"] = (
        module_summary["long_module_text"]
    )

    result["short_score"] = (
        module_summary["short_score"]
    )

    result["short_module_text"] = (
        module_summary["short_module_text"]
    )

    # Trust Me v2.0:
    # Minst en aktiv entry-modul krävs.
    result["min_confluence"] = 1

    # ========================================================
    # FINAL SIGNAL
    # ========================================================

    # För historiska färdigstängda Yahoo-bars motsvarar
    # dessa bars Pine barstate.isconfirmed.
    is_confirmed = pd.Series(
        True,
        index=result.index,
        dtype=bool,
    )

    entry_signal = entry_signal_context(
        allow_long=allow_long,
        allow_short=allow_short,

        long_score=result["long_score"],
        short_score=result["short_score"],

        min_confluence=1,

        volatility_ok=result["volatility_ok"],
        not_overextended=result["not_overextended"],
        session_ok=result["session_ok"],

        is_confirmed=is_confirmed,
    )

    # ========================================================
    # FINAL SIGNAL OUTPUT
    # ========================================================

    result["is_confirmed"] = is_confirmed

    result["long_signal"] = (
        entry_signal["long_signal"]
    )

    result["short_signal"] = (
        entry_signal["short_signal"]
    )

    # ========================================================
    # FAILURE / NEAR-MISS ENGINE
    # ========================================================
    #
    # Motsvarar Pine-blocket:
    # FAILURE / NEAR-MISS ENGINE
    #
    # Här analyserar vi varför den slutliga signalen
    # misslyckades, utan att ändra signal-logiken.
    # ========================================================

    # --------------------------------------------------------
    # LONG - INDIVIDUELLA SLUTFILTER
    # --------------------------------------------------------

    result["long_fail_direction"] = (
        ~result["allow_long"]
    )

    result["long_fail_score"] = (
        result["long_score"]
        < result["min_confluence"]
    )

    result["long_fail_volatility"] = (
        ~result["volatility_ok"]
    )

    result["long_fail_candle"] = (
        ~result["not_overextended"]
    )

    result["long_fail_session"] = (
        ~result["session_ok"]
    )

    result["long_fail_confirmed"] = (
        ~result["is_confirmed"]
    )

    # --------------------------------------------------------
    # LONG - FAIL COUNT
    # --------------------------------------------------------

    result["long_fail_count"] = (
        result["long_fail_direction"].astype(int)
        + result["long_fail_score"].astype(int)
        + result["long_fail_volatility"].astype(int)
        + result["long_fail_candle"].astype(int)
        + result["long_fail_session"].astype(int)
        + result["long_fail_confirmed"].astype(int)
    )

    # --------------------------------------------------------
    # LONG - SCORE GAP
    # --------------------------------------------------------

    result["long_score_gap"] = (
        result["min_confluence"]
        - result["long_score"]
    ).clip(lower=0)

    # --------------------------------------------------------
    # LONG - NEAR MISS
    # --------------------------------------------------------
    #
    # Pine:
    # longNearMiss =
    #     not longSignal and longFailCount == 1
    #
    # Exakt ETT slutfilter saknas.
    # --------------------------------------------------------

    result["long_near_miss"] = (
        (~result["long_signal"])
        & (result["long_fail_count"] == 1)
    )

    result["long_near_miss_direction"] = (
        result["long_near_miss"]
        & result["long_fail_direction"]
    )

    result["long_near_miss_score"] = (
        result["long_near_miss"]
        & result["long_fail_score"]
    )

    result["long_near_miss_volatility"] = (
        result["long_near_miss"]
        & result["long_fail_volatility"]
    )

    result["long_near_miss_candle"] = (
        result["long_near_miss"]
        & result["long_fail_candle"]
    )

    result["long_near_miss_session"] = (
        result["long_near_miss"]
        & result["long_fail_session"]
    )

    result["long_near_miss_confirmed"] = (
        result["long_near_miss"]
        & result["long_fail_confirmed"]
    )

    # --------------------------------------------------------
    # SHORT - INDIVIDUELLA SLUTFILTER
    # --------------------------------------------------------

    result["short_fail_direction"] = (
        ~result["allow_short"]
    )

    result["short_fail_score"] = (
        result["short_score"]
        < result["min_confluence"]
    )

    result["short_fail_volatility"] = (
        ~result["volatility_ok"]
    )

    result["short_fail_candle"] = (
        ~result["not_overextended"]
    )

    result["short_fail_session"] = (
        ~result["session_ok"]
    )

    result["short_fail_confirmed"] = (
        ~result["is_confirmed"]
    )

    # --------------------------------------------------------
    # SHORT - FAIL COUNT
    # --------------------------------------------------------

    result["short_fail_count"] = (
        result["short_fail_direction"].astype(int)
        + result["short_fail_score"].astype(int)
        + result["short_fail_volatility"].astype(int)
        + result["short_fail_candle"].astype(int)
        + result["short_fail_session"].astype(int)
        + result["short_fail_confirmed"].astype(int)
    )

    # --------------------------------------------------------
    # SHORT - SCORE GAP
    # --------------------------------------------------------

    result["short_score_gap"] = (
        result["min_confluence"]
        - result["short_score"]
    ).clip(lower=0)

    # --------------------------------------------------------
    # SHORT - NEAR MISS
    # --------------------------------------------------------

    result["short_near_miss"] = (
        (~result["short_signal"])
        & (result["short_fail_count"] == 1)
    )

    result["short_near_miss_direction"] = (
        result["short_near_miss"]
        & result["short_fail_direction"]
    )

    result["short_near_miss_score"] = (
        result["short_near_miss"]
        & result["short_fail_score"]
    )

    result["short_near_miss_volatility"] = (
        result["short_near_miss"]
        & result["short_fail_volatility"]
    )

    result["short_near_miss_candle"] = (
        result["short_near_miss"]
        & result["short_fail_candle"]
    )

    result["short_near_miss_session"] = (
        result["short_near_miss"]
        & result["short_fail_session"]
    )

    result["short_near_miss_confirmed"] = (
        result["short_near_miss"]
        & result["short_fail_confirmed"]
    )

    # ========================================================
    # MODULE FAILURE BREAKDOWN - LONG
    # ========================================================
    #
    # Motsvarar Pine-blocket:
    # MODULE FAILURE BREAKDOWN - LONG
    #
    # Syftet är att förklara varför respektive
    # Long-entrymodul INTE kvalificerade sig.
    # ========================================================

    # --------------------------------------------------------
    # PULLBACK LONG
    # --------------------------------------------------------
    #
    # Bitvärden:
    # 1  = Trend
    # 2  = Slow EMA
    # 4  = RSI
    # 8  = EMA Touch
    # 16 = Reclaim
    # --------------------------------------------------------

    result["pb_long_fail_trend"] = (
        ~result["uptrend"]
    )

    result["pb_long_fail_slow_ema"] = ~(
        result["close"] > result["htf_ema_slow"]
    )

    result["pb_long_fail_rsi"] = (
        ~result["rsi_up_recent"]
    )

    result["pb_long_fail_touch"] = (
        ~result["touched_ema_long"]
    )

    result["pb_long_fail_reclaim"] = (
        ~result["reclaimed_long"]
    )

    result["pb_long_fail_mask"] = (
        result["pb_long_fail_trend"].astype(int) * 1
        + result["pb_long_fail_slow_ema"].astype(int) * 2
        + result["pb_long_fail_rsi"].astype(int) * 4
        + result["pb_long_fail_touch"].astype(int) * 8
        + result["pb_long_fail_reclaim"].astype(int) * 16
    )

    # --------------------------------------------------------
    # BREAKOUT LONG
    # --------------------------------------------------------
    #
    # Bitvärden:
    # 1 = Trend
    # 2 = Price
    # 4 = Volume
    # 8 = RSI
    # --------------------------------------------------------

    result["bo_long_fail_trend"] = (
        ~result["uptrend"]
    )

    result["bo_long_fail_price"] = ~(
        result["close"] > result["breakout_level"]
    )

    result["bo_long_fail_volume"] = (
        ~result["volume_strong"]
    )

    result["bo_long_fail_rsi"] = (
        ~result["rsi_up_recent"]
    )

    result["bo_long_fail_mask"] = (
        result["bo_long_fail_trend"].astype(int) * 1
        + result["bo_long_fail_price"].astype(int) * 2
        + result["bo_long_fail_volume"].astype(int) * 4
        + result["bo_long_fail_rsi"].astype(int) * 8
    )

    # --------------------------------------------------------
    # SQUEEZE LONG
    # --------------------------------------------------------
    #
    # Bitvärden:
    # 1 = Trend
    # 2 = Recent squeeze
    # 4 = Release
    # 8 = Price above BB Upper
    #
    # Pine:
    # sqLongFailRelease = inSqueeze
    #
    # Detta är medvetet INTE inverterat:
    # om vi fortfarande är i squeeze har releasen misslyckats.
    # --------------------------------------------------------

    result["sq_long_fail_trend"] = (
        ~result["uptrend"]
    )

    result["sq_long_fail_recent"] = (
        ~result["squeeze_recent"]
    )

    result["sq_long_fail_release"] = (
        result["in_squeeze"]
    )

    result["sq_long_fail_price"] = ~(
        result["close"] > result["bb_upper"]
    )

    result["sq_long_fail_mask"] = (
        result["sq_long_fail_trend"].astype(int) * 1
        + result["sq_long_fail_recent"].astype(int) * 2
        + result["sq_long_fail_release"].astype(int) * 4
        + result["sq_long_fail_price"].astype(int) * 8
    )

    # --------------------------------------------------------
    # MEAN REVERSION LONG
    # --------------------------------------------------------
    #
    # Bitvärden:
    # 1  = Trend
    # 2  = Slow EMA
    # 4  = Oversold recently
    # 8  = RSI Cross Up
    # 16 = Bullish candle
    # --------------------------------------------------------

    result["mr_long_fail_trend"] = (
        ~result["uptrend"]
    )

    result["mr_long_fail_slow_ema"] = ~(
        result["close"] > result["htf_ema_slow"]
    )

    result["mr_long_fail_oversold"] = (
        ~result["was_oversold_recently"]
    )

    result["mr_long_fail_rsi_cross"] = (
        ~result["rsi_cross_up"]
    )

    result["mr_long_fail_candle"] = ~(
        result["close"] > result["open"]
    )

    result["mr_long_fail_mask"] = (
        result["mr_long_fail_trend"].astype(int) * 1
        + result["mr_long_fail_slow_ema"].astype(int) * 2
        + result["mr_long_fail_oversold"].astype(int) * 4
        + result["mr_long_fail_rsi_cross"].astype(int) * 8
        + result["mr_long_fail_candle"].astype(int) * 16
    )

    # ========================================================
    # MODULE FAILURE BREAKDOWN - SHORT
    # ========================================================
    #
    # Motsvarar Pine-blocket:
    # MODULE FAILURE BREAKDOWN - SHORT
    #
    # Syftet är att förklara varför respektive
    # Short-entrymodul INTE kvalificerade sig.
    # ========================================================

    # --------------------------------------------------------
    # PULLBACK SHORT
    # --------------------------------------------------------
    #
    # Bitvärden:
    # 1  = Trend
    # 2  = Slow EMA
    # 4  = RSI
    # 8  = EMA Touch
    # 16 = Reclaim
    # --------------------------------------------------------

    result["pb_short_fail_trend"] = (
        ~result["downtrend"]
    )

    result["pb_short_fail_slow_ema"] = ~(
        result["close"] < result["htf_ema_slow"]
    )

    result["pb_short_fail_rsi"] = (
        ~result["rsi_down_recent"]
    )

    result["pb_short_fail_touch"] = (
        ~result["touched_ema_short"]
    )

    result["pb_short_fail_reclaim"] = (
        ~result["reclaimed_short"]
    )

    result["pb_short_fail_mask"] = (
        result["pb_short_fail_trend"].astype(int) * 1
        + result["pb_short_fail_slow_ema"].astype(int) * 2
        + result["pb_short_fail_rsi"].astype(int) * 4
        + result["pb_short_fail_touch"].astype(int) * 8
        + result["pb_short_fail_reclaim"].astype(int) * 16
    )

    # --------------------------------------------------------
    # BREAKOUT SHORT
    # --------------------------------------------------------
    #
    # Bitvärden:
    # 1 = Trend
    # 2 = Price
    # 4 = Volume
    # 8 = RSI
    # --------------------------------------------------------

    result["bo_short_fail_trend"] = (
        ~result["downtrend"]
    )

    result["bo_short_fail_price"] = ~(
        result["close"] < result["breakdown_level"]
    )

    result["bo_short_fail_volume"] = (
        ~result["volume_strong"]
    )

    result["bo_short_fail_rsi"] = (
        ~result["rsi_down_recent"]
    )

    result["bo_short_fail_mask"] = (
        result["bo_short_fail_trend"].astype(int) * 1
        + result["bo_short_fail_price"].astype(int) * 2
        + result["bo_short_fail_volume"].astype(int) * 4
        + result["bo_short_fail_rsi"].astype(int) * 8
    )

    # --------------------------------------------------------
    # SQUEEZE SHORT
    # --------------------------------------------------------
    #
    # Bitvärden:
    # 1 = Trend
    # 2 = Recent squeeze
    # 4 = Release
    # 8 = Price below BB Lower
    #
    # Pine:
    # sqShortFailRelease = inSqueeze
    # --------------------------------------------------------

    result["sq_short_fail_trend"] = (
        ~result["downtrend"]
    )

    result["sq_short_fail_recent"] = (
        ~result["squeeze_recent"]
    )

    result["sq_short_fail_release"] = (
        result["in_squeeze"]
    )

    result["sq_short_fail_price"] = ~(
        result["close"] < result["bb_lower"]
    )

    result["sq_short_fail_mask"] = (
        result["sq_short_fail_trend"].astype(int) * 1
        + result["sq_short_fail_recent"].astype(int) * 2
        + result["sq_short_fail_release"].astype(int) * 4
        + result["sq_short_fail_price"].astype(int) * 8
    )

    # --------------------------------------------------------
    # MEAN REVERSION SHORT
    # --------------------------------------------------------
    #
    # Bitvärden:
    # 1  = Trend
    # 2  = Slow EMA
    # 4  = Overbought recently
    # 8  = RSI Cross Down
    # 16 = Bearish candle
    # --------------------------------------------------------

    result["mr_short_fail_trend"] = (
        ~result["downtrend"]
    )

    result["mr_short_fail_slow_ema"] = ~(
        result["close"] < result["htf_ema_slow"]
    )

    result["mr_short_fail_overbought"] = (
        ~result["was_overbought_recently"]
    )

    result["mr_short_fail_rsi_cross"] = (
        ~result["rsi_cross_down"]
    )

    result["mr_short_fail_candle"] = ~(
        result["close"] < result["open"]
    )

    result["mr_short_fail_mask"] = (
        result["mr_short_fail_trend"].astype(int) * 1
        + result["mr_short_fail_slow_ema"].astype(int) * 2
        + result["mr_short_fail_overbought"].astype(int) * 4
        + result["mr_short_fail_rsi_cross"].astype(int) * 8
        + result["mr_short_fail_candle"].astype(int) * 16
    )

    # ========================================================
    # ENTRY DELAY / OPPORTUNITY ANALYSIS
    # ========================================================
    #
    # Motsvarar Pine-blocket:
    # ENTRY DELAY / OPPORTUNITY ANALYSIS
    #
    # Här mäter vi:
    # - om allt utom score/modulkravet är redo
    # - hur länge strategin väntat på score
    # - hur lång väntan som föregick en riktig signal
    # - sammanhängande near-miss streaks
    # ========================================================

    # --------------------------------------------------------
    # ALLA SLUTFILTER UTOM SCORE
    # --------------------------------------------------------

    result["long_non_score_ready"] = (
        result["allow_long"]
        & result["volatility_ok"]
        & result["not_overextended"]
        & result["session_ok"]
        & result["is_confirmed"]
    )

    result["short_non_score_ready"] = (
        result["allow_short"]
        & result["volatility_ok"]
        & result["not_overextended"]
        & result["session_ok"]
        & result["is_confirmed"]
    )

    # --------------------------------------------------------
    # SCORE-WAIT
    # --------------------------------------------------------

    result["long_waiting_for_score"] = (
        result["long_non_score_ready"]
        & (
            result["long_score"]
            < result["min_confluence"]
        )
    )

    result["short_waiting_for_score"] = (
        result["short_non_score_ready"]
        & (
            result["short_score"]
            < result["min_confluence"]
        )
    )

    # --------------------------------------------------------
    # HELPER: CONSECUTIVE TRUE STREAK
    # --------------------------------------------------------
    #
    # Pine:
    #
    # streak :=
    #     condition
    #         ? nz(streak[1]) + 1
    #         : 0
    #
    # Resultat:
    # False False True True True False True
    #   0     0    1    2    3    0    1
    # --------------------------------------------------------

    def consecutive_true_streak(
        condition: pd.Series,
    ) -> pd.Series:
        condition = (
            condition
            .fillna(False)
            .astype(bool)
        )

        reset_group = (
            ~condition
        ).cumsum()

        streak = (
            condition.astype(int)
            .groupby(reset_group)
            .cumsum()
        )

        return streak.astype(int)

    # --------------------------------------------------------
    # SCORE WAIT BARS
    # --------------------------------------------------------

    result["long_score_wait_bars"] = (
        consecutive_true_streak(
            result["long_waiting_for_score"]
        )
    )

    result["short_score_wait_bars"] = (
        consecutive_true_streak(
            result["short_waiting_for_score"]
        )
    )

    # --------------------------------------------------------
    # DELAY ON SIGNAL
    # --------------------------------------------------------
    #
    # Pine:
    #
    # longDelayOnSignal =
    #     longSignal
    #         ? nz(longScoreWaitBars[1])
    #         : na
    #
    # Alltså:
    # På en faktisk signalbar sparar vi hur många
    # direkt föregående bars strategin endast
    # väntade på score.
    # --------------------------------------------------------

    previous_long_wait = (
        result["long_score_wait_bars"]
        .shift(1)
        .fillna(0)
    )

    previous_short_wait = (
        result["short_score_wait_bars"]
        .shift(1)
        .fillna(0)
    )

    result["long_delay_on_signal"] = (
        previous_long_wait.where(
            result["long_signal"]
        )
    )

    result["short_delay_on_signal"] = (
        previous_short_wait.where(
            result["short_signal"]
        )
    )

    # --------------------------------------------------------
    # NEAR-MISS STREAK
    # --------------------------------------------------------

    result["long_near_miss_streak"] = (
        consecutive_true_streak(
            result["long_near_miss"]
        )
    )

    result["short_near_miss_streak"] = (
        consecutive_true_streak(
            result["short_near_miss"]
        )
    )

    # --------------------------------------------------------
    # NEAR-MISS STREAK BEFORE SIGNAL
    # --------------------------------------------------------
    #
    # Pine:
    #
    # longNearMissStreakBeforeSignal =
    #     longSignal
    #         ? nz(longNearMissStreak[1])
    #         : na
    # --------------------------------------------------------

    previous_long_near_miss = (
        result["long_near_miss_streak"]
        .shift(1)
        .fillna(0)
    )

    previous_short_near_miss = (
        result["short_near_miss_streak"]
        .shift(1)
        .fillna(0)
    )

    result["long_near_miss_streak_before_signal"] = (
        previous_long_near_miss.where(
            result["long_signal"]
        )
    )

    result["short_near_miss_streak_before_signal"] = (
        previous_short_near_miss.where(
            result["short_signal"]
        )
    )

    # ========================================================
    # FINAL FILTER FAIL MASK
    # ========================================================
    #
    # Kodar vilka slutfilter som blockerade signalen.
    #
    # Bitvärden:
    # 1  = Direction
    # 2  = Score
    # 4  = Volatility
    # 8  = Candle / Overextension
    # 16 = Session
    # 32 = Confirmed Bar
    #
    # Flera samtidiga failures summeras till en mask.
    # ========================================================

    # --------------------------------------------------------
    # LONG
    # --------------------------------------------------------

    result["long_final_fail_mask"] = (
        result["long_fail_direction"].astype(int) * 1
        + result["long_fail_score"].astype(int) * 2
        + result["long_fail_volatility"].astype(int) * 4
        + result["long_fail_candle"].astype(int) * 8
        + result["long_fail_session"].astype(int) * 16
        + result["long_fail_confirmed"].astype(int) * 32
    )

    # --------------------------------------------------------
    # SHORT
    # --------------------------------------------------------

    result["short_final_fail_mask"] = (
        result["short_fail_direction"].astype(int) * 1
        + result["short_fail_score"].astype(int) * 2
        + result["short_fail_volatility"].astype(int) * 4
        + result["short_fail_candle"].astype(int) * 8
        + result["short_fail_session"].astype(int) * 16
        + result["short_fail_confirmed"].astype(int) * 32
    )

    # ========================================================
    # ACTIVE MODULE MASK
    # ========================================================
    #
    # Bitvärden:
    # 1 = Pullback
    # 2 = Breakout
    # 4 = Squeeze
    # 8 = Mean Reversion
    #
    # Masken visar exakt vilka entry-moduler
    # som är aktiva på aktuell bar.
    # ========================================================

    # --------------------------------------------------------
    # LONG
    # --------------------------------------------------------

    result["long_active_module_mask"] = (
        result["pullback_long"].astype(int) * 1
        + result["breakout_long"].astype(int) * 2
        + result["squeeze_long"].astype(int) * 4
        + result["mean_rev_long"].astype(int) * 8
    )

    # --------------------------------------------------------
    # SHORT
    # --------------------------------------------------------

    result["short_active_module_mask"] = (
        result["pullback_short"].astype(int) * 1
        + result["breakout_short"].astype(int) * 2
        + result["squeeze_short"].astype(int) * 4
        + result["mean_rev_short"].astype(int) * 8
    )

    return result