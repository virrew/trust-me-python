from __future__ import annotations

import numpy as np
import pandas as pd


def ema(series: pd.Series, length: int) -> pd.Series:
    """
    Beräknar exponential moving average.

    Ska motsvara Pine Scripts:
        ta.ema(series, length)
    """

    if length < 1:
        raise ValueError("EMA length måste vara minst 1.")

    return series.ewm(
        span=length,
        adjust=False,
    ).mean()


def rma(series: pd.Series, length: int) -> pd.Series:
    """
    Wilder's Moving Average / RMA.

    Avsikten är att efterlikna Pine:
        ta.rma(series, length)

    RMA startar när det finns 'length'
    giltiga värden för det första SMA-seedet.
    """

    if length < 1:
        raise ValueError("RMA length måste vara minst 1.")

    values = series.astype(float).to_numpy()

    result = np.full(
        len(values),
        np.nan,
        dtype=float,
    )

    valid_values = []
    previous_rma = np.nan

    for i, current in enumerate(values):

        # RMA är ännu inte initierad.
        if np.isnan(previous_rma):

            if not np.isnan(current):
                valid_values.append(current)

            # När vi fått length giltiga värden
            # använder vi deras SMA som första RMA.
            if len(valid_values) == length:
                previous_rma = float(
                    np.mean(valid_values)
                )

                result[i] = previous_rma

            continue

        # Wilder/RMA efter initieringen.
        if not np.isnan(current):
            previous_rma = (
                previous_rma
                + (current - previous_rma) / length
            )

        result[i] = previous_rma

    return pd.Series(
        result,
        index=series.index,
    )


def dmi_adx(
    df: pd.DataFrame,
    di_length: int,
    adx_smoothing: int,
) -> pd.DataFrame:
    """
    Beräknar +DI, -DI och ADX.

    Avsikten är att efterlikna Pine Scripts:
        ta.dmi(di_length, adx_smoothing)
    """

    high = df["high"].astype(float)
    low = df["low"].astype(float)
    close = df["close"].astype(float)

    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = pd.Series(
        np.where(
            (up_move > down_move) & (up_move > 0),
            up_move,
            0.0,
        ),
        index=df.index,
    )

    minus_dm = pd.Series(
        np.where(
            (down_move > up_move) & (down_move > 0),
            down_move,
            0.0,
        ),
        index=df.index,
    )

    previous_close = close.shift(1)

    true_range = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    atr_rma = rma(true_range, di_length)
    plus_dm_rma = rma(plus_dm, di_length)
    minus_dm_rma = rma(minus_dm, di_length)

    plus_di = 100 * plus_dm_rma / atr_rma
    minus_di = 100 * minus_dm_rma / atr_rma

    di_sum = plus_di + minus_di

    dx = 100 * (plus_di - minus_di).abs() / di_sum
    dx = dx.where(di_sum != 0, 0.0)

    adx = rma(dx, adx_smoothing)

    result = pd.DataFrame(index=df.index)

    result["di_plus"] = plus_di
    result["di_minus"] = minus_di
    result["adx"] = adx

    return result


def trend_context(
    df: pd.DataFrame,
    ema_fast_length: int,
    ema_slow_length: int,
    adx_length: int,
) -> pd.DataFrame:
    """
    Motsvarar TrustMeCore.trendContext i Pine.

    Returnerar:
    - ema_fast
    - ema_slow
    - adx
    """

    dmi = dmi_adx(
        df,
        di_length=adx_length,
        adx_smoothing=adx_length,
    )

    result = pd.DataFrame(index=df.index)

    result["ema_fast"] = ema(
        df["close"],
        ema_fast_length,
    )

    result["ema_slow"] = ema(
        df["close"],
        ema_slow_length,
    )

    result["adx"] = dmi["adx"]

    return result

def trend_regime_context(
    ema_fast: pd.Series,
    ema_slow: pd.Series,
    adx: pd.Series,
    adx_min: float,
) -> pd.DataFrame:
    """
    Motsvarar TrustMeCore.trendRegimeContext i Pine.

    Uptrend:
        ema_fast > ema_slow
        och
        adx >= adx_min

    Downtrend:
        ema_fast < ema_slow
        och
        adx >= adx_min
    """

    result = pd.DataFrame(index=ema_fast.index)

    result["uptrend"] = (
        (ema_fast > ema_slow)
        & (adx > adx_min)
    )

    result["downtrend"] = (
        (ema_fast < ema_slow)
        & (adx > adx_min)
    )

    return result

def true_range(df: pd.DataFrame) -> pd.Series:
    """
    Beräknar True Range.

    Motsvarar underlaget som används av Pine Scripts:
        ta.atr(...)
    """

    high = df["high"].astype(float)
    low = df["low"].astype(float)
    close = df["close"].astype(float)

    previous_close = close.shift(1)

    return pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)


def atr(df: pd.DataFrame, length: int) -> pd.Series:
    """
    Beräknar ATR med Wilder/RMA.

    Ska motsvara Pine Scripts:
        ta.atr(length)
    """

    return rma(
        true_range(df),
        length,
    )


def volatility_context(
    df: pd.DataFrame,
    atr_length: int,
    min_atr_pct: float,
    use_candle_filter: bool,
    max_candle_atr: float,
) -> pd.DataFrame:
    """
    Motsvarar TrustMeCore.volatilityContext i Pine.

    Returnerar:
    - atr
    - atr_pct
    - volatility_ok
    - candle_range
    - not_overextended
    """

    atr_value = atr(
        df,
        atr_length,
    )

    atr_pct = (
        atr_value / df["close"]
    ) * 100

    volatility_ok = atr_pct >= min_atr_pct

    candle_range = (
        df["high"] - df["low"]
    )

    if use_candle_filter:
        not_overextended = (
            candle_range < atr_value * max_candle_atr
        )
    else:
        not_overextended = pd.Series(
            True,
            index=df.index,
        )

    result = pd.DataFrame(index=df.index)

    result["atr"] = atr_value
    result["atr_pct"] = atr_pct
    result["volatility_ok"] = volatility_ok
    result["candle_range"] = candle_range
    result["not_overextended"] = not_overextended

    return result

def sma(series: pd.Series, length: int) -> pd.Series:
    """
    Simple Moving Average.

    Motsvarar Pine:
        ta.sma(series, length)
    """

    if length < 1:
        raise ValueError("SMA length måste vara minst 1.")

    return series.rolling(
        window=length,
        min_periods=length,
    ).mean()


def rsi(series: pd.Series, length: int) -> pd.Series:
    """
    RSI med Wilder/RMA.

    Avsikten är att motsvara Pine:
        ta.rsi(series, length)
    """

    if length < 1:
        raise ValueError("RSI length måste vara minst 1.")

    change = series.astype(float).diff()

    gain = change.clip(lower=0.0)
    loss = -change.clip(upper=0.0)

    # Första förändringen finns inte.
    # Sätter den till 0 så våra RMA-serier kan initieras.
    gain = gain.fillna(0.0)
    loss = loss.fillna(0.0)

    avg_gain = rma(gain, length)
    avg_loss = rma(loss, length)

    rs = avg_gain / avg_loss

    result = 100 - (100 / (1 + rs))

    # Wilder/Pine-lik hantering när ena sidan är noll.
    result = result.where(avg_loss != 0, 100.0)
    result = result.where(avg_gain != 0, 0.0)

    # Om både gain och loss är 0 betraktar vi RSI som neutral.
    both_zero = (avg_gain == 0) & (avg_loss == 0)
    result = result.where(~both_zero, 50.0)

    return result


def crossover(
    series_a: pd.Series,
    series_b: pd.Series,
) -> pd.Series:
    """
    Motsvarar Pine:
        ta.crossover(a, b)
    """

    return (
        (series_a > series_b)
        & (series_a.shift(1) <= series_b.shift(1))
    ).fillna(False)


def crossunder(
    series_a: pd.Series,
    series_b: pd.Series,
) -> pd.Series:
    """
    Motsvarar Pine:
        ta.crossunder(a, b)
    """

    return (
        (series_a < series_b)
        & (series_a.shift(1) >= series_b.shift(1))
    ).fillna(False)


def barssince(condition: pd.Series) -> pd.Series:
    """
    Motsvarar principen i Pine:
        ta.barssince(condition)

    0 på baren där condition är True.
    Därefter 1, 2, 3...
    NaN innan första True.
    """

    result = np.full(len(condition), np.nan, dtype=float)

    bars_since = None

    for i, value in enumerate(condition.fillna(False)):
        if bool(value):
            bars_since = 0
        elif bars_since is not None:
            bars_since += 1

        if bars_since is not None:
            result[i] = bars_since

    return pd.Series(
        result,
        index=condition.index,
    )


def momentum_context(
    df: pd.DataFrame,
    rsi_length: int,
    rsi_smooth_len: int,
    confluence_window: int,
) -> pd.DataFrame:
    """
    Motsvarar TrustMeCore.momentumContext i Pine.

    Returnerar:
    - rsi
    - rsi_avg
    - rsi_cross_up
    - rsi_cross_down
    - bars_since_rsi_up
    - bars_since_rsi_down
    - rsi_up_recent
    - rsi_down_recent
    - bars_since_oversold
    - bars_since_overbought
    - was_oversold_recently
    - was_overbought_recently
    """

    rsi_value = rsi(
        df["close"],
        rsi_length,
    )

    rsi_avg = sma(
        rsi_value,
        rsi_smooth_len,
    )

    rsi_cross_up = crossover(
        rsi_value,
        rsi_avg,
    )

    rsi_cross_down = crossunder(
        rsi_value,
        rsi_avg,
    )

    bars_since_rsi_up = barssince(rsi_cross_up)
    bars_since_rsi_down = barssince(rsi_cross_down)

    rsi_up_recent = (
        bars_since_rsi_up.notna()
        & (bars_since_rsi_up <= confluence_window)
    )

    rsi_down_recent = (
        bars_since_rsi_down.notna()
        & (bars_since_rsi_down <= confluence_window)
    )

    bars_since_oversold = barssince(
        rsi_value < 30
    )

    bars_since_overbought = barssince(
        rsi_value > 70
    )

    was_oversold_recently = (
        bars_since_oversold.notna()
        & (bars_since_oversold <= confluence_window)
    )

    was_overbought_recently = (
        bars_since_overbought.notna()
        & (bars_since_overbought <= confluence_window)
    )

    result = pd.DataFrame(index=df.index)

    result["rsi"] = rsi_value
    result["rsi_avg"] = rsi_avg
    result["rsi_cross_up"] = rsi_cross_up
    result["rsi_cross_down"] = rsi_cross_down
    result["bars_since_rsi_up"] = bars_since_rsi_up
    result["bars_since_rsi_down"] = bars_since_rsi_down
    result["rsi_up_recent"] = rsi_up_recent
    result["rsi_down_recent"] = rsi_down_recent
    result["bars_since_oversold"] = bars_since_oversold
    result["bars_since_overbought"] = bars_since_overbought
    result["was_oversold_recently"] = was_oversold_recently
    result["was_overbought_recently"] = was_overbought_recently

    return result

def volume_context(
    df: pd.DataFrame,
    volume_length: int,
    use_volume_filter: bool,
) -> pd.DataFrame:
    """
    Motsvarar TrustMeCore.volumeContext i Pine.

    Pine:
        averageVolume = ta.sma(volume, volumeLength)
        volumeStrong = not useVolumeFilter or volume > averageVolume

    Returnerar:
    - average_volume
    - volume_strong
    """

    average_volume = sma(
        df["volume"],
        volume_length,
    )

    if use_volume_filter:
        volume_strong = (
            df["volume"] > average_volume
        )
    else:
        volume_strong = pd.Series(
            True,
            index=df.index,
        )

    result = pd.DataFrame(index=df.index)

    result["average_volume"] = average_volume
    result["volume_strong"] = volume_strong

    return result

def breakout_context(
    df: pd.DataFrame,
    breakout_lookback: int,
) -> pd.DataFrame:
    """
    Motsvarar TrustMeCore.breakoutContext i Pine.

    Pine:
        breakoutLevel = ta.highest(high, breakoutLookback)[1]
        breakdownLevel = ta.lowest(low, breakoutLookback)[1]

    Den aktuella baren exkluderas genom shift(1).

    Returnerar:
    - breakout_level
    - breakdown_level
    """

    if breakout_lookback < 1:
        raise ValueError(
            "breakout_lookback måste vara minst 1."
        )

    breakout_level = (
        df["high"]
        .rolling(
            window=breakout_lookback,
            min_periods=breakout_lookback,
        )
        .max()
        .shift(1)
    )

    breakdown_level = (
        df["low"]
        .rolling(
            window=breakout_lookback,
            min_periods=breakout_lookback,
        )
        .min()
        .shift(1)
    )

    result = pd.DataFrame(index=df.index)

    result["breakout_level"] = breakout_level
    result["breakdown_level"] = breakdown_level

    return result

def squeeze_context(
    df: pd.DataFrame,
    bb_length: int,
    bb_mult: float,
    squeeze_window: int,
) -> pd.DataFrame:
    """
    Motsvarar TrustMeCore.squeezeContext i Pine.

    Pine:
        bbBasis = ta.sma(close, bbLength)
        bbDev = bbMult * ta.stdev(close, bbLength)
        bbUpper = bbBasis + bbDev
        bbLower = bbBasis - bbDev
        bbWidth = (bbUpper - bbLower) / bbBasis
        bbWidthAvg = ta.sma(bbWidth, bbLength * 2)
        inSqueeze = bbWidth < bbWidthAvg * 0.7
        barsSinceSqueeze = ta.barssince(inSqueeze)
        squeezeRecent = not na(barsSinceSqueeze)
                        and barsSinceSqueeze <= squeezeWindow
    """

    if bb_length < 1:
        raise ValueError("bb_length måste vara minst 1.")

    if squeeze_window < 0:
        raise ValueError("squeeze_window får inte vara negativ.")

    close = df["close"].astype(float)

    bb_basis = sma(
        close,
        bb_length,
    )

    # Pine ta.stdev använder populations-standardavvikelse.
    bb_std = close.rolling(
        window=bb_length,
        min_periods=bb_length,
    ).std(ddof=0)

    bb_dev = bb_mult * bb_std

    bb_upper = bb_basis + bb_dev
    bb_lower = bb_basis - bb_dev

    bb_width = (
        (bb_upper - bb_lower)
        / bb_basis
    )

    bb_width_avg = sma(
        bb_width,
        bb_length * 2,
    )

    in_squeeze = (
        bb_width
        < bb_width_avg * 0.7
    )

    bars_since_squeeze = barssince(
        in_squeeze
    )

    squeeze_recent = (
        bars_since_squeeze.notna()
        & (bars_since_squeeze <= squeeze_window)
    )

    result = pd.DataFrame(index=df.index)

    result["bb_basis"] = bb_basis
    result["bb_dev"] = bb_dev
    result["bb_upper"] = bb_upper
    result["bb_lower"] = bb_lower
    result["bb_width"] = bb_width
    result["bb_width_avg"] = bb_width_avg
    result["in_squeeze"] = in_squeeze
    result["bars_since_squeeze"] = bars_since_squeeze
    result["squeeze_recent"] = squeeze_recent

    return result

def pullback_context(
    df: pd.DataFrame,
    htf_ema_fast: pd.Series,
) -> pd.DataFrame:
    """
    Motsvarar TrustMeCore.pullbackContext i Pine.

    Pine:
        touchedEmaLong =
            ta.lowest(low, 3) <= htfEmaFast * 1.005

        reclaimedLong =
            close > htfEmaFast
            and close[1] <= htfEmaFast

        touchedEmaShort =
            ta.highest(high, 3) >= htfEmaFast * 0.995

        reclaimedShort =
            close < htfEmaFast
            and close[1] >= htfEmaFast
    """

    lowest_low_3 = (
        df["low"]
        .rolling(
            window=3,
            min_periods=3,
        )
        .min()
    )

    highest_high_3 = (
        df["high"]
        .rolling(
            window=3,
            min_periods=3,
        )
        .max()
    )

    touched_ema_long = (
        lowest_low_3
        <= htf_ema_fast * 1.005
    )

    reclaimed_long = (
        (df["close"] > htf_ema_fast)
        & (df["close"].shift(1) <= htf_ema_fast)
    )

    touched_ema_short = (
        highest_high_3
        >= htf_ema_fast * 0.995
    )

    reclaimed_short = (
        (df["close"] < htf_ema_fast)
        & (df["close"].shift(1) >= htf_ema_fast)
    )

    result = pd.DataFrame(index=df.index)

    result["touched_ema_long"] = touched_ema_long
    result["reclaimed_long"] = reclaimed_long
    result["touched_ema_short"] = touched_ema_short
    result["reclaimed_short"] = reclaimed_short

    return result

def entry_modules_context(
    df: pd.DataFrame,
    uptrend: pd.Series,
    downtrend: pd.Series,
    htf_ema_slow: pd.Series,
    rsi_up_recent: pd.Series,
    rsi_down_recent: pd.Series,
    touched_ema_long: pd.Series,
    reclaimed_long: pd.Series,
    touched_ema_short: pd.Series,
    reclaimed_short: pd.Series,
    breakout_level: pd.Series,
    breakdown_level: pd.Series,
    volume_strong: pd.Series,
    squeeze_recent: pd.Series,
    in_squeeze: pd.Series,
    bb_upper: pd.Series,
    bb_lower: pd.Series,
    was_oversold_recently: pd.Series,
    was_overbought_recently: pd.Series,
    rsi_cross_up: pd.Series,
    rsi_cross_down: pd.Series,
) -> pd.DataFrame:
    """
    Motsvarar TrustMeCore.entryModulesContext i Pine.

    Returnerar:
    - pullback_long
    - breakout_long
    - squeeze_long
    - mean_rev_long
    - pullback_short
    - breakout_short
    - squeeze_short
    - mean_rev_short
    """

    pullback_long = (
        uptrend
        & (df["close"] > htf_ema_slow)
        & rsi_up_recent
        & touched_ema_long
        & reclaimed_long
    )

    breakout_long = (
        uptrend
        & (df["close"] > breakout_level)
        & volume_strong
        & rsi_up_recent
    )

    squeeze_long = (
        uptrend
        & squeeze_recent
        & ~in_squeeze
        & (df["close"] > bb_upper)
    )

    mean_rev_long = (
        uptrend
        & (df["close"] > htf_ema_slow)
        & was_oversold_recently
        & rsi_cross_up
        & (df["close"] > df["open"])
    )

    pullback_short = (
        downtrend
        & (df["close"] < htf_ema_slow)
        & rsi_down_recent
        & touched_ema_short
        & reclaimed_short
    )

    breakout_short = (
        downtrend
        & (df["close"] < breakdown_level)
        & volume_strong
        & rsi_down_recent
    )

    squeeze_short = (
        downtrend
        & squeeze_recent
        & ~in_squeeze
        & (df["close"] < bb_lower)
    )

    mean_rev_short = (
        downtrend
        & (df["close"] < htf_ema_slow)
        & was_overbought_recently
        & rsi_cross_down
        & (df["close"] < df["open"])
    )

    result = pd.DataFrame(index=df.index)

    result["pullback_long"] = pullback_long
    result["breakout_long"] = breakout_long
    result["squeeze_long"] = squeeze_long
    result["mean_rev_long"] = mean_rev_long
    result["pullback_short"] = pullback_short
    result["breakout_short"] = breakout_short
    result["squeeze_short"] = squeeze_short
    result["mean_rev_short"] = mean_rev_short

    return result

def module_summary_context(
    pullback_long: pd.Series,
    breakout_long: pd.Series,
    squeeze_long: pd.Series,
    mean_rev_long: pd.Series,
    pullback_short: pd.Series,
    breakout_short: pd.Series,
    squeeze_short: pd.Series,
    mean_rev_short: pd.Series,
) -> pd.DataFrame:
    """
    Motsvarar TrustMeCore.moduleSummaryContext i Pine.

    Returnerar:
    - long_score
    - long_module_text
    - short_score
    - short_module_text
    """

    long_score = (
        pullback_long.astype(int)
        + breakout_long.astype(int)
        + squeeze_long.astype(int)
        + mean_rev_long.astype(int)
    )

    long_module_text = (
        pullback_long.map({True: "Pullback ", False: ""})
        + breakout_long.map({True: "Breakout ", False: ""})
        + squeeze_long.map({True: "Squeeze ", False: ""})
        + mean_rev_long.map({True: "MeanRev ", False: ""})
    )

    short_score = (
        pullback_short.astype(int)
        + breakout_short.astype(int)
        + squeeze_short.astype(int)
        + mean_rev_short.astype(int)
    )

    short_module_text = (
        pullback_short.map({True: "Pullback ", False: ""})
        + breakout_short.map({True: "Breakout ", False: ""})
        + squeeze_short.map({True: "Squeeze ", False: ""})
        + mean_rev_short.map({True: "MeanRev ", False: ""})
    )

    result = pd.DataFrame(index=pullback_long.index)

    result["long_score"] = long_score
    result["long_module_text"] = long_module_text
    result["short_score"] = short_score
    result["short_module_text"] = short_module_text

    return result

def entry_signal_context(
    allow_long: bool,
    allow_short: bool,
    long_score: pd.Series,
    short_score: pd.Series,
    min_confluence: int,
    volatility_ok: pd.Series,
    not_overextended: pd.Series,
    session_ok: pd.Series,
    is_confirmed: pd.Series | bool,
) -> pd.DataFrame:
    """
    Motsvarar TrustMeCore.entrySignalContext i Pine.

    Returnerar:
    - long_signal
    - short_signal
    """

    long_signal = (
        allow_long
        & (long_score >= min_confluence)
        & volatility_ok
        & not_overextended
        & session_ok
        & is_confirmed
    )

    short_signal = (
        allow_short
        & (short_score >= min_confluence)
        & volatility_ok
        & not_overextended
        & session_ok
        & is_confirmed
    )

    result = pd.DataFrame(index=long_score.index)

    result["long_signal"] = long_signal
    result["short_signal"] = short_signal

    return result

def session_entry_context(
    is_swing: bool,
    in_entry_session: pd.Series,
) -> pd.Series:
    """
    Motsvarar TrustMeCore.sessionEntryContext i Pine.

    Pine:
        sessionOk = isSwing or inEntrySession

    Swing:
        Sessionen begränsar inte entry.

    Intraday:
        Entry tillåts endast när aktuell bar
        ligger inom entry-sessionen.
    """

    if is_swing:
        return pd.Series(
            True,
            index=in_entry_session.index,
        )

    return in_entry_session.copy()

def breakout_context(
    df: pd.DataFrame,
    breakout_lookback: int,
) -> pd.DataFrame:
    """
    Motsvarar TrustMeCore.breakoutContext i Pine.

    Pine:
        breakoutLevel = ta.highest(high, breakoutLookback)[1]
        breakdownLevel = ta.lowest(low, breakoutLookback)[1]
    """

    if breakout_lookback < 1:
        raise ValueError(
            "breakout_lookback måste vara minst 1."
        )

    breakout_level = (
        df["high"]
        .rolling(
            window=breakout_lookback,
            min_periods=breakout_lookback,
        )
        .max()
        .shift(1)
    )

    breakdown_level = (
        df["low"]
        .rolling(
            window=breakout_lookback,
            min_periods=breakout_lookback,
        )
        .min()
        .shift(1)
    )

    result = pd.DataFrame(index=df.index)

    result["breakout_level"] = breakout_level
    result["breakdown_level"] = breakdown_level

    return result