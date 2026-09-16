import numpy as np
import pandas as pd
import pytest

from src.ab_rule_testing import (
    METADATA_SCHEMA, PAIRED_SCHEMA, RISK_PERFORMANCE_SCHEMA,
    SIGNAL_EXECUTION_SCHEMA, run_ab_rule_test,
)


def diagnostics(periods=8, tz="UTC"):
    index = pd.date_range("2026-01-01", periods=periods, tz=tz)
    frame = pd.DataFrame({
        "open": 100.0, "high": 102.0, "low": 99.0, "close": 100.0,
        "atr": 2.0, "htf_ema_fast": 90.0, "long_signal": False,
        "short_signal": False, "long_active_module_mask": 0,
        "short_active_module_mask": 0, "long_score": 0, "short_score": 0,
    }, index=index)
    requirements = {"pb": ("trend", "slow_ema", "rsi", "touch", "reclaim"),
                    "bo": ("trend", "price", "volume", "rsi"),
                    "sq": ("trend", "recent", "release", "price"),
                    "mr": ("trend", "slow_ema", "oversold", "rsi_cross", "candle")}
    for prefix, names in requirements.items():
        for direction in ("long", "short"):
            for name in names:
                if name == "oversold" and direction == "short":
                    name = "overbought"
                frame[f"{prefix}_{direction}_fail_{name}"] = False
    return frame


def signal(frame, pos, mask=3):
    frame.loc[frame.index[pos], ["long_signal", "long_active_module_mask", "long_score"]] = [True, mask, 2]


def run(frame, a=None, b=None, horizon=2):
    return run_ab_rule_test(frame, experiment_id="locked-atr-001",
                            experiment_name="Dynamic versus locked ATR",
                            baseline_config=a, variant_config=b,
                            excursion_horizon=horizon)


def test_identical_control_is_deterministic_non_mutating_and_timezone_safe():
    frame = diagnostics(5, "Europe/Stockholm"); signal(frame, 0)
    original = frame.copy(deep=True)
    first = run(frame); second = run(frame)
    pd.testing.assert_frame_equal(first["a_trade_lifecycle"], first["b_trade_lifecycle"])
    for key in first:
        pd.testing.assert_frame_equal(first[key], second[key])
    pd.testing.assert_frame_equal(frame, original)
    assert first["paired_signals"].signal_time.dtype == frame.index.dtype
    assert first["experiment_metadata"].iloc[0].changed_parameter == "NONE_CONTROL_RUN"


def test_locked_atr_changes_same_signal_exit_and_later_fill_sequence():
    frame = diagnostics(7); signal(frame, 0, 3); signal(frame, 3, 2)
    frame.loc[frame.index[1], ["high", "low", "atr"]] = [104, 100, 1]
    frame.loc[frame.index[2], ["high", "low", "atr"]] = [104, 100, 4]
    frame.loc[frame.index[3], "low"] = 100
    # Dynamic stop is 101.5 and exits on bar 2; locked stop is 99 and survives.
    result = run(frame, {"use_locked_atr": False}, {"use_locked_atr": True})
    paired = result["paired_signals"].set_index("signal_time")
    assert paired.loc[frame.index[0], "pair_status"] == "MATCHED_SIGNAL"
    assert paired.loc[frame.index[0], "exit_time_a"] != paired.loc[frame.index[0], "exit_time_b"]
    assert paired.loc[frame.index[3], "pair_status"] == "A_ONLY_FILL"
    assert result["experiment_metadata"].iloc[0].changed_parameter == "use_locked_atr"
    reversed_result = run(frame, {"use_locked_atr": True}, {"use_locked_atr": False})
    reversed_pairs = reversed_result["paired_signals"].set_index("signal_time")
    assert reversed_pairs.loc[frame.index[3], "pair_status"] == "B_ONLY_FILL"


def test_overlap_r_values_censoring_and_lifecycle_uncertainty():
    frame = diagnostics(5); signal(frame, 0, 3)
    frame.loc[frame.index[1], ["high", "low"]] = [120, 80]
    result = run(frame)
    life = result["a_trade_lifecycle"].iloc[0]
    assert life.initial_risk_pct == pytest.approx(.05)
    assert life.realized_R == pytest.approx(-1)
    assert np.isnan(life.in_trade_mfe) and np.isnan(life.mfe_R)
    perf = result["strategy_and_module_performance"]
    a_modules = perf[(perf.arm == "A") & (perf.group_type == "Module")]
    assert a_modules.set_index("module").loc["Pullback", "number_of_trades"] == 1
    assert a_modules.set_index("module").loc["Breakout", "number_of_trades"] == 1
    censored = diagnostics(2); signal(censored, 0)
    out = run(censored)
    assert out["a_reconciliation"].resolution.tolist() == ["FILLED_BUT_CENSORED_AT_END"]
    assert np.isnan(out["a_trade_lifecycle"].iloc[0].realized_R)


def test_empty_schemas_and_single_change_enforcement():
    result = run(diagnostics(0), horizon=1)
    assert list(result["experiment_metadata"]) == list(METADATA_SCHEMA)
    assert list(result["strategy_and_module_performance"]) == list(RISK_PERFORMANCE_SCHEMA)
    assert list(result["signal_execution"]) == list(SIGNAL_EXECUTION_SCHEMA)
    assert list(result["paired_signals"]) == list(PAIRED_SCHEMA)
    assert result["paired_signals"].empty
    with pytest.raises(ValueError, match="at most one"):
        run(diagnostics(2), {}, {"use_locked_atr": True, "atr_multiplier": 3})
