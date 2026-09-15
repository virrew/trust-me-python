import numpy as np
import pandas as pd
import pytest

from src.backtest import (
    RECONCILIATION_SCHEMA, run_swing_backtest,
    run_swing_backtest_with_reconciliation,
)
from src.trade_lifecycle import (
    LIFECYCLE_SCHEMA, STOP_PATH_SCHEMA, trade_lifecycle_diagnostics,
)
from test_backtest import diagnostics, signal


def analyze(frame, **kwargs):
    result, reconciliation = run_swing_backtest_with_reconciliation(frame, **kwargs)
    return trade_lifecycle_diagnostics(frame, result), reconciliation


@pytest.mark.parametrize("direction", ["Long", "Short"])
def test_actual_entry_censored_excursions_and_first_mfe_bar(direction):
    frame = diagnostics(3, "Europe/Stockholm")
    signal(frame, 0, direction, mask=2, score=1)
    frame["atr"] = 20.0
    frame["htf_ema_fast"] = 90 if direction == "Long" else 120
    frame.loc[frame.index[0], "close"] = 50  # not the excursion anchor
    frame.loc[frame.index[1:], ["open", "high", "low", "close"]] = [
        [110, 121, 99, 110], [110, 121, 99, 110]]
    tables, reconciliation = analyze(frame)
    row = tables["trade_lifecycle"].iloc[0]
    assert row.entry_price == 110
    assert row.in_trade_mfe == pytest.approx(.1)
    assert row.in_trade_mae == pytest.approx(-.1)
    assert row.mfe_bar == frame.index[1] and row.bars_to_mfe == 0
    assert not row.closed and row.censored_at_end
    assert np.isnan(row.realized_to_in_trade_mfe)
    assert reconciliation.resolution.tolist() == ["FILLED_BUT_CENSORED_AT_END"]


@pytest.mark.parametrize("direction", ["Long", "Short"])
def test_entry_bar_intrabar_stop_has_bounds_not_full_bar_excursion(direction):
    frame = diagnostics(2)
    signal(frame, 0, direction)
    frame.loc[frame.index[1], ["high", "low"]] = [120, 80]
    tables, _ = analyze(frame)
    row = tables["trade_lifecycle"].iloc[0]
    assert row.exit_timing == "INTRABAR_STOP" and row.intrabar_exit_uncertain
    assert row.exit_stop_source == "INITIAL_STOP"
    assert np.isnan(row.in_trade_mfe) and np.isnan(row.in_trade_mae)
    assert row.in_trade_mfe_lower == 0
    assert row.in_trade_mfe_upper == pytest.approx(.2)
    assert row.in_trade_mae_lower == pytest.approx(-.2)
    assert row.in_trade_mae_upper == pytest.approx(-.05)
    assert pd.isna(row.mfe_bar) and pd.isna(row.bars_to_mfe)
    assert np.isnan(row.realized_to_in_trade_mfe)


@pytest.mark.parametrize("direction", ["Long", "Short"])
def test_gap_stop_excludes_exit_high_low(direction):
    frame = diagnostics(3)
    signal(frame, 0, direction)
    frame["htf_ema_fast"] = 90 if direction == "Long" else 110
    frame.loc[frame.index[2], ["open", "high", "low", "close"]] = [
        90 if direction == "Long" else 110, 200, 1, 100]
    tables, _ = analyze(frame)
    row = tables["trade_lifecycle"].iloc[0]
    assert row.exit_timing == "OPEN" and not row.intrabar_exit_uncertain
    assert row.in_trade_mfe == pytest.approx(.01)
    assert row.in_trade_mae == pytest.approx(-.1)
    assert row.exit_stop_source == "TRAILING_STOP"
    assert tables["trade_stop_path"].iloc[-1].exit_at_open


@pytest.mark.parametrize("direction", ["Long", "Short"])
@pytest.mark.parametrize("combined", [False, True])
def test_trend_exit_includes_open_only_and_complete_stop_trace(direction, combined):
    frame = diagnostics(4)
    signal(frame, 0, direction)
    frame.loc[frame.index[1], "htf_ema_fast"] = 101 if direction == "Long" else 99
    exit_open = (90 if direction == "Long" else 110) if combined else 100
    frame.loc[frame.index[2], ["open", "high", "low", "close"]] = [exit_open, 200, 1, 100]
    tables, _ = analyze(frame)
    row = tables["trade_lifecycle"].iloc[0]
    assert row.exit_reason == ("TREND_AND_STOP_AT_OPEN" if combined else "TREND_EXIT")
    assert row.in_trade_mfe == pytest.approx(.01)
    assert row.in_trade_mae == pytest.approx(-.1 if combined else -.01)
    path = tables["trade_stop_path"]
    assert len(path) == row.bars_held == 2
    assert path.iloc[-1].active_stop_at_bar_start == path.iloc[0].active_stop_for_next_bar
    assert path.iloc[-1].exit_at_open


def test_known_prior_extreme_can_make_intrabar_mfe_exact_and_keep_timing():
    frame = diagnostics(3)
    signal(frame, 0)
    frame.loc[frame.index[1], ["high", "low", "close"]] = [110, 99, 109]
    frame.loc[frame.index[2], ["open", "high", "low", "close"]] = [108, 109, 104, 106]
    tables, _ = analyze(frame)
    row = tables["trade_lifecycle"].iloc[0]
    assert row.intrabar_exit_uncertain
    assert row.in_trade_mfe == pytest.approx(.1)
    assert row.in_trade_mae == pytest.approx(-.01)
    assert row.bars_to_mfe == 0
    assert row.realized_to_in_trade_mfe == pytest.approx(.5)
    assert row.in_trade_mfe_minus_realized == pytest.approx(.05)


def test_zero_atr_exits_at_entry_open_and_zero_mfe_ratio_is_na():
    frame = diagnostics(2)
    signal(frame, 0)
    frame.loc[frame.index[0], "atr"] = 0
    tables, reconciliation = analyze(frame)
    row = tables["trade_lifecycle"].iloc[0]
    assert row.exit_timing == "OPEN"
    assert row.in_trade_mfe == row.in_trade_mae == 0
    assert np.isnan(row.realized_to_in_trade_mfe)
    assert reconciliation.resolution.iloc[0] == "FILLED"


def test_reconciliation_precedence_active_conflict_invalid_and_final_bar():
    frame = diagnostics(8)
    signal(frame, 0); signal(frame, 0, "Short")
    signal(frame, 1)
    frame.loc[frame.index[1], "atr"] = np.nan
    signal(frame, 2)
    for pos in (3, 4, 7):
        signal(frame, pos)
        signal(frame, pos, "Short")
    _, rows = analyze(frame)
    assert rows.resolution.tolist() == [
        "CONFLICTING_SIGNAL", "CONFLICTING_SIGNAL",
        "INVALID_ENTRY_PREREQUISITE", "FILLED_BUT_CENSORED_AT_END",
        *["IGNORED_POSITION_OPEN"] * 6]
    ignored = rows[rows.resolution == "IGNORED_POSITION_OPEN"]
    assert (ignored.position_state_at_signal_close == "Long").all()
    assert (ignored.active_trade_id_at_signal_close == 1).all()
    assert ignored.trade_id.isna().all() and ignored.closed.isna().all()
    last = diagnostics(1); signal(last, 0); signal(last, 0, "Short")
    assert analyze(last)[1].resolution.tolist() == ["NO_NEXT_BAR", "NO_NEXT_BAR"]


@pytest.mark.parametrize("atr", [-1, np.nan, np.inf])
def test_invalid_prerequisite_is_signal_atr_only(atr):
    frame = diagnostics(2); signal(frame, 0)
    frame.loc[frame.index[0], "atr"] = atr
    assert analyze(frame)[1].resolution.iloc[0] == "INVALID_ENTRY_PREREQUISITE"


def test_exit_bar_signal_can_fill_and_counts_reconcile():
    frame = diagnostics(5)
    for pos in range(5):
        signal(frame, pos, mask=2, score=1)
    frame.loc[frame.index[2], "low"] = 94
    tables, rows = analyze(frame)
    assert rows.resolution.tolist() == [
        "FILLED", "IGNORED_POSITION_OPEN", "FILLED_BUT_CENSORED_AT_END",
        "IGNORED_POSITION_OPEN", "IGNORED_POSITION_OPEN"]
    assert rows.iloc[2].position_state_at_signal_close == "FLAT"
    assert rows.trade_id.dropna().tolist() == [1, 2]
    assert len(rows) == 5
    assert rows.closed.fillna(False).sum() == 1
    assert len(tables["trade_lifecycle"]) == 2


@pytest.mark.parametrize("periods", [0, 3])
@pytest.mark.parametrize("tz", [None, "Europe/Stockholm"])
def test_empty_stable_schemas_dtypes_timezone(periods, tz):
    frame = diagnostics(periods, tz)
    tables, rows = analyze(frame)
    for table, schema in [
        (tables["trade_lifecycle"], LIFECYCLE_SCHEMA),
        (tables["trade_stop_path"], STOP_PATH_SCHEMA), (rows, RECONCILIATION_SCHEMA),
    ]:
        assert table.empty and list(table) == list(schema)
        for name, dtype in schema.items():
            expected = frame.index.dtype if dtype == "datetime64[ns]" else pd.api.types.pandas_dtype(dtype)
            assert table[name].dtype == expected


def test_no_mutation_and_future_prices_cannot_change_closed_lifecycle():
    frame = diagnostics(25)
    signal(frame, 0)
    frame.loc[frame.index[1], "htf_ema_fast"] = 101
    original = frame.copy(deep=True)
    backtest = run_swing_backtest(frame)
    tables = trade_lifecycle_diagnostics(frame, backtest)
    pd.testing.assert_frame_equal(frame, original)
    frame.loc[frame.index[3:21], "high"] = 150
    changed = trade_lifecycle_diagnostics(frame, run_swing_backtest(frame))
    columns = [c for c in LIFECYCLE_SCHEMA if not c.startswith("post_exit")]
    pd.testing.assert_frame_equal(tables["trade_lifecycle"][columns], changed["trade_lifecycle"][columns])
    assert changed["trade_lifecycle"].post_exit_mfe_from_entry.iloc[0] == .5
    assert changed["trade_lifecycle"].in_trade_mfe.iloc[0] == pytest.approx(.01)
    pd.testing.assert_frame_equal(backtest.trades, run_swing_backtest(frame).trades)


def test_missing_extreme_marks_excursion_unknown():
    frame = diagnostics(2); signal(frame, 0)
    frame.loc[frame.index[1], "high"] = np.nan
    row = analyze(frame)[0]["trade_lifecycle"].iloc[0]
    assert not row.excursion_data_valid
    assert np.isnan(row.in_trade_mfe_lower) and np.isnan(row.in_trade_mae_upper)


def test_censored_pending_trend_has_no_exit_or_realized_value():
    frame = diagnostics(2); signal(frame, 0)
    frame.loc[frame.index[1], "htf_ema_fast"] = 101
    tables, _ = analyze(frame)
    row = tables["trade_lifecycle"].iloc[0]
    assert row.censored_at_end and pd.isna(row.exit_time)
    assert row.in_trade_mfe == pytest.approx(.01)
    assert tables["trade_stop_path"].iloc[-1].trend_exit_triggered_at_close


def test_post_exit_window_excludes_uncertain_exit_bar_and_requires_full_horizon():
    frame = diagnostics(5); signal(frame, 0)
    frame.loc[frame.index[1], ["high", "low"]] = [200, 90]
    result = run_swing_backtest(frame)
    complete = trade_lifecycle_diagnostics(frame, result, post_exit_horizon=4)["trade_lifecycle"].iloc[0]
    assert complete.post_exit_observed_bars == 3
    assert complete.post_exit_mfe_from_entry == pytest.approx(.01)
    incomplete = trade_lifecycle_diagnostics(frame, result, post_exit_horizon=5)["trade_lifecycle"].iloc[0]
    assert not incomplete.post_exit_window_complete
    assert np.isnan(incomplete.post_exit_mfe_from_entry)


@pytest.mark.parametrize("locked", [False, True])
def test_stop_path_preserves_original_state_and_monotonic_stops(locked):
    frame = diagnostics(4); signal(frame, 0)
    frame.loc[frame.index[1:], "high"] = [104, 106, 107]
    frame.loc[frame.index[1:], "atr"] = [1, 4, 1]
    result = run_swing_backtest(frame, use_locked_atr=locked)
    path = trade_lifecycle_diagnostics(frame, result)["trade_stop_path"]
    pd.testing.assert_frame_equal(path[list(result.state)], result.state)
    assert path.active_stop_at_bar_start.is_monotonic_increasing
    assert path.iloc[0].stop_source_at_bar_start == "INITIAL_STOP"


def test_thirty_approved_signals_reconcile_to_thirteen_closed_trades():
    frame = diagnostics(31)
    for pos in range(30):
        signal(frame, pos, mask=2, score=1)
    # Thirteen consecutive entry-bar stops, then one surviving position.
    frame.loc[frame.index[1:14], "low"] = 90
    tables, rows = analyze(frame)
    assert len(rows) == 30
    assert rows.resolution.value_counts().to_dict() == {
        "IGNORED_POSITION_OPEN": 16, "FILLED": 13,
        "FILLED_BUT_CENSORED_AT_END": 1}
    assert tables["trade_lifecycle"].closed.sum() == 13
