"""Daily availability and append-only input validation, separate from strategy."""
from __future__ import annotations

import tempfile
import json
from pathlib import Path
import pandas as pd
from pandas.testing import assert_frame_equal

from src.exit_research_runner import (
    validate_ohlcv, store_frame as legacy_store_frame, load_frame as legacy_load_frame, save_json,
)
from src.market_data import download_yahoo_data

OHLCV = ["open", "high", "low", "close", "volume"]
NY = "America/New_York"


def store_frame(path, frame):
    """Extend existing typed CSV sidecars to preserve empty/literal NA strings."""
    legacy_store_frame(path, frame)
    sidecar = Path(path).with_suffix(".schema.json")
    schema = json.loads(sidecar.read_text())
    schema["object_strings"] = {
        c: {str(i): v for i, v in enumerate(frame[c]) if isinstance(v, str)}
        for c in frame if frame[c].dtype == object}
    save_json(sidecar, schema)


def load_frame(path):
    frame = legacy_load_frame(path)
    schema = json.loads(Path(path).with_suffix(".schema.json").read_text())
    for column, values in schema.get("object_strings", {}).items():
        for offset, value in values.items():
            frame.iat[int(offset), frame.columns.get_loc(column)] = value
    return frame


def utc(value):
    stamp = pd.Timestamp(value)
    if stamp.tzinfo is None:
        raise ValueError("Observation clocks must be timezone-aware")
    return stamp.tz_convert("UTC")


def daily_clock(label, hour, minute=0):
    """Daily index is a session label; retain it, derive separate wall-clock fields."""
    stamp = pd.Timestamp(label)
    if stamp.tzinfo is not None:
        if str(stamp.tzinfo) != NY:
            raise ValueError("Daily timezone must be naive or America/New_York")
        stamp = stamp.tz_localize(None)
    return (stamp.normalize() + pd.Timedelta(hours=hour, minutes=minute)).tz_localize(NY).tz_convert("UTC")


def completed_daily(frame, observed_at):
    if not isinstance(frame.index, pd.DatetimeIndex):
        raise ValueError("Daily data requires DatetimeIndex")
    if not frame.index.is_unique or not frame.index.is_monotonic_increasing:
        raise ValueError("Duplicate or out-of-order daily bars")
    if not frame.index.equals(frame.index.normalize()) or frame.index.hasnans:
        raise ValueError("Only midnight-labelled Daily bars are supported")
    # Conservative normal close + 15 minutes, including early-close sessions.
    # No assumption about an observed intraday last bar or provider confirmation.
    keep = [daily_clock(t, 16, 15) <= utc(observed_at) for t in frame.index]
    result = frame.loc[keep, OHLCV].copy()
    if not result.empty:
        validate_ohlcv(result)
        if (result.index.dayofweek >= 5).any():
            raise ValueError("Weekend daily bar")
    return result


def append_daily(previous, incoming, cutoff):
    """Keep original indicator seed. Revised observed validation bars fail closed."""
    if previous.index.dtype != incoming.index.dtype:
        raise ValueError("Daily index timezone/dtype changed")
    new = incoming.loc[incoming.index >= pd.Timestamp(cutoff, tz=incoming.index.tz)]
    old = previous.loc[previous.index >= pd.Timestamp(cutoff, tz=previous.index.tz)]
    if not old.index.isin(new.index).all():
        raise ValueError("Provider omitted previously observed validation bars")
    common = old.index.intersection(new.index)
    try:
        seed_overlap = previous.index.intersection(incoming.index)
        assert_frame_equal(previous.loc[seed_overlap, OHLCV], incoming.loc[seed_overlap, OHLCV],
                           check_dtype=False, check_exact=True, check_freq=False)
        assert_frame_equal(previous.loc[common, OHLCV], new.loc[common, OHLCV],
                           check_dtype=False, check_exact=True, check_freq=False)
    except AssertionError as exc:
        raise ValueError("Previously observed OHLCV revised; new session/review required") from exc
    additions = new.loc[~new.index.isin(previous.index)]
    if len(additions) and additions.index.min() <= previous.index.max():
        raise ValueError("Late inserted historical bar would change indicator history")
    result = pd.concat([previous, additions]) if len(additions) else previous.copy()
    validate_ohlcv(result)
    return result


def evidence_class(label, frozen_at, observed_at, mode, latest):
    available = daily_clock(label, 16, 15)
    if available < utc(frozen_at):
        return "TEMPORAL_OOS_LATER_UNSEEN"
    # Conservative deadline: next CALENDAR day 09:30. Holidays/weekends may
    # reject a still-actionable signal, but cannot grant a retrospective fill.
    deadline = daily_clock(pd.Timestamp(label) + pd.Timedelta(days=1), 9, 30)
    after_freeze_day = pd.Timestamp(label).date() > utc(frozen_at).tz_convert(NY).date()
    if (mode == "scan" and after_freeze_day and label == latest
            and available <= utc(observed_at) < deadline):
        return "PROSPECTIVE_PAPER"
    return "POST_FREEZE_BACKFILL_NOT_PROSPECTIVE"


def yahoo_daily(symbol):
    """Caller must verify the persisted freeze before invoking this provider."""
    import yfinance as yf
    with tempfile.TemporaryDirectory(prefix="paper-yahoo-") as cache:
        yf.set_tz_cache_location(cache)
        return download_yahoo_data(symbol, period="5y", interval="1d")
