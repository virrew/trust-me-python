"""Compact operational paper scanner. Reuses V1 unchanged; never places orders.

Run under session_lock, including library use. `init` uses old frozen inputs only.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import uuid

import pandas as pd

from src import live_scanner as v1
from src.prospective_validation_data import OHLCV, NY, utc
from src.prospective_validation_storage import TABLES, canonical, combine, pack, unpack, project

PARENT = v1.ROOT / "results/prospective_validation/PV-V1-20261020"
SESSION = "PV-V2-20261020"
STORAGE_CONTRACT = {
    "version": 2,
    "primary": "Verified freeze + original seed + immutable linked event partitions",
    "tables": list(TABLES),
    "keys": {
        "bars": ["symbol", "timestamp"], "decisions": ["symbol", "timestamp"],
        "signals": ["signal_key"], "trade_events": ["event_key"],
        "lifecycle_states": ["trade_key", "bar_time"],
    },
    "events": {
        "ENTRY_FILLED": "Entry fields only, available at entry bar open",
        "EXIT_FILLED": "Closed lifecycle/accounting record; open or completed-bar availability",
        "EXECUTION_BAR": "Unchanged engine stop trace, observed at completed bar",
    },
    "decision_scope": "All 191 production diagnostics once per symbol/new bar; arm signals separate",
    "state": "Survived-close causal_path rows once per trade/bar; no future labels",
    "pending": "One atomic checksummed JSON checkpoint; completed symbols reused on resume",
    "publication": "All symbols required; atomic directory rename; sequence/hash chain",
    "partition": "NY invocation date / monotonically increasing run sequence",
    "cache": "Mutable open trades/cursors/latest pointer; reconstruct from seed and events",
    "replay": "V1 _symbol in temporary scratch; full replay CPU retained, snapshots discarded",
    "idempotency": "No newly observed bars => no new event partition",
}


def write_bundle(folder, tables):
    """Five CSVs and one consolidated schema; no per-symbol/arm evidence paths."""
    folder.mkdir(parents=True, exist_ok=True)
    schemas = {}
    for name, table in tables.items():
        payload = pack(table)
        v1.atomic_bytes(folder/f"{name}.csv", payload["csv"].encode())
        schemas[name] = payload["schema"]
    v1.save_json(folder/"schemas.json", schemas)


def read_table(folder, name):
    schemas = v1.read_json(folder/"schemas.json")
    return unpack(dict(csv=(folder/f"{name}.csv").read_text(), schema=schemas[name]))


def checkpoint_write(path, payload):
    v1.save_json(path, dict(payload=payload, sha256=v1.sha_bytes(canonical(payload))))


def checkpoint_read(path):
    envelope = v1.read_json(path)
    if envelope["sha256"] != v1.sha_bytes(canonical(envelope["payload"])):
        raise ValueError("Pending checkpoint checksum mismatch")
    return envelope["payload"]


def freeze(base, parent=PARENT, symbols=None, clock=v1.now):
    """Copy the actual V1 scientific definitions, never recreate candidates."""
    base, parent = Path(base), Path(parent)
    if (base/"freeze").exists():
        return PaperScannerV2(base).plan
    if (base/"events").exists() or (base/".checkpoint.json").exists():
        raise ValueError("Cannot freeze over existing evidence")
    parent_hash = (parent/"freeze/validation_plan.sha256").read_text().strip()
    v1.verify(parent/"freeze", parent_hash)
    original = v1.read_json(parent/"freeze/validation_plan.json")
    if v1.digest(parent/"freeze/validation_plan.json") != parent_hash:
        raise ValueError("Parent plan checksum mismatch")
    current_sources = v1.source_identity()
    if any(current_sources.get(p) != h for p, h in original["sources"].items()):
        raise ValueError("V1 scientific implementation changed; review required")
    symbols = original["symbols"] if symbols is None else list(symbols)
    if not symbols or len(set(symbols)) != len(symbols) or not set(symbols) <= set(original["symbols"]):
        raise ValueError("Invalid fixed universe")
    base.mkdir(parents=True, exist_ok=True)
    # Scratch freeze is valid before the old-seed-only schema probe; only the
    # final atomic publication can authorize a future real scan.
    with tempfile.TemporaryDirectory(prefix=".freeze-build-", dir=base) as work:
        probe = Path(work)
        frozen = probe/"freeze"
        frozen.mkdir()
        for name in ("candidates.json", "snapshot_manifest.json"):
            shutil.copyfile(parent/"freeze"/name, frozen/name)
        universe = [u for u in v1.read_json(parent/"freeze/universe.json") if u["symbol"] in symbols]
        v1.save_json(frozen/"universe.json", universe)
        for symbol in symbols:
            for suffix in (".csv", ".schema.json"):
                target = frozen/"seed"/(symbol+suffix)
                v1.atomic_bytes(target, (parent/"freeze/seed"/target.name).read_bytes())
        plan = copy.deepcopy(original)
        diff = subprocess.check_output(["git", "diff", "HEAD", "--binary"], cwd=v1.ROOT)
        v1.atomic_bytes(frozen/"working_tree.diff", diff)
        plan.update(
            version=2, session_id=base.name, frozen_at=clock(),
            parent_session=original["session_id"], parent_plan_sha256=parent_hash,
            parent_reproduction_commit="4ddd33c050273fec587e1172adffae4d6b1bd188",
            baseline_commit=subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=v1.ROOT, text=True).strip(),
            working_tree_status=subprocess.check_output(
                ["git", "status", "--porcelain=v1"], cwd=v1.ROOT, text=True),
            working_tree_diff_sha256=v1.sha_bytes(diff),
            sources=current_sources, runtime=v1.runtime_identity(), symbols=symbols,
            universe_sha256=v1.digest(frozen/"universe.json"),
            seed_sha256={str(p.relative_to(frozen)): v1.digest(p)
                         for p in sorted((frozen/"seed").glob("*"))},
            storage=STORAGE_CONTRACT,
        )

        def seal_plan():
            v1.save_json(frozen/"validation_plan.json", plan)
            identity = v1.digest(frozen/"validation_plan.json")
            v1.atomic_bytes(frozen/"validation_plan.sha256", (identity+"\n").encode())
            v1.seal(frozen, identity)

        seal_plan()
        scanner = PaperScannerV2(probe)
        symbol = symbols[0]
        seed, _ = scanner._previous(symbol, [])
        tables, trades, _ = scanner._compute(
            symbol, "catch-up", lambda _: seed, lambda: plan["frozen_at"], [])
        plan["table_schemas"] = {n: pack(t.iloc[:0])["schema"] for n, t in tables.items()}
        plan["trade_schema"] = pack(trades.iloc[:0])["schema"]
        # This timestamp, after all schema computation, is the V2 boundary.
        plan["frozen_at"] = utc(clock()).isoformat()
        seal_plan()
        os.rename(frozen, base/"freeze")
    return plan


class PaperScannerV2(v1.PaperScanner):
    """V1's tested computation adapter with V2-only storage and recovery."""

    def __init__(self, base):
        super().__init__(base)
        if self.plan["version"] != 2 or self.plan["storage"] != STORAGE_CONTRACT:
            raise ValueError("A distinct V2 protocol is required")

    @property
    def arms(self):
        return ([v1.BASELINE] + [f"REFERENCE-{m}" for m in self.plan["module_reference_policies"]]
                + [f"SHADOW-{c['module']}-{c['id']}" for c in self.plan["shadow_candidates"]])

    def runs(self):
        folders = list((self.base/"events").glob("*/*/*/*"))
        paths = sorted((p for p in folders if p.is_dir()), key=lambda p: p.name)
        previous = self.identity
        for i, folder in enumerate(paths, 1):
            if folder.name != f"{i:06d}":
                raise ValueError("Event chain has a missing sequence")
            marker = v1.verify(folder, self.identity)
            if marker["previous"] != previous:
                raise ValueError("Event chain mismatch")
            run = v1.read_json(folder/"run.json")
            if run["sequence"] != i or run["symbols"] != self.plan["symbols"]:
                raise ValueError("Incomplete universe or invalid run sequence")
            previous = v1.digest(folder/"completed.json")
        # Small append-only publication receipts detect loss of the ledger tail.
        # They are evidence, not the disposable state/latest_run.json cache.
        receipt = self.base/"publication.jsonl"
        lines = receipt.read_text().splitlines() if receipt.exists() else []
        if len(lines) > len(paths):
            raise ValueError("Published event partition was removed")
        for folder, line in zip(paths, lines):
            if json.loads(line) != dict(path=str(folder.relative_to(self.base)),
                                        sha256=v1.digest(folder/"completed.json")):
                raise ValueError("Publication receipt mismatch")
        if len(lines) < len(paths):
            # Adopt fully sealed orphan(s) after rename but before receipt/cache.
            lines += [json.dumps(dict(path=str(p.relative_to(self.base)),
                                      sha256=v1.digest(p/"completed.json")), sort_keys=True)
                      for p in paths[len(lines):]]
            v1.atomic_bytes(receipt, ("\n".join(lines)+"\n").encode())
        return paths

    def history(self, name, runs=None):
        runs = self.runs() if runs is None else runs
        if not runs:
            schema = self.plan["table_schemas"][name]
            return pd.DataFrame({c: pd.Series(dtype=t) for c, t in schema["dtypes"].items()})[
                schema["columns"]]
        result = combine(read_table(p, name) for p in runs)
        keys = self.plan["storage"]["keys"][name]
        if result.duplicated(keys).any():
            raise ValueError(f"Duplicate immutable {name} keys")
        return result

    def _previous(self, symbol, runs):
        seed = v1.load_frame(self.base/"freeze/seed"/f"{symbol}.csv").set_index("timestamp")
        if not runs:
            return seed, None
        # Run calls preload once to avoid rereading every partition per symbol.
        history = getattr(self, "_history", None)
        bars = history["bars"] if history is not None else self.history("bars", runs)
        decisions = history["decisions"] if history is not None else self.history("decisions", runs)
        bars = bars.loc[bars.symbol.eq(symbol)].set_index("timestamp")[OHLCV]
        observations = decisions.loc[decisions.symbol.eq(symbol)].drop(columns="symbol").set_index("timestamp")
        prices = pd.concat([seed, bars]) if len(bars) else seed
        return prices, observations if len(observations) else None

    def _compute(self, symbol, mode, loader, clock, runs):
        # The unmodified V1 implementation is the sole source of diagnostic,
        # replay, lifecycle and accounting semantics. Scratch never publishes.
        with tempfile.TemporaryDirectory(prefix="pv-v2-compute-") as work:
            folder = Path(work)
            super()._symbol(folder, symbol, mode, loader, clock, runs)
            decisions = v1.load_frame(folder/"new_decisions.csv")
            arms = {arm: {n: v1.load_frame(folder/arm/f"{n}.csv")
                          for n in ("trades", "states", "stop_path", "new_signals")}
                    for arm in self.arms}
            tables, trades = project(symbol, decisions, arms, self.plan["session_id"])
            return tables, trades, v1.read_json(folder/"metadata.json")

    def _checkpoint(self, request, completed):
        checkpoint_write(self.base/".checkpoint.json", dict(
            plan_sha256=self.identity, request=request, completed=completed))

    def _publish(self, tables, request, coverage, runs, clock):
        stage = self.base/".event-pending"
        if stage.exists():
            # Incomplete compact publication is never authoritative.
            shutil.rmtree(stage)
        write_bundle(stage, tables)
        v1.save_json(stage/"run.json", dict(
            **request, completed_at=utc(clock()).isoformat(), symbols=self.plan["symbols"],
            coverage=coverage, plan_sha256=self.identity,
            rows={n: len(t) for n, t in tables.items()}))
        previous = v1.digest(runs[-1]/"completed.json") if runs else self.identity
        v1.seal(stage, self.identity, previous=previous)
        date = utc(request["started_at"]).tz_convert(NY)
        destination = self.base/"events"/date.strftime("%Y/%m/%Y-%m-%d")/f"{request['sequence']:06d}"
        destination.parent.mkdir(parents=True, exist_ok=True)
        os.rename(stage, destination)

    def _write_state(self, trades, coverage, runs):
        state = self.base/"state"
        state.mkdir(exist_ok=True)
        # Closed records are already immutable EXIT_FILLED evidence.
        open_trades = trades.loc[~trades.closed].copy()
        write_bundle(state, {"open_trades": open_trades})
        v1.save_json(state/"cursors.json", {c["symbol"]: c for c in coverage})
        v1.save_json(state/"latest_run.json", dict(
            sequence=len(runs), sha256=v1.digest(runs[-1]/"completed.json") if runs else self.identity))
        v1.seal(state, self.identity)

    def recover(self):
        """Rebuild mutable state using only the original seed and verified ledger."""
        self.assert_identity()
        runs = self.runs()
        self._history = {n: self.history(n, runs) for n in ("bars", "decisions")}
        trades, coverage = [], []
        previous_meta = (v1.read_json(runs[-1]/"run.json")["coverage"] if runs else [])
        try:
            for symbol in self.plan["symbols"]:
                prices, _ = self._previous(symbol, runs)
                original_meta = next((c for c in previous_meta if c["symbol"] == symbol), None)
                observed = original_meta["observed_at"] if original_meta else self.plan["frozen_at"]
                _, t, metadata = self._compute(symbol, "update", lambda _: prices,
                                               lambda: observed, runs)
                trades.append(t)
                coverage.append(original_meta if original_meta else metadata)
            result = combine(trades)
            self._write_state(result, coverage, runs)
            return result
        finally:
            self._history = None

    def current_trades(self, runs):
        state = self.base/"state"
        expected = dict(sequence=len(runs),
                        sha256=v1.digest(runs[-1]/"completed.json") if runs else self.identity)
        try:
            v1.verify(state, self.identity)
            if v1.read_json(state/"latest_run.json") != expected:
                raise ValueError("Stale cache")
            opened = read_table(state, "open_trades")
        except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError):
            return self.recover()
        events = self.history("trade_events", runs)
        closed = events.loc[events.event_type.eq("EXIT_FILLED")].copy()
        schema = self.plan["trade_schema"]
        closed = closed[schema["columns"]]
        # Trade snapshots use original V1 keys; ledger keys include the session.
        closed["trade_key"] = closed.trade_key.str.removeprefix(self.plan["session_id"]+"|")
        for c, dtype in schema["dtypes"].items():
            closed[c] = closed[c].astype(dtype)
        return combine([closed, opened])

    def run(self, mode, loader=v1.yahoo_daily, clock=v1.now):
        if mode not in ("scan", "catch-up", "update", "resume"):
            raise ValueError("Unknown scanner mode")
        self.assert_identity()  # includes source/config/universe/candidate/cost gate
        runs = self.runs()
        checkpoint = self.base/".checkpoint.json"
        completed = {}
        if checkpoint.exists():
            saved = checkpoint_read(checkpoint)
            if saved["plan_sha256"] != self.identity:
                raise ValueError("Pending protocol mismatch")
            request, completed = saved["request"], saved["completed"]
            if request["sequence"] == len(runs) and runs:
                published = v1.read_json(runs[-1]/"run.json")
                if published["request_id"] != request["request_id"]:
                    raise ValueError("Pending publication mismatch")
                checkpoint.unlink()  # verified orphan already published
                return self.report()
            if request["sequence"] != len(runs)+1 or mode != "resume":
                raise ValueError("Interrupted run exists; use resume with matching sequence")
            mode = request["mode"]
        else:
            if mode == "resume":
                return self.report()
            request = dict(mode=mode, started_at=utc(clock()).isoformat(), sequence=len(runs)+1,
                           request_id=uuid.uuid4().hex)
            self._checkpoint(request, completed)
        self._history = {n: self.history(n, runs) for n in ("bars", "decisions")}
        try:
            if set(completed) - set(self.plan["symbols"]):
                raise ValueError("Unexpected pending symbol")
            for symbol in self.plan["symbols"]:
                if symbol in completed:
                    continue
                try:
                    tables, trades, metadata = self._compute(symbol, mode, loader, clock, runs)
                    # Only new evidence + open state in the checkpoint, never seed/full histories.
                    completed[symbol] = dict(tables={n: pack(t) for n, t in tables.items()},
                                             open_trades=pack(trades.loc[~trades.closed]),
                                             metadata=metadata)
                    self._checkpoint(request, completed)
                except Exception as exc:
                    v1.save_json(self.base/"failures"/f"{request['request_id']}-{symbol}.json",
                                 dict(error=f"{type(exc).__name__}: {exc}", published=False,
                                      observed_at=utc(clock()).isoformat(), symbol=symbol))
                    raise
            tables = {n: combine(unpack(completed[s]["tables"][n]) for s in self.plan["symbols"])
                      for n in TABLES}
            coverage = [completed[s]["metadata"] for s in self.plan["symbols"]]
            if any(len(t) for t in tables.values()):
                for n, table in tables.items():
                    if list(table) != self.plan["table_schemas"][n]["columns"]:
                        raise ValueError(f"Frozen schema mismatch: {n}")
                    if table.duplicated(self.plan["storage"]["keys"][n]).any():
                        raise ValueError(f"Duplicate run keys: {n}")
                self._publish(tables, request, coverage, runs, clock)
                runs = self.runs()
                # No-new-data invocations must not introduce an unrecorded
                # as-of clock into the reconstructible state.
                opened = combine(unpack(completed[s]["open_trades"]) for s in self.plan["symbols"])
                self._write_state(opened, coverage, runs)
            checkpoint.unlink()
        finally:
            self._history = None
        return self.report()

    def report(self):
        self.assert_identity()
        runs = self.runs()
        trades = self.current_trades(runs)
        for name, table in v1.evaluation(trades, sorted(self.arms), self.plan["cost_assumptions"]).items():
            v1.store_frame(self.base/"reports/latest"/f"{name}.csv", table)
        signals = self.history("signals", runs)
        counts = {}
        for evidence in v1.EVIDENCE:
            t = trades.loc[trades.arm.eq(v1.BASELINE) & trades.evidence_class.eq(evidence)]
            counts[evidence] = dict(
                signals=int((signals.arm.eq(v1.BASELINE) & signals.evidence_class.eq(evidence)).sum()),
                fills=len(t), closed=int(t.closed.sum()))
        report = dict(session_id=self.plan["session_id"], plan_sha256=self.identity,
                      frozen_at=self.plan["frozen_at"], universe_size=len(self.plan["symbols"]),
                      completed_runs=len(runs), incomplete_run=(self.base/".checkpoint.json").exists(),
                      baseline_counts=counts,
                      coverage=list(v1.read_json(self.base/"state/cursors.json").values()),
                      status="AWAITING_VALIDATION_DATA" if not runs else "LOW_SAMPLE_OR_DESCRIPTIVE_ONLY")
        v1.save_json(self.base/"reports/latest/report.json", report)
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("init", "scan", "catch-up", "update", "resume", "recover", "report"))
    parser.add_argument("--session", default=SESSION)
    parser.add_argument("--input-dir", type=Path)
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9-]+", args.session):
        parser.error("Invalid session name")
    base = v1.ROOT/"results/prospective_validation"/args.session
    with v1.session_lock(base):
        if args.command == "init":
            freeze(base)
        scanner = PaperScannerV2(base)
        loader = v1.yahoo_daily if args.input_dir is None else (
            lambda symbol: v1.load_frame(args.input_dir/f"{symbol}.csv").set_index("timestamp"))
        if args.command == "recover":
            scanner.recover()
        report = (scanner.report() if args.command in ("init", "report", "recover")
                  else scanner.run(args.command, loader))
        print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
