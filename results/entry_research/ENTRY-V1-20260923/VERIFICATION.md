# Entry Research V1 completion verification

Behavior change: NO. Existing strategy behavior changed: NO.

The preceding process completed all 168 stages before continuation. No discovery,
holdout calculation, hypothesis generation or research-plan extension was rerun
on continuation. All checkpoint contents, frozen bin edges, discovery markers,
public reports, source/runtime identity and the original snapshot were verified.
The existing state remains COMPLETED; all 50 symbols succeeded.

Frozen hypotheses SHA-256:
`fde0abb632bb69da9998b195902f76f84ec24d1b7c9cf35fd10bad80176e6353`.
98 hypotheses: 1 REPLICATED, 10 PARTIAL, 9 FAILED HOLDOUT, 78 LOW SAMPLE,
0 INCONCLUSIVE. No hypotheses or bins were modified after holdout began.

Unit / regression:

- Baseline: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider`
  — 147 passed, 1 warning, 13.12s.
- Targeted: same command with `tests/test_entry_research.py`
  — 12 passed, 1 warning, 28.22s. Includes full synthetic execution and cache-only
  rerun, interrupted checkpoint recovery, corruption rejection, immutable
  hypotheses, feature-prefix causality, pure cohorts and empty schemas.
- Final full suite: baseline command — 159 passed, 1 warning, 38.09s.
- `git diff --check` — passed.
- `PYTHONPYCACHEPREFIX=/private/tmp/trust-me-entry-final-pycache .venv/bin/python -m py_compile src/entry_research_analysis.py src/entry_research_runner.py tests/test_entry_research.py`
  — passed.

The warning is the existing urllib3 / LibreSSL compatibility warning.

Integration: the complete frozen-data pipeline ran for all 50 symbols and all
four modules. Snapshot: EXIT-V1-20260923-CLOSED, 62,154 bars, 191 diagnostics.
No network integration or new Yahoo download was needed. Labels and features
are physically separate; 20-bar censoring is 1,000 bar observations in each
partition. Pure holdout signals with incomplete 20-bar outcomes: MeanRev 2,
Pullback 1, Breakout 15, Squeeze 5. Censoring is not failure or imputation.

Parity / reference: entry predicates were checked against the existing Pine
reference. No external TradingView numerical/broker-emulator parity was run.

`git diff --exit-code` over all production/core/diagnostic/outcome/backtest/exit
modules, reference files, research_registry.csv, EXIT_POLICY_MATRIX_V1.md,
results/exit_research, results/ab_tests and results/research_data was empty.
The separate entry registry contains one completed session record. Existing
uncommitted work has been retained; nothing was committed or pushed.

Added: src/entry_research_runner.py, src/entry_research_analysis.py,
tests/test_entry_research.py, results/entry_research_registry.csv and the session
artifacts (454 CSV files, schemas, checkpoints, frozen plan/hypotheses and reports).
Modified: .gitignore, ARCHITECTURE.md, README.md. No production Python file changed.

Important limits: Entry Holdout was previously used by Exit Research and is not
untouched strategy OOS. Cohorts/windows are dependent and unpaired, the universe
is selected today, many samples are small, and several effects depend on tails,
years or symbols. The only fully replicated observation is the descriptive
Breakout price sole-blocker contrast, not a safe module-rule ablation or proof
that relaxing the rule improves trading. No TAKE/SKIP feature fully replicated.

Exact next phase: a separately preregistered confirmatory walk-forward/OOS
entry study, with explicit research-only semantics for the Breakout price
hypothesis and suitably untouched evaluation data. No next-phase work,
production rule changes, ML training or automated TAKE/SKIP was started.
