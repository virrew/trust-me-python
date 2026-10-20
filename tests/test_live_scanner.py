"""Synthetic post-cutoff bars only: tests never retrieve unseen market outcomes."""
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

import src.live_scanner as scanner
from src.backtest import run_swing_backtest_with_reconciliation
from src.prospective_validation_analysis import account, return_metrics
from src.prospective_validation_data import (
    completed_daily, evidence_class, append_daily, daily_clock, load_frame, store_frame,
)
from src.strategy_improvement_execution import replay, research_stream


@pytest.fixture
def session(tmp_path, monkeypatch):
    monkeypatch.setattr(scanner, "now", lambda: "2026-10-01T12:00:00+00:00")
    base = tmp_path/"PV-TEST"
    base.mkdir()
    scanner.freeze(base, symbols=("AAPL",))
    return scanner.PaperScanner(base)


def seed(s):
    return load_frame(s.base/"freeze/seed/AAPL.csv").set_index("timestamp")


def synthetic(s, end="2026-10-05"):
    old = seed(s)
    index = pd.bdate_range("2026-09-22", end)
    # Artificial prices, not post-cutoff downloaded observations.
    close = old.close.iloc[-1] * (1 + np.arange(len(index))*.002)
    extra = pd.DataFrame(dict(open=close, high=close*1.006, low=close*.994,
                              close=close, volume=100000000), index=index)
    return pd.concat([old, extra])


def force_signal(monkeypatch):
    original = scanner.signal_diagnostics

    def diagnostics(data, **kwargs):
        d = original(data, **kwargs)
        # Deliberately synthetic, consistent production-shaped test signals.
        active = d.index >= pd.Timestamp("2026-09-22")
        d["long_signal"] = active
        d["short_signal"] = False
        for col in ("pullback_long", "squeeze_long", "mean_rev_long"):
            d[col] = False
        d["breakout_long"] = active
        d["long_active_module_mask"] = active.astype(int)*2
        d["long_score"] = active.astype(int)
        for col in d:
            if col.startswith(("bo_long_fail_", "long_fail_")) and not col.endswith("mask"):
                d[col] = False
        d["bo_long_fail_trend"] = ~active
        d["long_fail_score"] = ~active
        return d
    monkeypatch.setattr(scanner, "signal_diagnostics", diagnostics)


def run(s, data, clock="2026-10-05T21:00:00+00:00", mode="scan"):
    return s.run(mode, loader=lambda _: data, clock=lambda: clock)


def latest(s, name, arm=None):
    folder = s.runs()[-1]/"AAPL"
    return load_frame((folder/arm if arm else folder)/f"{name}.csv")


def test_freeze_is_gate_before_any_provider_access(tmp_path):
    called = []
    with pytest.raises(FileNotFoundError):
        scanner.PaperScanner(tmp_path).run("scan", loader=lambda s: called.append(s))
    assert called == []


def test_freeze_records_sources_universe_candidates_and_costs(session):
    p = session.plan
    assert p["baseline_commit"] and p["working_tree_diff_sha256"]
    assert p["symbols"] == ["AAPL"] and len(p["shadow_candidates"]) == 10
    assert p["candidate_sha256"] == "7992a5bb7537c1cb0dc4a4976af104d9b391a2236b8413258d8c9385acfc9b21"
    assert p["diagnostics_config"]["allow_short"] is False
    assert p["baseline_execution"]["atr_multiplier"] == 2.5
    assert p["cost_assumptions"]["primary"]["slippage_bps_per_side"] == 5


@pytest.mark.parametrize("local_date,close", [
    ("2026-10-05", "2026-10-05T20:15:00Z"),
    ("2026-11-02", "2026-11-02T21:15:00Z"),
])
def test_completed_bar_clock_dst_and_incomplete_ohlcv(local_date, close):
    d = pd.DataFrame(dict(open=[100.], high=[101.], low=[99.], close=[100.], volume=[10]),
                     index=pd.DatetimeIndex([local_date]))
    assert daily_clock(d.index[0], 16, 15) == pd.Timestamp(close)
    assert completed_daily(d, pd.Timestamp(close)-pd.Timedelta(seconds=1)).empty
    assert len(completed_daily(d, close)) == 1
    d.iloc[0, 3] = np.nan
    assert completed_daily(d, pd.Timestamp(close)-pd.Timedelta(seconds=1)).empty
    with pytest.raises(ValueError, match="Nonfinite"):
        completed_daily(d, close)


def test_evidence_boundaries_missed_bars_and_freeze_day():
    frozen = "2026-10-01T12:00:00Z"
    old, today = pd.Timestamp("2026-09-30"), pd.Timestamp("2026-10-02")
    assert evidence_class(old, frozen, "2026-10-02T21:00Z", "scan", today) == "TEMPORAL_OOS_LATER_UNSEEN"
    assert evidence_class(today, frozen, "2026-10-02T21:00Z", "scan", today) == "PROSPECTIVE_PAPER"
    for mode, now, label in [
        ("catch-up", "2026-10-02T21:00Z", today),
        ("update", "2026-10-02T21:00Z", today),
        ("scan", "2026-10-03T13:30Z", today),
        ("scan", "2026-10-01T21:00Z", pd.Timestamp("2026-10-01")),
    ]:
        assert evidence_class(label, frozen, now, mode, label) == "POST_FREEZE_BACKFILL_NOT_PROSPECTIVE"


def test_exact_baseline_and_shadow_engine_reuse_and_costs(session, monkeypatch):
    force_signal(monkeypatch)
    data = synthetic(session)
    report = run(session, data)
    d = latest(session, "observations").set_index("timestamp")
    columns = [c for c in d if c not in scanner.META_COLUMNS]
    eligible = d.evidence_class.isin(scanner.EVIDENCE)
    production = d[columns].copy()
    production["long_signal"] &= eligible
    expected, _ = run_swing_backtest_with_reconciliation(production, **session.plan["baseline_execution"])
    actual = latest(session, "trades", "BASELINE")
    assert_frame_equal(actual[list(expected.trades)], expected.trades, check_freq=False)
    for candidate in session.plan["shadow_candidates"]:
        arm = f"SHADOW-{candidate['module']}-{candidate['id']}"
        stream = research_stream(d[columns], candidate["module"], candidate["entry_rule"])
        stream["long_signal"] &= eligible
        expected, _ = replay(stream, scanner.POLICIES[candidate["module"]], candidate["exit_rule"])
        actual = latest(session, "trades", arm)
        assert_frame_equal(actual[list(expected.trades)], expected.trades, check_freq=False)
    assert report["baseline_counts"]["PROSPECTIVE_PAPER"]["signals"] == 1
    assert report["baseline_counts"]["TEMPORAL_OOS_LATER_UNSEEN"]["signals"] == 7
    assert len(load_frame(session.runs()[-1]/"evaluation.csv")) == 60  # 15 arms, two classes, two costs


def test_rerun_is_idempotent_and_preserves_first_observation(session, monkeypatch):
    force_signal(monkeypatch)
    data = synthetic(session)
    first = run(session, data)
    observations = latest(session, "observations")
    trades = latest(session, "trades", "BASELINE")
    first_run = session.runs()[0]
    hashes = {str(p): scanner.digest(p) for p in first_run.rglob("*") if p.is_file()}
    second = run(session, data, "2026-10-05T22:00:00Z")
    assert first["baseline_counts"] == second["baseline_counts"]
    assert_frame_equal(observations, latest(session, "observations"))
    assert latest(session, "new_signals", "BASELINE").empty
    assert_frame_equal(trades.drop(columns="as_of_observed_at"),
                       latest(session, "trades", "BASELINE").drop(columns="as_of_observed_at"))
    assert all(scanner.digest(Path(p)) == h for p, h in hashes.items())


def test_prefix_invariance_open_then_closed_no_future_features(session, monkeypatch):
    force_signal(monkeypatch)
    data = synthetic(session, "2026-10-05")
    run(session, data)
    old = latest(session, "observations")
    previous = latest(session, "trades", "BASELINE")
    data = synthetic(session, "2026-10-06")
    data.loc[pd.Timestamp("2026-10-06"), ["open", "high", "low", "close"]] = [100, 101, 90, 95]
    run(session, data, "2026-10-06T21:00Z")
    new = latest(session, "observations")
    assert_frame_equal(old, new.iloc[:len(old)].reset_index(drop=True))
    assert not previous.closed.all()
    assert latest(session, "trades", "BASELINE").closed.any()
    assert not any(c.startswith(("final_", "future_", "exit_", "in_trade_")) for c in new)
    states = latest(session, "states", "BASELINE")
    assert not any(c.startswith(("final_", "future_")) for c in states)
    assert not states.bar_time.eq(pd.Timestamp("2026-10-06")).any()


def test_revision_missing_and_insertion_fail_closed(session):
    data = synthetic(session)
    run(session, data)
    changed = data.copy()
    changed.loc["2026-09-22", "close"] += .01
    with pytest.raises(ValueError, match="revised"):
        run(session, changed)
    assert len(session.runs()) == 1
    assert list((session.base/"failures").glob("*.json"))
    with pytest.raises(ValueError, match="omitted"):
        append_daily(data, data.drop(pd.Timestamp("2026-09-23")), "2026-09-22")
    with pytest.raises(ValueError, match="out-of-order"):
        completed_daily(data.iloc[::-1], "2026-10-05T21:00Z")
    with pytest.raises(ValueError, match="timezone"):
        append_daily(data, data.tz_localize("America/New_York"), "2026-09-22")


def test_corruption_or_source_drift_stops_before_fetch(session, monkeypatch):
    called = []
    monkeypatch.setattr(scanner, "source_identity", lambda: {})
    with pytest.raises(ValueError, match="Source/runtime"):
        session.run("scan", loader=lambda s: called.append(s))
    assert not called


def test_corrupted_plan_and_candidate_fail_closed(session):
    path = session.base/"freeze/candidates.json"
    path.write_text("{}")
    with pytest.raises(ValueError, match="Corrupt artifact"):
        scanner.PaperScanner(session.base)


def test_recovery_after_checkpoint_and_rename(session, monkeypatch):
    data = synthetic(session)
    original = scanner.evaluation
    monkeypatch.setattr(scanner, "evaluation", lambda *a: (_ for _ in ()).throw(RuntimeError("interrupt")))
    with pytest.raises(RuntimeError):
        run(session, data)
    assert (session.base/".run-pending/AAPL/completed.json").exists()
    monkeypatch.setattr(scanner, "evaluation", original)
    result = session.run("resume", loader=lambda _: pytest.fail("Completed symbol refetched"),
                         clock=lambda: "2026-10-05T22:00:00Z")
    assert result["completed_runs"] == 1
    (session.base/"head.json").unlink()
    assert session.report()["completed_runs"] == 1  # verified committed orphan recovered
    assert (session.base/"head.json").exists()


def test_missing_committed_run_detected(session):
    run(session, synthetic(session))
    shutil.move(str(session.runs()[0]), str(session.base/"removed-run"))
    with pytest.raises(ValueError, match="removed"):
        session.report()


def test_empty_validation_outputs_keep_schemas(session):
    report = run(session, seed(session), "2026-10-01T13:00Z", "catch-up")
    assert report["baseline_counts"]["TEMPORAL_OOS_LATER_UNSEEN"]["signals"] == 0
    assert "long_signal" in latest(session, "latest")
    assert len(latest(session, "latest")) == 1
    assert "signal_key" in latest(session, "new_signals", "BASELINE")
    assert "trade_key" in latest(session, "trades", "BASELINE")
    assert "bar_time" in latest(session, "states", "BASELINE")
    table = load_frame(session.runs()[-1]/"evaluation.csv")
    assert table.gross_trade_count.eq(0).all() and table.net_trade_count.eq(0).all()
    assert table.sample_status.eq("LOW SAMPLE").all()


def test_costs_closed_only_and_exact_statistics():
    frame = pd.DataFrame(dict(entry_price=[100., 100., 100.], exit_price=[110., 90., np.nan],
                              return_pct=[.1, -.1, np.nan], closed=[True, True, False]))
    a = account(frame)
    assert a.cost_primary.iloc[0] == pytest.approx(.00315)
    assert a.cost_primary.iloc[1] == pytest.approx(.00285)
    assert np.isnan(a.net_return_primary.iloc[2])
    assert a.net_return_stress.iloc[0] < a.net_return_primary.iloc[0]
    m = return_metrics([.1, -.05, 0., .2])
    assert (m["trade_count"], m["winners"], m["losers"], m["ties"]) == (4, 2, 1, 1)
    assert m["win_rate"] == .5 and m["profit_factor"] == pytest.approx(6.)
    assert m["expected_shortfall_05"] == -.05
    assert m["expectancy_without_top_1"] == pytest.approx(.05/3)


def test_diagnostic_string_and_nan_roundtrip(tmp_path):
    frame = pd.DataFrame(dict(text=["", "NA", "nan", None, np.nan, "Breakout "],
                              number=[np.nan, 1., 2., 3., 4., 5.]))
    store_frame(tmp_path/"test.csv", frame)
    assert_frame_equal(frame, load_frame(tmp_path/"test.csv"))


def test_incomplete_future_bar_cannot_change_current_scan(session):
    data = synthetic(session)
    run(session, data)
    before = latest(session, "observations")
    future = synthetic(session, "2026-10-06")
    future.loc["2026-10-06", ["open", "high", "low", "close"]] = [1, 9000, -1, np.nan]
    run(session, future, "2026-10-06T15:00Z")
    assert_frame_equal(before, latest(session, "observations"))


def test_partial_universe_not_published_and_resume_reuses_completed_symbol(tmp_path, monkeypatch):
    monkeypatch.setattr(scanner, "now", lambda: "2026-10-01T12:00:00Z")
    base = tmp_path/"MULTI"
    base.mkdir()
    scanner.freeze(base, symbols=("AAPL", "MSFT"))
    s = scanner.PaperScanner(base)
    calls = []

    def provider(symbol):
        calls.append(symbol)
        if symbol == "MSFT":
            raise RuntimeError("provider unavailable")
        return load_frame(base/"freeze/seed"/f"{symbol}.csv").set_index("timestamp")

    with pytest.raises(RuntimeError, match="provider"):
        s.run("scan", provider, clock=lambda: "2026-10-05T21:00Z")
    assert not s.runs() and calls == ["AAPL", "MSFT"]
    assert s.report()["incomplete_run"]

    def recovered(symbol):
        assert symbol == "MSFT"
        return load_frame(base/"freeze/seed/MSFT.csv").set_index("timestamp")

    result = s.run("resume", recovered, clock=lambda: "2026-10-06T21:00Z")
    assert result["completed_runs"] == 1 and not result["incomplete_run"]
    assert len(result["coverage"]) == 2


def test_committed_artifact_corruption_stops_report(session):
    run(session, synthetic(session))
    path = session.runs()[0]/"AAPL/BASELINE/trades.csv"
    path.write_text(path.read_text()+"\n")
    with pytest.raises(ValueError, match="Corrupt"):
        session.report()


def test_plan_configuration_cannot_change_in_memory(session):
    session.plan["baseline_execution"]["atr_multiplier"] = 9.
    with pytest.raises(ValueError, match="configuration"):
        session.run("scan", loader=lambda _: pytest.fail("Data access before identity check"))
