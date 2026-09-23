# Verification and completion

Behavior change: NO. Existing strategy behavior changed: NO.
No existing strategy, diagnostics, backtest, evaluation, Pine or execution-contract
source file was modified. The research-only cohort gate retains all bars,
indicators, score/masks and initial warm-up. Outputs are retrospective.

## Unit / regression

Baseline command:
`PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider`

Before implementation: **127 passed, 1 warning in 5.79s**.

Focused command:
`PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_exit_research_runner.py`

**20 passed, 1 warning in 2.50s**. Coverage includes exact A/B equivalence,
pure-cohort exclusion without index/warm-up mutation, nullable/timezone cache
roundtrip, tail calculations, sample gates, one-sided/censored fills, bounded
retry, failure continuation, hash corruption, registry preservation, interrupted
symbol recovery, finite stopping and both required final interaction screens.

After implementation, before research: **147 passed, 1 warning in 7.34s**.
Final complete suite after research: **147 passed, 1 warning in 8.25s**.
The warning is the existing urllib3/LibreSSL compatibility warning.

`git diff --check`: passed.
`PYTHONPYCACHEPREFIX=/tmp/trust-me-exit-pycache .venv/bin/python -m py_compile src/exit_research_runner.py src/exit_research_analysis.py tests/test_exit_research_runner.py`: passed.

## Integration

Executed locally through `.venv/bin/python -u -m src.exit_research_runner --remaining`.
The existing Yahoo pipeline froze all 50 symbols; 49 have 1,253 daily rows from
2021-09-23 through 2026-09-21, ARM has 757 rows from 2023-09-14 through 2026-09-21.
The valid snapshot has **zero download, diagnostics or execution failures**.

Initial pre-research data validation rejected 12 symbols after two attempts each
because the latest response contained nonfinite OHLCV. AAPL inspection isolated
a missing close on 2026-09-22. The initial run was stopped before any backtest.
Its manifest remains available and the common cutoff was fixed before research.
Rejected initial symbols: AAPL, AMD, ARM, ASML, AVGO, MRVL, MSFT, MU, NVDA, QCOM, SMCI, TSM.

Executed **20 new A/B comparisons** (10 per module), registered exactly once;
**16 unique configurations / 800 symbol-configuration executions**.
Reused **15 completed historical experiments as evidence** (5 MeanRev, 10 Pure
Pullback); did not rerun any. Three older broad experiments were inspected as
context, not substituted for a pure-only execution population.

Ran the complete CLI a second time with the frozen snapshot, inside the network
sandbox. All 20 completed comparisons were reused, with no download or execution.
SHA256 verification found **304 snapshot, experiment and registry files
byte-identical** before/after resume. Registry remains 35 unique rows (15 original
plus 20 new), preserving original bytes. All 18 original experiment folders'
CSV hashes were unchanged. New artifacts have 50-symbol metadata/summaries,
unique symbol/signal_time/direction keys, Long direction and exact pure mask.

## Parity / reference

Reviewed Pine intent and the research execution contract. Existing deterministic
regressions and direct paired-schema equivalence pass. No new TradingView or
manual network parity run was performed; no parity claim is made.

## Completion

Breakout: INCONCLUSIVE, 1,013 signals, 485–643 comparable pairs.
Squeeze: INCONCLUSIVE, 282 signals, 186–203 comparable pairs.
Both finite grids are complete. No multiplier passed the predefined candidate
screen, so candidate-dependent final interactions are not applicable. The runner
was tested to require both interactions before promoting a candidate.
No grid extension, entry research, adaptive policy or production setting change.

Limits: conservative descriptive gates, current-universe selection bias,
unequal IPO histories, no costs/sizing/portfolio contention, correlated trades,
no OOS verification. Next requested phase is entry research; exit uncertainties
must remain explicit and OOS evaluation is still pending.
