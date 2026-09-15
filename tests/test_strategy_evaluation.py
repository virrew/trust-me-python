import numpy as np
import pandas as pd
import pytest

from src.strategy_evaluation import (
    COMPARISON_SCHEMA, EXCURSION_SCHEMA, MODULE_BITS, PERFORMANCE_SCHEMA,
    approved_vs_blocked_evaluation, evaluate_strategy, trade_performance,
)


def _diagnostics(periods=7, tz="UTC"):
    index = pd.date_range("2026-01-01", periods=periods, tz=tz)
    frame = pd.DataFrame({
        "open": 100.0, "high": 102.0, "low": 98.0, "close": 100.0,
        "atr": 2.0, "htf_ema_fast": 90.0, "long_signal": False,
        "short_signal": False, "long_active_module_mask": 0,
        "short_active_module_mask": 0, "long_score": 0, "short_score": 0,
    }, index=index)
    requirements = {
        "pb": ("trend", "slow_ema", "rsi", "touch", "reclaim"),
        "bo": ("trend", "price", "volume", "rsi"),
        "sq": ("trend", "recent", "release", "price"),
        "mr": ("trend", "slow_ema", "oversold", "rsi_cross", "candle"),
    }
    for prefix, names in requirements.items():
        for direction in ("long", "short"):
            adjusted = tuple("overbought" if name == "oversold" and direction == "short"
                             else name for name in names)
            for name in adjusted:
                frame[f"{prefix}_{direction}_fail_{name}"] = False
    return frame


def test_trade_performance_total_direction_and_overlapping_module_attribution():
    trades = pd.DataFrame({
        "direction": ["Long", "Long", "Short", "Short"],
        "active_module_mask": [3, 1, 2, 4],
        "closed": [True, True, True, False],
        "return_pct": [.10, -.05, .20, np.nan],
    })
    result = trade_performance(trades)
    assert list(result) == list(PERFORMANCE_SCHEMA)
    total = result[result.group_type == "Total"].iloc[0]
    assert total.number_of_trades == 3
    assert total.win_rate == pytest.approx(2 / 3)
    assert total.profit_factor == pytest.approx(6)
    assert total.expectancy == pytest.approx(.25 / 3)
    breakout = result[(result.group_type == "Module")
                      & (result.module == "Breakout")].iloc[0]
    assert breakout.number_of_trades == 2
    # The first trade is deliberately present in both module cohorts.
    pullback = result[(result.group_type == "Module")
                      & (result.module == "Pullback")].iloc[0]
    assert pullback.number_of_trades == 2


def test_approved_vs_blocked_metrics_exclude_censored_rows():
    outcomes = pd.DataFrame({
        "direction": ["Long"] * 3, "module": ["Pullback"] * 3,
        "sample_type": ["Approved Signal", "Approved Signal", "Blocked Opportunity"],
        "complete_2": pd.array([True, False, True], dtype="boolean"),
        "forward_return_2": [.10, np.nan, -.05], "mfe_2": [.15, np.nan, .02],
        "mae_2": [-.03, np.nan, -.08],
    })
    result = approved_vs_blocked_evaluation(outcomes, 2)
    approved = result[result.evaluation_group == "Approved Signal"].iloc[0]
    assert approved.sample_size == 2 and approved.complete_samples == 1
    assert approved.censored_samples == 1 and approved.win_rate == 1
    blocked = result[result.evaluation_group == "Blocked Opportunity"].iloc[0]
    assert blocked.expectancy == pytest.approx(-.05)
    assert blocked.profit_factor == 0


def test_end_to_end_evaluation_matches_excursions_to_realized_trade():
    frame = _diagnostics()
    frame.loc[frame.index[0], ["long_signal", "long_active_module_mask", "long_score"]] = [True, 3, 2]
    frame.loc[frame.index[1], ["high", "low", "close"]] = [106, 99, 105]
    frame.loc[frame.index[2], ["open", "high", "low", "close"]] = [105, 106, 104, 105]
    frame.loc[frame.index[1], ["close", "htf_ema_fast"]] = [89, 90]
    frame.loc[frame.index[3], "pb_long_fail_trend"] = True

    result = evaluate_strategy(frame, horizons=(2,), excursion_horizon=2)
    assert set(result) == {"trade_performance", "approved_vs_blocked",
                           "excursion_vs_realized", "excursion_summary",
                           "trades", "evaluation_outcomes", "trade_lifecycle",
                           "trade_stop_path", "signal_fill_reconciliation"}
    total = result["trade_performance"].iloc[0]
    assert total.number_of_trades == 1
    comparison = result["excursion_vs_realized"]
    assert set(comparison.module) == {"Pullback", "Breakout"}
    assert comparison.realized_return.nunique() == 1
    assert comparison.mfe.iloc[0] == pytest.approx(.06)
    groups = result["approved_vs_blocked"].evaluation_group
    assert {"Approved Signal", "Blocked Opportunity"}.issubset(set(groups))


def test_empty_evaluation_preserves_schema_and_timezone():
    frame = _diagnostics(0, "Europe/Stockholm")
    result = evaluate_strategy(frame, horizons=(1,), excursion_horizon=1)
    assert list(result["trade_performance"]) == list(PERFORMANCE_SCHEMA)
    assert list(result["approved_vs_blocked"]) == list(COMPARISON_SCHEMA)
    assert list(result["excursion_vs_realized"]) == list(EXCURSION_SCHEMA)
    assert result["excursion_vs_realized"].signal_time.dtype == frame.index.dtype


@pytest.mark.parametrize("mask", [0, 16, -1])
def test_module_masks_outside_documented_contract_do_not_create_unknown_groups(mask):
    trades = pd.DataFrame({"direction": ["Long"], "active_module_mask": [mask],
                           "closed": [True], "return_pct": [.1]})
    result = trade_performance(trades)
    assert set(result[result.group_type == "Module"].module) == set(MODULE_BITS)


def test_evaluation_lifecycle_and_reconciliation_share_trade_ids_and_provenance():
    frame = _diagnostics(23, "Europe/Stockholm")
    frame.loc[frame.index[:3], ["long_signal", "long_active_module_mask", "long_score"]] = [True, 3, 2]
    frame.loc[frame.index[1], "htf_ema_fast"] = 101
    frame.loc[frame.index[4:21], "high"] = 150
    result = evaluate_strategy(frame)
    lifecycle = result["trade_lifecycle"]
    reconciliation = result["signal_fill_reconciliation"]
    assert lifecycle.trade_id.tolist() == result["trades"].trade_id.tolist()
    assert reconciliation.resolution.iloc[1] == "IGNORED_POSITION_OPEN"
    assert lifecycle.iloc[0].post_exit_mfe_from_entry == .5
    assert lifecycle.iloc[0].in_trade_mfe == pytest.approx(.02)
    assert lifecycle.iloc[0].active_module_mask == 3
    assert lifecycle.iloc[0].module_score == 2
    assert lifecycle.entry_time.dtype == frame.index.dtype
    assert reconciliation.entry_time.dtype == frame.index.dtype
