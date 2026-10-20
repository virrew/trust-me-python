"""Offline V2 equivalence, evidence integrity and recovery; no market downloads."""
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from src import live_scanner as v1
from src import live_scanner_v2 as v2
from src.prospective_validation_storage import pack, unpack, TABLES
from test_live_scanner import synthetic, seed, force_signal


@pytest.fixture
def parent(tmp_path):
    # Fresh test-only identity: archived production protocols must stay frozen
    # when source code changes. No source checks or stored hashes are bypassed.
    base = tmp_path/"PARENT-TEST"
    v1.freeze(base, symbols=["AAPL", "MSFT"])
    return base


@pytest.fixture
def session(tmp_path, parent):
    base = tmp_path/"PV-V2-TEST"
    v2.freeze(base, parent=parent, symbols=["AAPL"], clock=lambda: "2026-10-01T12:00:00Z")
    return v2.PaperScannerV2(base)


def run(s, data, clock="2026-10-05T21:00:00Z", mode="scan"):
    return s.run(mode, lambda _: data, lambda: clock)


def normalized(frame, sort):
    return frame.sort_values(sort).reset_index(drop=True)


def test_freeze_exact_parent_science_and_distinct_protocol(session, parent):
    parent = v1.read_json(parent/"freeze/validation_plan.json")
    for name in ("diagnostics_config", "baseline_execution", "module_reference_policies",
                 "candidate_sha256", "shadow_candidates", "cost_assumptions", "metrics",
                 "old_cutoff_exclusive", "data_contract", "population_contract"):
        assert session.plan[name] == parent[name]
    assert session.plan["version"] == 2
    assert session.identity != session.plan["parent_plan_sha256"]
    assert v1.digest(session.base/"freeze/candidates.json") == parent["candidate_sha256"]
    assert set(session.plan["table_schemas"]) == set(TABLES)
    assert not session.runs()


def test_freeze_gate_and_parent_drift(tmp_path):
    with pytest.raises(FileNotFoundError):
        v2.PaperScannerV2(tmp_path)
    parent = tmp_path/"PARENT"
    shutil.copytree(v2.PARENT/"freeze", parent/"freeze")
    (parent/"freeze/candidates.json").write_text("{}")
    with pytest.raises(ValueError, match="Corrupt"):
        v2.freeze(tmp_path/"CHILD", parent=parent)


def test_parent_source_drift_still_blocks_freeze(tmp_path, parent, monkeypatch):
    sources = v1.source_identity()
    sources["src/market_data.py"] = "changed-provider-source"
    monkeypatch.setattr(v1, "source_identity", lambda: sources)
    with pytest.raises(ValueError, match="V1 scientific implementation changed"):
        v2.freeze(tmp_path/"CHILD", parent=parent)
    assert not (tmp_path/"CHILD"/"freeze").exists()


def test_empty_seed_no_evidence_and_stable_schemas(session):
    result = run(session, seed(session), "2026-10-01T13:00Z", "catch-up")
    assert result["status"] == "AWAITING_VALIDATION_DATA"
    assert result["completed_runs"] == 0
    for name in TABLES:
        frame = session.history(name)
        assert frame.empty and len(frame.columns) > 0
    metrics = v1.load_frame(session.base/"reports/latest/evaluation.csv")
    assert len(metrics) == 60 and metrics.gross_trade_count.eq(0).all()
    assert len(list((session.base/"state").glob("*"))) == 5


def test_v1_v2_full_offline_equivalence_across_prefixes(session, tmp_path, monkeypatch):
    # The same frozen scientific inputs and controlled observation clock.
    legacy = tmp_path/"V1-CONTROL"
    shutil.copytree(session.base/"freeze", legacy/"freeze")
    reference = v1.PaperScanner(legacy)
    force_signal(monkeypatch)
    forced = v1.signal_diagnostics

    def all_arms(data, **kwargs):
        d = forced(data, **kwargs)
        active = d.index >= pd.Timestamp("2026-09-22")
        masks = np.zeros(len(d), dtype=int)
        masks[active] = np.resize([1, 2, 4, 8, 0], int(active.sum()))
        for col, bit in [("pullback_long", 1), ("breakout_long", 2),
                         ("squeeze_long", 4), ("mean_rev_long", 8)]:
            d[col] = masks == bit
        relaxed = active & (masks == 0)
        d["long_active_module_mask"] = masks
        d["long_score"] = (masks != 0).astype(int)
        d["long_signal"] = masks != 0
        d["long_fail_score"] = masks == 0
        d["bo_long_fail_trend"] = ~(d.breakout_long | relaxed)
        d["bo_long_fail_price"] = relaxed
        return d

    monkeypatch.setattr(v1, "signal_diagnostics", all_arms)
    for date, end in [("2026-10-05", "2026-10-05"), ("2026-10-06", "2026-10-06")]:
        data = synthetic(session, end)
        if end == "2026-10-06":
            data.loc["2026-10-06", ["open", "high", "low", "close"]] = [100, 101, 90, 95]
        clock = date+"T21:00:00Z"
        expected_report = reference.run("scan", lambda _: data, lambda: clock)
        actual_report = run(session, data, clock)
        assert actual_report["baseline_counts"] == expected_report["baseline_counts"]
        folder = reference.runs()[-1]/"AAPL"
        d = session.history("decisions").drop(columns="symbol")
        assert_frame_equal(d, v1.load_frame(folder/"observations.csv"), check_freq=False)
        current = session.current_trades(session.runs())
        assert set(current.arm) == set(session.arms)  # every reference/shadow has actual fills
        all_states, all_trace, all_signals = [], [], []
        for arm in session.arms:
            t = v1.load_frame(folder/arm/"trades.csv")
            # V1 infers float for this empty mapped string column; V2 fixes
            # its storage dtype without changing a value or signal.
            t["research_signal_source"] = t.research_signal_source.astype(object)
            actual = current.loc[current.arm.eq(arm)]
            # Publication clocks of already-closed records are intentionally immutable.
            cols = [c for c in t if c != "as_of_observed_at"]
            assert_frame_equal(normalized(actual[cols], ["signal_time"]),
                               normalized(t[cols], ["signal_time"]), check_freq=False)
            states = v1.load_frame(folder/arm/"states.csv")
            states["trade_key"] = session.plan["session_id"]+"|"+states.trade_key
            all_states.append(states)
            trace = v1.load_frame(folder/arm/"stop_path.csv")
            all_trace.append(trace)
            all_signals.extend(v1.load_frame(p/"AAPL"/arm/"new_signals.csv")
                               for p in reference.runs())
        states = pd.concat(all_states, ignore_index=True)
        actual = session.history("lifecycle_states")
        cols = [c for c in states if c != "as_of_observed_at"]
        assert_frame_equal(normalized(actual[cols], ["arm", "bar_time", "trade_id"]),
                           normalized(states[cols], ["arm", "bar_time", "trade_id"]), check_freq=False)
        trace = pd.concat(all_trace, ignore_index=True)
        events = session.history("trade_events")
        actual = events.loc[events.event_type.eq("EXECUTION_BAR"), trace.columns].copy()
        for c, dtype in trace.dtypes.items():
            actual[c] = actual[c].astype(dtype)
        assert_frame_equal(normalized(actual, ["arm", "bar_time", "trade_id"]),
                           normalized(trace, ["arm", "bar_time", "trade_id"]), check_freq=False)
        signals = pd.concat(all_signals, ignore_index=True)
        signals["signal_key"] = session.plan["session_id"]+"|"+signals.signal_key
        actual = session.history("signals")
        assert_frame_equal(normalized(actual, ["arm", "signal_time"]),
                           normalized(signals[list(actual)], ["arm", "signal_time"]), check_freq=False)
        for name in ("evaluation", "distributions"):
            actual = v1.load_frame(session.base/"reports/latest"/f"{name}.csv")
            expected = v1.load_frame(reference.runs()[-1]/f"{name}.csv")
            assert_frame_equal(actual, expected)
    assert (session.history("trade_events").event_type == "EXIT_FILLED").any()
    assert session.history("signals").research_signal_source.eq("EXPERIMENTAL_SOLE_PRICE_BLOCKER").any()


def test_same_day_idempotency_and_only_new_prices(session, monkeypatch):
    force_signal(monkeypatch)
    data = synthetic(session)
    first = run(session, data)
    hashes = {p: v1.digest(p) for p in (session.base/"events").rglob("*") if p.is_file()}
    second = run(session, data, "2026-10-05T22:00Z")
    assert first["baseline_counts"] == second["baseline_counts"]
    assert len(session.runs()) == 1
    assert all(v1.digest(p) == h for p, h in hashes.items())
    folder = session.runs()[0]
    assert len(list(folder.iterdir())) == 8
    assert not any(p.is_dir() for p in folder.iterdir())
    assert len(session.history("bars")) == len(data.loc["2026-09-22":])
    run(session, synthetic(session, "2026-10-06"), "2026-10-06T21:00Z")
    assert len(v2.read_table(session.runs()[-1], "bars")) == 1
    for name in TABLES:
        assert not session.history(name).duplicated(session.plan["storage"]["keys"][name]).any()


def test_entry_events_never_contain_future_closure_and_state_has_no_labels(session, monkeypatch):
    force_signal(monkeypatch)
    data = synthetic(session)
    data.loc["2026-10-05", ["open", "high", "low", "close"]] = [100, 101, 90, 95]
    run(session, data)
    events = session.history("trade_events")
    entry = events.loc[events.event_type.eq("ENTRY_FILLED")]
    assert len(entry) and entry[["exit_time", "exit_price", "return_pct", "closed"]].isna().all().all()
    assert entry.event_available_at_utc.str.contains("13:30:00").all()
    states = session.history("lifecycle_states")
    assert not any(c.startswith(("future_", "final_", "exit_")) for c in states)
    assert not states.bar_time.eq(pd.Timestamp("2026-10-05")).any()


@pytest.mark.parametrize("kind", ["duplicate", "revised", "missing"])
def test_invalid_input_cannot_publish(session, kind):
    data = synthetic(session)
    run(session, data)
    if kind == "duplicate":
        data = pd.concat([data, data.tail(1)])
    elif kind == "revised":
        data.loc["2026-09-22", "close"] += .01
    else:
        data = data.drop(pd.Timestamp("2026-09-22"))
    with pytest.raises(ValueError):
        run(session, data)
    assert len(session.runs()) == 1
    assert session.report()["incomplete_run"]


@pytest.mark.parametrize("field", ["cost_assumptions", "symbols", "shadow_candidates",
                                   "diagnostics_config", "sources"])
def test_in_memory_identity_drift_prevents_loader(session, field):
    session.plan[field] = {}
    with pytest.raises(ValueError, match="configuration"):
        run(session, None)


@pytest.mark.parametrize("file", ["candidates.json", "universe.json", "validation_plan.json"])
def test_frozen_artifact_drift_prevents_loader(session, file):
    (session.base/"freeze"/file).write_text("{}")
    called = []
    with pytest.raises(ValueError):
        session.run("scan", lambda s: called.append(s))
    assert not called


def test_source_identity_drift(session, monkeypatch):
    monkeypatch.setattr(v1, "source_identity", lambda: {})
    with pytest.raises(ValueError, match="Source/runtime"):
        session.run("scan", lambda _: pytest.fail("Loader must not run"))


def test_corrupt_events_fail_closed_before_fetch(session):
    run(session, synthetic(session))
    (session.runs()[0]/"bars.csv").write_text("corrupt")
    with pytest.raises(ValueError, match="Corrupt"):
        session.run("scan", lambda _: pytest.fail("Loader must not run"))


def test_removed_tail_detected_by_publication_receipt(session):
    run(session, synthetic(session))
    shutil.move(str(session.runs()[0]), str(session.base/"removed"))
    with pytest.raises(ValueError, match="removed"):
        session.report()


def test_partial_universe_resume_keeps_completed_clocks(tmp_path, parent):
    base = tmp_path/"MULTI"
    v2.freeze(base, parent=parent, symbols=["AAPL", "MSFT"], clock=lambda: "2026-10-01T12:00Z")
    scanner = v2.PaperScannerV2(base)
    data = synthetic(scanner)

    def first(symbol):
        if symbol == "MSFT":
            raise RuntimeError("interruption during computation")
        return data

    with pytest.raises(RuntimeError):
        scanner.run("scan", first, lambda: "2026-10-05T21:00Z")
    assert not scanner.runs()
    pending = v2.checkpoint_read(base/".checkpoint.json")
    assert list(pending["completed"]) == ["AAPL"]
    assert len(list(base.glob(".checkpoint*"))) == 1

    def resume(symbol):
        assert symbol == "MSFT"
        return v1.load_frame(base/"freeze/seed/MSFT.csv").set_index("timestamp")

    result = scanner.run("resume", resume, lambda: "2026-10-06T21:00Z")
    assert result["completed_runs"] == 1
    assert len(result["coverage"]) == 2
    assert scanner.history("decisions").observed_at.eq("2026-10-05T21:00:00+00:00").all()
    assert len(list(scanner.runs()[0].iterdir())) == 8


@pytest.mark.parametrize("after_rename", [False, True])
def test_interruption_around_publication(session, monkeypatch, after_rename):
    original = session._publish

    def interrupt(*args):
        if after_rename:
            original(*args)
        raise RuntimeError("interrupted publication")

    monkeypatch.setattr(session, "_publish", interrupt)
    with pytest.raises(RuntimeError):
        run(session, synthetic(session))
    monkeypatch.setattr(session, "_publish", original)
    result = session.run("resume", lambda _: pytest.fail("Checkpointed symbol refetched"),
                         lambda: "2026-10-06T21:00Z")
    assert result["completed_runs"] == 1 and not result["incomplete_run"]
    assert not (session.base/".checkpoint.json").exists()


def test_pending_corruption_fails_closed(session, monkeypatch):
    monkeypatch.setattr(session, "_publish", lambda *a: (_ for _ in ()).throw(RuntimeError()))
    with pytest.raises(RuntimeError):
        run(session, synthetic(session))
    path = session.base/".checkpoint.json"
    envelope = v1.read_json(path)
    envelope["payload"]["request"]["mode"] = "update"
    v1.save_json(path, envelope)
    with pytest.raises(ValueError, match="checksum"):
        session.run("resume", lambda _: pytest.fail("No fetch"))


def test_partial_symbol_computation_has_no_checkpoint_or_publication(session, monkeypatch):
    original = session._compute

    def interrupt(*args):
        original(*args)
        raise RuntimeError("before symbol checkpoint")

    monkeypatch.setattr(session, "_compute", interrupt)
    with pytest.raises(RuntimeError, match="checkpoint"):
        run(session, synthetic(session))
    assert not session.runs()
    assert not v2.checkpoint_read(session.base/".checkpoint.json")["completed"]
    monkeypatch.setattr(session, "_compute", original)
    result = run(session, synthetic(session), mode="resume")
    assert result["completed_runs"] == 1


def test_incomplete_future_bar_is_not_persisted(session):
    data = synthetic(session)
    run(session, data)
    before = session.history("decisions")
    future = synthetic(session, "2026-10-06")
    future.loc["2026-10-06", ["open", "high", "low", "close"]] = [1, 9000, -1, np.nan]
    run(session, future, "2026-10-06T15:00Z")
    assert len(session.runs()) == 1
    assert_frame_equal(before, session.history("decisions"))


@pytest.mark.parametrize("damage", ["corrupt", "remove"])
def test_state_reconstruction_exact_and_no_primary_changes(session, monkeypatch, damage):
    force_signal(monkeypatch)
    run(session, synthetic(session))
    before = session.current_trades(session.runs())
    hashes = {p: v1.digest(p) for p in (session.base/"events").rglob("*") if p.is_file()}
    if damage == "corrupt":
        (session.base/"state/open_trades.csv").write_text("corrupt")
        (session.base/"state/latest_run.json").write_text("{}")
    else:
        shutil.rmtree(session.base/"state")
    monkeypatch.setattr(v1, "yahoo_daily", lambda _: pytest.fail("Recovery must be offline"))
    session.report()
    after = session.current_trades(session.runs())
    assert_frame_equal(normalized(before, ["arm", "signal_time"]),
                       normalized(after, ["arm", "signal_time"]))
    assert all(v1.digest(p) == h for p, h in hashes.items())


def test_consolidated_codec_retains_strings_nullable_timezone_and_empty():
    frame = pd.DataFrame(dict(
        text=["", "NA", "nan", None], value=[np.nan, 1., 2., 3.],
        flag=pd.array([True, False, None, True], dtype="boolean"),
        count=pd.array([1, None, 3, 4], dtype="Int64"),
        time=pd.date_range("2026-10-01", periods=4, tz="America/New_York")))
    assert_frame_equal(unpack(pack(frame)), frame)
    assert_frame_equal(unpack(pack(frame.iloc[:0])), frame.iloc[:0])
