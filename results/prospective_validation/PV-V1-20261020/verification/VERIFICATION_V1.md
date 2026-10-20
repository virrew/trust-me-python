# Prospective Validation + Paper Scanner V1 — completion verification

Implementation complete. **Behavior change: YES. Existing strategy behavior
changed: NO.** The new layer adds paper evidence collection and separate cost
accounting. Production strategy rules, indicator warm-up, masks, diagnostics,
execution engines, authoritative references and previous research results are
unchanged. No optimization, Strategy V2, ML, brokerage, real orders, scheduler,
sector filter or dashboard was implemented.

## Session identity and evidence collected

| Field | Value |
| --- | --- |
| Session | `PV-V1-20261020` |
| Actual pre-implementation/baseline HEAD | `64ccb996c04142149d48b17e93806de78e70f0e2` |
| Initial checkout | clean `main` |
| Frozen plan SHA256 | `4dd6c6c687bbee0272fa7d061649c68539fbbb2107cc2ff83184d099955da1bf` |
| Universe | `PV-UNIVERSE-V1`, 50 symbols, unchanged Exit V1 universe |
| Old snapshot | `EXIT-V1-20260923-CLOSED`, strictly before `2026-09-22`; last bar `2026-09-21` |
| Validation freeze UTC | `2026-10-20T13:54:27.785014+00:00` |
| Validation freeze Europe/Stockholm | `2026-10-20 15:54:27.785014 CEST` |
| Prospective protocol start | freeze timestamp above |
| First possible eligible prospective bar | `2026-10-21`, accepted after `2026-10-21T20:15:00Z` (16:15 New York), under V1's conservative next-date rule |
| Frozen candidate SHA256 | `7992a5bb7537c1cb0dc4a4976af104d9b391a2236b8413258d8c9385acfc9b21` |
| Shadow candidates | all 10 existing SI candidates, exact definitions, no retuning |
| New post-snapshot market data fetched | **NO** |
| Actual post-snapshot market outcomes viewed before freeze | **NO** |
| Temporal OOS period evaluated | **NONE** |
| Later-unseen signals / fills / closed trades | **0 / 0 / 0**; no later-unseen market sample evaluated |
| Genuine prospective signals / fills / closed trades | **0 / 0 / 0** |
| Current research state | `AWAITING_VALIDATION_DATA` |

Synthetic post-cutoff prices in regression tests are artificial fixtures, not
new market observations. The actual integration run imported only the previously
frozen historical snapshot. Its zero validation counts are not a measured
zero-signal result for any newer market period.

`freeze/validation_plan.json` contains the actual working-tree status and all
source/runtime/configuration identities. `freeze/working_tree.diff` retains
the tracked implementation diff at freeze. The source hashes also identify
new untracked implementation modules. All work remains uncommitted; no commit,
push, merge, reset or overwrite of another contributor's work occurred.

## Baseline and shadow identity

The actionable paper baseline is the existing broad Trust Me final signal with
current Daily/Swing defaults: Long enabled, Short disabled, ATR length 14,
dynamic multiplier 2.5, trend exit ON. It is not a selected combination of
historical module exits.

| Production source | SHA256 |
| --- | --- |
| `src/trust_me_core.py` | `67b34d8decdb7ffc833bfcf4a5e035f89c2fea49afb067eabc9a80ab00f2a18c` |
| `src/diagnostics_context.py` | `950250293fd65c5ceea66327384668c144ca329edc4187cb9a25d010da0f318e` |
| `src/diagnostics_signals.py` | `4e528cc815412b62916be5dc895ebee048af42d6bc2791937dc85a2bea88f175` |
| `src/backtest.py` | `a5fe84dda34531e1099d669d0b73932865eb4eddfcd743b9c0dd702dc1b9401c` |

Four independent module references retain the existing policies: MeanRev dynamic
2/trend OFF; Pullback dynamic 1.5/trend ON; Breakout and Squeeze dynamic
2.5/trend ON. The nine lifecycle candidates and one Breakout price-relaxation
candidate use the unchanged SI stream/replay implementation. These remain
research shadows, not recommendations or production TAKE/SKIP logic.

Costs are frozen in the separate accounting layer:

| Scenario | Commission per side | Slippage per side |
| --- | ---: | ---: |
| Primary | 10 bps | 5 bps |
| Stress | 10 bps | 15 bps |

For closed trades, debit
`(commission_bps + slippage_bps)/10000 * (1 + exit_price/entry_price)` from
gross return. This charges entry and exit notionals in entry-notional return
units. At an unchanged price the round-trip debit is 30 bps primary / 50 bps
stress. Open final returns stay missing. These assumptions are not calibrated
brokerage costs, position sizing, equity accounting or TradingView slippage
parity. No fill or stop price is changed.

## Files and contracts

Modified:

- `src/live_scanner.py`: replaces the empty placeholder with freeze, scan,
  catch-up, update, resume and report orchestration.
- `ARCHITECTURE.md`: updates scanner/roadmap ownership and documents section 20.

Added:

- `src/prospective_validation_data.py`: completion clocks, OHLCV append validation,
  Yahoo adapter and exact typed CSV/string round trips.
- `src/prospective_validation_analysis.py`: frozen accounting and separate
  evidence/arm/cost metrics and distributions.
- `tests/test_live_scanner.py`: 20 deterministic regressions.
- `results/prospective_validation/PV-V1-20261020/`: frozen protocol, original
  seed copies, offline run, head state and verification artifacts.

Preserved input contracts: `open, high, low, close, volume`, original unique
increasing Daily DatetimeIndex, unchanged timezone, full original warm-up,
original NaN handling, existing 191 diagnostics, module/score/failure masks and
current strategy defaults. Daily input is limited to midnight session labels,
naive or America/New_York. Separate UTC fields express availability.

New evidence contracts:

- Loader access requires a complete, hash-verified freeze and unchanged sources,
  runtime and configuration. The test suite verifies rejection before invoking
  the loader.
- Only completed bars pass the NY 16:15 gate. Temporal OOS, genuinely observed
  prospective signals and post-freeze backfill stay separate. A first
  observation is never retrospectively upgraded.
- Signals are unique by symbol/arm/signal time/direction. The append stream
  contains only newly observed signals; complete trade snapshots are not new
  trades and must not be concatenated as an append stream.
- Existing engines retain next-open fills, causal stop updates, occupancy and
  censoring. States contain only survived-close information. Final labels and
  lifecycle bounds are separate, and retain intrabar uncertainty.
- Existing engine-equivalent open prefix trades are `OPEN` with
  `censored_at_end=True`. Subsequent immutable snapshots may close them.
- Evaluation retains exact sample sizes, gross/net metrics, lower tails,
  winner dependence, holding periods, MFE/MAE/retention and symbol/module-mask
  distributions per evidence class and arm. Empty tables keep schemas.

## Unit / regression

Measured before implementation:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider
```

**201 passed, 1 warning, 48.77 seconds.**

Final focused scanner and execution/reference regressions:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_live_scanner.py tests/test_backtest.py tests/test_trade_lifecycle.py tests/test_strategy_improvement.py
```

**87 passed, 1 warning, 42.65 seconds.**

Final full deterministic suite:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider
```

**221 passed, 1 warning, 89.97 seconds.**

The warning is the pre-existing urllib3/LibreSSL compatibility warning.
The scanner locally suppresses only the existing diagnostics' repetitive pandas
fragmentation PerformanceWarning; it does not suppress data or correctness
errors. No existing test expectations were changed.

Coverage includes freeze-before-loader access, candidate/source/config identity,
DST/completion boundaries, incomplete future-bar exclusion, old/new population
separation, next-open/stop/lifecycle engine equality, causal prefixes, immutable
reruns, stable signal/trade keys, exact empty/string/NaN schemas, primary/stress
cost arithmetic, ties/PF/tails, source drift, revised/missing bars, corrupt or
removed artifacts, symbol checkpoints, partial-universe failure and recovery.
Short execution remains covered by existing engine tests; this frozen scanner
protocol deliberately retains current Long-only defaults.

## Integration

Executed from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m src.live_scanner init
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m src.live_scanner scan --input-dir results/research_data/EXIT-V1-20260923-CLOSED
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m src.live_scanner resume
```

Initialization completed with the plan hash above. Offline scan completed for
**50/50 symbols**, with all 15 arms per symbol and 60 separate empty
evidence/arm/cost summary rows. Every symbol's latest input bar is 2026-09-21;
every symbol has zero validation bars. Historical latest-bar diagnostics are
labelled `HISTORICAL_RESEARCH_CONTEXT`, not prospective evidence.

Run 000001 started `2026-10-20T13:54:45.158809+00:00` and completed
`2026-10-20T13:56:14.916441+00:00`. No symbol was excluded, no failure was
recorded, and no pending run remains.

Resume reused the completed run. All **51 run/symbol completion markers** kept
their SHA256 and nanosecond modification time. `recovery_check.json` records
the independent assertions. The verified report remains
`AWAITING_VALIDATION_DATA`.

No Yahoo/network integration was executed. No real post-snapshot market prices
or outcomes were retrieved, evaluated or inspected.

## Parity / reference

The new scanner test compares every candidate's complete trade ledger directly
with the existing SI replay, and the broad baseline directly with the original
backtest. Existing backtest/lifecycle/SI regression cases also passed, including
disabled-rule equivalence, gap stops, close-only updates and causal prefixes.
Production source/reference/historical SI artifacts are unchanged against HEAD.

Manual Yahoo-dependent diagnostic programs and TradingView/Pine external
parity programs were **not run**. No broker-emulator parity, profitability,
independence or robust OOS edge is claimed.

## Compile / diff

```sh
PYTHONPYCACHEPREFIX=/private/tmp/trust-me-pv-pycache .venv/bin/python -m py_compile src/live_scanner.py src/prospective_validation_data.py src/prospective_validation_analysis.py tests/test_live_scanner.py
git diff --check
```

Both passed. The three new Python files additionally passed
`git diff --no-index --check /dev/null <file>` with no whitespace diagnostics
(exit 1 indicates an expected new-file difference). A restricted
`git diff --quiet HEAD -- ...` confirmed unchanged production core, diagnostics,
backtest, lifecycle/SI execution, authoritative references and prior SI results.

## Storage and commands

All paths below are relative to this session directory:

- `freeze/validation_plan.json` and `.sha256`: immutable protocol.
- `freeze/universe.json`, `candidates.json`, `seed/`, source/config hashes in
  the plan: universe and baseline/shadow identity.
- `runs/000001/<symbol>/`: immutable data, diagnostics, current scan and new
  decisions, including no-signal symbols.
- `runs/000001/<symbol>/{BASELINE,REFERENCE-*,SHADOW-*}/`: append-only
  `new_signals.csv`; as-of `trades.csv`, `states.csv`, `stop_path.csv`,
  `reconciliation.csv`, all with typed schema sidecars.
- `runs/000001/evaluation.csv`, `distributions.csv`: separate metrics.
- `head.json`: recoverable current committed-run pointer.
- `.run-pending/` and `failures/`: created when needed for interrupted/failed
  work; neither a silent partial publication nor evidence deletion.
- `verification/`: this report, offline CLI report, resume report and recovery
  assertions.

Read scanner CSVs with `src.prospective_validation_data.load_frame` to preserve
empty strings, literal NA strings, NaN/None, dtypes and timestamps.

First new-market-data operation:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m src.live_scanner scan
```

This verifies the existing freeze before invoking Yahoo. It catches up the
pre-freeze later-unseen period and can capture the latest eligible prospective
bar, preserving their separate classes. Use `catch-up` for historical ingestion,
`update` to follow open trades without originating prospective signals,
`resume` after interruption, and `report` for current verified state. Run
`scan` after 16:15 New York and before the next calendar day's 09:30 for
prospective eligibility. No automation was installed.

## Remaining limitations and exact next research step

No actual new-market validation sample exists yet. The software is verified
offline; Yahoo/provider operation and genuine prospective acquisition remain
unverified. This is an operational evidence gap, not an invented zero-signal
or successful-OOS conclusion.

V1 is Daily/Swing, current Long defaults only. It deliberately excludes the
freeze date and missed/backfilled signal bars from prospective entries.
Without an exchange calendar it delays early-close bars to 16:15, may exclude
usable weekend/holiday signal windows, and does not certify that no exchange
session is missing. Fills remain the research contract's next observed open.
No live intraday fill observation or real execution is performed.

All streams start flat at cutoff. Temporal trades can occupy positions in the
prospective period; their original evidence class remains unchanged. Open
prefix trades are censored; final outcomes are unknown. Across interrupted
multi-day runs, per-symbol cutoffs can differ and are explicitly reported.
Overlapping/provider-adjusted prices, including corporate-action revisions,
fail closed rather than rewriting the seed or historical decisions.

Source/runtime changes stop reuse; preserve this implementation/environment
or create an explicitly reviewed new protocol. Hash chains detect accidental
corruption but are not an external timestamp authority. Complete immutable
snapshots consume disk space. Fixed-current-universe survivorship, dependent
signals, modelled fills, intrabar excursion uncertainty and uncalibrated cost
assumptions limit interpretation. MeanRev remains low sample/provisional;
Breakout/Squeeze reference exits remain unresolved.

Once at least 100 closed trades per relevant arm/evidence class have
accumulated, review the **already frozen** gross/net expectancy, PF, WR,
winner/loss preservation, lower tails, MFE/MAE retention, top-winner dependence
and symbol/module distributions against the corresponding frozen reference,
with exact sample sizes and unresolved censoring reported. This threshold
only ends the LOW SAMPLE label; it is not a statistical acceptance rule.
Do not promote on WR alone. Any new hypothesis or parameter change requires
a separate protocol and a later untouched sample. Stop here: no ML or Strategy
V2 work follows automatically.
