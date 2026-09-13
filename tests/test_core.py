import pandas as pd
import pandas as pd

from src.market_data import validate_ohlcv
from src.trust_me_core import (
    ema,
    trend_context,
    trend_regime_context,
    volatility_context,
    momentum_context,
    volume_context,
    breakout_context,
    squeeze_context,
    pullback_context,
    entry_modules_context,
    module_summary_context,
    entry_signal_context,
    session_entry_context,
)


def test_validate_ohlcv():
    index = pd.date_range(
        start="2026-08-20 09:30",
        periods=3,
        freq="45min",
    )

    data = pd.DataFrame(
        {
            "open": [100.0, 101.0, 102.0],
            "high": [102.0, 103.0, 104.0],
            "low": [99.0, 100.0, 101.0],
            "close": [101.0, 102.0, 103.0],
            "volume": [1000, 1200, 1100],
        },
        index=index,
    )

    result = validate_ohlcv(data)

    assert isinstance(result.index, pd.DatetimeIndex)
    assert len(result) == 3
    assert list(result.columns) == [
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]


def test_trend_context_ema():
    index = pd.date_range(
        start="2026-08-20 09:30",
        periods=5,
        freq="45min",
    )

    data = pd.DataFrame(
        {
            "open": [100, 101, 102, 103, 104],
            "high": [102, 103, 104, 105, 106],
            "low": [99, 100, 101, 102, 103],
            "close": [100, 102, 104, 106, 108],
            "volume": [1000, 1100, 1200, 1300, 1400],
        },
        index=index,
    )

    result = trend_context(
        data,
        ema_fast_length=2,
        ema_slow_length=3,
        adx_length=2,
    )

    assert "ema_fast" in result.columns
    assert "ema_slow" in result.columns
    assert "adx" in result.columns
    assert len(result) == len(data)
    assert result["ema_fast"].iloc[-1] > result["ema_slow"].iloc[-1]


def test_trend_regime_context():
    index = pd.date_range(
        start="2026-08-20 09:30",
        periods=4,
        freq="45min",
    )

    ema_fast = pd.Series(
        [100.0, 105.0, 95.0, 90.0],
        index=index,
    )

    ema_slow = pd.Series(
        [100.0, 100.0, 100.0, 100.0],
        index=index,
    )

    adx = pd.Series(
        [10.0, 20.0, 20.0, 12.0],
        index=index,
    )

    result = trend_regime_context(
        ema_fast=ema_fast,
        ema_slow=ema_slow,
        adx=adx,
        adx_min=18.0,
    )

    assert result["uptrend"].tolist() == [
        False,
        True,
        False,
        False,
    ]

    assert result["downtrend"].tolist() == [
        False,
        False,
        True,
        False,
    ]

def test_volatility_context():
    index = pd.date_range(
        start="2026-08-20 09:30",
        periods=6,
        freq="45min",
    )

    data = pd.DataFrame(
        {
            "open": [100, 101, 102, 103, 104, 105],
            "high": [102, 103, 104, 105, 106, 107],
            "low": [99, 100, 101, 102, 103, 104],
            "close": [101, 102, 103, 104, 105, 106],
            "volume": [1000, 1100, 1200, 1300, 1400, 1500],
        },
        index=index,
    )

    result = volatility_context(
        data,
        atr_length=3,
        min_atr_pct=1.0,
        use_candle_filter=True,
        max_candle_atr=2.0,
    )

    assert "atr" in result.columns
    assert "atr_pct" in result.columns
    assert "volatility_ok" in result.columns
    assert "candle_range" in result.columns
    assert "not_overextended" in result.columns

    assert len(result) == len(data)

    assert result["atr"].dropna().ge(0).all()
    assert result["candle_range"].eq(3).all()

def test_momentum_context():
    index = pd.date_range(
        start="2026-08-20 09:30",
        periods=12,
        freq="45min",
    )

    data = pd.DataFrame(
        {
            "open": [
                100, 101, 102, 103, 104, 105,
                104, 103, 102, 103, 104, 105,
            ],
            "high": [
                102, 103, 104, 105, 106, 107,
                106, 105, 104, 105, 106, 107,
            ],
            "low": [
                99, 100, 101, 102, 103, 104,
                103, 102, 101, 102, 103, 104,
            ],
            "close": [
                100, 102, 104, 106, 108, 110,
                106, 102, 98, 101, 105, 109,
            ],
            "volume": [
                1000, 1100, 1200, 1300, 1400, 1500,
                1400, 1300, 1200, 1300, 1400, 1500,
            ],
        },
        index=index,
    )

    result = momentum_context(
        data,
        rsi_length=3,
        rsi_smooth_len=2,
        confluence_window=3,
    )

    expected_columns = [
        "rsi",
        "rsi_avg",
        "rsi_cross_up",
        "rsi_cross_down",
        "bars_since_rsi_up",
        "bars_since_rsi_down",
        "rsi_up_recent",
        "rsi_down_recent",
        "bars_since_oversold",
        "bars_since_overbought",
        "was_oversold_recently",
        "was_overbought_recently",
    ]

    for column in expected_columns:
        assert column in result.columns

    assert len(result) == len(data)

    assert result["rsi"].dropna().between(
        0,
        100,
    ).all()

    assert result["rsi_cross_up"].dtype == bool
    assert result["rsi_cross_down"].dtype == bool

def test_volume_context():
    index = pd.date_range(
        start="2026-08-20 09:30",
        periods=6,
        freq="45min",
    )

    data = pd.DataFrame(
        {
            "open": [100, 101, 102, 103, 104, 105],
            "high": [102, 103, 104, 105, 106, 107],
            "low": [99, 100, 101, 102, 103, 104],
            "close": [101, 102, 103, 104, 105, 106],
            "volume": [1000, 1000, 1000, 2000, 500, 3000],
        },
        index=index,
    )

    result = volume_context(
        data,
        volume_length=3,
        use_volume_filter=True,
    )

    assert "average_volume" in result.columns
    assert "volume_strong" in result.columns

    assert len(result) == len(data)

    # Första två barerna saknar ännu ett komplett
    # 3-bars volymsnitt.
    assert pd.isna(result["average_volume"].iloc[0])
    assert pd.isna(result["average_volume"].iloc[1])

    # Bar 4:
    # SMA = (1000 + 1000 + 2000) / 3
    # 2000 > SMA -> volumeStrong = True
    assert bool(result["volume_strong"].iloc[3]) is True

    # Bar 5:
    # 500 ligger under sitt volymsnitt.
    assert bool(result["volume_strong"].iloc[4]) is False

def test_breakout_context():
    index = pd.date_range(
        start="2026-08-20 09:30",
        periods=6,
        freq="45min",
    )

    data = pd.DataFrame(
        {
            "open": [100, 101, 102, 103, 104, 105],
            "high": [101, 105, 103, 110, 106, 107],
            "low": [99, 98, 97, 96, 95, 94],
            "close": [100, 102, 101, 108, 105, 106],
            "volume": [1000, 1100, 1200, 1300, 1400, 1500],
        },
        index=index,
    )

    result = breakout_context(
        data,
        breakout_lookback=3,
    )

    assert "breakout_level" in result.columns
    assert "breakdown_level" in result.columns
    assert len(result) == len(data)

    # För bar index 3 används ENDAST bar 0, 1 och 2.
    #
    # High: 101, 105, 103 -> högsta = 105
    # Low:   99,  98,  97 -> lägsta = 97
    assert result["breakout_level"].iloc[3] == 105
    assert result["breakdown_level"].iloc[3] == 97

    # Viktigt:
    # Aktuell bars high = 110 får INTE påverka
    # breakout_level på samma bar.
    assert result["breakout_level"].iloc[3] != 110

def test_squeeze_context():
    index = pd.date_range(
        start="2026-08-20 09:30",
        periods=12,
        freq="45min",
    )

    data = pd.DataFrame(
        {
            "open": [
                100, 100, 100, 100, 100, 100,
                100, 100, 100, 100, 100, 100,
            ],
            "high": [
                101, 101, 101, 101, 101, 101,
                101, 101, 101, 101, 101, 101,
            ],
            "low": [
                99, 99, 99, 99, 99, 99,
                99, 99, 99, 99, 99, 99,
            ],
            "close": [
                100, 102, 98, 103, 97, 102,
                99.8, 100.1, 100.0, 100.2, 99.9, 100.0,
            ],
            "volume": [
                1000, 1000, 1000, 1000, 1000, 1000,
                1000, 1000, 1000, 1000, 1000, 1000,
            ],
        },
        index=index,
    )

    result = squeeze_context(
        data,
        bb_length=3,
        bb_mult=2.0,
        squeeze_window=2,
    )

    expected_columns = [
        "bb_basis",
        "bb_dev",
        "bb_upper",
        "bb_lower",
        "bb_width",
        "bb_width_avg",
        "in_squeeze",
        "bars_since_squeeze",
        "squeeze_recent",
    ]

    for column in expected_columns:
        assert column in result.columns

    assert len(result) == len(data)

    assert (
        result["bb_upper"].dropna()
        >= result["bb_lower"].dropna()
    ).all()

    assert result["bb_width"].dropna().ge(0).all()

    assert result["in_squeeze"].dtype == bool
    assert result["squeeze_recent"].dtype == bool

def test_pullback_context():
    index = pd.date_range(
        start="2026-08-20 09:30",
        periods=6,
        freq="45min",
    )

    data = pd.DataFrame(
        {
            "open": [99, 100, 101, 103, 102, 99],
            "high": [101, 102, 103, 105, 104, 101],
            "low": [98, 99, 100, 102, 100, 97],
            "close": [99, 100, 101, 104, 101, 98],
            "volume": [1000, 1100, 1200, 1300, 1400, 1500],
        },
        index=index,
    )

    htf_ema_fast = pd.Series(
        [100.0, 100.0, 100.0, 100.0, 100.0, 100.0],
        index=index,
    )

    result = pullback_context(
        data,
        htf_ema_fast=htf_ema_fast,
    )

    expected_columns = [
        "touched_ema_long",
        "reclaimed_long",
        "touched_ema_short",
        "reclaimed_short",
    ]

    for column in expected_columns:
        assert column in result.columns

    assert len(result) == len(data)

    # På bar 2:
    # lägsta low under bar 0-2 = 98
    # 98 <= 100 * 1.005 -> True
    assert bool(result["touched_ema_long"].iloc[2]) is True

    # På bar 3:
    # close går från 101 till 104.
    # Föregående close var redan över EMA,
    # så reclaim ska inte trigga.
    assert bool(result["reclaimed_long"].iloc[3]) is False

    assert result["touched_ema_long"].dtype == bool
    assert result["reclaimed_long"].dtype == bool
    assert result["touched_ema_short"].dtype == bool
    assert result["reclaimed_short"].dtype == bool

def test_entry_modules_context():
    index = pd.date_range(
        start="2026-08-20 09:30",
        periods=4,
        freq="45min",
    )

    data = pd.DataFrame(
        {
            "open": [100, 100, 100, 100],
            "high": [105, 105, 105, 105],
            "low": [95, 95, 95, 95],
            "close": [102, 110, 90, 98],
            "volume": [1000, 1000, 1000, 1000],
        },
        index=index,
    )

    uptrend = pd.Series(
        [True, True, False, False],
        index=index,
    )

    downtrend = pd.Series(
        [False, False, True, True],
        index=index,
    )

    htf_ema_slow = pd.Series(
        [100, 100, 100, 100],
        index=index,
    )

    rsi_up_recent = pd.Series(
        [True, True, False, False],
        index=index,
    )

    rsi_down_recent = pd.Series(
        [False, False, True, True],
        index=index,
    )

    touched_ema_long = pd.Series(
        [True, False, False, False],
        index=index,
    )

    reclaimed_long = pd.Series(
        [True, False, False, False],
        index=index,
    )

    touched_ema_short = pd.Series(
        [False, False, True, False],
        index=index,
    )

    reclaimed_short = pd.Series(
        [False, False, True, False],
        index=index,
    )

    breakout_level = pd.Series(
        [105, 105, 105, 105],
        index=index,
    )

    breakdown_level = pd.Series(
        [95, 95, 95, 95],
        index=index,
    )

    volume_strong = pd.Series(
        [True, True, True, True],
        index=index,
    )

    squeeze_recent = pd.Series(
        [False, False, False, False],
        index=index,
    )

    in_squeeze = pd.Series(
        [False, False, False, False],
        index=index,
    )

    bb_upper = pd.Series(
        [108, 108, 108, 108],
        index=index,
    )

    bb_lower = pd.Series(
        [92, 92, 92, 92],
        index=index,
    )

    was_oversold_recently = pd.Series(
        [False, False, False, False],
        index=index,
    )

    was_overbought_recently = pd.Series(
        [False, False, False, False],
        index=index,
    )

    rsi_cross_up = pd.Series(
        [False, False, False, False],
        index=index,
    )

    rsi_cross_down = pd.Series(
        [False, False, False, False],
        index=index,
    )

    result = entry_modules_context(
        data,
        uptrend=uptrend,
        downtrend=downtrend,
        htf_ema_slow=htf_ema_slow,
        rsi_up_recent=rsi_up_recent,
        rsi_down_recent=rsi_down_recent,
        touched_ema_long=touched_ema_long,
        reclaimed_long=reclaimed_long,
        touched_ema_short=touched_ema_short,
        reclaimed_short=reclaimed_short,
        breakout_level=breakout_level,
        breakdown_level=breakdown_level,
        volume_strong=volume_strong,
        squeeze_recent=squeeze_recent,
        in_squeeze=in_squeeze,
        bb_upper=bb_upper,
        bb_lower=bb_lower,
        was_oversold_recently=was_oversold_recently,
        was_overbought_recently=was_overbought_recently,
        rsi_cross_up=rsi_cross_up,
        rsi_cross_down=rsi_cross_down,
    )

    expected_columns = [
        "pullback_long",
        "breakout_long",
        "squeeze_long",
        "mean_rev_long",
        "pullback_short",
        "breakout_short",
        "squeeze_short",
        "mean_rev_short",
    ]

    for column in expected_columns:
        assert column in result.columns

    assert bool(result["pullback_long"].iloc[0]) is True
    assert bool(result["breakout_long"].iloc[1]) is True
    assert bool(result["pullback_short"].iloc[2]) is True

    assert result.dtypes.eq(bool).all()

def test_module_summary_context():
    index = pd.date_range(
        start="2026-08-20 09:30",
        periods=4,
        freq="45min",
    )

    pullback_long = pd.Series(
        [True, False, True, False],
        index=index,
    )

    breakout_long = pd.Series(
        [False, True, True, False],
        index=index,
    )

    squeeze_long = pd.Series(
        [False, False, True, False],
        index=index,
    )

    mean_rev_long = pd.Series(
        [False, False, False, True],
        index=index,
    )

    pullback_short = pd.Series(
        [False, True, False, False],
        index=index,
    )

    breakout_short = pd.Series(
        [False, False, True, False],
        index=index,
    )

    squeeze_short = pd.Series(
        [False, False, False, True],
        index=index,
    )

    mean_rev_short = pd.Series(
        [False, False, False, True],
        index=index,
    )

    result = module_summary_context(
        pullback_long=pullback_long,
        breakout_long=breakout_long,
        squeeze_long=squeeze_long,
        mean_rev_long=mean_rev_long,
        pullback_short=pullback_short,
        breakout_short=breakout_short,
        squeeze_short=squeeze_short,
        mean_rev_short=mean_rev_short,
    )

    assert result["long_score"].tolist() == [
        1,
        1,
        3,
        1,
    ]

    assert result["short_score"].tolist() == [
        0,
        1,
        1,
        2,
    ]

    assert result["long_module_text"].tolist() == [
        "Pullback ",
        "Breakout ",
        "Pullback Breakout Squeeze ",
        "MeanRev ",
    ]

    assert result["short_module_text"].tolist() == [
        "",
        "Pullback ",
        "Breakout ",
        "Squeeze MeanRev ",
    ]

def test_entry_signal_context():
    index = pd.date_range(
        start="2026-08-20 09:30",
        periods=4,
        freq="45min",
    )

    long_score = pd.Series(
        [1, 0, 2, 1],
        index=index,
    )

    short_score = pd.Series(
        [0, 1, 1, 2],
        index=index,
    )

    volatility_ok = pd.Series(
        [True, True, False, True],
        index=index,
    )

    not_overextended = pd.Series(
        [True, True, True, False],
        index=index,
    )

    session_ok = pd.Series(
        [True, True, True, True],
        index=index,
    )

    is_confirmed = pd.Series(
        [True, True, True, True],
        index=index,
    )

    result = entry_signal_context(
        allow_long=True,
        allow_short=True,
        long_score=long_score,
        short_score=short_score,
        min_confluence=1,
        volatility_ok=volatility_ok,
        not_overextended=not_overextended,
        session_ok=session_ok,
        is_confirmed=is_confirmed,
    )

    assert result["long_signal"].tolist() == [
        True,
        False,
        False,
        False,
    ]

    assert result["short_signal"].tolist() == [
        False,
        True,
        False,
        False,
    ]

def test_session_entry_context():
    index = pd.date_range(
        start="2026-08-20 09:30",
        periods=4,
        freq="45min",
    )

    in_entry_session = pd.Series(
        [True, True, False, False],
        index=index,
    )

    # Swing ska alltid tillåta entry ur sessionsperspektiv.
    swing_result = session_entry_context(
        is_swing=True,
        in_entry_session=in_entry_session,
    )

    assert swing_result.tolist() == [
        True,
        True,
        True,
        True,
    ]

    # Intraday ska följa entry-sessionen.
    intraday_result = session_entry_context(
        is_swing=False,
        in_entry_session=in_entry_session,
    )

    assert intraday_result.tolist() == [
        True,
        True,
        False,
        False,
    ]