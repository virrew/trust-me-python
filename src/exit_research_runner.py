"""Finite, resumable Pure Breakout/Squeeze exit research (research only).

python -m src.exit_research_runner --remaining
python -m src.exit_research_runner --module breakout
python -m src.exit_research_runner --freeze

The default session is persistent. An explicit --session starts a separately
identified snapshot; existing completed outputs are immutable and hash checked.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import fcntl
import hashlib
import io
import inspect
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import traceback
import warnings

import numpy as np
import pandas as pd

from src.ab_rule_testing import PAIRED_SCHEMA, _paired, _risk_enriched, _validated_configs
from src.backtest import RECONCILIATION_SCHEMA, run_swing_backtest_with_reconciliation
from src.diagnostics_signals import signal_diagnostics
from src.exit_research_analysis import arm_metrics, comparison_tables, summarize, supported_winner
from src.market_data import download_yahoo_data
from src.strategy_evaluation import MODULE_BITS
from src.trade_lifecycle import trade_lifecycle_diagnostics

ROOT = Path(__file__).resolve().parents[1]
UNIVERSE = tuple("NVDA AMD MU AVGO MRVL QCOM ARM SMCI TSM ASML AAPL MSFT GOOGL META AMZN NFLX ORCL CRM NOW PLTR TSLA COIN HOOD ROKU SHOP UBER ABNB CRWD PANW DDOG JPM GS MS BAC V MA CAT GE DE ETN HON RTX XOM CVX COP LLY COST WMT HD NKE".split())
GRID = (1.5, 1.75, 2.0, 2.25, 2.5, 3.0)
DEFAULT_SESSION = "EXIT-V1-20260923-CLOSED"
DEFAULT_END_BEFORE = "2026-09-22"
MODULES = {"breakout": "Breakout", "squeeze": "Squeeze"}
FAILURE_COLUMNS = ["symbol", "stage", "attempt", "retry_attempted", "error"]
PLAN_VERSION = 1
SOURCE_FILES = ("src/market_data.py", "src/trust_me_core.py", "src/diagnostics_context.py",
                "src/diagnostics_signals.py", "src/backtest.py", "src/ab_rule_testing.py",
                "src/trade_lifecycle.py", "src/strategy_evaluation.py",
                "src/exit_research_analysis.py", "src/exit_research_runner.py",
                "reference/RESEARCH_EXECUTION_CONTRACT.md")


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_bytes(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".pending-", delete=False) as f:
        temp = Path(f.name)
        f.write(content)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp, path)


def save_json(path, data):
    atomic_bytes(path, (json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n").encode())


def save_csv(path, frame):
    atomic_bytes(path, frame.to_csv(index=False).encode())


def store_frame(path, frame):
    """CSV plus explicit dtypes: no executable pickle; float round-trip fidelity."""
    path = Path(path)
    save_csv(path, frame)
    save_json(path.with_suffix(".schema.json"), dict(
        dtypes={c: str(t) for c, t in frame.dtypes.items()},
        object_none={c: [i for i, value in enumerate(frame[c]) if value is None]
                     for c in frame.columns if frame[c].dtype == object}))


def load_frame(path):
    path = Path(path)
    frame = pd.read_csv(path, float_precision="round_trip")
    schema = json.loads(path.with_suffix(".schema.json").read_text())
    for col, dtype in schema["dtypes"].items():
        if dtype.startswith("datetime64"):
            frame[col] = pd.to_datetime(frame[col], utc="," in dtype)
        frame[col] = frame[col].astype(dtype)
    for col, offsets in schema["object_none"].items():
        for offset in offsets:
            frame.iat[offset, frame.columns.get_loc(col)] = None
    return frame


def config(multiplier=2.5, trend=True, locked=False):
    if multiplier not in GRID or type(trend) is not bool or type(locked) is not bool:
        raise ValueError("Only predefined multipliers and boolean exit dimensions are allowed")
    return dict(atr_multiplier=float(multiplier), use_locked_atr=locked, use_trend_exit=trend)


def config_key(c):
    config(c["atr_multiplier"], c["use_trend_exit"], c["use_locked_atr"])
    return f"ATR{c['atr_multiplier']:g}-{'LOCKED' if c['use_locked_atr'] else 'DYNAMIC'}-TREND{'ON' if c['use_trend_exit'] else 'OFF'}"


def pure_diagnostics(diagnostics, module):
    """Gate only the research stream; preserve bars, modules, scores and NaNs."""
    bit = MODULE_BITS[MODULES[module]]
    columns = ("pullback_long", "breakout_long", "squeeze_long", "mean_rev_long")
    expected = sum(diagnostics[c].astype(int) * b for c, b in zip(columns, (1, 2, 4, 8)))
    if not expected.equals(diagnostics.long_active_module_mask.astype(int)):
        raise ValueError("Module columns disagree with active module mask")
    result = diagnostics.copy(deep=True)
    result["long_signal"] = diagnostics.long_signal & (diagnostics.long_active_module_mask == bit)
    result["short_signal"] = False
    return result


def execute_arm(diagnostics, settings):
    """The same execution/lifecycle calls used by evaluate_strategy and A/B.

    Unused opportunity/horizon reports are deliberately not recomputed per exit.
    Regression tests compare every paired column against run_ab_rule_test.
    """
    config_key(settings)
    result, reconciliation = run_swing_backtest_with_reconciliation(diagnostics, **settings)
    life = trade_lifecycle_diagnostics(diagnostics, result, post_exit_horizon=20)
    return {"signal_fill_reconciliation": reconciliation,
            "ab_trade_lifecycle": _risk_enriched(life["trade_lifecycle"])}


def grid_pairs():
    return sorted({tuple(sorted((2.5, m))) for m in GRID if m != 2.5}
                  | set(zip(GRID[:-1], GRID[1:])))


def validate_ohlcv(frame):
    if (frame.empty or not isinstance(frame.index, pd.DatetimeIndex)
            or not frame.index.is_unique or not frame.index.is_monotonic_increasing
            or frame.index.hasnans):
        raise ValueError("Snapshot requires nonempty unique increasing dated OHLCV")
    values = frame[["open", "high", "low", "close", "volume"]]
    if not np.isfinite(values.to_numpy(dtype=float)).all():
        raise ValueError("Nonfinite OHLCV; no imputation allowed")
    if ((values[["open", "high", "low", "close"]] <= 0).any().any()
            or (values.volume < 0).any()
            or (values.high < values[["open", "close", "low"]].max(axis=1)).any()
            or (values.low > values[["open", "close", "high"]].min(axis=1)).any()):
        raise ValueError("Invalid OHLCV price/volume relationships")


def download_one(symbol, target, cutoff):
    import yfinance as yf
    with tempfile.TemporaryDirectory(prefix="exit-yahoo-") as cache:
        yf.set_tz_cache_location(cache)
        frame = download_yahoo_data(symbol, period="5y", interval="1d")
    # Discard today's possibly incomplete session, regardless of download hour.
    dates = frame.index.tz_localize(None) if frame.index.tz is not None else frame.index
    frame = frame.loc[(dates < pd.Timestamp(cutoff)) &
                      (dates >= pd.Timestamp(cutoff) - pd.DateOffset(years=5))]
    validate_ohlcv(frame)
    store_frame(target, frame.rename_axis("timestamp").reset_index())


def append_registry(path, row):
    """Preserve every historical byte; atomic append and duplicate-ID rejection."""
    path = Path(path)
    original = path.read_bytes()
    entries = list(csv.DictReader(io.StringIO(original.decode())))
    fields = next(csv.reader(io.StringIO(original.decode())))
    existing = [e for e in entries if e["experiment_id"] == row["experiment_id"]]
    if existing:
        if any(e["result_path"] != row["result_path"] or
               e["baseline_config"] != row["baseline_config"] or
               e["variant_config"] != row["variant_config"] for e in existing):
            raise ValueError("Registry ID collision")
        return False
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
    writer.writerow(row)
    atomic_bytes(path, original + (b"" if original.endswith(b"\n") else b"\n") + stream.getvalue().encode())
    return True


def inventory(root):
    registered = pd.read_csv(root / "results/research_registry.csv")
    ids = set(registered.experiment_id)
    rows = []
    for folder in sorted((root / "results/ab_tests").iterdir()):
        if not folder.is_dir() or folder.name.startswith((".", "_")):
            continue
        files = sorted(folder.glob("*.csv"))
        paired = folder / "paired_signals.csv"
        if not paired.exists():
            paired = folder / "paired_signals_with_module.csv"
        count = len(pd.read_csv(paired)) if paired.exists() else 0
        historical = "MEANREV" in folder.name or "PURE-PULLBACK" in folder.name
        rows.append(dict(experiment_id=folder.name, registered=folder.name in ids,
                         signals=count, disposition="reused_historical_evidence" if historical else "context_only",
                         reason="Completed module evidence; no rerun" if historical else
                         "Broad stream does not establish pure-only replay or frozen snapshot equivalence",
                         hashes=json.dumps({f.name: digest(f) for f in files}, sort_keys=True)))
    return pd.DataFrame(rows)


class Runner:
    def __init__(self, root=ROOT, session=DEFAULT_SESSION, end_before=None):
        if not re.fullmatch(r"[A-Za-z0-9-]+", session):
            raise ValueError("Session must contain only letters, digits and hyphens")
        self.root, self.session = Path(root), session
        self.base = self.root / "results/exit_research" / session
        self.raw = self.root / "results/ab_tests"
        self.snapshot = self.root / "results/research_data" / session
        self.cache = self.raw / "_exit_runner_cache" / session
        self.base.mkdir(parents=True, exist_ok=True)
        self.diagnostics = {}
        self.arm_memory = {}
        path = self.base / "session.json"
        hashes = {p: digest(ROOT/p) for p in SOURCE_FILES}
        import yfinance as yf
        environment = dict(python=sys.version, pandas=pd.__version__, numpy=np.__version__, yfinance=yf.__version__)
        if path.exists():
            self.session_state = json.loads(path.read_text())
            if end_before is not None and end_before != self.session_state["cutoff"]:
                raise ValueError("Cannot change the cutoff of an existing session")
            if self.session_state["source_hashes"] != hashes:
                raise ValueError("Source changed since preregistration; use a new explicit session, never mix code versions")
            if self.session_state["environment"] != environment:
                raise ValueError("Runtime versions changed since preregistration")
        else:
            today = str(pd.Timestamp.now(tz="America/New_York").date())
            cutoff = end_before or (DEFAULT_END_BEFORE if session == DEFAULT_SESSION else today)
            if str(pd.Timestamp(cutoff).date()) != cutoff or cutoff > today:
                raise ValueError("end-before must be an ISO date no later than today")
            self.session_state = dict(session=session, created_at=now(), plan_version=PLAN_VERSION,
                                      source_hashes=hashes, universe=list(UNIVERSE), period="5y", interval="1d",
                                      cutoff=cutoff, download_session_date=today,
                                      grid=list(GRID), status="pending", environment=environment,
                                      diagnostics_defaults={k: v.default for k, v in inspect.signature(signal_diagnostics).parameters.items()
                                                            if v.default is not inspect.Parameter.empty})
            save_csv(self.base/"existing_experiments.csv", inventory(self.root))
            save_json(path, self.session_state)
            atomic_bytes(self.base/"plan.md", PLAN.encode())

    def freeze(self):
        self.snapshot.mkdir(parents=True, exist_ok=True)
        path = self.snapshot / "manifest.json"
        state = json.loads(path.read_text()) if path.exists() else dict(
            session=self.session, cutoff=self.session_state["cutoff"], symbols={}, failures=[], status="pending")
        if state["status"] == "completed":
            self.verify_snapshot(state)
            return state
        if str(pd.Timestamp.now(tz="America/New_York").date()) != self.session_state["download_session_date"]:
            raise ValueError("Incomplete snapshot crossed a calendar day; start a new explicit session")
        for symbol in UNIVERSE:
            if symbol in state["symbols"]:
                continue
            target = self.snapshot / f"{symbol}.csv"
            record = None
            for attempt in (1, 2):
                try:
                    process = subprocess.run(
                        [sys.executable, "-m", "src.exit_research_runner", "--download-one", symbol,
                         "--target", str(target), "--cutoff", state["cutoff"]], cwd=ROOT,
                        capture_output=True, text=True, timeout=35,
                        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
                    if process.returncode:
                        raise RuntimeError(process.stdout + process.stderr)
                    frame = load_frame(target).set_index("timestamp")
                    validate_ohlcv(frame)
                    record = dict(status="completed", symbol=symbol, first_timestamp=str(frame.index[0]),
                                  last_timestamp=str(frame.index[-1]), rows=len(frame), downloaded_at=now(),
                                  period="5y", interval="1d", timezone=str(frame.index.tz),
                                  sha256=digest(target), schema_sha256=digest(target.with_suffix(".schema.json")),
                                  retry_attempted=attempt == 2)
                    break
                except (Exception, subprocess.TimeoutExpired) as exc:
                    state["failures"].append(dict(symbol=symbol, stage="download", attempt=attempt,
                                                  retry_attempted=attempt == 2, error=str(exc)))
                    save_json(path, state)
            state["symbols"][symbol] = record or dict(status="failed", symbol=symbol, retry_attempted=True)
            save_json(path, state)
            print(f"Snapshot {symbol}: {state['symbols'][symbol]['status']}", flush=True)
        state["status"] = "completed"
        state["frozen_at"] = now()
        state["snapshot_id"] = hashlib.sha256(json.dumps(state["symbols"], sort_keys=True).encode()).hexdigest()
        save_json(path, state)
        save_csv(self.snapshot/"manifest.csv", pd.DataFrame(state["symbols"].values()))
        save_csv(self.snapshot/"failures.csv", pd.DataFrame(state["failures"], columns=FAILURE_COLUMNS))
        self.verify_snapshot(state)
        return state

    def verify_snapshot(self, state):
        expected = hashlib.sha256(json.dumps(state["symbols"], sort_keys=True).encode()).hexdigest()
        if state["snapshot_id"] != expected:
            raise ValueError("Snapshot manifest integrity compromised")
        for symbol, entry in state["symbols"].items():
            if entry["status"] == "completed":
                path = self.snapshot/f"{symbol}.csv"
                if digest(path) != entry["sha256"] or digest(path.with_suffix(".schema.json")) != entry["schema_sha256"]:
                    raise ValueError(f"Snapshot integrity compromised: {symbol}")

    def prepare_diagnostics(self, snapshot):
        failures = []
        for symbol, entry in snapshot["symbols"].items():
            if entry["status"] != "completed":
                continue
            try:
                frame = load_frame(self.snapshot/f"{symbol}.csv").set_index("timestamp")
                validate_ohlcv(frame)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", pd.errors.PerformanceWarning)
                    self.diagnostics[symbol] = signal_diagnostics(frame, is_swing=True, allow_long=True, allow_short=False)
            except Exception:
                failures.append(dict(symbol=symbol, stage="diagnostics", attempt=1, retry_attempted=False,
                                     error=traceback.format_exc()))
        self.diagnostic_failures = failures
        save_csv(self.base/"diagnostic_failures.csv", pd.DataFrame(failures, columns=FAILURE_COLUMNS))

    def arm(self, module, c):
        key = (module, config_key(c))
        if key in self.arm_memory:
            return self.arm_memory[key]
        folder = self.cache / module / key[1]
        folder.mkdir(parents=True, exist_ok=True)
        arms, failures = {}, []
        for symbol, source in self.diagnostics.items():
            target = folder/symbol
            marker = target/"completed.json"
            if marker.exists():
                meta = json.loads(marker.read_text())
                for filename, sha in meta["hashes"].items():
                    if digest(target/filename) != sha:
                        raise ValueError(f"Execution cache integrity compromised: {target}")
                arms[symbol] = {name: load_frame(target/f"{name}.csv") for name in
                                ("signal_fill_reconciliation", "ab_trade_lifecycle")}
                continue
            try:
                target.mkdir(parents=True, exist_ok=True)
                result = execute_arm(pure_diagnostics(source, module), c)
                for name, table in result.items():
                    store_frame(target/f"{name}.csv", table)
                save_json(marker, dict(settings=c, symbol=symbol, hashes={
                    f.name: digest(f) for f in target.iterdir() if f.name != "completed.json"}))
                arms[symbol] = result
            except Exception:
                failures.append(dict(symbol=symbol, stage=f"execution:{key[1]}", attempt=1,
                                     retry_attempted=False, error=traceback.format_exc()))
        self.arm_memory[key] = (arms, failures)
        save_csv(folder/"failures.csv", pd.DataFrame(failures, columns=FAILURE_COLUMNS))
        print(f"{module}: cached {key[1]} for {len(arms)} symbols", flush=True)
        return arms, failures

    def compare(self, module, a, b, state, stage):
        a, b, changed = _validated_configs(a, b)
        if len(changed) != 1:
            raise ValueError("Research comparisons require exactly one change")
        eid = f"{self.session}-PURE-{module.upper()}-{config_key(a)}-VS-{config_key(b)}"
        # Identity is the frozen data + pure execution cohort + configurations,
        # not the filename or which orchestration generated an experiment.
        for marker in sorted(self.raw.glob("*/completed.json")):
            prior = json.loads(marker.read_text())
            if (prior.get("snapshot_id") == state["snapshot_id"] and prior.get("baseline") == a
                    and prior.get("variant") == b
                    and prior.get("registry_row", {}).get("module") == f"Pure {MODULES[module]}"):
                eid = marker.parent.name
                break
        final = self.raw/eid
        entry = state["experiments"].setdefault(eid, dict(status="pending", stages=[], baseline=a, variant=b))
        if stage not in entry["stages"]:
            entry["stages"].append(stage)
        state_path = self.base/module/"research_state.json"
        if final.exists():
            marker = final/"completed.json"
            if not marker.exists():
                raise ValueError(f"Unverified existing experiment: {eid}; refusing overwrite")
            meta = json.loads(marker.read_text())
            if meta["snapshot_id"] != state["snapshot_id"] or meta["baseline"] != a or meta["variant"] != b:
                raise ValueError(f"Existing experiment metadata mismatch: {eid}")
            for filename, sha in meta["hashes"].items():
                if digest(final/filename) != sha:
                    raise ValueError(f"Experiment integrity compromised: {eid}/{filename}")
            entry["status"] = "completed" if entry.get("status") == "completed" else "reused from existing research"
            entry["reuse_count"] = entry.get("reuse_count", 0) + 1
            entry["common_symbols"] = meta["common_symbols"]
            entry["included_symbols"] = meta["included_symbols"]
            entry["result_path"] = meta["registry_row"]["result_path"]
            entry["failed_symbols"] = meta["failed_symbols"]
            append_registry(self.root/"results/research_registry.csv", meta["registry_row"])
            save_json(state_path, state)
            return pd.read_csv(final/"paired_signals.csv", float_precision="round_trip"), eid
        entry["status"] = "running"
        save_json(state_path, state)
        try:
            aa, fa = self.arm(module, a)
            bb, fb = self.arm(module, b)
            common = sorted(set(aa) & set(bb))
            paired = []
            metadata = []
            for symbol in common:
                p = _paired(aa[symbol], bb[symbol], self.diagnostics[symbol].index.dtype)
                p.insert(0, "symbol", symbol)
                p["research_module"] = f"Pure {MODULES[module]}"
                p["active_module_mask"] = MODULE_BITS[MODULES[module]]
                paired.append(p)
                source = self.diagnostics[symbol]
                metadata.append(dict(symbol=symbol, input_start=str(source.index[0]),
                                     input_end=str(source.index[-1]), input_bars=len(source),
                                     timezone=str(source.index.tz)))
            if not common:
                raise RuntimeError("No common successful symbols; experiment cannot complete")
            p = pd.concat(paired, ignore_index=True)
            failures = state["data_failures"] + self.diagnostic_failures + fa + fb
            row = dict(experiment_id=eid, experiment_name=f"Pure {MODULES[module]} {stage}",
                       experiment_type="A/B exit rule", module_scope=f"Pure {MODULES[module]}",
                       symbols_requested=len(UNIVERSE), period="5y", timeframe="1d", direction="Long",
                       baseline_config=json.dumps(a, sort_keys=True), variant_config=json.dumps(b, sort_keys=True),
                       changed_parameter=changed[0], created_at=now(), result_path=f"results/ab_tests/{eid}",
                       module=f"Pure {MODULES[module]}", baseline_atr_multiplier=a["atr_multiplier"],
                       variant_atr_multiplier=b["atr_multiplier"], label_a=config_key(a), label_b=config_key(b))
            with tempfile.TemporaryDirectory(dir=self.raw, prefix=".pending-") as tmp:
                staging = Path(tmp)/"experiment"
                staging.mkdir()
                save_csv(staging/"paired_signals.csv", p)
                meta = [{**row, **m, "snapshot_id": state["snapshot_id"],
                         "cohort_execution": "pure signals gated before replay; all bars retained",
                         "signal_available_at": "signal bar close", "fill_at": "next bar open",
                         "common_symbols": len(common), "stage": stage} for m in metadata]
                save_csv(staging/"experiment_metadata.csv", pd.DataFrame(meta))
                save_csv(staging/"failures.csv", pd.DataFrame(failures, columns=FAILURE_COLUMNS))
                tables = comparison_tables(p)
                missing_symbols = set(common) - set(tables["symbol_summary"].symbol)
                if missing_symbols:
                    zero = pd.DataFrame([dict(symbol=s, **summarize(p.iloc[:0])) for s in sorted(missing_symbols)])
                    tables["symbol_summary"] = pd.concat([tables["symbol_summary"], zero], ignore_index=True).sort_values("symbol")
                for name, table in tables.items():
                    save_csv(staging/f"{name}.csv", table)
                save_json(staging/"completed.json", dict(snapshot_id=state["snapshot_id"], baseline=a,
                          variant=b, registry_row=row, common_symbols=len(common),
                          included_symbols=common,
                          failed_symbols=sorted(set(UNIVERSE)-set(common)),
                          hashes={f.name: digest(f) for f in staging.iterdir()}))
                staging.rename(final)
            append_registry(self.root/"results/research_registry.csv", row)
            entry.update(status="completed", result_path=row["result_path"], common_symbols=len(common), included_symbols=common,
                         failed_symbols=sorted({f["symbol"] for f in failures if f["stage"] != "download"
                                                or state["snapshot_symbols"][f["symbol"]]["status"] == "failed"}))
            save_json(state_path, state)
            print(f"{module}: completed {stage}: {len(p)} signals", flush=True)
            return p, eid
        except Exception:
            entry.update(status="failed", error=traceback.format_exc())
            save_json(state_path, state)
            raise

    def run_module(self, module, snapshot):
        folder = self.base/module
        folder.mkdir(parents=True, exist_ok=True)
        path = folder/"research_state.json"
        state = json.loads(path.read_text()) if path.exists() else dict(
            module=module, status="pending", snapshot_id=snapshot["snapshot_id"],
            snapshot_symbols=snapshot["symbols"], data_failures=snapshot["failures"],
            experiments={}, steps={s: "pending" for s in ("A", "B", "C", "D", "E")})
        # Completed runs still verify all immutable experiment artifacts on resume.
        state["status"] = "running"
        save_json(path, state)
        comparisons = []
        def compare(a, b, stage):
            p, eid = self.compare(module, a, b, state, stage)
            comparisons.append((stage, eid, p))
            return p
        baseline = compare(config(), config(trend=False), "A-trend")
        trend_winner = supported_winner(baseline)
        trend = trend_winner != "B"
        state["trend_decision"] = dict(value=trend, evidence=trend_winner or "INCONCLUSIVE; historical Trend ON convention")
        state["steps"]["A"] = "completed"
        mode_test = compare(config(trend=trend), config(trend=trend, locked=True), "B-mode")
        mode_winner = supported_winner(mode_test)
        locked = mode_winner == "B"
        state["mode_decision"] = dict(value=locked, evidence=mode_winner or "INCONCLUSIVE; historical Dynamic convention")
        state["steps"]["B"] = "completed"
        grid_results = {}
        for x, y in grid_pairs():
            grid_results[(x, y)] = compare(config(x, trend, locked), config(y, trend, locked), f"C-grid-{x:g}-{y:g}")
        state["steps"]["C"] = "completed"
        candidates = []
        evidence = []
        for i, m in enumerate(GRID):
            opponents = set(GRID[max(0, i-1):i] + GRID[i+1:i+2])
            if m != 2.5:
                opponents.add(2.5)
            passed = []
            for other in sorted(opponents):
                pair = tuple(sorted((m, other)))
                winner = supported_winner(grid_results[pair])
                passed.append(winner == ("A" if m == pair[0] else "B"))
            profile = arm_metrics(grid_results[pair], "a" if m == pair[0] else "b")
            positive_profile = profile["mean_return"] > 0 and profile["profit_factor"] > 1
            qualifies = all(passed) and positive_profile
            evidence.append(dict(multiplier=m, required_opponents=sorted(opponents),
                                 positive_mean_and_pf=bool(positive_profile), qualifies=bool(qualifies)))
            if qualifies:
                candidates.append(m)
        # Fixed preference for minimum departure from historical 2.5, never maximum return/R.
        candidate = min(candidates, key=lambda m: (abs(m-2.5), m)) if candidates else None
        state["candidate_screen"] = evidence
        state["steps"]["D"] = "completed"
        validation = []
        if candidate is not None:
            tp = compare(config(candidate, True, locked), config(candidate, False, locked), "E-final-trend")
            mp = compare(config(candidate, trend, False), config(candidate, trend, True), "E-final-mode")
            validation = [supported_winner(tp) == ("A" if trend else "B"),
                          supported_winner(mp) == ("B" if locked else "A")]
        state["steps"]["E"] = "completed" if candidate is not None else "not applicable: no candidate passed grid screen"
        completed = [e for e in state["experiments"].values() if e["status"] in ("completed", "reused from existing research")]
        enough_data = min((e.get("common_symbols", 0) for e in completed), default=0) >= 45
        consistent_population = len({tuple(e["included_symbols"]) for e in completed}) == 1
        enough_data = enough_data and consistent_population
        accepted = candidate is not None and all(validation) and enough_data
        state.update(status="completed", final_status="PROVISIONAL EXIT V1 CANDIDATE" if accepted else "INCONCLUSIVE",
                     candidate=config(candidate, trend, locked) if accepted else None,
                     screened_multiplier=candidate, final_interaction_support=validation,
                     reason="Grid and both final interactions pass preregistered descriptive gates; PENDING OOS" if accepted else
                     ("Fewer than 45/50 common symbols or inconsistent successful symbol populations" if not enough_data else
                      "No multiplier coherently beats its adjacent grid values and 2.5 baseline under the preregistered robustness screen"
                      if candidate is None else "Candidate does not pass both final interaction screens"))
        save_json(path, state)
        self.write_report(module, state, comparisons, trend, locked, snapshot)
        return state

    def write_report(self, module, state, comparisons, trend, locked, snapshot):
        folder = self.base/module
        summaries, configurations = [], {}
        for stage, eid, p in comparisons:
            s = comparison_tables(p)["robustness_summary"].iloc[0].to_dict()
            summaries.append(dict(stage=stage, experiment_id=eid, **s))
            entry = state["experiments"][eid]
            for arm, name in (("a", "baseline"), ("b", "variant")):
                c = entry[name]
                configurations.setdefault(config_key(c), dict(configuration=config_key(c), **c, **arm_metrics(p, arm)))
        summary = pd.DataFrame(summaries)
        configs = pd.DataFrame(configurations.values())
        save_csv(folder/"robustness_summary.csv", summary)
        save_csv(folder/"configuration_summary.csv", configs)
        grid = configs[(configs.use_trend_exit == trend) & (configs.use_locked_atr == locked)].sort_values("atr_multiplier")
        lines = [f"# Pure {MODULES[module]} exit research", "", f"**{state['final_status']}** — {state['reason']}", "",
                 f"Final Long signal AND long_active_module_mask == {MODULE_BITS[MODULES[module]]}. Other modules excluded before replay; all bars retained.",
                 f"Snapshot `{self.session}`, SHA256 `{snapshot['snapshot_id']}`; 5y / daily, Swing, Long only.",
                 f"Snapshot cutoff: strictly before {snapshot['cutoff']}; {len(self.diagnostics)}/50 symbols available. See `../../../research_data/{self.session}/manifest.csv` for each symbol's dates, rows, download time and checksums.",
                 f"Number of pure signals: {int(summary.total_signals.iloc[0])}.", "",
                 "## Trend test (Dynamic ATR 2.5)", self.comparison_text(summaries[0]),
                 f"Decision: {state['trend_decision']}", "", "## ATR mode test (2.5)",
                 self.comparison_text(summaries[1]), f"Decision: {state['mode_decision']}", "",
                 "## Predefined ATR grid", "All return values below are fractions; win rates are fractions. PF is return-based, without costs.",
                 markdown_table(grid, ["atr_multiplier", "trades", "win_rate", "mean_return", "median_return", "profit_factor", "mean_R", "median_R", "average_bars_held", "mean_without_top_5"]), "",
                 "Paired grid evidence (B minus A); full symbol/year/tail/exit tables are in each canonical experiment directory."]
        for s in summaries[2:]:
            lines += [f"### {s['stage']}", self.comparison_text(s)]
        lines += ["", "## Final interaction tests", str(state["steps"]["E"]),
                  "Both Trend and ATR-mode tests at the selected multiplier must pass before promotion. No additional multiplier search is permitted.",
                  "", "## Interpretation and limitations",
                  "Paired statistics use finite closed trades filled in BOTH arms. One-sided fills and censored outcomes are excluded from paired deltas and retained separately. Aggregate arm metrics can reflect changed trade sequences.",
                  "R has a different initial-risk denominator across multipliers; raw return, PF, medians, stability and fill behavior govern the screen. R never chooses the candidate.",
                  "LOW SAMPLE, MIXED and TAIL-SENSITIVE are descriptive labels, not significance tests. A failed conservative gate is insufficient support, not proof an exit has no value.",
                  "This is in-sample research on a present-day stock universe, with survivorship/selection bias, unequal IPO histories, Yahoo revisions and no transaction costs, sizing or portfolio constraints. No TradingView parity or OOS validation is claimed.",
                  "Additional evidence required: a frozen later or walk-forward sample with sufficient independent trades across years/symbols, plus cost-aware evaluation under an explicitly approved execution contract.",
                  "", "## Adaptive hypotheses (not implemented)",
                  "Study whether signal-time ATR regime or trend context explains tail-sensitive exits, using separately preregistered hypotheses and untouched validation data. No adaptive rules or entry filters were changed.", ""]
        atomic_bytes(folder/"report.md", "\n\n".join(lines).encode())

    @staticmethod
    def comparison_text(s):
        return (f"`{s['experiment_id']}`\n\n"
                f"{s['comparable_pairs']} pairs; A/B wins/ties {s['a_wins']}/{s['b_wins']}/{s['ties']}; "
                f"fill-status changes {s['fill_status_changes']} ({s['one_sided_fills']} one-sided fills). "
                f"Mean delta {s['mean_paired_delta']:.6f}; median {s['median_paired_delta']:.6f}; "
                f"10% trimmed {s['trimmed_mean_paired_delta']:.6f}; without top 1/3/5 "
                f"{s['paired_mean_without_top_1']:.6f}/{s['paired_mean_without_top_3']:.6f}/{s['paired_mean_without_top_5']:.6f}. "
                f"Label: {s['label']}; supported winner: {s['supported_winner']}.")

    def matrix(self):
        legacy = pd.read_csv(self.base/"existing_experiments.csv")
        historical = []
        for entry in legacy[legacy.disposition == "reused_historical_evidence"].itertuples():
            paired = pd.read_csv(self.raw/entry.experiment_id/"paired_signals.csv")
            historical.append(dict(experiment_id=entry.experiment_id, **summarize(paired)))
        save_csv(self.base/"historical_robustness.csv", pd.DataFrame(historical))
        rows = []
        for label, fragment, trend, mult, status, caveat in (
            ("MeanRev", "MEANREV", "OFF", 2.0, "PROVISIONAL", "57 historical signals; final interaction completion not recorded"),
            ("Pure Pullback", "PURE-PULLBACK", "ON", 1.5, "RESEARCH BASELINE", "380–382 historical signals; final interactions stored; tail sensitivity remains")):
            entries = legacy[legacy.experiment_id.str.contains(fragment)]
            rows.append(dict(module=label, trend_exit=trend, atr_mode="Dynamic", atr_multiplier=mult,
                             research_status=status, sample_size=caveat.split(";")[0],
                             major_caveats=caveat, adaptive_candidates="Signal-time volatility/trend interaction (unimplemented)",
                             OOS_status="PENDING OOS", evidence=f"{len(entries)} existing experiments reused; see existing_experiments.csv"))
        for module in MODULES:
            path = self.base/module/"research_state.json"
            if not path.exists():
                rows.append(dict(module=f"Pure {MODULES[module]}", research_status="PENDING", OOS_status="PENDING OOS"))
                continue
            state = json.loads(path.read_text())
            summary = pd.read_csv(self.base/module/"robustness_summary.csv")
            c = state["candidate"] or {}
            rows.append(dict(module=f"Pure {MODULES[module]}", trend_exit=("ON" if c["use_trend_exit"] else "OFF") if c else "Unresolved",
                             atr_mode=("Locked" if c["use_locked_atr"] else "Dynamic") if c else "Unresolved",
                             atr_multiplier=c.get("atr_multiplier", "Unresolved"), research_status="PROVISIONAL" if c else "INCONCLUSIVE",
                             sample_size=f"{int(summary.total_signals.iloc[0])} signals; {int(summary.comparable_pairs.min())}–{int(summary.comparable_pairs.max())} pairs",
                             major_caveats=state["reason"], adaptive_candidates="Signal-time volatility/trend interaction (unimplemented)",
                             OOS_status="PENDING OOS", evidence=f"exit_research/{self.session}/{module}/report.md"))
        matrix = pd.DataFrame(rows)
        text = ("# Exit Policy Matrix V1\n\nBehavior change: NO. Existing strategy behavior changed: NO. "
                "Research candidates only; no production policy or entry rule changed.\n\n"
                + markdown_table(matrix, list(matrix.columns)) + "\n\n"
                "Historical MeanRev/Pullback evidence is reused without rerunning or rewriting artifacts. "
                "The old broad Breakout/Squeeze cohorts are context only: other modules affected fills, and no frozen data permits exact equivalence. "
                "The new pure-only replay uses one shared frozen Yahoo snapshot. All results are in sample, without costs or portfolio sizing.\n\n"
                "Next phase: ENTRY RESEARCH, with exit uncertainty retained explicitly and hypotheses preregistered. "
                "Do not treat entry research as validation of these exits. Walk-forward/OOS confirmation remains pending.\n")
        atomic_bytes(self.base/"EXIT_POLICY_MATRIX_V1.md", text.encode())
        atomic_bytes(self.root/"results/EXIT_POLICY_MATRIX_V1.md", text.encode())

    def impossible(self, module, error):
        """All-symbol execution failure: preserve failed experiments, no registry entry."""
        folder = self.base/module
        path = folder/"research_state.json"
        state = json.loads(path.read_text())
        state.update(status="inconclusive", final_status="INCONCLUSIVE", candidate=None,
                     reason=str(error), screened_multiplier=None)
        state["steps"] = {k: v if v == "completed" else "impossible: no common successful symbols"
                          for k, v in state["steps"].items()}
        save_json(path, state)
        empty = pd.DataFrame({"symbol": pd.Series(dtype=object), **{
            k: pd.Series(dtype="object" if t == "object" else "float64") for k, t in PAIRED_SCHEMA.items()}})
        save_csv(folder/"robustness_summary.csv", pd.DataFrame([summarize(empty)]))
        save_csv(folder/"configuration_summary.csv", pd.DataFrame(columns=["configuration", "atr_multiplier", "use_locked_atr", "use_trend_exit"]))
        atomic_bytes(folder/"report.md", (f"# Pure {MODULES[module]}\n\nINCONCLUSIVE: {error}\n\n"
                     "No common successful symbols. Failed experiments remain failed and unregistered. "
                     "The finite grid is impossible on this snapshot; resolve captured failures before a new session.\n").encode())


def markdown_table(frame, columns):
    def fmt(value):
        if isinstance(value, float):
            return f"{value:.6g}"
        return str(value).replace("|", "/").replace("\n", " ")
    return "\n".join(["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"]*len(columns)) + " |"] +
                     ["| " + " | ".join(fmt(row[c]) for c in columns) + " |" for row in frame.to_dict("records")])


PLAN = """# Preregistered finite exit research plan V1

Pure Breakout then Pure Squeeze. Same 50-symbol universe, 5y Yahoo daily,
auto_adjust=False, Swing, Long only. Original indicator defaults and all warm-up
bars retained. Gate final long signal by exact module mask before replay.
No changes to production code, execution contract, Pine or entry rules.

Freeze one dataset per symbol before experiments; exclude the current New York
date (possibly incomplete daily bar), or use an explicit earlier common cutoff.
Default session excludes 2026-09-22 and later because the original Yahoo five-year
response has a missing final close; the failed initial snapshot is retained.
This cutoff was fixed before any backtests. No internal bars are dropped.
Preserve dtypes, timestamps, SHA256,
per-symbol download times and source hashes. Two download attempts, 35 seconds
each, then explicit failure. Stop on hash/data corruption. At least 45/50 common
symbols are required for a candidate. No provider substitution or imputation.

A: Dynamic ATR 2.5, Trend ON vs OFF. B: Dynamic vs Locked ATR 2.5 with supported
Trend setting. If inconclusive, use historical Trend ON / Dynamic conventions.
C: ONLY 1.5, 1.75, 2.0, 2.25, 2.5, 3.0. Run each configuration once; derive
comparisons against 2.5 and adjacent grid points (8 unique pairs).

Descriptive support screen (fixed before new results): >=100 closed pairs,
>=20 non-ties, >=10 symbols, >=3 years with >=10 pairs; mean, 10% symmetric
trim, removing the winner's best 5 paired deltas, and paired majority agree.
At least 60% informative symbols and eligible years agree, no year contributes
>60% of positive directional gain, at least 2 of win rate / median / PF do not
worsen, and <=10% of signals have one-sided fills. R is descriptive only.
These are conservative research gates, not statistical significance tests.

D: A multiplier must pass against adjacent grid values AND the 2.5 reference
(reference itself must pass against its neighbors). If multiple qualify, use
the smallest departure from 2.5 then the smaller multiplier, not highest return.
The chosen arm must also have positive mean raw return and return-based PF > 1.
E: If a multiplier qualifies, evaluate Trend ON/OFF and Dynamic/Locked there.
Both chosen settings must pass the same screen; otherwise INCONCLUSIVE.
No qualifying multiplier means E is not applicable, never an excuse to expand
the grid. At most 12 comparisons and 10 unique configurations per module.

Report all arm/paired metrics, tails, years, symbols, censoring, fill transitions
and exit reasons. New completed comparisons belong under results/ab_tests and
are appended once to the existing registry. Completed artifacts are hash checked
and reused. Interrupted per-symbol executions resume from verified caches.
Existing historical evidence is inventoried and reused; broad all-module
replays are not substituted for pure-only execution. Final outcome is candidate
or INCONCLUSIVE. Stop after the matrix; no entry research or adaptive policy.
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", choices=tuple(MODULES))
    parser.add_argument("--remaining", action="store_true")
    parser.add_argument("--freeze", action="store_true")
    parser.add_argument("--session", default=DEFAULT_SESSION)
    parser.add_argument("--end-before", help="Exclusive common data cutoff, YYYY-MM-DD; fixed on session creation")
    parser.add_argument("--download-one", choices=UNIVERSE, help=argparse.SUPPRESS)
    parser.add_argument("--target", help=argparse.SUPPRESS)
    parser.add_argument("--cutoff", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.download_one:
        download_one(args.download_one, args.target, args.cutoff)
        return
    if not (args.module or args.remaining or args.freeze):
        parser.error("Choose --module, --remaining or --freeze")
    lock_path = ROOT/"results/exit_research/.runner.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit("Another exit runner holds the registry/session lock")
        runner = Runner(session=args.session, end_before=args.end_before)
        print("Finite plan: shared snapshot → pure Breakout → pure Squeeze → Exit Policy Matrix V1. No entry research.", flush=True)
        snapshot = runner.freeze()
        if args.freeze:
            return
        runner.prepare_diagnostics(snapshot)
        for module in (tuple(MODULES) if args.remaining else (args.module,)):
            try:
                runner.run_module(module, snapshot)
            except RuntimeError as exc:
                if str(exc) != "No common successful symbols; experiment cannot complete":
                    raise
                runner.impossible(module, exc)
        runner.matrix()
        runner.session_state["status"] = "completed" if args.remaining else "partially completed"
        save_json(runner.base/"session.json", runner.session_state)
        print("Research complete; no additional search.", flush=True)


if __name__ == "__main__":
    main()
