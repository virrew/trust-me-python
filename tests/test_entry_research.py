import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.diagnostics_signals import signal_diagnostics
from src.entry_research_analysis import (
    MODULES, KEYS, cohorts, requirements, decision_features, feature_manifest,
    future_labels, ablation, fit_bins, bin_numbers, analyze_module,
    hypothesis_rows, evaluate_hypotheses, metrics,
)
from src.entry_research_runner import checkpoint, verify_marker, EntryRunner
from src.exit_research_runner import digest, save_json

ROOT=Path(__file__).resolve().parents[1]


def fixture(n=120,tz=None):
    rng=np.random.default_rng(732)
    close=100*np.exp(np.cumsum(rng.normal(.001,.02,n)))
    frame=pd.DataFrame(dict(open=close*.998,high=close*1.025,low=close*.975,
                            close=close,volume=rng.integers(100,1000,n)),
                       index=pd.date_range('2022-01-01',periods=n,tz=tz))
    with warnings.catch_warnings():
        warnings.simplefilter('ignore',pd.errors.PerformanceWarning)
        return signal_diagnostics(frame)


def synthetic(module):
    d=fixture(8)
    prefix={'pullback':'pb','breakout':'bo','squeeze':'sq','meanrev':'mr'}[module]
    col={'pullback':'pullback_long','breakout':'breakout_long','squeeze':'squeeze_long','meanrev':'mean_rev_long'}[module]
    bit={'pullback':1,'breakout':2,'squeeze':4,'meanrev':8}[module]
    for c in ['pullback_long','breakout_long','squeeze_long','mean_rev_long']:
        d[c]=False
    for c in requirements(d,module):
        d[c]=False
    for c in ['direction','score','volatility','candle','session','confirmed']:
        d['long_fail_'+c]=False
    d[col]=True
    d['long_active_module_mask']=bit
    d['long_score']=1
    d['long_signal']=True
    # 0 baseline; 1 final sole; 2 module sole; 3 multi; 4 overlap;
    # 5 other-only module; 6 module+final failure; 7 another final sole.
    d.loc[d.index[1],'long_fail_candle']=True
    cols=requirements(d,module)
    d.loc[d.index[[2,3,5,6]],cols[0]]=True
    d.loc[d.index[3],cols[1]]=True
    d.loc[d.index[[2,3,5,6]],col]=False
    d.loc[d.index[[2,3,5,6]],'long_active_module_mask']=0
    other='breakout_long' if module!='breakout' else 'pullback_long'
    obit=2 if module!='breakout' else 1
    d.loc[d.index[[4,5]],other]=True
    d.loc[d.index[4],'long_active_module_mask']=bit|obit
    d.loc[d.index[5],'long_active_module_mask']=obit
    d.loc[d.index[6],'long_fail_volatility']=True
    d.loc[d.index[7],'long_fail_volatility']=True
    d['long_fail_score']=d.long_active_module_mask==0
    d['long_signal']=~d[['long_fail_'+c for c in ['direction','score','volatility','candle','session','confirmed']]].any(axis=1)
    return d


@pytest.mark.parametrize('module',MODULES)
def test_pure_single_multi_and_safe_ablation(module):
    d=synthetic(module)
    original=d.copy(deep=True)
    c,f=cohorts(d,module)
    assert c.approved.tolist()==[True,False,False,False,False,False,False,False]
    assert c.single_blocker.tolist()==[False,True,True,False,False,False,False,True]
    assert c.multi_blocker.tolist()==[False,False,False,True,False,False,True,False]
    union,extra=ablation(d,module,'long_fail_candle')
    assert union.tolist()==[True,True,False,False,False,False,False,False]
    assert extra.sum()==1
    for unsafe in [requirements(d,module)[0],'long_fail_score']:
        with pytest.raises(ValueError,match='NOT SAFE'):
            ablation(d,module,unsafe)
    pd.testing.assert_frame_equal(d,original)


def test_all_feature_prefixes_causal_and_no_labels_accepted():
    full=fixture(100,'America/New_York')
    prefix=fixture(100,'America/New_York')[['open','high','low','close','volume']].iloc[:70]
    with warnings.catch_warnings():
        warnings.simplefilter('ignore',pd.errors.PerformanceWarning)
        partial=signal_diagnostics(prefix)
    a=decision_features(full,'X',ROOT)
    b=decision_features(partial,'X',ROOT)
    pd.testing.assert_frame_equal(a.iloc[:70],b)
    manifest=feature_manifest(full,ROOT)
    assert set(manifest.name)==set(full.columns)
    assert manifest.safe_decision_time_feature.all()
    assert a.observation_id.is_unique
    with pytest.raises(ValueError,match='Unreviewed'):
        decision_features(full.assign(forward_return_10=1),'X',ROOT)


def test_labels_anchor_and_censoring_and_discovery_boundary():
    d=fixture(60,'Europe/Stockholm')
    split=d.index[35]
    discovery=d.loc[d.index<split]
    f=decision_features(discovery,'X',ROOT)
    labels=future_labels(discovery,f)
    assert set(f).intersection(set(labels))==set(KEYS)
    assert labels.complete_20.sum()==15
    assert labels.label_end_20.dropna().max()<split
    assert labels.forward_return_1.iloc[0]==pytest.approx(d.close.iloc[1]/d.close.iloc[0]-1)
    assert labels.mfe_3.iloc[0]==pytest.approx((d.high.iloc[1:4]/d.close.iloc[0]-1).max())
    # Mutating holdout never affects discovery labels.
    changed=d.copy()
    changed.loc[changed.index>=split,['close','high','low']]*=100
    pd.testing.assert_frame_equal(labels,future_labels(changed.loc[changed.index<split],f))


def test_bin_edges_fixed_and_ties_not_forced():
    d=fixture(100)
    edges=fit_bins(d)
    values=pd.Series([-1e9,edges['rsi'][0],1e9,np.nan])
    actual=bin_numbers(values,edges['rsi'])
    assert actual.iloc[:3].tolist()==[1,1,5]
    assert pd.isna(actual.iloc[3])
    tied=d.copy()
    tied['rsi']=50
    assert fit_bins(tied)['rsi']==[50]


def test_checkpoint_resume_interruption_and_corruption(tmp_path):
    folder=tmp_path/'stage'
    def failed(p):
        (p/'part.csv').write_text('partial')
        raise RuntimeError('interrupted')
    with pytest.raises(RuntimeError):
        checkpoint(folder,'identity',failed)
    assert not verify_marker(folder,'identity')
    calls=[]
    def complete(p):
        calls.append(1)
        (p/'part.csv').write_text('complete')
    assert checkpoint(folder,'identity',complete)=='COMPLETED'
    assert checkpoint(folder,'identity',complete)=='REUSED'
    assert calls==[1]
    with pytest.raises(ValueError,match='identity'):
        verify_marker(folder,'changed')
    (folder/'part.csv').write_text('corrupted')
    with pytest.raises(ValueError,match='checksum'):
        verify_marker(folder,'identity')


def test_holdout_is_sealed_without_frozen_hypotheses(tmp_path):
    runner=EntryRunner.__new__(EntryRunner)
    runner.base=tmp_path
    runner.identity='test'
    with pytest.raises(ValueError,match='sealed'):
        runner.labels('holdout')


def test_empty_artifact_schemas_and_research_outputs():
    d=fixture(80)
    f=decision_features(d,'X',ROOT)
    l=future_labels(d,f)
    full=f.merge(l,on=KEYS,validate='one_to_one')
    for module in MODULES:
        tables,edges=analyze_module(full.iloc[:0],module)
        assert all(len(t.columns)>0 for t in tables.values())
        assert tables['feature_bins'].empty
        hypotheses=hypothesis_rows(full.iloc[:0],module,tables,edges)
        result,groups=evaluate_hypotheses(full.iloc[:0],hypotheses,{module:edges})
        assert (result.final_status=='LOW SAMPLE').all()
        assert len(groups.columns)>0
    assert metrics(full.iloc[:0])['complete']==0


def test_mask_mismatch_rejected():
    d=fixture()
    d['long_active_module_mask']=128
    with pytest.raises(ValueError,match='mask'):
        cohorts(d,'breakout')


def test_complete_runner_and_rerun_preserve_hypotheses_and_outputs(tmp_path,monkeypatch):
    import src.entry_research_runner as runner_module
    from src.exit_research_runner import store_frame
    import hashlib
    monkeypatch.setattr(runner_module,'UNIVERSE',('X',))
    snapshot=tmp_path/'results/research_data'/runner_module.SNAPSHOT_SESSION
    snapshot.mkdir(parents=True)
    d=fixture(90)[['open','high','low','close','volume']]
    d.index=pd.date_range('2022-01-01',periods=90,freq='7D')
    path=snapshot/'X.csv'
    store_frame(path,d.rename_axis('timestamp').reset_index())
    symbols={'X':dict(status='completed',interval='1d',sha256=digest(path),
                     schema_sha256=digest(path.with_suffix('.schema.json')),
                     first_timestamp=str(d.index[0]),last_timestamp=str(d.index[-1]),rows=len(d))}
    snap=dict(status='completed',symbols=symbols,
              snapshot_id=hashlib.sha256(json.dumps(symbols,sort_keys=True).encode()).hexdigest())
    save_json(snapshot/'manifest.json',snap)
    (tmp_path/'results/EXIT_POLICY_MATRIX_V1.md').write_text('test fixture exit context')
    runner=EntryRunner(root=tmp_path)
    runner.run(list(MODULES))
    assert runner.state['status']=='COMPLETED'
    hypothesis=runner.base/'candidate_entry_hypotheses.csv'
    first=digest(hypothesis)
    matrix=runner.base/'ENTRY_RESEARCH_MATRIX_V1.md'
    matrix_hash=digest(matrix)
    registry=tmp_path/'results/entry_research_registry.csv'
    registry_bytes=registry.read_bytes()
    # Computation must be skipped on a compatible completed rerun.
    def unexpected(*args,**kwargs):
        raise AssertionError('Completed computation was repeated')
    monkeypatch.setattr(runner_module,'future_labels',unexpected)
    monkeypatch.setattr(runner_module,'analyze_module',unexpected)
    second=EntryRunner(root=tmp_path)
    second.run(list(MODULES))
    assert digest(hypothesis)==first and digest(matrix)==matrix_hash
    assert registry.read_bytes()==registry_bytes
    # A frozen file cannot silently be changed even when cache exists.
    hypothesis.write_text(hypothesis.read_text()+'\n')
    with pytest.raises(ValueError,match='hypothesis checksum'):
        second.labels('holdout')
