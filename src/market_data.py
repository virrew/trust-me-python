from __future__ import annotations

import pandas as pd
import yfinance as yf

REQUIRED_OHLCV_COLUMNS = {
    "open",
    "high",
    "low",
    "close",
    "volume",
}


def validate_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validerar att en DataFrame innehåller den OHLCV-data
    som Trust Me behöver.

    Förväntar sig:
    - DatetimeIndex
    - open
    - high
    - low
    - close
    - volume
    """

    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError("OHLCV-data måste använda DatetimeIndex.")

    missing_columns = REQUIRED_OHLCV_COLUMNS - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"OHLCV-data saknar kolumner: {sorted(missing_columns)}"
        )

    df = df.sort_index().copy()

    return df

def download_yahoo_data(
    ticker: str,
    period: str = "5d",
    interval: str = "15m",
) -> pd.DataFrame:
    """
    Hämtar OHLCV-data från Yahoo Finance via yfinance.

    Datan normaliseras till Trust Me-format:
    - open
    - high
    - low
    - close
    - volume
    """

    df = yf.download(
        ticker,
        period=period,
        interval=interval,
        auto_adjust=False,
        prepost=False,
        progress=False,
    )

    if df.empty:
        raise ValueError(
            f"Ingen data hämtades för {ticker}."
        )

    # yfinance kan returnera MultiIndex-kolumner.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.rename(
        columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
    )

    df = df[
        [
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]
    ]

    return validate_ohlcv(df)

def resample_regular_session(
    df: pd.DataFrame,
    timeframe_minutes: int = 45,
) -> pd.DataFrame:
    """
    Bygger egna intraday-candles från mindre bars.

    Session:
        09:30 - 16:00 America/New_York

    Exempel för 45 minuter:
        09:30
        10:15
        11:00
        11:45
        12:30
        13:15
        14:00
        14:45
        15:30

    Sista 45m-baren blir partiell eftersom börsen
    stänger 16:00.
    """

    if timeframe_minutes < 1:
        raise ValueError(
            "timeframe_minutes måste vara minst 1."
        )

    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError(
            "Datan måste använda DatetimeIndex."
        )

    if df.index.tz is None:
        raise ValueError(
            "Intraday-datan måste ha timezone."
        )

    data = df.copy()

    # All sessionslogik görs i New York-tid.
    data.index = data.index.tz_convert(
        "America/New_York"
    )

    # Behåll endast ordinarie USA-session.
    session_minutes = (
        data.index.hour * 60
        + data.index.minute
    )

    market_open = 9 * 60 + 30
    market_close = 16 * 60

    in_session = (
        (session_minutes >= market_open)
        & (session_minutes < market_close)
    )

    data = data.loc[in_session].copy()

    minutes_since_open = (
        data.index.hour * 60
        + data.index.minute
        - market_open
    )

    data["_session_date"] = data.index.date

    data["_bucket"] = (
        minutes_since_open
        // timeframe_minutes
    )

    grouped = data.groupby(
        ["_session_date", "_bucket"],
        sort=True,
    )

    result = grouped.agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
    )

    # Använd första underliggande barens timestamp
    # som timestamp för den nya candlen.
    timestamps = grouped.apply(
        lambda group: group.index[0],
        include_groups=False,
    )

    result.index = pd.DatetimeIndex(
        timestamps,
        name="Datetime",
    )

    return validate_ohlcv(result)

def map_daily_context_to_intraday(
    intraday_df: pd.DataFrame,
    daily_context: pd.DataFrame,
) -> pd.DataFrame:
    """
    Mappar Daily-context till intraday-bars på ett sätt som
    efterliknar Pine:

        request.security(
            syminfo.tickerid,
            "D",
            ...,
            lookahead=barmerge.lookahead_off
        )

    För historiska intraday-bars:
    - tidigare bars under dagen använder föregående bekräftade Daily-värde
    - dagens sista intraday-bar får dagens Daily-värde
    """

    if intraday_df.index.tz is None:
        raise ValueError(
            "Intraday-datan måste ha timezone."
        )

    intraday = intraday_df.copy()

    intraday.index = intraday.index.tz_convert(
        "America/New_York"
    )

    daily = daily_context.copy()

    # Daily-data kan vara timezone-naive.
    daily_dates = pd.Index(
        pd.to_datetime(daily.index).date
    )

    daily.index = daily_dates

    result = pd.DataFrame(
        index=intraday.index,
        columns=daily.columns,
        dtype=float,
    )

    # Senast bekräftade Daily-rad från föregående dag.
    previous_daily = daily.shift(1)

    for session_date, group in intraday.groupby(
        intraday.index.date
    ):
        if session_date not in daily.index:
            continue

        # Alla intraday-bars utom dagens sista
        # använder föregående Daily-context.
        previous_values = previous_daily.loc[session_date]

        if previous_values.notna().any():
            result.loc[group.index, :] = previous_values.to_numpy()

        # Sista intraday-baren stänger samtidigt med Daily-baren.
        # Där blir dagens Daily-context historiskt tillgängligt.
        last_bar = group.index[-1]

        result.loc[last_bar, :] = (
            daily.loc[session_date].to_numpy()
        )

    return result