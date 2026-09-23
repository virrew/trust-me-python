import csv
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from src.ab_rule_testing import _paired, run_ab_rule_test
from src.exit_research_analysis import (
    comparable, comparison_tables, summarize, supported_winner, trimmed_mean, without_top,
)
from src.exit_research_runner import (
    GRID, MODULE_BITS, Runner, append_registry, config, execute_arm, grid_pairs,
    load_frame, pure_diagnostics, store_frame, validate_ohlcv,
)
from test_ab_rule_testing import diagnostics, signal


def module_columns(frame):
    for col, bit in zip(("pullback_long", "breakout_long", "squeeze_long", "mean_rev_long"), (1, 2, 4, 8)):
        frame[col] = (frame.long_active_module_mask & bit) != 0
    return frame


@pytest.mark.parametrize("module,bit", [("breakout", 2), ("squeeze", 4)])
def test_pure_cohort_preserves_input_index_nan_score_and_filters_overlaps(module, bit):
    frame = diagnostics(6, "Europe/Stockholm")
    for i, mask in enumerate((bit, bit | 1, 8, bit, bit | 8)):
        signal(frame, i, mask)
    frame.loc[frame.index[3], "long_signal"] = False
    frame.loc[frame.index[0], "atr"] = np.nan
    frame["short_signal"] = True
    module_columns(frame)
    original = frame.copy(deep=True)
    result = pure_diagnostics(frame, module)
    assert result.long_signal.tolist() == [True, False, False, False, False, False]
    assert not result.short_signal.any()
    pd.testing.assert_frame_equal(frame, original)
    pd.testing.assert_frame_equal(result.drop(columns=["long_signal", "short_signal"]),
                                  frame.drop(columns=["long_signal", "short_signal"]))
    assert MODULE_BITS[module.title()] == bit
    frame.loc[frame.index[0], "long_active_module_mask"] = 0
    with pytest.raises(ValueError, match="disagree"):
        pure_diagnostics(frame, module)


@pytest.mark.parametrize("a,b", [(config(), config(locked=True)),
                                (config(), config(trend=False)),
                                (config(1.5), config(3))])
def test_cached_execution_matches_existing_ab_all_columns(a, b):
    frame = diagnostics(12, "Europe/Stockholm")
    signal(frame, 0, 2); signal(frame, 3, 2); signal(frame, 11, 2)
    frame.loc[frame.index[1], ["high", "low", "atr"]] = [104, 100, 1]
    frame.loc[frame.index[2], ["high", "low", "atr"]] = [104, 100, 4]
    frame.loc[frame.index[4], "htf_ema_fast"] = 105
    original = frame.copy(deep=True)
    actual = _paired(execute_arm(frame, a), execute_arm(frame, b), frame.index.dtype)
    expected = run_ab_rule_test(frame, experiment_id="test", experiment_name="test",
                                baseline_config=a, variant_config=b)["paired_signals"]
    pd.testing.assert_frame_equal(actual, expected)
    pd.testing.assert_frame_equal(frame, original)


@pytest.mark.parametrize("periods", [0, 5])
def test_cache_csv_roundtrip_preserves_empty_timezone_nullable_types(tmp_path, periods):
    frame = diagnostics(periods, "Europe/Stockholm")
    if periods:
        signal(frame, 0, 2)
    arm = execute_arm(frame, config())
    for name, table in arm.items():
        target = tmp_path/f"{name}.csv"
        store_frame(target, table)
        result = load_frame(target)
        pd.testing.assert_frame_equal(result, table, check_exact=True)


def pairs(deltas):
    n = len(deltas)
    frame = pd.DataFrame({
        "symbol": [f"S{i % 20}" for i in range(n)],
        "signal_time": [pd.Timestamp(2020 + i % 4, 1, 1) + pd.Timedelta(days=i//4) for i in range(n)],
        "direction": "Long", "pair_status": "MATCHED_SIGNAL", "resolution_a": "FILLED",
        "resolution_b": "FILLED", "return_a": -.01, "return_b": np.asarray(deltas)-.01,
        "realized_R_a": -.1, "realized_R_b": (np.asarray(deltas)-.01)*10,
        "bars_held_a": 5, "bars_held_b": 6, "exit_reason_a": "ATR_STOP", "exit_reason_b": "ATR_STOP",
        "delta_return": deltas, "delta_R": np.asarray(deltas)*10,
    })
    return frame


def test_robustness_known_numbers_and_one_sided_censoring():
    p = pairs([.1, -.02, 0, .04])
    p.loc[2, ["pair_status", "resolution_b", "return_b", "realized_R_b"]] = ["A_ONLY_FILL", "IGNORED_POSITION_OPEN", np.nan, np.nan]
    p.loc[3, ["resolution_b", "return_b", "realized_R_b"]] = ["FILLED_BUT_CENSORED_AT_END", np.nan, np.nan]
    s = summarize(p)
    assert s["comparable_pairs"] == 2
    assert s["one_sided_fills"] == 1 and s["fill_status_changes"] == 2
    assert s["trades_a"] == 4 and s["trades_b"] == 2
    assert s["b_wins"] == s["a_wins"] == 1
    assert s["mean_paired_delta"] == pytest.approx(.04)
    assert s["mean_paired_delta_R"] == pytest.approx(.4)
    assert s["paired_mean_without_top_1"] == pytest.approx(-.02)
    assert np.isnan(s["paired_mean_without_top_5"])
    assert len(comparable(p)) == 2


def test_trim_is_symmetric_and_tail_flags_are_direction_symmetric():
    p = pairs([-.01] * 199 + [4.0])
    s = summarize(p)
    assert s["mean_paired_delta"] > 0 and s["trimmed_mean_paired_delta"] < 0
    assert s["majority_mean_disagree"] and s["top5_reverse_advantage"]
    assert s["label"] == "TAIL-SENSITIVE"
    assert supported_winner(p) is None
    assert trimmed_mean(range(10)) == 4.5
    assert without_top([1, 2, 3], 1) == 1.5
    assert supported_winner(pairs([.01]*199 + [-4.0])) is None


def test_supported_winner_requires_sample_stability_and_no_tail_dependence():
    p = pairs([.02]*200)
    assert supported_winner(p) == "B"
    assert supported_winner(p.iloc[:50]) is None
    p["symbol"] = "ONE"
    assert supported_winner(p) is None
    p = pairs([.02]*200)
    p["signal_time"] = pd.Timestamp("2025-01-01")
    assert supported_winner(p) is None


def test_empty_analysis_retains_schemas_and_no_false_zero_rates():
    p = pairs([])
    tables = comparison_tables(p)
    assert tables["symbol_summary"].columns[0] == "symbol"
    assert tables["year_summary"].columns[0] == "year"
    assert tables["exit_reason_distribution"].columns.tolist() == ["arm", "exit_reason", "count"]
    s = tables["robustness_summary"].iloc[0]
    assert s.comparable_pairs == 0 and np.isnan(s.mean_paired_delta)
    assert s.supported_winner == "INCONCLUSIVE"


def test_finite_grid_and_invalid_parameters():
    assert GRID == (1.5, 1.75, 2.0, 2.25, 2.5, 3.0)
    assert len(grid_pairs()) == 8
    assert len(set(grid_pairs())) == 8
    with pytest.raises(ValueError):
        config(1.6)
    with pytest.raises(ValueError):
        config(trend="False")


def test_registry_append_preserves_history_bytes_and_is_idempotent(tmp_path):
    path = tmp_path/"registry.csv"
    content = b'experiment_id,result_path,baseline_config,variant_config\r\nold,original,a,b\r\n'
    path.write_bytes(content)
    row = dict(experiment_id="new", result_path="results/new", baseline_config="{}", variant_config='{"x":1}')
    assert append_registry(path, row)
    first = path.read_bytes()
    assert first.startswith(content)
    assert not append_registry(path, row)
    assert path.read_bytes() == first
    with pytest.raises(ValueError, match="collision"):
        append_registry(path, {**row, "result_path": "different"})


def test_invalid_snapshot_fails_without_imputation():
    f = pd.DataFrame(dict(open=[100.], high=[101.], low=[99.], close=[100.], volume=[2.]),
                     index=pd.date_range("2025-01-01", periods=1))
    validate_ohlcv(f)
    for bad in [f.assign(high=98), f.assign(close=np.nan), f.assign(volume=-1), pd.concat([f, f])]:
        with pytest.raises(ValueError):
            validate_ohlcv(bad)


def bare_runner(tmp_path):
    r = object.__new__(Runner)
    r.root, r.session = tmp_path, "TEST"
    r.base, r.raw, r.cache = tmp_path/"orchestration", tmp_path/"results/ab_tests", tmp_path/"cache"
    r.raw.mkdir(parents=True)
    (tmp_path/"results/research_registry.csv").write_text(
        "experiment_id,result_path,baseline_config,variant_config\n")
    r.arm_memory = {}
    r.diagnostic_failures = []
    f = diagnostics(8)
    signal(f, 0, 2); signal(f, 4, 2)
    f.loc[f.index[2], "low"] = 90
    r.diagnostics = {"TEST": module_columns(f)}
    return r


def test_resume_reuses_completed_experiments_without_reexecution_and_detects_corruption(tmp_path, monkeypatch):
    r = bare_runner(tmp_path)
    state = dict(snapshot_id="frozen", experiments={}, data_failures=[], snapshot_symbols={})
    p, eid = r.compare("breakout", config(), config(locked=True), state, "B")
    original = {f.name: f.read_bytes() for f in (r.raw/eid).iterdir()}
    monkeypatch.setattr(r, "arm", lambda *args: pytest.fail("completed experiment was rerun"))
    restored = dict(snapshot_id="frozen", experiments={}, data_failures=[], snapshot_symbols={})
    loaded, same_id = r.compare("breakout", config(), config(locked=True), restored, "B")
    assert same_id == eid and len(p) == len(loaded)
    assert restored["experiments"][eid]["status"] == "reused from existing research"
    assert all((r.raw/eid/f).read_bytes() == b for f, b in original.items())
    assert len(list(csv.DictReader((tmp_path/"results/research_registry.csv").open()))) == 1
    (r.raw/eid/"paired_signals.csv").write_text("corrupt")
    with pytest.raises(ValueError, match="integrity"):
        r.compare("breakout", config(), config(locked=True), state, "B")


def test_failed_symbol_does_not_kill_valid_arm_and_checkpoint_resumes(tmp_path, monkeypatch):
    r = bare_runner(tmp_path)
    r.diagnostics["BAD"] = r.diagnostics["TEST"].drop(columns="atr")
    arms, failures = r.arm("breakout", config())
    assert set(arms) == {"TEST"} and failures[0]["symbol"] == "BAD"
    r.arm_memory.clear()
    del r.diagnostics["BAD"]
    monkeypatch.setattr("src.exit_research_runner.execute_arm", lambda *args: pytest.fail("cached symbol rerun"))
    resumed, failures = r.arm("breakout", config())
    pd.testing.assert_frame_equal(resumed["TEST"]["ab_trade_lifecycle"], arms["TEST"]["ab_trade_lifecycle"])
    assert not failures


def test_failed_experiment_is_not_completed_or_registered(tmp_path, monkeypatch):
    r = bare_runner(tmp_path)
    monkeypatch.setattr(r, "arm", lambda *args: ({}, []))
    state = dict(snapshot_id="frozen", experiments={}, data_failures=[], snapshot_symbols={})
    with pytest.raises(RuntimeError, match="No common"):
        r.compare("breakout", config(), config(locked=True), state, "B")
    assert list(state["experiments"].values())[0]["status"] == "failed"
    assert len(list(csv.DictReader((tmp_path/"results/research_registry.csv").open()))) == 0


def test_snapshot_download_once_retry_failure_and_integrity(tmp_path, monkeypatch):
    bare_runner(tmp_path)
    r = Runner(root=tmp_path, session="TEST")
    monkeypatch.setattr("src.exit_research_runner.UNIVERSE", ("TEST", "BAD"))
    calls = []
    def download(command, **kwargs):
        symbol = command[command.index("--download-one") + 1]
        calls.append(symbol)
        if symbol == "BAD":
            return SimpleNamespace(returncode=1, stdout="", stderr="DNS failed")
        frame = pd.DataFrame(dict(timestamp=pd.date_range("2025-01-01", periods=2),
                                  open=[100., 101.], high=[102., 103.], low=[99., 100.],
                                  close=[101., 102.], volume=[10, 20]))
        store_frame(Path(command[command.index("--target") + 1]), frame)
        return SimpleNamespace(returncode=0, stdout="", stderr="")
    monkeypatch.setattr("src.exit_research_runner.subprocess.run", download)
    first = r.freeze()
    assert calls == ["TEST", "BAD", "BAD"]
    assert first["symbols"]["BAD"]["status"] == "failed"
    assert len(first["failures"]) == 2 and first["failures"][1]["retry_attempted"]
    assert r.freeze() == first
    assert calls == ["TEST", "BAD", "BAD"]
    (r.snapshot/"TEST.csv").write_text("corrupt")
    with pytest.raises(ValueError, match="integrity"):
        r.freeze()


def test_no_candidate_stops_after_finite_grid_without_forced_interactions(tmp_path, monkeypatch):
    r = bare_runner(tmp_path)
    p = pairs([0.0]*200)
    seen = []
    def compare(module, a, b, state, stage):
        eid = str(len(seen))
        seen.append(stage)
        state["experiments"][eid] = dict(status="completed", common_symbols=50, included_symbols=list(range(50)))
        return p, eid
    monkeypatch.setattr(r, "compare", compare)
    monkeypatch.setattr(r, "write_report", lambda *args: None)
    snapshot = dict(snapshot_id="frozen", symbols={}, failures=[])
    result = r.run_module("breakout", snapshot)
    assert len(seen) == 10
    assert result["final_status"] == "INCONCLUSIVE" and result["candidate"] is None
    assert result["trend_decision"]["value"] is True and result["mode_decision"]["value"] is False
    assert result["steps"]["E"].startswith("not applicable")


def test_candidate_requires_both_final_interactions(tmp_path, monkeypatch):
    r = bare_runner(tmp_path)
    seen = []
    def compare(module, a, b, state, stage):
        eid = str(len(seen))
        seen.append(stage)
        # Smaller multiplier wins coherently; both baseline dimensions favor A.
        # Final mode deliberately contradicts its selected baseline dimension.
        delta = .02 if stage == "E-final-mode" else -.02
        p = pairs([delta]*200)
        p["return_a"] = .04
        p["return_b"] = .04 + delta
        state["experiments"][eid] = dict(status="completed", common_symbols=50, included_symbols=list(range(50)))
        return p, eid
    monkeypatch.setattr(r, "compare", compare)
    monkeypatch.setattr(r, "write_report", lambda *args: None)
    result = r.run_module("breakout", dict(snapshot_id="frozen", symbols={}, failures=[]))
    assert len(seen) == 12
    assert result["screened_multiplier"] == 1.5
    assert result["final_interaction_support"] == [True, False]
    assert result["candidate"] is None and result["final_status"] == "INCONCLUSIVE"
