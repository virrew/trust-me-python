import json

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from src.backtest import run_swing_backtest_with_reconciliation
from src.trade_lifecycle import trade_lifecycle_diagnostics
from src.exit_research_runner import config, load_frame, store_frame
from src.win_rate_research_analysis import partition, path_observations
from src.strategy_improvement_execution import known_state, policy_action, replay, research_stream
from src.strategy_improvement_analysis import (causal_path, label_trades, future_labels,
    threshold_analysis, state_curves, comparison_summary, paired_comparison, screen)
from src.strategy_improvement_runner import StrategyImprovementRunner, STAGES, freeze_json, read_frozen


def data(n=9, tz='UTC'):
    d = pd.DataFrame(dict(open=100., high=100.4, low=99.8, close=100., atr=4.,
        htf_ema_fast=90., long_signal=False, short_signal=False, long_active_module_mask=2,
        short_active_module_mask=0, long_score=1, short_score=0),
        index=pd.date_range('2024-01-01', periods=n, tz=tz))
    if n:
        d.iloc[0, d.columns.get_loc('long_signal')] = True
    return d


def rule(family='giveback', level=.02, stall=3, give=.5):
    return dict(family=family, level=level, stall_bars=stall, giveback_fraction=give, lock_fraction=.1)


def tables(d, policy=None, settings=None):
    result, rec = replay(d, settings or config(2.5, False), policy)
    life = path_observations(d, trade_lifecycle_diagnostics(d, result)['trade_lifecycle'])
    t = partition(life.assign(module='breakout', symbol='TEST'), pd.Timestamp('2025-01-01', tz=d.index.tz))
    s = causal_path(d, result).merge(result.trades[['trade_id', 'signal_time']], on='trade_id', validate='many_to_one')
    s = s.assign(module='breakout', symbol='TEST')
    t = label_trades(t, s)
    return result, rec, t, s


def test_running_extremes_stalls_giveback_and_ties():
    a = known_state({}, age=1, entry=100, high=104, low=97, close=103)
    assert a['running_mfe'] == pytest.approx(.04)
    assert a['running_mae'] == pytest.approx(-.03)
    assert a['new_mfe_high'] and a['last_high_age'] == 1
    assert a['mfe_retention'] == pytest.approx(.75)
    b = known_state(a, age=2, entry=100, high=104, low=99, close=101)
    assert b['bars_since_mfe_high'] == 1 and not b['new_mfe_high']
    assert b['giveback'] == pytest.approx(.03)
    assert b['giveback_fraction'] == pytest.approx(.75)
    assert b['running_mae'] == pytest.approx(-.03)
    assert b['close_relative_peak'] == pytest.approx(101/104-1)
    c = known_state(b, age=3, entry=100, high=105, low=95, close=104)
    assert c['last_high_age'] == 3 and c['bars_since_mfe_high'] == 0
    assert c['running_mae'] == pytest.approx(-.05)


def test_no_mfe_retention_for_zero_mfe():
    s = known_state({}, age=1, entry=100, high=100, low=99, close=99)
    assert s['running_mfe'] == 0 and np.isnan(s['mfe_retention'])
    assert not s['new_mfe_high'] and s['bars_since_mfe_high'] == 1


@pytest.mark.parametrize('trend,locked', [(False, False), (True, False), (False, True), (True, True)])
def test_disabled_engine_full_equivalence(trend, locked):
    rng = np.random.default_rng(834)
    d = data(120)
    d['close'] = 100*np.exp(rng.normal(0, .03, len(d)).cumsum())
    d['open'] = np.r_[100, d.close.iloc[:-1]]*(1+rng.normal(0, .01, len(d)))
    d['high'] = d[['open', 'close']].max(axis=1)*1.02
    d['low'] = d[['open', 'close']].min(axis=1)*.98
    d['atr'] = d.close*.025
    d.loc[d.index[20], 'atr'] = np.nan
    d['long_signal'] = rng.random(len(d)) < .6
    d['htf_ema_fast'] = d.close.rolling(3).mean()
    settings = config(2.5, trend, locked)
    a, ar = run_swing_backtest_with_reconciliation(d, **settings)
    b, br = replay(d, settings)
    assert_frame_equal(a.trades, b.trades)
    assert_frame_equal(a.state, b.state)
    assert_frame_equal(ar, br)


@pytest.mark.parametrize('n', [0, 1])
def test_empty_schemas_and_timezone(n):
    d = data(n, 'America/New_York')
    result, rec, t, s = tables(d)
    assert str(s.bar_time.dtype) == str(d.index.dtype)
    labels = future_labels(t, s)
    raw, summary = threshold_analysis(t, s, labels)
    assert 'new_high_next_5' in labels and 'final_win_rate' in summary
    assert 'state_rows' in state_curves(s, labels)
    assert 'winner_damaged' in paired_comparison(t, t)
    assert comparison_summary(t, t)['trades'] == 0
    assert not screen(t, t)['survived']


def test_causal_next_open_giveback_and_gap():
    d = data(5)
    d.loc[d.index[1], ['high', 'low', 'close']] = [105, 99, 101]
    d.loc[d.index[2], ['open', 'high', 'low', 'close']] = [98, 110, 97, 108]
    result, _, t, s = tables(d, rule())
    assert result.trades.iloc[0].exit_time == d.index[2]
    assert result.trades.iloc[0].exit_price == 98  # no fill at trigger close or at MFE
    assert result.trades.iloc[0].exit_reason == 'RESEARCH_LIFECYCLE_EXIT'
    assert s.age.tolist() == [1]
    assert t.in_trade_mfe.iloc[0] == pytest.approx(.05)
    assert t.peak_age_exact.iloc[0] == 1
    assert t.bars_peak_to_exit_exact.iloc[0] == 1
    assert t.final_giveback_lower.iloc[0] == pytest.approx(.07)


def test_same_bar_stop_precedes_new_high_and_policy():
    d = data(4)
    d.loc[d.index[1], ['high', 'low', 'close']] = [120, 89, 119]
    result, _, t, s = tables(d, rule())
    assert result.trades.iloc[0].exit_price == 90
    assert s.empty
    assert t.in_trade_mfe_lower.iloc[0] == 0
    assert t.in_trade_mfe_upper.iloc[0] == pytest.approx(.2)
    assert pd.isna(t.peak_age_exact.iloc[0])


def test_adaptive_stop_active_only_next_bar():
    d = data(7)
    d.loc[d.index[1], ['high', 'low', 'close']] = [105, 99, 104]
    d.loc[d.index[2:5], ['open', 'high', 'low', 'close']] = [103, 104, 99, 103]
    d.loc[d.index[5], ['open', 'high', 'low', 'close']] = [100, 104, 99, 102]
    result, _, t, s = tables(d, rule('adaptive'))
    assert result.trades.iloc[0].exit_time == d.index[5]
    assert result.trades.iloc[0].exit_price == 100  # gap below next-bar 100.5 stop
    assert result.state.iloc[3].active_stop_at_bar_start == 95
    assert result.state.iloc[3].active_stop_for_next_bar == pytest.approx(100.5)


def test_stalled_exit_and_censoring():
    d = data(5)
    d.loc[d.index[1], ['high', 'low', 'close']] = [104, 99, 103]
    d.loc[d.index[2:], ['open', 'high', 'low', 'close']] = [102, 103, 99, 101]
    result, _, _, _ = tables(d, rule('stalled'))
    assert not result.trades.iloc[0].closed  # trigger at last close, no next open
    e = pd.concat([d, d.iloc[-1:].set_axis(pd.DatetimeIndex([d.index[-1]+pd.Timedelta(days=1)]))])
    result, _, _, _ = tables(e, rule('stalled'))
    assert result.trades.iloc[0].exit_time == e.index[-1]
    assert result.trades.iloc[0].exit_price == 102


def test_prefix_invariance_and_separate_future_labels():
    d = data(12)
    d.loc[d.index[1], ['high', 'close']] = [105, 104]
    d.loc[d.index[3], 'high'] = 106
    a, ar, at, astates = tables(d, rule('adaptive'))
    changed = d.copy()
    changed.loc[d.index[7]:, ['high', 'low', 'close']] = [300, 1, 200]
    b, br, bt, bstates = tables(changed, rule('adaptive'))
    assert_frame_equal(astates[astates.bar_time < d.index[7]], bstates[bstates.bar_time < d.index[7]])
    assert not any(c.startswith(('final_', 'future_', 'peak_age', 'outcome')) for c in astates)
    labels = future_labels(at, astates)
    assert 'final_return' in labels
    assert 'final_return' not in astates
    prefix, _, _, prefix_states = tables(d.iloc[:7], rule('adaptive'))
    assert_frame_equal(astates[astates.bar_time < d.index[7]].reset_index(drop=True), prefix_states.reset_index(drop=True))


def test_future_horizons_censoring_and_ambiguous_stop():
    d = data(5)
    d.loc[d.index[1], ['high', 'close']] = [104, 103]
    d.loc[d.index[2], ['high', 'low', 'close']] = [120, 89, 110]
    _, _, t, s = tables(d)
    labels = future_labels(t, s)
    assert pd.isna(labels.new_high_next_3.iloc[0])  # possible exit-bar high cannot be treated as reached
    assert labels.additional_mfe_lower.iloc[0] == 0
    assert labels.additional_mfe_upper.iloc[0] == pytest.approx(.16)
    _, _, t, s = tables(d.iloc[:2])
    assert pd.isna(future_labels(t, s).new_high_next_3.iloc[0])


def test_threshold_remaining_upside_and_pre_high_giveback():
    d = data(5)
    d.loc[d.index[1], ['high', 'low', 'close']] = [102, 99, 101]
    d.loc[d.index[2], ['open', 'high', 'low', 'close']] = [101, 101, 99, 100]
    d.loc[d.index[3], ['open', 'high', 'low', 'close']] = [101, 106, 96, 105]
    d.loc[d.index[4], ['open', 'high', 'low', 'close']] = [95, 97, 94, 96]
    _, _, t, s = tables(d)
    labels = future_labels(t, s)
    assert labels.bars_to_next_high.iloc[0] == 2
    assert labels.giveback_before_next_high.iloc[0] == pytest.approx(1.5)
    raw, summary = threshold_analysis(t, s, labels)
    r = raw[raw.threshold == .02].iloc[0]
    assert r.additional_mfe_lower == pytest.approx(.04)
    assert r.crossing == 'SURVIVED_CLOSE'


def test_pairing_damage_zero_and_one_sided_fills():
    d = data(5)
    d.loc[d.index[1], ['high', 'close']] = [115, 114]
    d.loc[d.index[2], ['open', 'high', 'low', 'close']] = [112, 114, 110, 112]
    d.loc[d.index[3], ['open', 'high', 'low', 'close']] = [110, 114, 100, 105]
    _, _, a, _ = tables(d)
    b = a.copy()
    a['return_pct'] = .15
    b['return_pct'] = 0.
    b['trade_id'] = 99
    r = comparison_summary(a, b)
    assert r['winner_damaged'] == r['winner_destroyed'] == r['large_winner_truncated'] == 1
    assert r['loser_to_win'] == 0 and r['winners'] == 0 and r['ties'] == 1
    a['return_pct'] = -.01
    r = comparison_summary(a, b)
    assert r['loser_to_nonloss'] == 1 and r['loser_to_win'] == 0
    b['signal_time'] += pd.Timedelta(days=1)
    r = comparison_summary(a, b)
    assert r['a_only_fills'] == r['b_only_fills'] == 1 and r['comparable_trades'] == 0


def test_short_and_invalid_rule_rejected():
    d = data()
    d['short_signal'] = True
    with pytest.raises(ValueError, match='Long only'):
        replay(d, config())
    d['short_signal'] = False
    with pytest.raises(ValueError, match='Invalid finite'):
        replay(d, config(), rule(level=.2))


@pytest.mark.filterwarnings('ignore:DataFrame is highly fragmented:pandas.errors.PerformanceWarning')
def test_price_relaxation_preserves_original_mask_and_other_gates():
    from src.diagnostics_signals import signal_diagnostics
    from src.entry_research_analysis import cohorts
    rng = np.random.default_rng(28)
    d = data(240, None)
    d['close'] = 100*np.exp(rng.normal(.001, .025, len(d)).cumsum())
    d['open'] = d.close.shift().fillna(100)
    d['high'] = d[['open', 'close']].max(axis=1)*1.01
    d['low'] = d[['open', 'close']].min(axis=1)*.99
    d['volume'] = rng.integers(100, 1000, len(d))
    diagnostics = signal_diagnostics(d[['open', 'high', 'low', 'close', 'volume']])
    original = diagnostics.copy(deep=True)
    c, _ = cohorts(diagnostics, 'breakout')
    added = c.single_blocker & c.sole_blocker.eq('bo_long_fail_price')
    assert added.any()
    out = research_stream(diagnostics, 'breakout', dict(family='relax_price'))
    pd.testing.assert_series_equal(out.long_signal, (c.approved | added).rename('long_signal'))
    pd.testing.assert_series_equal(out.long_active_module_mask, diagnostics.long_active_module_mask)
    assert (out.loc[added, 'long_active_module_mask'] == 0).all()
    assert_frame_equal(diagnostics, original)


def test_freeze_and_corruption(tmp_path):
    path = tmp_path/'candidate_strategy_improvements.json'
    payload = dict(candidates=[dict(level=.02)])
    sha = freeze_json(path, payload)
    stamp = path.stat().st_mtime_ns
    assert freeze_json(path, payload) == sha and path.stat().st_mtime_ns == stamp
    assert read_frozen(path) == payload
    with pytest.raises(ValueError, match='Frozen'):
        freeze_json(path, dict(candidates=[]))
    path.write_text(json.dumps(dict(candidates=[])))
    with pytest.raises(ValueError, match='checksum'):
        read_frozen(path)


def test_stage_zero_resume_and_state_recovery(tmp_path):
    runner = StrategyImprovementRunner.__new__(StrategyImprovementRunner)
    runner.base, runner.identity = tmp_path, 'test'
    runner.state_path = tmp_path/'research_state.json'
    calls = []
    for i in range(11):
        def action(folder, n=i):
            calls.append(n)
            (folder/'raw.csv').write_text('x\n1\n')
            (folder/'summary.csv').write_text('n\n1\n')
        setattr(runner, f'stage_{i}', action)
    runner.publish = lambda: None
    runner.run(0)
    def fail(folder):
        raise RuntimeError('interruption')
    original = runner.stage_3
    runner.stage_3 = fail
    with pytest.raises(RuntimeError):
        runner.run()
    assert calls == [0, 1, 2]
    runner.state_path.unlink()  # emulate interruption between marker and state write
    runner.stage_3 = original
    runner.run()
    assert calls == list(range(11))
    assert runner.state['status'] == 'COMPLETED'
    runner.run()
    assert calls == list(range(11))
    (tmp_path/STAGES[4]/'raw.csv').write_text('corrupt')
    with pytest.raises(ValueError, match='checksum'):
        runner.run()


def test_stage_requires_predecessor(tmp_path):
    runner = StrategyImprovementRunner.__new__(StrategyImprovementRunner)
    runner.base, runner.identity = tmp_path, 'test'
    with pytest.raises(ValueError, match='Prerequisite'):
        runner.run(2)


def test_replay_robustness_and_final_stages_with_no_surviving_combination(tmp_path, monkeypatch):
    """Exercise real stage composition, schema IO and the no-survivor branch."""
    from types import SimpleNamespace
    import src.strategy_improvement_runner as runner_module
    monkeypatch.setattr(runner_module, 'UNIVERSE', ['TEST'])
    d = data(6, None)
    d['atr'] = 2.
    d['htf_adx'] = 22.
    d.loc[d.index[1], ['high', 'low', 'close']] = [110, 99, 101]
    d.loc[d.index[2], ['open', 'high', 'low', 'close']] = [107, 108, 104, 106]
    d.loc[d.index[3], 'long_signal'] = True
    d.loc[d.index[4], ['high', 'low', 'close']] = [101, 94, 96]
    for col in ['pullback_long', 'squeeze_long', 'mean_rev_long']:
        d[col] = False
    d['breakout_long'] = True
    _, rec, one, states = tables(d)
    assert one.return_pct.gt(0).any() and one.return_pct.lt(0).any()
    base = pd.concat([one.assign(module=m, regime='ADX 18-25') for m in runner_module.MODULE_BITS], ignore_index=True)
    runner = StrategyImprovementRunner.__new__(StrategyImprovementRunner)
    runner.base, runner.identity, runner.split = tmp_path, 'test', '2025-01-01'
    runner.diagnostics = lambda s: d
    runner.prior = SimpleNamespace(read=lambda stage, name: rec.assign(module='breakout', symbol='TEST'))
    runner.plan = dict(identity=dict(git_commit='fixture', snapshot='fixture'))
    runner.write(tmp_path/STAGES[1], 'retrospective_trade_labels', base)
    runner.write(tmp_path/STAGES[2], 'summary', pd.DataFrame(columns=['module', 'classification', 'filter']))
    runner.write(tmp_path/STAGES[6], 'entry_region_evidence', pd.DataFrame(columns=['module', 'passed', 'candidate']))
    _, threshold = threshold_analysis(one, states, future_labels(one, states))
    runner.write(tmp_path/STAGES[3], 'summary', threshold)
    freeze_json(tmp_path/STAGES[6]/'candidate_strategy_improvements.json', dict(candidates=[
        dict(module='breakout', id='giveback', family='lifecycle', exit_rule=rule(), entry_rule=None)]))
    for stage in range(7, 11):
        folder = tmp_path/STAGES[stage]
        folder.mkdir(parents=True, exist_ok=True)
        getattr(runner, f'stage_{stage}')(folder)
    summary = runner.read(7, 'summary')
    assert summary.comparable_trades.iloc[0] == 2
    assert runner.read(8, 'trades').empty
    assert not runner.read(9, 'summary').discovery_survived.any()
    assert len(runner.read(10, 'module_answers')) == 100
    assert len(runner.read(10, 'research_answers')) == 17
    assert (tmp_path/STAGES[10]/'STRATEGY_IMPROVEMENT_MATRIX_V1.md').exists()


def test_candidate_selection_cannot_use_holdout_outcomes(tmp_path):
    from types import SimpleNamespace
    from src.strategy_improvement_runner import MODULE_BITS
    candidates = []
    for run, future_scale in [('a', .01), ('b', 10.)]:
        runner = StrategyImprovementRunner.__new__(StrategyImprovementRunner)
        runner.base, runner.identity = tmp_path/run, 'test'
        runner.prior = SimpleNamespace(plan=dict(entry_rules={m: [] for m in MODULE_BITS}))
        rows, paths = [], []
        for module in MODULE_BITS:
            for i in range(100):
                time = pd.Timestamp('2023-01-01')+pd.Timedelta(days=i)
                holdout = i >= 80
                winner = i % 2 == 0
                rows.append(dict(module=module, symbol='TEST', signal_time=time, closed=True,
                    partition='ENTRY HOLDOUT / EXIT-USED HISTORY' if holdout else 'IN-SAMPLE',
                    outcome='WINNER' if winner else 'LOSER', return_pct=.05 if winner else -.01,
                    in_trade_mfe_lower=future_scale if holdout else .03, entry_price=100))
                paths.append(dict(module=module, symbol='TEST', signal_time=time,
                    running_mfe=future_scale if holdout else .04, bars_since_mfe_high=3,
                    giveback_fraction=future_scale if holdout else .6, stop_for_next_bar=95, age=4))
        runner.write(runner.base/STAGES[1], 'retrospective_trade_labels', pd.DataFrame(rows))
        runner.write(runner.base/STAGES[1], 'decision_time_states', pd.DataFrame(paths))
        runner.write(runner.base/STAGES[2], 'approved_trade_bins', pd.DataFrame(columns=['module', 'feature', 'partition']))
        runner.write(runner.base/STAGES[0], 'entry_evidence', pd.DataFrame(columns=['module', 'feature', 'final_status']))
        for stage in (3, 4, 5):
            runner.write(runner.base/STAGES[stage], 'summary', pd.DataFrame(dict(n=[1])))
        folder = runner.base/STAGES[6]
        folder.mkdir(parents=True)
        runner.stage_6(folder)
        candidates.append(read_frozen(folder/'candidate_strategy_improvements.json')['candidates'])
    assert candidates[0] == candidates[1]
    assert len(candidates[0]) == 12
    assert candidates[0][0]['exit_rule']['giveback_fraction'] == .65
