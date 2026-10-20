"""V2 storage projections of V1 outputs; no strategy or execution decisions."""
from __future__ import annotations

import io
import json

import pandas as pd

from src.live_scanner import META_COLUMNS
from src.prospective_validation_data import OHLCV, daily_clock

TABLES = ("bars", "decisions", "signals", "trade_events", "lifecycle_states")
SIGNAL_COLUMNS = [
    "signal_time", "signal_key", "direction", "symbol", "arm", *META_COLUMNS,
    "long_signal", "short_signal", "long_active_module_mask", "long_score",
    "research_signal_source",
]
ENTRY_COLUMNS = [
    "trade_id", "trade_key", "symbol", "arm", "direction", "signal_time",
    "signal_available_at", "entry_time", "entry_price", "atr_at_entry",
    "initial_stop", "active_module_mask", "module_score", *META_COLUMNS,
    "entry_available_at_utc", "research_signal_source",
]
EVENT_META = {
    "event_key": "object", "event_type": "object", "event_time": "datetime64[ns]",
    "event_available_at_utc": "object", "event_observed_at": "object",
}


def pack(frame):
    """Same CSV/dtype/string contract as V1, consolidated into one schema map."""
    return dict(csv=frame.to_csv(index=False), schema=dict(
        columns=list(frame),
        dtypes={c: str(t) for c, t in frame.dtypes.items()},
        object_none={c: [i for i, v in enumerate(frame[c]) if v is None]
                     for c in frame if frame[c].dtype == object},
        object_strings={c: {str(i): v for i, v in enumerate(frame[c]) if isinstance(v, str)}
                        for c in frame if frame[c].dtype == object}))


def unpack(payload):
    schema = payload["schema"]
    frame = pd.read_csv(io.StringIO(payload["csv"]), float_precision="round_trip")
    if list(frame) != schema["columns"]:
        raise ValueError("CSV/schema column mismatch")
    for c, dtype in schema["dtypes"].items():
        if dtype.startswith("datetime64"):
            frame[c] = pd.to_datetime(frame[c], utc="," in dtype)
        frame[c] = frame[c].astype(dtype)
    for c, offsets in schema["object_none"].items():
        for offset in offsets:
            frame.iat[offset, frame.columns.get_loc(c)] = None
    for c, values in schema["object_strings"].items():
        for offset, value in values.items():
            frame.iat[int(offset), frame.columns.get_loc(c)] = value
    return frame


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def combine(frames):
    """Preserve empty schemas and avoid dtype inference from all-missing rows."""
    frames = list(frames)
    nonempty = [f for f in frames if len(f)]
    return pd.concat(nonempty, ignore_index=True) if nonempty else frames[0].iloc[:0].copy()


def event_schema(trades, trace):
    # Sparse union: missing entry/exit/trace fields must remain missing, not False/0.
    schema = {}
    for table in (trades, trace):
        for c, dtype in table.dtypes.items():
            dtype = str(dtype)
            schema[c] = {"int64": "Int64", "bool": "boolean"}.get(dtype, dtype)
    schema.update(EVENT_META)
    schema["event_time"] = str(trades.signal_time.dtype)
    return schema


def typed(rows, schema):
    frame = pd.DataFrame(rows)
    return pd.DataFrame({c: pd.Series(pd.array(
        frame[c] if c in frame else [None]*len(frame), dtype=dtype))
        for c, dtype in schema.items()})


def project(symbol, decisions, arms, namespace):
    """Project existing engine artifacts, filtering solely by new observed bars.

    ENTRY_FILLED contains only entry-known fields, never the later closed record.
    EXIT_FILLED is explicitly retrospective. EXECUTION_BAR copies the original
    engine trace (including stop and trend decision); it is not a second engine.
    """
    fresh = pd.Index(decisions.timestamp)
    meta = decisions.set_index("timestamp")
    tables = {
        "bars": decisions[["timestamp", *OHLCV, *META_COLUMNS]].assign(symbol=symbol),
        "decisions": decisions.assign(symbol=symbol),
    }
    signals, states, events, trades = [], [], [], []
    schema = None
    for arm, outputs in arms.items():
        life = outputs["trades"].astype({"research_signal_source": "object"})
        trace = outputs["stop_path"]
        trades.append(life)
        schema = event_schema(life, trace) if schema is None else schema
        sig = outputs["new_signals"][SIGNAL_COLUMNS].copy()
        sig["signal_key"] = namespace + "|" + sig.signal_key
        signals.append(sig)
        state = outputs["states"]
        state = state.loc[state.bar_time.isin(fresh)].copy()
        state["trade_key"] = namespace + "|" + state.trade_key
        states.append(state)
        by_id = life.set_index("trade_id")

        def emit(row, kind, time, trade):
            key = namespace + "|" + trade["trade_key"]
            row.update(trade_key=key, symbol=symbol, arm=arm,
                       signal_time=trade["signal_time"], direction=trade["direction"],
                       evidence_class=trade["evidence_class"],
                       event_key=f"{key}|{kind}|{time.isoformat()}",
                       event_type=kind, event_time=time,
                       event_observed_at=meta.loc[time, "observed_at"])
            at_open = kind == "ENTRY_FILLED" or (
                kind == "EXIT_FILLED" and trade["exit_timing"] == "OPEN")
            row["event_available_at_utc"] = daily_clock(
                time, 9 if at_open else 16, 30 if at_open else 15).isoformat()
            events.append(row)

        for _, trade in life.iterrows():
            if trade.entry_time in fresh:
                emit(trade[ENTRY_COLUMNS].to_dict(), "ENTRY_FILLED", trade.entry_time, trade)
            if trade.closed and trade.exit_time in fresh:
                emit(trade.to_dict(), "EXIT_FILLED", trade.exit_time, trade)
        for row in trace.loc[trace.bar_time.isin(fresh)].to_dict("records"):
            emit(row, "EXECUTION_BAR", row["bar_time"], by_id.loc[row["trade_id"]])
    tables["signals"] = combine(signals)
    tables["lifecycle_states"] = combine(states)
    tables["trade_events"] = typed(events, schema)
    return tables, combine(trades)
