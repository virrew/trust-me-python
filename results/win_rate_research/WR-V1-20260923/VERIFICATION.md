# Win Rate Research V1 — verification

Behavior change: NO. Existing strategy behavior changed: NO.

Production functions, parameters and authoritative reference files are unchanged.
The requested research-only arms test different exits and entry skipping without
promoting a policy. Starting branch: `main`; starting working tree: clean.
No commit, push, merge or dependency installation was performed.

## Files

Added: `src/win_rate_research_runner.py`, `src/win_rate_research_analysis.py`,
`tests/test_win_rate_research.py`, and the session artifacts in
`results/win_rate_research/WR-V1-20260923/`.
Modified: `ARCHITECTURE.md` and `.gitignore` (research process lock only).
Historical research artifacts and registries remain unchanged, checked through
the saved source/input hash identity during the completed resume run.

## Unit / regression

Before implementation, from the project root:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider
```

**159 passed, 1 warning in 37.23s.**

Focused suite after implementation:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_win_rate_research.py -q -p no:cacheprovider
```

**19 passed, 1 warning in 1.54s.** Includes disabled-rule ledger/state/reconciliation
identity, dynamic/locked ATR and trend modes, empty/timezone schemas, same-bar
stop causality, gap fills, delayed market exits, final censoring, future mutation
prefix invariance, re-entry, unsupported Short/research rule rejection, taxonomy
thresholds and uncertain bounds, winner timing, ties/PF, boundary purging,
provenance pairing, robust frontier gates, stage prerequisites, interruption,
resume and corrupted artifact rejection.

Full deterministic suite after implementation, same command as baseline:

**178 passed, 1 warning in 78.62s.**

The warning is the existing urllib3/LibreSSL environment warning. The research
run additionally emitted a pandas FutureWarning about concatenating empty
frames; no calculation failed and the environment is frozen in the plan.

```sh
git diff --check
PYTHONPYCACHEPREFIX=/tmp/win-rate-pycache .venv/bin/python -m py_compile src/win_rate_research_runner.py src/win_rate_research_analysis.py tests/test_win_rate_research.py
```

Both passed (exit 0). Final scope inspection found only the files listed above.

## Integration

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m src.win_rate_research_runner --all
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m src.win_rate_research_runner --resume
```

Both passed (exit 0). All **8 stages COMPLETED**. The second command reported
**REUSED** for every stage. All **15,575** existing immutable artifact modification
timestamps were unchanged (the mutable `research_state.json` was excluded).
This verification note was added afterward, outside stage completion manifests.

Frozen local integration covered all 50 symbols and four pure Long modules,
with 1,159 closed baseline trades. Disabled-intervention ledgers/reconciliation
matched the existing reference outputs on all 200 symbol/module streams.
Actual-data assertions passed for MFE/MAE bounds, exhaustive loss category
fractions, closed-loss denominators and unique symbol/module/signal provenance.
48 predefined exit scenarios and 9 existing entry-region skips completed.
No exit scenario survived the frozen discovery screen; therefore the combined
stage correctly recorded no admissible combinations rather than running a grid.
All 61 baseline/scenario streams have robustness outputs.

Yahoo/network integration was **not run**: the task uses the verified frozen
snapshot and existing Entry/Exit V1 outputs.

## Parity / reference

Original Python engine equivalence: passed as described above. Pine/reference
files were read for semantics and left unchanged. External TradingView/Pine
broker-emulator parity was **not run or claimed**.

## Contracts and limitations

Signals/features are available at signal-bar close; entries and scheduled market
exits fill at the next open. Stops update only after survived closes and become
active next bar. Original OHLCV/index/timezone/warm-up and lifecycle bounds are
preserved. New retrospective fields remain separate from decision-time inputs.
Rates/returns are fractions; zero return is not a winner; censored trades are
not losses. Short interventions are unsupported and rejected explicitly.

No untouched confirmatory data, transaction costs, sizing or portfolio model is
available. Prior Entry Holdout and all exit-used history are labeled accordingly.
Low MeanRev sample, unresolved Breakout/Squeeze exits, winner-tail dependence,
correlated observations and present-day universe selection limit conclusions.
Path categories are not causal attribution. No production change follows this
research, and no next phase or automation has been started.
