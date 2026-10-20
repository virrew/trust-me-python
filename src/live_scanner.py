"""Prospective Validation + Paper Scanner V1; no broker or strategy overrides.

python -m src.live_scanner init
python -m src.live_scanner scan
python -m src.live_scanner catch-up
python -m src.live_scanner update
python -m src.live_scanner resume
python -m src.live_scanner report
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import inspect
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid
import warnings

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from src.backtest import run_swing_backtest_with_reconciliation
from src.diagnostics_signals import signal_diagnostics
from src.exit_research_runner import (
    ROOT, UNIVERSE, DEFAULT_SESSION as SNAPSHOT, DEFAULT_END_BEFORE,
    atomic_bytes, digest, save_json, now, validate_ohlcv,
)
from src.prospective_validation_analysis import COSTS, EVIDENCE, METRIC_DEFINITION, account, evaluation
from src.prospective_validation_data import (
    completed_daily, append_daily, daily_clock, utc, evidence_class, yahoo_daily,
    store_frame, load_frame,
)
from src.strategy_improvement_analysis import causal_path
from src.strategy_improvement_execution import research_stream, replay
from src.trade_lifecycle import trade_lifecycle_diagnostics
from src.win_rate_research_runner import POLICIES

SESSION = "PV-V1-20261020"
CANDIDATE_DIR = "results/strategy_improvement/SI-V1-20260930"
SNAPSHOT_DIR = f"results/research_data/{SNAPSHOT}"
BASELINE = "BASELINE"
META_COLUMNS = ["evidence_class", "observed_at", "available_at_utc"]


def read_json(path):
    return json.loads(Path(path).read_text())


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def source_identity():
    paths = sorted((ROOT/"src").glob("*.py")) + [
        ROOT/"reference/trust_me_strategy.pine",
        ROOT/"reference/RESEARCH_EXECUTION_CONTRACT.md", ROOT/"requirements.txt"]
    return {str(p.relative_to(ROOT)): digest(p) for p in paths}


def runtime_identity():
    import yfinance
    return dict(python=sys.version, pandas=pd.__version__, numpy=np.__version__,
                yfinance=yfinance.__version__)


def seal(folder, identity, **metadata):
    files = {str(p.relative_to(folder)): digest(p) for p in sorted(folder.rglob("*"))
             if p.is_file() and p != folder/"completed.json" and not p.name.startswith(".pending-")}
    save_json(folder/"completed.json", dict(identity=identity, hashes=files, **metadata))


def verify(folder, identity):
    record = read_json(folder/"completed.json")
    if record["identity"] != identity:
        raise ValueError(f"Artifact identity mismatch: {folder}")
    actual = {str(p.relative_to(folder)) for p in folder.rglob("*")
              if p.is_file() and p != folder/"completed.json" and not p.name.startswith(".pending-")}
    if actual != set(record["hashes"]):
        raise ValueError(f"Artifact inventory mismatch: {folder}")
    for name, expected in record["hashes"].items():
        if digest(folder/name) != expected:
            raise ValueError(f"Corrupt artifact: {folder/name}")
    return record


@contextmanager
def session_lock(base):
    base.mkdir(parents=True, exist_ok=True)
    with (base/".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def freeze(base, root=ROOT, symbols=UNIVERSE):
    """Only old snapshot and research identities are read; no provider is called."""
    base, root = Path(base), Path(root)
    if (base/"freeze").exists():
        return PaperScanner(base).plan
    if (base/"runs").exists():
        raise ValueError("Cannot freeze over existing evidence")
    symbols = list(symbols)
    if not symbols or len(set(symbols)) != len(symbols) or any(
            not re.fullmatch(r"[A-Z][A-Z0-9.-]*", s) for s in symbols):
        raise ValueError("Invalid fixed universe")
    snapshot = root/SNAPSHOT_DIR
    manifest = read_json(snapshot/"manifest.json")
    if manifest["status"] != "completed" or manifest["cutoff"] != DEFAULT_END_BEFORE:
        raise ValueError("Canonical pre-validation snapshot required")
    candidate_path = root/CANDIDATE_DIR/"candidate_strategy_improvements.json"
    candidate_sha = digest(candidate_path)
    if candidate_sha != (candidate_path.with_suffix(".sha256")).read_text().strip():
        raise ValueError("Frozen candidate checksum mismatch")
    candidates = read_json(candidate_path)["candidates"]
    # Exercise supported identities without touching any new data.
    for c in candidates:
        if c["module"] not in POLICIES or c["id"] not in ("giveback", "stalled", "adaptive", "relax_price"):
            raise ValueError("Unsupported frozen candidate; do not reinterpret")
    staging = base/".freeze-pending"
    staging.mkdir(parents=True, exist_ok=True)
    for symbol in symbols:
        item = manifest["symbols"][symbol]
        for suffix, key in ((".csv", "sha256"), (".schema.json", "schema_sha256")):
            original = snapshot/(symbol+suffix)
            if digest(original) != item[key]:
                raise ValueError("Old snapshot checksum mismatch")
            atomic_bytes(staging/"seed"/(symbol+suffix), original.read_bytes())
        frame = load_frame(staging/"seed"/f"{symbol}.csv").set_index("timestamp")
        validate_ohlcv(frame)
        if frame.index.max() >= pd.Timestamp(DEFAULT_END_BEFORE, tz=frame.index.tz):
            raise ValueError("Seed contains post-snapshot outcomes")
    atomic_bytes(staging/"candidates.json", candidate_path.read_bytes())
    atomic_bytes(staging/"snapshot_manifest.json", (snapshot/"manifest.json").read_bytes())
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    status = subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=ROOT, text=True)
    diff = subprocess.check_output(["git", "diff", "HEAD", "--binary"], cwd=ROOT)
    atomic_bytes(staging/"working_tree.diff", diff)
    universe = [dict(symbol=s, universe_version="PV-UNIVERSE-V1",
                     inclusion_source=f"{SNAPSHOT}: existing research universe, no performance selection",
                     first_eligible_validation_date=DEFAULT_END_BEFORE) for s in symbols]
    save_json(staging/"universe.json", universe)
    plan = dict(
        version=1, session_id=base.name, frozen_at=now(),
        old_cutoff_exclusive=DEFAULT_END_BEFORE, baseline_commit=head,
        working_tree_status=status, working_tree_diff_sha256=sha_bytes(diff),
        sources=source_identity(), runtime=runtime_identity(),
        diagnostics_config={k: p.default for k, p in inspect.signature(signal_diagnostics).parameters.items()
                            if p.default is not inspect.Parameter.empty},
        baseline_execution=dict(atr_multiplier=2.5, use_locked_atr=False, use_trend_exit=True),
        module_reference_policies=POLICIES,
        universe_version="PV-UNIVERSE-V1", symbols=symbols,
        universe_sha256=digest(staging/"universe.json"),
        candidate_sha256=candidate_sha, shadow_candidates=candidates,
        seed_sha256={str(p.relative_to(staging)): digest(p) for p in sorted((staging/"seed").glob("*"))},
        cost_assumptions=COSTS, metrics=METRIC_DEFINITION,
        data_contract="Original seed retained; append unadjusted Yahoo Daily OHLCV. "
                      "Completed at NY 16:15 conservatively even on early-close days. "
                      "Naive or America/New_York midnight session labels only. "
                      "Changed/missing previously observed validation bars fail closed.",
        population_contract="Signal availability before freeze is TEMPORAL_OOS_LATER_UNSEEN. "
                            "PROSPECTIVE_PAPER requires scan-mode persisted observation after freeze "
                            "on a session date strictly after the freeze's NY date "
                            "and before next calendar day 09:30 NY; missed bars are excluded backfill. "
                            "Eligibility is frozen at first observation, never upgraded on rerun.",
        execution_contract="All streams start flat at cutoff; one position per symbol/arm; "
                           "baseline broad production Long stream; separate pure module references "
                           "and exact frozen shadows. No portfolio or live orders. "
                           "Existing engines replay only persisted eligible signals. "
                           "Open positions are observed-prefix censored, updated in new artifacts.",
        monitoring="Gross/net metrics by signal evidence class, arm and cost. No pooling or promotion. "
                   "Review after >=100 closed trades per arm/class; low sample stays low sample. "
                   "No parameter changes or ML from this protocol.",
        historical_context=f"{CANDIDATE_DIR}/STRATEGY_IMPROVEMENT_MATRIX_V1.md; "
                           "already-used history; never pooled with validation",
        behavior_change="YES", existing_strategy_behavior_changed="NO",
    )
    save_json(staging/"validation_plan.json", plan)
    identity = digest(staging/"validation_plan.json")
    atomic_bytes(staging/"validation_plan.sha256", (identity+"\n").encode())
    seal(staging, identity)
    # One atomic publication is the data-access gate. No unsealed freeze counts.
    os.rename(staging, base/"freeze")
    return plan


class PaperScanner:
    def __init__(self, base):
        self.base = Path(base)
        frozen = self.base/"freeze"
        self.identity = (frozen/"validation_plan.sha256").read_text().strip()
        verify(frozen, self.identity)
        if digest(frozen/"validation_plan.json") != self.identity:
            raise ValueError("Plan checksum mismatch")
        self.plan = read_json(frozen/"validation_plan.json")
        self.assert_identity()

    def assert_identity(self):
        verify(self.base/"freeze", self.identity)
        if self.plan != read_json(self.base/"freeze/validation_plan.json"):
            raise ValueError("In-memory plan differs from frozen configuration")
        if self.plan["sources"] != source_identity() or self.plan["runtime"] != runtime_identity():
            raise ValueError("Source/runtime changed; refusing mixed validation versions")

    def runs(self):
        paths = sorted((self.base/"runs").glob("[0-9]*"))
        previous = self.identity
        for i, folder in enumerate(paths, 1):
            if folder.name != f"{i:06d}":
                raise ValueError("Run chain has a missing sequence")
            marker = verify(folder, self.identity)
            if marker["previous"] != previous:
                raise ValueError("Run chain mismatch")
            previous = digest(folder/"completed.json")
        head = self.base/"head.json"
        if head.exists():
            stored = read_json(head)
            if stored["sequence"] > len(paths):
                raise ValueError("Committed run was removed")
            if stored["sequence"] and digest(paths[stored["sequence"]-1]/"completed.json") != stored["sha256"]:
                raise ValueError("Committed head changed")
        # A rename completed just before an interruption is a verified orphan;
        # adopt it without repeating data access or losing its observations.
        if paths:
            save_json(head, dict(sequence=len(paths), sha256=previous))
        return paths

    def _previous(self, symbol, runs):
        if runs:
            folder = runs[-1]/symbol
            return (load_frame(folder/"prices.csv").set_index("timestamp"),
                    load_frame(folder/"observations.csv").set_index("timestamp"))
        seed = load_frame(self.base/"freeze/seed"/f"{symbol}.csv").set_index("timestamp")
        return seed, None

    def _symbol(self, folder, symbol, mode, loader, clock, runs):
        self.assert_identity()  # gate BEFORE loader (including imported files)
        previous, observations = self._previous(symbol, runs)
        incoming = loader(symbol)
        observed = utc(clock())
        if observed < utc(self.plan["frozen_at"]):
            raise ValueError("Observation predates freeze")
        store_frame(folder/"received_prices.csv", incoming.rename_axis("timestamp").reset_index())
        incoming = completed_daily(incoming, observed)
        prices = append_daily(previous, incoming, self.plan["old_cutoff_exclusive"])
        with warnings.catch_warnings():
            # Existing diagnostics builds 191 columns incrementally. This known
            # performance warning says nothing about values; do not change core.
            warnings.simplefilter("ignore", pd.errors.PerformanceWarning)
            full = signal_diagnostics(prices, **self.plan["diagnostics_config"])
        observed = utc(clock())  # decision clock after diagnostic computation
        d = full
        boundary = pd.Timestamp(self.plan["old_cutoff_exclusive"], tz=d.index.tz)
        d = d.loc[d.index >= boundary].copy()
        meta = pd.DataFrame(index=d.index)
        meta["evidence_class"] = pd.Series(
            [evidence_class(t, self.plan["frozen_at"], observed, mode, d.index[-1])
             for t in d.index], index=d.index, dtype=object)
        meta["observed_at"] = observed.isoformat()
        meta["available_at_utc"] = pd.Series(
            [daily_clock(t, 16, 15).isoformat() for t in d.index], index=d.index, dtype=object)
        if observations is not None:
            common = observations.index
            assert_frame_equal(d.loc[common], observations.loc[common, d.columns],
                               check_freq=False, check_exact=True)
            meta.loc[common, META_COLUMNS] = observations.loc[common, META_COLUMNS]
        decision = pd.concat([d, meta], axis=1)
        store_frame(folder/"prices.csv", prices.rename_axis("timestamp").reset_index())
        store_frame(folder/"observations.csv", decision.rename_axis("timestamp").reset_index())
        # Current snapshot includes no-signal symbols and every existing diagnostic column.
        latest = decision.tail(1).copy()
        if latest.empty:
            latest = full.tail(1).assign(evidence_class="HISTORICAL_RESEARCH_CONTEXT",
                                        observed_at=observed.isoformat())
            latest["available_at_utc"] = [daily_clock(t, 16, 15).isoformat() for t in latest.index]
        latest["scan_run_at"] = observed.isoformat()
        latest["strategy_sha256"] = self.plan["sources"]["src/trust_me_core.py"]
        latest["plan_sha256"] = self.identity
        latest["universe_version"] = self.plan["universe_version"]
        store_frame(folder/"latest.csv", latest.rename_axis("timestamp").reset_index())
        old_index = observations.index if observations is not None else d.index[:0]
        fresh = decision.loc[~decision.index.isin(old_index)]
        store_frame(folder/"new_decisions.csv", fresh.rename_axis("timestamp").reset_index())
        eligible = decision.evidence_class.isin(EVIDENCE)
        specs = [(BASELINE, None, None)]
        specs += [(f"REFERENCE-{m}", m, None) for m in POLICIES]
        specs += [(f"SHADOW-{c['module']}-{c['id']}", c["module"], c)
                  for c in self.plan["shadow_candidates"]]
        for arm, module, candidate in specs:
            entry_rule = candidate["entry_rule"] if candidate else None
            stream = research_stream(d, module, entry_rule) if module else d.copy()
            if "research_signal_source" not in stream:
                stream["research_signal_source"] = "PRODUCTION_FINAL_SIGNAL"
            stream["long_signal"] &= eligible
            stream["short_signal"] &= eligible
            settings = (self.plan["module_reference_policies"][module] if module
                        else self.plan["baseline_execution"])
            result, reconciliation = (replay(stream, settings, candidate["exit_rule"]) if candidate else
                                      run_swing_backtest_with_reconciliation(stream, **settings))
            life = trade_lifecycle_diagnostics(stream, result)["trade_lifecycle"]
            # Post-exit observations are outside this protocol, never mixed into state features.
            life = life.drop(columns=[c for c in life if c.startswith("post_exit_")])
            life = life.merge(meta, left_on="signal_time", right_index=True, how="left", validate="many_to_one")
            life["status"] = np.where(life.closed, "CLOSED", "OPEN")
            life["as_of_observed_at"] = observed.isoformat()
            life["entry_available_at_utc"] = life.entry_time.map(
                lambda t: daily_clock(t, 9, 30).isoformat()).astype(object)
            life["exit_observation_available_at"] = life.exit_timing.map({
                "OPEN": "exit bar open", "INTRABAR_STOP": "exit occurred intrabar; confirmed by completed Daily bar",
                "CENSORED": "not yet observed"})
            life["trade_key"] = pd.Series(
                [f"{symbol}|{arm}|{t.isoformat()}|{direction}"
                 for t, direction in zip(life.signal_time, life.direction)], index=life.index, dtype=object)
            life["research_signal_source"] = life.signal_time.map(stream.research_signal_source)
            life = account(life, self.plan["cost_assumptions"])
            states = causal_path(stream, result).merge(
                result.trades[["trade_id", "signal_time"]], on="trade_id", validate="many_to_one")
            states["as_of_observed_at"] = observed.isoformat()
            states["evidence_class"] = states.signal_time.map(meta.evidence_class).astype(object)
            states["state_first_observed_at"] = states.bar_time.map(meta.observed_at).astype(object)
            states["state_collection_class"] = states.bar_time.map(meta.evidence_class).astype(object)
            states["trade_key"] = states.signal_time.map(
                lambda t: f"{symbol}|{arm}|{t.isoformat()}|Long").astype(object)
            # State clocks describe actual persisted observation, not a fabricated past scan.
            states["bar_available_at_utc"] = states.bar_time.map(
                lambda t: daily_clock(t, 16, 15).isoformat()).astype(object)
            for name, table in (("trades", life), ("states", states), ("stop_path", result.state),
                                ("reconciliation", reconciliation)):
                table = table.assign(symbol=symbol, arm=arm)
                store_frame(folder/arm/f"{name}.csv", table)
            signals = stream.loc[stream.long_signal | stream.short_signal].copy()
            signals = signals.join(meta)
            signals["signal_key"] = pd.Series(
                [f"{symbol}|{arm}|{t.isoformat()}|Long" for t in signals.index], index=signals.index, dtype=object)
            signals["direction"] = "Long"
            signals["symbol"], signals["arm"] = symbol, arm
            new_signals = signals.loc[~signals.index.isin(old_index)]
            store_frame(folder/arm/"new_signals.csv", new_signals.rename_axis("signal_time").reset_index())
        save_json(folder/"metadata.json", dict(symbol=symbol, observed_at=observed.isoformat(),
                  latest_completed_bar=prices.index[-1].isoformat(), mode=mode,
                  data_sha256=digest(folder/"prices.csv"), plan_sha256=self.identity,
                  bars=len(prices), validation_bars=len(d), new_decisions=len(fresh),
                  backfill_bars=int(decision.evidence_class.eq(
                      "POST_FREEZE_BACKFILL_NOT_PROSPECTIVE").sum())))
        seal(folder, self.identity)

    def run(self, mode, loader=yahoo_daily, clock=now):
        if mode not in ("scan", "catch-up", "update", "resume"):
            raise ValueError("Unknown scanner mode")
        self.assert_identity()
        runs = self.runs()
        pending = self.base/".run-pending"
        if pending.exists():
            request = read_json(pending/"request.json")
            if digest(pending/"request.json") != (pending/"request.sha256").read_text().strip():
                raise ValueError("Interrupted request checksum mismatch")
            if mode != "resume":
                raise ValueError("Interrupted run exists; use resume")
            mode = request["mode"]
            if request["sequence"] != len(runs)+1:
                raise ValueError("Interrupted run sequence mismatch")
        else:
            if mode == "resume":
                return self.report()
            pending.mkdir()
            save_json(pending/"request.json", dict(mode=mode, started_at=clock(), sequence=len(runs)+1))
            atomic_bytes(pending/"request.sha256", (digest(pending/"request.json")+"\n").encode())
        for symbol in self.plan["symbols"]:
            folder = pending/symbol
            if (folder/"completed.json").exists():
                verify(folder, self.identity)
                continue
            if folder.exists():
                abandoned = self.base/"failures"/f"interrupted-{symbol}-{uuid.uuid4().hex}"
                abandoned.parent.mkdir(exist_ok=True)
                os.rename(folder, abandoned)
            folder.mkdir(exist_ok=True)
            try:
                self._symbol(folder, symbol, mode, loader, clock, runs)
            except Exception as exc:
                save_json(self.base/"failures"/f"{uuid.uuid4().hex}.json",
                          dict(symbol=symbol, observed_at=clock(), mode=mode,
                               error=f"{type(exc).__name__}: {exc}", published=False))
                raise
        # All symbols must succeed. A partial universe is never silently published.
        arms = [p.name for p in (pending/self.plan["symbols"][0]).iterdir() if p.is_dir()]
        trades = pd.concat([load_frame(pending/s/arm/"trades.csv")
                            for s in self.plan["symbols"] for arm in sorted(arms)], ignore_index=True)
        for name, table in evaluation(trades, sorted(arms), self.plan["cost_assumptions"]).items():
            store_frame(pending/f"{name}.csv", table)
        previous = digest(runs[-1]/"completed.json") if runs else self.identity
        seal(pending, self.identity, previous=previous, completed_at=clock())
        destination = self.base/"runs"/f"{len(runs)+1:06d}"
        destination.parent.mkdir(exist_ok=True)
        os.rename(pending, destination)
        self.runs()
        return self.report()

    def report(self):
        self.assert_identity()
        runs = self.runs()
        counts = {e: dict(signals=0, fills=0, closed=0) for e in EVIDENCE}
        for run in runs:
            for symbol in self.plan["symbols"]:
                signals = load_frame(run/symbol/BASELINE/"new_signals.csv")
                for e in EVIDENCE:
                    counts[e]["signals"] += int(signals.evidence_class.eq(e).sum())
        coverage = []
        if runs:
            for symbol in self.plan["symbols"]:
                folder = runs[-1]/symbol
                coverage.append(read_json(folder/"metadata.json"))
                trades = load_frame(folder/BASELINE/"trades.csv")
                for e in EVIDENCE:
                    part = trades.loc[trades.evidence_class.eq(e)]
                    counts[e]["fills"] += len(part)
                    counts[e]["closed"] += int(part.closed.sum())
        return dict(session_id=self.plan["session_id"], plan_sha256=self.identity,
                    frozen_at=self.plan["frozen_at"], universe_size=len(self.plan["symbols"]),
                    completed_runs=len(runs), incomplete_run=(self.base/".run-pending").exists(),
                    baseline_counts=counts, coverage=coverage,
                    evaluation_path=str(runs[-1]/"evaluation.csv") if runs else None,
                    status=("AWAITING_VALIDATION_DATA" if not coverage or not any(
                        c["validation_bars"] for c in coverage) else "LOW_SAMPLE_OR_DESCRIPTIVE_ONLY"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("init", "scan", "catch-up", "update", "resume", "report"))
    parser.add_argument("--session", default=SESSION)
    parser.add_argument("--input-dir", type=Path,
                        help="Import symbol.csv plus schema sidecars instead of fetching Yahoo; gate checked first")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9-]+", args.session):
        parser.error("Invalid session name")
    base = ROOT/"results/prospective_validation"/args.session
    with session_lock(base):
        if args.command == "init":
            freeze(base)
        scanner = PaperScanner(base)
        loader = yahoo_daily
        if args.input_dir:
            loader = lambda symbol: load_frame(args.input_dir/f"{symbol}.csv").set_index("timestamp")
        report = (scanner.report() if args.command in ("init", "report")
                  else scanner.run(args.command, loader=loader))
        print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
