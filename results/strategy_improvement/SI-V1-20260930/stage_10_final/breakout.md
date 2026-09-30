# Strategy Improvement / Trade Lifecycle Research V1

Behavior change: NO. Existing strategy behavior changed: NO. Existing production functions, defaults, references and earlier research artifacts are unchanged. Alternative behavior exists only in explicitly isolated research arms.

Git commit studied: `14dc1659a824ad7142693e3ed55de879077881a3`. Frozen snapshot: `EXIT-V1-20260923-CLOSED` (`b3208fa046c8a09e6067f5dbfa8ffafd11b1d4855662d79b9e42b5cc8d5300d3`). 1163 lifecycle trades, 1159 closed, 4 censored. 50 symbols, Long only, independent module streams; this is not a combined portfolio.

**ALL CURRENT HISTORY HAS ALREADY BEEN TOUCHED BY PREVIOUS RESEARCH. No untouched OOS or confirmatory data.** Discovery is strictly closed before 2025-09-21; boundary-crossing outcomes cannot select candidates. Entry Holdout begins at that boundary. Earlier Entry/Exit/WR studies used the history, including holdout.

Reference exits: MeanRev Dynamic ATR 2 / Trend OFF (PROVISIONAL), Pullback Dynamic 1.5 / Trend ON (RESEARCH BASELINE), Breakout and Squeeze Dynamic 2.5 / Trend ON (INCONCLUSIVE). No transaction costs, sizing or portfolio effects. All returns and rates in CSVs/tables are fractions; peak ages are one-based holding bars. Exact-peak summaries exclude intrabar-ambiguous peaks and export their missing counts.

## breakout

1. **What currently causes most losses?** Largest descriptive category: MAJOR_GIVEBACK; this is a path description, not an identified cause.
2. **What fraction of losers never worked?** 47/324 (14.5%) never reached even a possible +0.5%.
3. **What fraction became materially profitable first?** 169/324 (52.2%) definitely reached +2%; 276/324 (85.2%) reached +0.5%.
4. **Typical loser MFE?** Median known lower bound 2.11%; upper bounds remain in raw labels.
5. **Typical winner MFE?** Median known lower bound 11.25%.
6. **Typical winner MFE peak?** Exact median holding bar 12.0; 7 of 223 peaks ambiguous.
7. **Typical loser MFE peak?** Exact median holding bar 2.0; 2 of 324 peaks ambiguous.
8. **Typical winner giveback?** Median surrendered return 6.67%; median exact-MFE fraction 59.1%.
9. **Typical loser giveback?** Median surrendered return 6.39%; median exact-MFE fraction 274.2%.
10. **How much positive excursion is surrendered?** Across closed independent trades: mean known MFE minus realized return 7.38%; this is not capturable portfolio profit.
11. **Which entry filters appear too strict?** bo_long_fail_price
12. **Which accepted regions appear too loose?** No previously frozen region passed the repeated weak-lifecycle discovery screen; unconfirmed associations remain in stage 2.
13. **Best isolated entry intervention?** relax_price by discovery expectancy only; this ranking is descriptive and never a production recommendation.
14. **Best lifecycle intervention?** adaptive by discovery expectancy only; all tested candidates and failed gates are shown below.
15. **How many losers did the displayed lifecycle candidate rescue?** 19 to winners, 19 to non-loss; denominator 324 matched historical losers; all-baseline rescue rate 5.9%.
16. **How many winners did it damage?** 8 earned less, 1 became non-winners, 3 large winners lost >25% of return. 0 original winners lost their fill.
17. **Effect on WR?** 40.77% → 43.94% (+3.17 percentage points).
18. **Effect on PF?** 1.114 → 1.119 (+0.005).
19. **Effect on expectancy?** 0.29% → 0.29% (+0.00%).
20. **Effect on mean / median winner?** 7.05%/3.88% → 6.28%/3.03%.
21. **Effect on mean / median loser?** -4.36%/-4.01% → -4.40%/-4.05%.
22. **Effect on median trade?** -1.32% → -1.04% (+0.28%).
23. **Effect on tail dependence?** Top-five winners share gross profit: 14.0% → 14.4%; status TAIL-SENSITIVE. Exact top-1/3/5 deletion results are in stage 9.
24. **Is a combined Strategy V2 candidate justified?** NO COMBINATION: independent discovery screen failed
25. **What remains unresolved?** Causal entry vs management attribution, cost sensitivity, unseen-data replication, intrabar order, and regime stability. Exit-policy uncertainty remains INCONCLUSIVE.

All isolated/combined scenarios; ranking never overrides the frozen screen:

| scenario | status | trades | win_rate | profit_factor | expectancy | median_return | mean_winner | median_winner | mean_loser | median_loser | loser_to_win | winner_damaged | winner_destroyed | large_winner_truncated | a_only_fills | b_only_fills |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| giveback | TAIL-SENSITIVE | 577 | 0.44714 | 1.0724 | 0.0016157 | -0.0054015 | 0.053517 | 0.025256 | -0.040361 | -0.036273 | 32 | 28 | 9 | 14 | 0 | 29 |
| stalled | TAIL-SENSITIVE | 553 | 0.42495 | 1.1119 | 0.0027835 | -0.01048 | 0.065063 | 0.032902 | -0.04324 | -0.040345 | 12 | 8 | 1 | 4 | 0 | 5 |
| adaptive | TAIL-SENSITIVE | 553 | 0.43942 | 1.1189 | 0.0029347 | -0.010397 | 0.062843 | 0.030271 | -0.044025 | -0.040478 | 19 | 8 | 1 | 3 | 0 | 5 |
| relax_price | MIXED | 2004 | 0.43513 | 1.2078 | 0.0039839 | -0.0051209 | 0.053207 | 0.024286 | -0.033933 | -0.025882 | 0 | 0 | 0 | 0 | 279 | 1748 |

Threshold crossings by chronological period (conditional outcomes; not executable rescue probabilities):

| partition | threshold | closed | final_win_rate | probability_loss | median_final_return | median_remaining_upside_lower | median_bars_to_next_high | median_giveback_before_next_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BOUNDARY / CENSORED | 0.005 | 12 | 0.5 | 0.5 | -0.006244 | 0.025239 | 1 | 0.47619 |
| BOUNDARY / CENSORED | 0.01 | 12 | 0.5 | 0.5 | -0.006244 | 0.019467 | 1 | 0.37076 |
| BOUNDARY / CENSORED | 0.02 | 9 | 0.66667 | 0.33333 | 0.0090939 | 0.039094 | 2 | 0.784 |
| BOUNDARY / CENSORED | 0.03 | 8 | 0.75 | 0.25 | 0.013614 | 0.036827 | 1 | 0.24304 |
| BOUNDARY / CENSORED | 0.04 | 7 | 0.85714 | 0.14286 | 0.018135 | 0.029315 | 2.5 | 0.47534 |
| ENTRY HOLDOUT / EXIT-USED HISTORY | 0.005 | 113 | 0.38938 | 0.61062 | -0.013714 | 0.031013 | 1 | 0.65431 |
| ENTRY HOLDOUT / EXIT-USED HISTORY | 0.01 | 101 | 0.43564 | 0.56436 | -0.01036 | 0.036141 | 1 | 0.55185 |
| ENTRY HOLDOUT / EXIT-USED HISTORY | 0.02 | 88 | 0.5 | 0.5 | -0.0025408 | 0.035568 | 1 | 0.39239 |
| ENTRY HOLDOUT / EXIT-USED HISTORY | 0.03 | 77 | 0.55844 | 0.44156 | 0.0055585 | 0.037465 | 1 | 0.21636 |
| ENTRY HOLDOUT / EXIT-USED HISTORY | 0.04 | 69 | 0.62319 | 0.37681 | 0.01102 | 0.037465 | 1 | 0.18251 |
| IN-SAMPLE | 0.005 | 373 | 0.46113 | 0.53887 | -0.0050714 | 0.034318 | 1 | 0.57895 |
| IN-SAMPLE | 0.01 | 345 | 0.49855 | 0.50145 | -0.0013975 | 0.035743 | 1 | 0.46359 |
| IN-SAMPLE | 0.02 | 294 | 0.58503 | 0.41497 | 0.010423 | 0.036257 | 1 | 0.27602 |
| IN-SAMPLE | 0.03 | 252 | 0.6746 | 0.3254 | 0.018428 | 0.036664 | 1 | 0.23284 |
| IN-SAMPLE | 0.04 | 221 | 0.76471 | 0.23529 | 0.025734 | 0.038333 | 1 | 0.2255 |
