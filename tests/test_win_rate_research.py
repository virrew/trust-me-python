import json

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from src.backtest import run_swing_backtest_with_reconciliation
from src.trade_lifecycle import trade_lifecycle_diagnostics
from src.exit_research_runner import config
from src.entry_research_runner import checkpoint, verify_marker
from src.win_rate_research_analysis import (
    replay, EXIT_RULES, metrics, classify_losses, path_observations,
    partition, screen, paired_effects, frontier_targets,
)
from src.win_rate_research_runner import WinRateRunner, STAGES


def data(n=8, tz='UTC'):
    d = pd.DataFrame(dict(open=100.,high=100.4,low=99.8,close=100.,atr=4.,
        htf_ema_fast=90.,long_signal=False,short_signal=False,long_active_module_mask=2,
        short_active_module_mask=0,long_score=1,short_score=0),
        index=pd.date_range('2024-01-01',periods=n,tz=tz))
    if n:
        d.iloc[0,d.columns.get_loc('long_signal')] = True
    return d


@pytest.mark.parametrize('trend,locked',[(False,False),(True,False),(False,True),(True,True)])
def test_disabled_research_replay_exact_equivalence(trend,locked):
    rng = np.random.default_rng(9876)
    d = data(240)
    close = 100*np.exp(np.cumsum(rng.normal(0,.025,len(d))))
    d['open'] = np.r_[100,close[:-1]]*(1+rng.normal(0,.01,len(d)))
    d['close'] = close
    d['high'] = d[['open','close']].max(axis=1)*1.025
    d['low'] = d[['open','close']].min(axis=1)*.975
    d['long_signal'] = rng.random(len(d)) < .5
    d['htf_ema_fast'] = d.close.rolling(3).mean()
    d['atr'] = d.close*.025
    d.iloc[20,d.columns.get_loc('atr')] = np.nan
    c = config(2.5,trend,locked)
    a, ar = run_swing_backtest_with_reconciliation(d,**c)
    b, br = replay(d,c)
    assert_frame_equal(a.trades,b.trades)
    assert_frame_equal(a.state,b.state)
    assert_frame_equal(ar,br)


@pytest.mark.parametrize('n',[0,1])
def test_empty_schema_and_timezone(n):
    d = data(n,'America/New_York')
    a, ar = run_swing_backtest_with_reconciliation(d)
    b, br = replay(d,config())
    assert_frame_equal(a.trades,b.trades)
    assert_frame_equal(ar,br)
    assert metrics(b.trades)['trades'] == 0


def test_stop_cannot_use_same_bar_future_high():
    d = data(4)
    d.loc[d.index[1],['high','low','close']] = [105.,99.,104.]
    d.loc[d.index[2],['open','high','low','close']] = [98.,101.,97.,100.]
    r, _ = replay(d,config(2.5,False),EXIT_RULES[0])
    t = r.trades.iloc[0]
    assert t.exit_time == d.index[2]
    assert t.exit_price == 98  # gap through break-even, not a fictitious zero-return fill
    assert r.state.iloc[0].active_stop_at_bar_start == 90
    assert r.state.iloc[0].active_stop_for_next_bar == 100


def test_intrabar_stop_precedes_protection_trigger():
    d = data(3)
    d.loc[d.index[1],['high','low']] = [110.,89.]
    r, _ = replay(d,config(2.5,False),EXIT_RULES[0])
    assert r.trades.iloc[0].exit_price == 90
    assert pd.isna(r.state.iloc[0].active_stop_for_next_bar)


def test_time_exit_next_open_and_final_censoring():
    rule = next(r for r in EXIT_RULES if r['id'] == 'time_5')
    d = data(7)
    d.loc[d.index[6],'open'] = 97.
    r, _ = replay(d,config(2.5,False),rule)
    assert r.trades.iloc[0].exit_time == d.index[6]
    assert r.trades.iloc[0].exit_price == 97.
    assert r.trades.iloc[0].exit_reason == 'RESEARCH_TIME_EXIT'
    truncated, _ = replay(d.iloc[:6],config(2.5,False),rule)
    assert not truncated.trades.iloc[0].closed


def test_prefix_causality_and_reentry():
    d = data(9)
    d.loc[d.index[1],'high'] = 103.
    d.loc[d.index[2],'low'] = 99.
    d.loc[d.index[2],'long_signal'] = True
    rule = EXIT_RULES[0]
    a, ar = replay(d,config(2.5,False),rule)
    mutated = d.copy()
    mutated.loc[mutated.index[5]:,['high','low','close']] = [200.,1.,150.]
    b, br = replay(mutated,config(2.5,False),rule)
    assert_frame_equal(a.state[a.state.bar_time < d.index[5]],b.state[b.state.bar_time < d.index[5]])
    assert a.trades.iloc[1].entry_time == d.index[3]
    assert_frame_equal(ar[ar.signal_time < d.index[2]],br[br.signal_time < d.index[2]])


def test_no_short_or_unregistered_rule():
    d = data()
    d['short_signal'] = True
    with pytest.raises(ValueError,match='Long only'):
        replay(d,config())
    d['short_signal'] = False
    with pytest.raises(ValueError,match='Unregistered'):
        replay(d,config(),dict(family='breakeven',level=.013))


def test_taxonomy_thresholds_priority_and_uncertainty():
    f = pd.DataFrame(dict(closed=[True]*7,return_pct=[-.01]*7,
        in_trade_mfe_lower=[.02,.005,.0,0.,0.,.004,.019],
        in_trade_mfe_upper=[.03,.019,.004,.004,.004,.006,.021],
        flat_first10=[False,False,True,False,False,False,False],
        early_mae_known=[-.02]*4+[-.01]*3,early_mfe_upper=[0.]*7))
    assert list(classify_losses(f).category) == ['GIVEBACK_LOSER','SMALL_PROFIT_GIVEBACK',
        'DEAD_TRADE','IMMEDIATE_FAILURE','NEVER_WORKED','UNCERTAIN_PATH','UNCERTAIN_PATH']
    assert 'category' in classify_losses(f.iloc[:0])


def test_survival_does_not_use_exit_bar_future_high_or_close():
    d = data(4)
    d.loc[d.index[1],['low','high','close']] = [98.,103.,102.]
    d.loc[d.index[2],['open','low','high','close']] = [100.,90.,120.,110.]
    bt,_ = run_swing_backtest_with_reconciliation(d,**config(2.5,False))
    life = trade_lifecycle_diagnostics(d,bt)['trade_lifecycle']
    paths = path_observations(d,life)
    t = paths.iloc[0]
    assert t.first_positive_close_bar == 1
    assert t['first_known_0.020'] == 1
    assert pd.isna(t['first_known_0.040'])
    assert t['first_possible_0.040'] == 2
    assert t.mae_before_positive_close == 0
    assert t.in_trade_mfe_upper > t.in_trade_mfe_lower


def test_ties_censoring_pf_and_tail_metrics():
    f = pd.DataFrame(dict(closed=[True,True,True,False],return_pct=[.04,-.02,0,np.nan],bars_held=[3,4,1,2]))
    m = metrics(f)
    assert m['win_rate'] == 1/3
    assert m['profit_factor'] == 2
    assert m['expectancy'] == pytest.approx(.02/3)
    assert m['censored'] == 1 and m['ties'] == 1


def test_purge_boundary_and_pair_by_signal_not_id():
    f = pd.DataFrame(dict(module=['breakout']*3,symbol=['A']*3,closed=[True]*3,
        return_pct=[-.01,.01,0],bars_held=[2]*3,
        signal_time=pd.to_datetime(['2024-01-01','2024-02-01','2024-03-01']),
        exit_time=pd.to_datetime(['2024-01-04','2024-03-02','2024-03-03'])))
    p = partition(f,'2024-03-01')
    assert list(p.partition) == ['IN-SAMPLE','BOUNDARY / CENSORED','ENTRY HOLDOUT / EXIT-USED HISTORY']
    b = f.iloc[[0,2]].copy()
    b.loc[0,'return_pct'] = .02
    pairs = paired_effects(f,b)
    assert pairs.loser_to_win.sum() == 1
    assert (pairs._merge == 'left_only').sum() == 1


def test_frontier_requires_robust_status_not_just_high_wr():
    f = pd.DataFrame(dict(module=['breakout']*2,scenario=['a','b'],win_rate=[.8,.6],status=['MIXED','ROBUST'],
                          trades=[10,200],expectancy=[.01,.02],profit_factor=[1.1,2.]))
    out = frontier_targets(f)
    r = out[(out.module == 'breakout')&(out.target == .75)].iloc[0]
    assert r.any_predefined_reached and not r.robust_reached
    assert r.scenario == 'UNSUPPORTED'


def test_checkpoint_resume_no_action_and_corruption(tmp_path):
    calls = []
    def action(folder):
        calls.append(1)
        (folder/'raw.csv').write_text('x\n1\n')
    assert checkpoint(tmp_path,'identity',action) == 'COMPLETED'
    stamp = (tmp_path/'completed.json').stat().st_mtime_ns
    assert checkpoint(tmp_path,'identity',action) == 'REUSED'
    assert len(calls) == 1
    assert (tmp_path/'completed.json').stat().st_mtime_ns == stamp
    with pytest.raises(ValueError,match='identity'):
        verify_marker(tmp_path,'different')
    (tmp_path/'raw.csv').write_text('x\n2\n')
    with pytest.raises(ValueError,match='checksum'):
        checkpoint(tmp_path,'identity',action)


def test_failed_stage_resumes_first_incomplete_and_state_recovery(tmp_path):
    runner = WinRateRunner.__new__(WinRateRunner)
    runner.base,runner.identity = tmp_path,'test'
    runner.state_path = tmp_path/'research_state.json'
    runner.state = dict(status='PENDING',stages={})
    calls = []
    runner.stage_1 = lambda f: ((f/'raw.csv').write_text('x\n1\n'),calls.append(1))
    def fail(f):
        raise RuntimeError('interrupted')
    runner.stage_2 = fail
    with pytest.raises(RuntimeError):
        runner.run()
    assert calls == [1]
    assert runner.state['status'] == 'FAILED'
    runner.stage_2 = lambda f:(f/'raw.csv').write_text('x\n2\n')
    runner.run(2)
    runner.run(1)
    assert calls == [1]
    assert runner.state['stages'][STAGES[1]]['status'] == 'COMPLETED'


def test_stage_requires_predecessor(tmp_path):
    runner = WinRateRunner.__new__(WinRateRunner)
    runner.base,runner.identity = tmp_path,'test'
    with pytest.raises(ValueError,match='Prerequisite'):
        runner.run(2)
