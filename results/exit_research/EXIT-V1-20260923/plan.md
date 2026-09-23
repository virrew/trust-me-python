# Preregistered finite exit research plan V1

Pure Breakout then Pure Squeeze. Same 50-symbol universe, 5y Yahoo daily,
auto_adjust=False, Swing, Long only. Original indicator defaults and all warm-up
bars retained. Gate final long signal by exact module mask before replay.
No changes to production code, execution contract, Pine or entry rules.

Freeze one dataset per symbol before experiments; exclude the current New York
date (possibly incomplete daily bar). Preserve dtypes, timestamps, SHA256,
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
