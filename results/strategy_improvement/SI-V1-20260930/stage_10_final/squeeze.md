# Strategy Improvement / Trade Lifecycle Research V1

Behavior change: NO. Existing strategy behavior changed: NO. Existing production functions, defaults, references and earlier research artifacts are unchanged. Alternative behavior exists only in explicitly isolated research arms.

Git commit studied: `14dc1659a824ad7142693e3ed55de879077881a3`. Frozen snapshot: `EXIT-V1-20260923-CLOSED` (`b3208fa046c8a09e6067f5dbfa8ffafd11b1d4855662d79b9e42b5cc8d5300d3`). 1163 lifecycle trades, 1159 closed, 4 censored. 50 symbols, Long only, independent module streams; this is not a combined portfolio.

**ALL CURRENT HISTORY HAS ALREADY BEEN TOUCHED BY PREVIOUS RESEARCH. No untouched OOS or confirmatory data.** Discovery is strictly closed before 2025-09-21; boundary-crossing outcomes cannot select candidates. Entry Holdout begins at that boundary. Earlier Entry/Exit/WR studies used the history, including holdout.

Reference exits: MeanRev Dynamic ATR 2 / Trend OFF (PROVISIONAL), Pullback Dynamic 1.5 / Trend ON (RESEARCH BASELINE), Breakout and Squeeze Dynamic 2.5 / Trend ON (INCONCLUSIVE). No transaction costs, sizing or portfolio effects. All returns and rates in CSVs/tables are fractions; peak ages are one-based holding bars. Exact-peak summaries exclude intrabar-ambiguous peaks and export their missing counts.

## squeeze

1. **What currently causes most losses?** Largest descriptive category: MAJOR_GIVEBACK; this is a path description, not an identified cause.
2. **What fraction of losers never worked?** 22/128 (17.2%) never reached even a possible +0.5%.
3. **What fraction became materially profitable first?** 73/128 (57.0%) definitely reached +2%; 105/128 (82.0%) reached +0.5%.
4. **Typical loser MFE?** Median known lower bound 2.35%; upper bounds remain in raw labels.
5. **Typical winner MFE?** Median known lower bound 12.54%.
6. **Typical winner MFE peak?** Exact median holding bar 16.0; 1 of 66 peaks ambiguous.
7. **Typical loser MFE peak?** Exact median holding bar 2.0; 6 of 128 peaks ambiguous.
8. **Typical winner giveback?** Median surrendered return 6.56%; median exact-MFE fraction 53.7%.
9. **Typical loser giveback?** Median surrendered return 5.63%; median exact-MFE fraction 226.2%.
10. **How much positive excursion is surrendered?** Across closed independent trades: mean known MFE minus realized return 7.00%; this is not capturable portfolio profit.
11. **Which entry filters appear too strict?** None with fully replicated strictness evidence.
12. **Which accepted regions appear too loose?** No previously frozen region passed the repeated weak-lifecycle discovery screen; unconfirmed associations remain in stage 2.
13. **Best isolated entry intervention?** NONE by discovery expectancy only; this ranking is descriptive and never a production recommendation.
14. **Best lifecycle intervention?** adaptive by discovery expectancy only; all tested candidates and failed gates are shown below.
15. **How many losers did the displayed lifecycle candidate rescue?** 2 to winners, 2 to non-loss; denominator 128 matched historical losers; all-baseline rescue rate 1.6%.
16. **How many winners did it damage?** 3 earned less, 2 became non-winners, 0 large winners lost >25% of return. 0 original winners lost their fill.
17. **Effect on WR?** 34.02% → 34.02% (+0.00 percentage points).
18. **Effect on PF?** 1.144 → 1.131 (-0.013).
19. **Effect on expectancy?** 0.35% → 0.32% (-0.03%).
20. **Effect on mean / median winner?** 8.18%/5.36% → 8.06%/5.21%.
21. **Effect on mean / median loser?** -3.69%/-3.17% → -3.67%/-3.17%.
22. **Effect on median trade?** -1.93% → -1.93% (+0.00%).
23. **Effect on tail dependence?** Top-five winners share gross profit: 30.6% → 31.1%; status TAIL-SENSITIVE. Exact top-1/3/5 deletion results are in stage 9.
24. **Is a combined Strategy V2 candidate justified?** NO COMBINATION: independent discovery screen failed
25. **What remains unresolved?** Causal entry vs management attribution, cost sensitivity, unseen-data replication, intrabar order, and regime stability. Exit-policy uncertainty remains INCONCLUSIVE.

All isolated/combined scenarios; ranking never overrides the frozen screen:

| scenario | status | trades | win_rate | profit_factor | expectancy | median_return | mean_winner | median_winner | mean_loser | median_loser | loser_to_win | winner_damaged | winner_destroyed | large_winner_truncated | a_only_fills | b_only_fills |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| giveback | TAIL-SENSITIVE | 197 | 0.41624 | 0.97293 | -0.00056865 | -0.0083801 | 0.049099 | 0.021268 | -0.035984 | -0.031562 | 17 | 14 | 4 | 8 | 0 | 2 |
| stalled | TAIL-SENSITIVE | 194 | 0.34021 | 1.1299 | 0.0031519 | -0.019263 | 0.08059 | 0.052074 | -0.036777 | -0.031667 | 1 | 3 | 1 | 0 | 0 | 0 |
| adaptive | TAIL-SENSITIVE | 194 | 0.34021 | 1.1307 | 0.0031681 | -0.019263 | 0.080575 | 0.052074 | -0.036745 | -0.031667 | 2 | 3 | 2 | 0 | 0 | 0 |

Threshold crossings by chronological period (conditional outcomes; not executable rescue probabilities):

| partition | threshold | closed | final_win_rate | probability_loss | median_final_return | median_remaining_upside_lower | median_bars_to_next_high | median_giveback_before_next_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BOUNDARY / CENSORED | 0.005 | 2 | 0.5 | 0.5 | 0.01397 | 0.071247 | 1 | 0.94444 |
| BOUNDARY / CENSORED | 0.01 | 2 | 0.5 | 0.5 | 0.01397 | 0.071247 | 1 | 0.94444 |
| BOUNDARY / CENSORED | 0.02 | 1 | 1 | 0 | 0.072791 | 0.14249 | 1 | 0.94444 |
| BOUNDARY / CENSORED | 0.03 | 1 | 1 | 0 | 0.072791 | 0.02964 | 1 | 0.026849 |
| BOUNDARY / CENSORED | 0.04 | 1 | 1 | 0 | 0.072791 | 0.02964 | 1 | 0.026849 |
| ENTRY HOLDOUT / EXIT-USED HISTORY | 0.005 | 32 | 0.375 | 0.625 | -0.022824 | 0.024559 | 1 | 0.92325 |
| ENTRY HOLDOUT / EXIT-USED HISTORY | 0.01 | 29 | 0.41379 | 0.58621 | -0.015575 | 0.030698 | 1 | 0.59391 |
| ENTRY HOLDOUT / EXIT-USED HISTORY | 0.02 | 24 | 0.5 | 0.5 | -0.00062269 | 0.032784 | 1 | 0.22398 |
| ENTRY HOLDOUT / EXIT-USED HISTORY | 0.03 | 22 | 0.54545 | 0.45455 | 0.0070325 | 0.030131 | 1 | 0.39505 |
| ENTRY HOLDOUT / EXIT-USED HISTORY | 0.04 | 18 | 0.66667 | 0.33333 | 0.012431 | 0.031122 | 1 | 0.39024 |
| IN-SAMPLE | 0.005 | 137 | 0.38686 | 0.61314 | -0.0097942 | 0.030187 | 1 | 0.75903 |
| IN-SAMPLE | 0.01 | 131 | 0.40458 | 0.59542 | -0.0072421 | 0.030187 | 1 | 0.66062 |
| IN-SAMPLE | 0.02 | 114 | 0.46491 | 0.53509 | -0.0037896 | 0.030808 | 1 | 0.41907 |
| IN-SAMPLE | 0.03 | 93 | 0.56989 | 0.43011 | 0.010804 | 0.033666 | 1 | 0.26846 |
| IN-SAMPLE | 0.04 | 79 | 0.67089 | 0.32911 | 0.02846 | 0.03456 | 1 | 0.17623 |
