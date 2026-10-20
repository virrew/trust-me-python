# Prospective Validation Storage / Operational V2 — verification

**PV-V2 ready for first real scan.** Research status:
**AWAITING_VALIDATION_DATA**. No real post-snapshot data or outcomes were
retrieved, inspected or evaluated. The first real scan is deferred until review.

**Behavior change: YES. Existing strategy behavior changed: NO.**
The new behavior is storage, event publication, idempotency and state recovery.
Existing indicators, entry rules, masks, warm-up, execution, lifecycle, candidate
definitions and cost formulas are unchanged. No strategy research, tuning,
ML, broker, orders, dashboard, sector work, launchd or scheduler was added.

## Identity and preservation

| Field | Verified value |
| --- | --- |
| Actual starting HEAD | `4ddd33c050273fec587e1172adffae4d6b1bd188` |
| Starting commit subject | `Prospective Validation + Paper Scanner V1` |
| Starting branch/worktree | clean `main`, empty `git status --short` and relevant diff |
| Final branch/HEAD | unchanged `main` / same commit; implementation is uncommitted |
| V1 session | `PV-V1-20261020`, preserved unchanged |
| V1 plan SHA256 | `4dd6c6c687bbee0272fa7d061649c68539fbbb2107cc2ff83184d099955da1bf` |
| V1 preservation | 8,221 files unchanged; 51 run/symbol completion markers verified |
| V2 session | `PV-V2-20261020` |
| V2 plan SHA256 | `9abe8188ecebe7ac2758df559ab950fdcc79c82bf275ca606d9ab30466fcb6f4` |
| V2 freeze UTC | `2026-10-20T15:10:17.710393+00:00` |
| V2 freeze Stockholm | `2026-10-20 17:10:17.710393 CEST` |
| Prospective-start boundary | V2 freeze timestamp above |
| First prospective-eligible session | `2026-10-21`, after `2026-10-21T20:15:00+00:00` (16:15 New York), before next calendar day 09:30 New York |
| Historical cutoff | strictly before `2026-09-22`; seed ends `2026-09-21` |
| Seed source | original `EXIT-V1-20260923-CLOSED`, full warm-up preserved once |
| Universe | unchanged `PV-UNIVERSE-V1`, 50 symbols |
| Candidate SHA256 | `7992a5bb7537c1cb0dc4a4976af104d9b391a2236b8413258d8c9385acfc9b21` |
| Candidates/arms | 10 exact SI shadows; baseline + 4 references + 10 shadows = 15 independent streams per symbol |
| Real V2 temporal/prospective observations | 0 / 0 |
| Real V2 temporal signals/fills/closed trades | 0 / 0 / 0 |
| Real V2 prospective signals/fills/closed trades | 0 / 0 / 0 |
| Real post-snapshot Yahoo retrieval | NO |
| Real new-market outcomes viewed | NO |

The plan captures actual HEAD, working-tree status/diff hash, every current
`src/*.py` hash, runtime versions, scientific configuration, exact universe,
candidate bytes/hash, old seed identities and event schemas. New untracked
modules are identified by their source hashes even though Git's tracked diff
does not include them. Final source hashes were reverified after integration.
No commit, push, merge, reset or modification of another contributor's work
was performed.

V1's source files and artifacts were not modified. V1 hashes the entire source
file set, so adding V2 modules intentionally makes its current-source check
fail. V1 remains reproducible at its original completed commit shown above;
its protocol was not rewritten to accept V2.

Universe, unchanged:

NVDA, AMD, MU, AVGO, MRVL, QCOM, ARM, SMCI, TSM, ASML, AAPL, MSFT, GOOGL,
META, AMZN, NFLX, ORCL, CRM, NOW, PLTR, TSLA, COIN, HOOD, ROKU, SHOP, UBER,
ABNB, CRWD, PANW, DDOG, JPM, GS, MS, BAC, V, MA, CAT, GE, DE, ETN, HON,
RTX, XOM, CVX, COP, LLY, COST, WMT, HD, NKE.

## Scientific contracts carried forward

The production baseline remains the broad default Long signal, Dynamic ATR
2.5 and trend exit ON. Separate reference policies remain MeanRev Dynamic
2/trend OFF, Pullback Dynamic 1.5/trend ON, Breakout and Squeeze Dynamic
2.5/trend ON. Exact candidates are copied from V1's frozen JSON; no candidate
was selected, rewritten or retuned.

Primary costs are commission 10 bps + slippage 5 bps per side. Stress costs
are commission 10 bps + slippage 15 bps per side. The unchanged debit is
`(commission_bps + slippage_bps)/10000 * (1 + exit_price/entry_price)`.
Net return subtracts that debit from gross return; execution prices/stops
are unchanged. Open final returns remain missing.

Evidence separation remains `TEMPORAL_OOS_LATER_UNSEEN`,
`PROSPECTIVE_PAPER` and excluded
`POST_FREEZE_BACKFILL_NOT_PROSPECTIVE`. V2 uses its own freeze time.
Only first-persisted completed bars become evidence; original classification
is never upgraded. Temporal positions can continue into the prospective
period with their original signal evidence class and continuous occupancy.

OHLCV remains `open, high, low, close, volume` with original Daily labels,
DatetimeIndex timezone/order, full seed and NaNs. All 191 contemporaneous
diagnostics are retained once per new symbol/bar. Availability uses separate
UTC fields; no fabricated exact intrabar fill time or future label enters
decision/state features.

V2 invokes the unmodified V1 symbol orchestration in temporary scratch. That
orchestration calls existing diagnostics, baseline/reference backtest, shadow
replay, `causal_path`, lifecycle and accounting functions. V2 projects their
outputs into storage; it does not implement trading predicates or an engine.

## Storage and recovery

```text
PV-V2-20261020/
  freeze/                         immutable protocol, hashes and original seed
  events/YYYY/MM/YYYY-MM-DD/NNNNNN/
    run.json
    bars.csv
    decisions.csv
    signals.csv
    trade_events.csv
    lifecycle_states.csv
    schemas.json
    completed.json
  publication.jsonl               append-only publication receipts
  state/                          mutable, reconstructible
    open_trades.csv
    schemas.json
    cursors.json
    latest_run.json
    completed.json
  reports/latest/                 mutable derived evaluation/distributions/report
  failures/                       compact errors, only when needed
  verification/
```

Each new-data run retains **8 immutable evidence files**, independent of
symbol/arm count. Approximately **2,000 evidence files per 250-session year**
(2,016 at 252 runs), plus one-time freeze, one receipt, 5 current-state files, 5 latest-report
files and exceptional verification/failure artifacts. Repeated input with no
new completed bars publishes no partition. Catch-up grows rows, not file count.
An explicit additional new-data run on the same invocation date uses the next
global sequence rather than overwriting the first.

A normal fully covered day has 50 bar and 50 diagnostic rows, 0–750 signal
rows, up to roughly 750 survived lifecycle rows and 2,250 entry/exit/execution
events. These are structural row bounds, not measured signal forecasts.

Repeated full historical price snapshots and retained per-symbol/per-arm
directory multiplication are eliminated. The full original seed is stored
once. Symbol and arm are columns. Each new OHLCV also occurs in its
contemporaneous diagnostic row, not in repeated full histories.

CSV is transparent and uses existing dependencies. One `schemas.json`
consolidates exact dtypes, string and None restoration. Read with
`live_scanner_v2.read_table`. Empty `research_signal_source` is explicitly
object-typed instead of V1's inferred empty float column; no values change.
No Parquet, SQLite or other dependency was added.

Immutable `trade_events` contains:

- `ENTRY_FILLED`: only entry-known fields, with entry-open availability.
- `EXIT_FILLED`: closed lifecycle and cost record, explicitly retrospective.
- `EXECUTION_BAR`: original engine stop trace, close-known next stop and trend
  flags; next stops apply on the following bar.

Signals are eligible observations, not asserted orders. Pending/reconciliation
and shadow pending-exit state can be replayed with the unchanged engine. An
ordinary daily prefix does not create a false terminal censorship event.
Open prefix trades remain censored only in the mutable as-of view.

Keys include the protocol session plus symbol, arm, signal time and direction.
Event keys add type/time, state keys add bar time. Bars/decisions are unique
by symbol/time. Actual observation clocks are separate from model availability.

Source of truth is **freeze + seed + verified events**. State is not a replay
input. Missing/corrupt/stale state is reconstructed offline through existing
engines. Closed evaluation records come from exit events, while only open
trades are cached. Reports remain separated by evidence, arm and cost;
zero-sample combinations retain schema/rows. No daily evaluation tree or
automatic monthly snapshots are kept.

One atomic checksummed checkpoint holds each completed symbol's new rows,
open trades and original observation clock. Incomplete symbol computation
does not publish. Resume reuses complete symbols; all symbols must complete
before atomic partition publication. The run hash chain, inventory, sequence
and append-only receipt detect corruption and missing partitions. Verified
orphans after rename are adopted without refetching. A process lock protects
CLI writers; library users must also hold `session_lock`.

## Verification

Unit / regression baseline, before modifications:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider
```

**221 passed, 1 warning, 87.06 seconds.**

Final focused V2 and scanner/execution/lifecycle/Strategy Improvement regressions:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_live_scanner_v2.py tests/test_live_scanner.py tests/test_backtest.py tests/test_trade_lifecycle.py tests/test_strategy_improvement.py
```

**116 passed, 1 warning, 243.65 seconds**, including 29 V2 tests.

Final full deterministic suite, same baseline command:

**250 passed, 1 warning, 267.16 seconds.**

The sole warning is the pre-existing urllib3/LibreSSL compatibility warning.
No existing test expectation was changed.
On continuation, the existing outputs were reused after verifying unchanged
frozen source hashes; the expensive suites were not repeated merely to resume.

The V1/V2 multi-prefix comparison exercises actual fills in **all 15 arms**,
including experimental sole-price-blocker signals. It compares exact baseline/
reference/shadow signal timestamps and provenance, complete trade values,
entry/exit prices and reasons, gross/net/cost accounting, lifecycle MFE/MAE,
causal state, original execution traces, evidence classification and evaluation/
distribution tables. Immutable publication clocks are intentionally not rewritten
for old closed records; that storage difference is excluded from value equality.

Tests also cover same-day idempotency, first-observation preservation, incomplete
future-bar exclusion, duplicate/revised/missing input, partial computation,
partial universe, pre-/post-publication interruption, pending/event corruption,
missing published tail, source/config/universe/candidate/cost drift, state
corruption/deletion and reconstruction, exact string/nullable/timezone codec and
empty schemas. Existing backtest/SI regressions cover threshold, stop, long/short,
gap and causal-prefix behavior. V2 remains the frozen Long-only protocol.

Integration, **old seed only**, from repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m src.live_scanner_v2 init
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m src.live_scanner_v2 scan --input-dir results/research_data/EXIT-V1-20260923-CLOSED
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m src.live_scanner_v2 recover
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m src.live_scanner_v2 resume
```

All four CLI operations completed successfully. Each report covers **50/50 symbols**, ending at 2026-09-21 with **zero validation bars, zero event partitions and zero signals/fills/closed trades in both evidence classes**. The report retains all 60 zero-sample arm/evidence/cost rows. Explicit recovery reconstructed all **5 state files byte-for-byte**, preserving all **107 frozen files**. Resume required no data fetch or publication. No pending work or failures remain. Assertion results, preservation checksum inventories and CLI reports are saved beside this document.

Parity / reference: deterministic equivalence against existing V1/backtest/SI
implementations passed. Yahoo integration, manual network diagnostics and
TradingView/Pine external parity were **not run**. No broker-emulator parity,
robust edge, profitability or out-of-sample generalization is claimed.

Compile / whitespace:

```sh
PYTHONPYCACHEPREFIX=/private/tmp/trust-me-pv-v2-pycache .venv/bin/python -m py_compile src/live_scanner_v2.py src/prospective_validation_storage.py tests/test_live_scanner_v2.py
git diff --check
```

Both passed. New Python files also passed `git diff --no-index --check /dev/null
<file>` with no whitespace diagnostics (exit 1 is the expected new-file diff).
Final preservation assertions and source hashes are recorded separately.

## Files and final working tree

Added:

- `src/live_scanner_v2.py`
- `src/prospective_validation_storage.py`
- `tests/test_live_scanner_v2.py`
- `results/prospective_validation/PV-V2-20261020/` (freeze, derived state/reports,
  verification; no real event partitions)

Modified: `ARCHITECTURE.md`, scoped map/roadmap entries and the new V2 section.
No existing implementation, reference, historical result or V1 file was modified.

Final `git status --short`:

```text
 M ARCHITECTURE.md
?? results/prospective_validation/PV-V2-20261020/
?? src/live_scanner_v2.py
?? src/prospective_validation_storage.py
?? tests/test_live_scanner_v2.py
```

## First real scan and remaining limits

After review, run from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m src.live_scanner_v2 scan --session PV-V2-20261020
```

Run after 16:15 New York and before next calendar day 09:30 for prospective
eligibility. Catch-up/update cannot manufacture prospective entries.
No automation was installed, and this command was **not** run against Yahoo
during implementation.

**Ready for launchd automation now: NO for unattended real-data operation.**
The CLI, process lock, compact storage, idempotency and recovery infrastructure
are implemented and verified offline, so a separate launchd implementation
task has a concrete operational interface. This task deliberately leaves the
first real provider scan unverified and deferred until review. Launchd has
not been implemented, installed or activated; no next phase has started.

There is no remaining implementation blocker found by the offline checks.
Real provider acquisition remains unverified. Full replay CPU and temporary
V1 snapshot file I/O are deliberately retained; **8 is the retained evidence
file count, not the total number of transient file writes**. Scratch is removed
normally, but OS termination can leave temporary files. Ledger verification
and in-memory history still grow with time.

Existing limits remain: Daily/Long-only scope, no exchange calendar, next
observed open, strict provider revision/omission rejection, rolling five-year
provider overlap needing a later reviewed extension, fixed-universe
survivorship, dependent independent-arm signals, intrabar excursion uncertainty,
unresolved reference policies and uncalibrated research costs. Local hashes
are not external notarization and cannot detect coordinated deletion of both
the entire ledger tail and its publication receipt.

No new-market sample exists yet. Zero counts mean **awaiting data**, not an
observed zero-signal market, successful validation or an improved strategy.
