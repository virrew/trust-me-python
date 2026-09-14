import numpy as np
import pandas as pd
import pytest

from src.backtest import (
    STATE_SCHEMA, TRADE_SCHEMA, run_swing_backtest, summarize_trades,
)


def diagnostics(periods=5, tz="UTC"):
    index = pd.date_range("2026-01-01", periods=periods, tz=tz)
    frame = pd.DataFrame({
        "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0,
        "atr": 2.0, "htf_ema_fast": 90.0, "long_signal": False,
        "short_signal": False, "long_active_module_mask": 0,
        "short_active_module_mask": 0, "long_score": 0, "short_score": 0,
    }, index=index)
    return frame


def signal(frame, position, direction="Long", mask=3, score=2):
    prefix = direction.lower()
    frame.loc[frame.index[position], f"{prefix}_signal"] = True
    frame.loc[frame.index[position], f"{prefix}_active_module_mask"] = mask
    frame.loc[frame.index[position], f"{prefix}_score"] = score


def test_signal_is_available_at_close_and_fills_only_at_next_open():
    frame = diagnostics()
    signal(frame, 0)
    frame.loc[frame.index[0], "close"] = 87
    frame.loc[frame.index[1], "open"] = 103
    trades, _ = run_swing_backtest(frame)
    trade = trades.iloc[0]
    assert trade.signal_time == frame.index[0]
    assert trade.signal_available_at == "signal bar close"
    assert trade.entry_time == frame.index[1]
    assert trade.entry_price == 103
    assert trade.entry_price != frame.close.iloc[0]
    assert trade.active_module_mask == 3 and trade.module_score == 2


def test_last_bar_signal_and_conflicting_signal_do_not_fill():
    last = diagnostics(2); signal(last, 1)
    conflict = diagnostics(3); signal(conflict, 0); signal(conflict, 0, "Short")
    assert run_swing_backtest(last).trades.empty
    assert run_swing_backtest(conflict).trades.empty


def test_one_position_and_repeated_signals_are_ignored():
    frame = diagnostics(6)
    signal(frame, 0); signal(frame, 1); signal(frame, 2)
    result = run_swing_backtest(frame)
    assert len(result.trades) == 1
    assert not result.trades.iloc[0].closed


@pytest.mark.parametrize("direction,expected", [("Long", 95.0), ("Short", 105.0)])
def test_initial_atr_stop_uses_signal_bar_atr(direction, expected):
    frame = diagnostics(3); signal(frame, 0, direction)
    frame.loc[frame.index[0], "atr"] = 2
    frame.loc[frame.index[1], "atr"] = 50
    if direction == "Short":
        frame["htf_ema_fast"] = 110
    trades, state = run_swing_backtest(frame)
    assert trades.iloc[0].atr_at_entry == 2
    assert trades.iloc[0].initial_stop == expected
    assert state.iloc[0].active_stop_at_bar_start == expected


def test_locked_and_dynamic_atr_and_monotonic_trailing_stop():
    frame = diagnostics(4); signal(frame, 0)
    frame.loc[frame.index[1:], "high"] = [104, 106, 107]
    frame.loc[frame.index[1:], "low"] = 99
    frame.loc[frame.index[1:], "atr"] = [1, 4, 1]
    locked = run_swing_backtest(frame, use_locked_atr=True).state
    dynamic = run_swing_backtest(frame, use_locked_atr=False).state
    assert locked.active_stop_for_next_bar.iloc[0] == 99
    assert dynamic.active_stop_for_next_bar.iloc[0] == 101.5
    assert dynamic.active_stop_at_bar_start.iloc[0] == 95  # high cannot move it early
    assert dynamic.active_stop_at_bar_start.is_monotonic_increasing


@pytest.mark.parametrize("direction,gap,expected", [
    ("Long", False, 95.0), ("Long", True, 94.0),
    ("Short", False, 105.0), ("Short", True, 106.0),
])
def test_stop_touch_and_gap_fill(direction, gap, expected):
    frame = diagnostics(4); signal(frame, 0, direction)
    if direction == "Long":
        position = 2 if gap else 1
        frame.loc[frame.index[position], "open"] = 94 if gap else 100
        frame.loc[frame.index[position], "low"] = 94
    else:
        frame["htf_ema_fast"] = 110
        position = 2 if gap else 1
        frame.loc[frame.index[position], "open"] = 106 if gap else 100
        frame.loc[frame.index[position], "high"] = 106
    trades, state = run_swing_backtest(frame)
    assert trades.iloc[0].exit_reason == "ATR_STOP"
    assert trades.iloc[0].exit_price == expected
    assert state.iloc[-1].stop_hit


@pytest.mark.parametrize("direction", ["Long", "Short"])
def test_trend_exit_is_decided_at_close_and_filled_next_open(direction):
    frame = diagnostics(4); signal(frame, 0, direction)
    if direction == "Long":
        frame.loc[frame.index[1], ["close", "htf_ema_fast"]] = [89, 90]
    else:
        frame["htf_ema_fast"] = 110
        frame.loc[frame.index[1], ["close", "htf_ema_fast"]] = [111, 110]
    frame.loc[frame.index[2], "open"] = 102
    trades, state = run_swing_backtest(frame)
    assert state.iloc[0].trend_exit_triggered_at_close
    assert trades.iloc[0].exit_time == frame.index[2]
    assert trades.iloc[0].exit_price == 102
    assert trades.iloc[0].exit_reason == "TREND_EXIT"


def test_trend_and_stop_at_same_open_has_combined_reason():
    frame = diagnostics(4); signal(frame, 0)
    frame.loc[frame.index[1], ["close", "htf_ema_fast"]] = [89, 90]
    frame.loc[frame.index[2], "open"] = 94
    trade = run_swing_backtest(frame).trades.iloc[0]
    assert trade.exit_price == 94
    assert trade.exit_reason == "TREND_AND_STOP_AT_OPEN"


def test_open_trade_is_censored_without_invented_exit():
    frame = diagnostics(2); signal(frame, 0)
    trade = run_swing_backtest(frame).trades.iloc[0]
    assert not trade.closed and trade.censored_at_end
    assert pd.isna(trade.exit_time) and np.isnan(trade.exit_price)
    assert np.isnan(trade.return_pct)


def test_timezone_empty_schema_no_mutation_and_no_lookahead():
    empty = diagnostics(0, "Europe/Stockholm")
    result = run_swing_backtest(empty)
    assert list(result.trades) == list(TRADE_SCHEMA)
    assert list(result.state) == list(STATE_SCHEMA)
    assert result.trades.signal_time.dtype == empty.index.dtype
    frame = diagnostics(3); signal(frame, 0); original = frame.copy(deep=True)
    first = run_swing_backtest(frame).trades.iloc[0]
    frame.loc[frame.index[2], ["open", "high", "low", "close", "atr"]] = 10000
    second = run_swing_backtest(frame).trades.iloc[0]
    assert first.entry_price == second.entry_price
    expected = diagnostics(3); signal(expected, 0)
    pd.testing.assert_frame_equal(original, expected)


def test_summary_uses_closed_only_and_calculates_metrics():
    trades = pd.DataFrame({"closed": [True, True, True, False],
                           "return_pct": [.10, -.05, .20, np.nan]})
    row = summarize_trades(trades).iloc[0]
    assert (row.number_of_trades, row.wins, row.losses) == (3, 2, 1)
    assert row.win_rate == pytest.approx(2 / 3)
    assert row.mean_return == row.expectancy == pytest.approx(.25 / 3)
    assert row.median_return == pytest.approx(.10)
    assert row.average_win == pytest.approx(.15)
    assert row.average_loss == pytest.approx(-.05)
    assert row.profit_factor == pytest.approx(6)
