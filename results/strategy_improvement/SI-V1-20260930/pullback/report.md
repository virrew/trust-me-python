# Strategy Improvement / Trade Lifecycle Research V1

Behavior change: NO. Existing strategy behavior changed: NO. Existing production functions, defaults, references and earlier research artifacts are unchanged. Alternative behavior exists only in explicitly isolated research arms.

Git commit studied: `14dc1659a824ad7142693e3ed55de879077881a3`. Frozen snapshot: `EXIT-V1-20260923-CLOSED` (`b3208fa046c8a09e6067f5dbfa8ffafd11b1d4855662d79b9e42b5cc8d5300d3`). 1163 lifecycle trades, 1159 closed, 4 censored. 50 symbols, Long only, independent module streams; this is not a combined portfolio.

**ALL CURRENT HISTORY HAS ALREADY BEEN TOUCHED BY PREVIOUS RESEARCH. No untouched OOS or confirmatory data.** Discovery is strictly closed before 2025-09-21; boundary-crossing outcomes cannot select candidates. Entry Holdout begins at that boundary. Earlier Entry/Exit/WR studies used the history, including holdout.

Reference exits: MeanRev Dynamic ATR 2 / Trend OFF (PROVISIONAL), Pullback Dynamic 1.5 / Trend ON (RESEARCH BASELINE), Breakout and Squeeze Dynamic 2.5 / Trend ON (INCONCLUSIVE). No transaction costs, sizing or portfolio effects. All returns and rates in CSVs/tables are fractions; peak ages are one-based holding bars. Exact-peak summaries exclude intrabar-ambiguous peaks and export their missing counts.

## pullback

1. **What currently causes most losses?** Largest descriptive category: SMALL_PROFIT_GIVEBACK; this is a path description, not an identified cause.
2. **What fraction of losers never worked?** 59/208 (28.4%) never reached even a possible +0.5%.
3. **What fraction became materially profitable first?** 60/208 (28.8%) definitely reached +2%; 144/208 (69.2%) reached +0.5%.
4. **Typical loser MFE?** Median known lower bound 1.13%; upper bounds remain in raw labels.
5. **Typical winner MFE?** Median known lower bound 8.08%.
6. **Typical winner MFE peak?** Exact median holding bar 6.0; 3 of 155 peaks ambiguous.
7. **Typical loser MFE peak?** Exact median holding bar 1.0; 17 of 208 peaks ambiguous.
8. **Typical winner giveback?** Median surrendered return 4.26%; median exact-MFE fraction 51.0%.
9. **Typical loser giveback?** Median surrendered return 3.65%; median exact-MFE fraction 245.3%.
10. **How much positive excursion is surrendered?** Across closed independent trades: mean known MFE minus realized return 4.35%; this is not capturable portfolio profit.
11. **Which entry filters appear too strict?** None with fully replicated strictness evidence.
12. **Which accepted regions appear too loose?** No previously frozen region passed the repeated weak-lifecycle discovery screen; unconfirmed associations remain in stage 2.
13. **Best isolated entry intervention?** NONE by discovery expectancy only; this ranking is descriptive and never a production recommendation.
14. **Best lifecycle intervention?** adaptive by discovery expectancy only; all tested candidates and failed gates are shown below.
15. **How many losers did the displayed lifecycle candidate rescue?** 3 to winners, 3 to non-loss; denominator 208 matched historical losers; all-baseline rescue rate 1.4%.
16. **How many winners did it damage?** 0 earned less, 0 became non-winners, 0 large winners lost >25% of return. 0 original winners lost their fill.
17. **Effect on WR?** 42.70% → 43.53% (+0.83 percentage points).
18. **Effect on PF?** 1.617 → 1.623 (+0.005).
19. **Effect on expectancy?** 0.97% → 0.97% (+0.01%).
20. **Effect on mean / median winner?** 5.92%/2.95% → 5.82%/2.83%.
21. **Effect on mean / median loser?** -2.73%/-2.15% → -2.76%/-2.17%.
22. **Effect on median trade?** -0.68% → -0.61% (+0.07%).
23. **Effect on tail dependence?** Top-five winners share gross profit: 17.7% → 17.7%; status MIXED. Exact top-1/3/5 deletion results are in stage 9.
24. **Is a combined Strategy V2 candidate justified?** NO COMBINATION: independent discovery screen failed
25. **What remains unresolved?** Causal entry vs management attribution, cost sensitivity, unseen-data replication, intrabar order, and regime stability. No untested lifecycle threshold is promoted.

All isolated/combined scenarios; ranking never overrides the frozen screen:

| scenario | status | trades | win_rate | profit_factor | expectancy | median_return | mean_winner | median_winner | mean_loser | median_loser | loser_to_win | winner_damaged | winner_destroyed | large_winner_truncated | a_only_fills | b_only_fills |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| giveback | FAILED | 364 | 0.43956 | 1.4977 | 0.0074036 | -0.0050522 | 0.050684 | 0.020495 | -0.026542 | -0.021166 | 10 | 20 | 6 | 5 | 0 | 1 |
| stalled | FAILED | 363 | 0.42975 | 1.6123 | 0.009568 | -0.0067863 | 0.058627 | 0.028318 | -0.027404 | -0.021562 | 1 | 2 | 0 | 0 | 0 | 0 |
| adaptive | MIXED | 363 | 0.43526 | 1.6227 | 0.0097145 | -0.0061272 | 0.058159 | 0.028318 | -0.027623 | -0.02166 | 3 | 0 | 0 | 0 | 0 | 0 |

Threshold crossings by chronological period (conditional outcomes; not executable rescue probabilities):

| partition | threshold | closed | final_win_rate | probability_loss | median_final_return | median_remaining_upside_lower | median_bars_to_next_high | median_giveback_before_next_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BOUNDARY / CENSORED | 0.005 | 2 | 0.5 | 0.5 | 0.0018491 | 0.022169 | 1 | 0.31343 |
| BOUNDARY / CENSORED | 0.01 | 2 | 0.5 | 0.5 | 0.0018491 | 0.022169 | 1 | 0.31343 |
| BOUNDARY / CENSORED | 0.02 | 2 | 0.5 | 0.5 | 0.0018491 | 0 | NA | NA |
| BOUNDARY / CENSORED | 0.03 | 1 | 1 | 0 | 0.0057707 | 0 | NA | NA |
| BOUNDARY / CENSORED | 0.04 | 1 | 1 | 0 | 0.0057707 | 0 | NA | NA |
| ENTRY HOLDOUT / EXIT-USED HISTORY | 0.005 | 67 | 0.41791 | 0.58209 | -0.0054444 | 0.0045545 | 1 | 0.28527 |
| ENTRY HOLDOUT / EXIT-USED HISTORY | 0.01 | 56 | 0.48214 | 0.51786 | -0.00095606 | 0.011473 | 1 | 0.28527 |
| ENTRY HOLDOUT / EXIT-USED HISTORY | 0.02 | 46 | 0.58696 | 0.41304 | 0.01036 | 0.016122 | 1 | 0.269 |
| ENTRY HOLDOUT / EXIT-USED HISTORY | 0.03 | 34 | 0.76471 | 0.23529 | 0.02505 | 0.024161 | 1 | 0.21801 |
| ENTRY HOLDOUT / EXIT-USED HISTORY | 0.04 | 29 | 0.82759 | 0.17241 | 0.027472 | 0.023156 | 1 | 0.20369 |
| IN-SAMPLE | 0.005 | 227 | 0.54185 | 0.45815 | 0.0022589 | 0.0215 | 1 | 0.50587 |
| IN-SAMPLE | 0.01 | 201 | 0.58706 | 0.41294 | 0.0061056 | 0.023152 | 1 | 0.33111 |
| IN-SAMPLE | 0.02 | 152 | 0.73684 | 0.26316 | 0.018359 | 0.035977 | 1 | 0.22341 |
| IN-SAMPLE | 0.03 | 131 | 0.81679 | 0.18321 | 0.026477 | 0.030319 | 1 | 0.1799 |
| IN-SAMPLE | 0.04 | 114 | 0.86842 | 0.13158 | 0.035249 | 0.032281 | 1 | 0.17311 |
