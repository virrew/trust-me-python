# Strategy Improvement / Trade Lifecycle Research V1

Behavior change: NO. Existing strategy behavior changed: NO. Existing production functions, defaults, references and earlier research artifacts are unchanged. Alternative behavior exists only in explicitly isolated research arms.

Git commit studied: `14dc1659a824ad7142693e3ed55de879077881a3`. Frozen snapshot: `EXIT-V1-20260923-CLOSED` (`b3208fa046c8a09e6067f5dbfa8ffafd11b1d4855662d79b9e42b5cc8d5300d3`). 1163 lifecycle trades, 1159 closed, 4 censored. 50 symbols, Long only, independent module streams; this is not a combined portfolio.

**ALL CURRENT HISTORY HAS ALREADY BEEN TOUCHED BY PREVIOUS RESEARCH. No untouched OOS or confirmatory data.** Discovery is strictly closed before 2025-09-21; boundary-crossing outcomes cannot select candidates. Entry Holdout begins at that boundary. Earlier Entry/Exit/WR studies used the history, including holdout.

Reference exits: MeanRev Dynamic ATR 2 / Trend OFF (PROVISIONAL), Pullback Dynamic 1.5 / Trend ON (RESEARCH BASELINE), Breakout and Squeeze Dynamic 2.5 / Trend ON (INCONCLUSIVE). No transaction costs, sizing or portfolio effects. All returns and rates in CSVs/tables are fractions; peak ages are one-based holding bars. Exact-peak summaries exclude intrabar-ambiguous peaks and export their missing counts.

## meanrev

1. **What currently causes most losses?** Largest descriptive category: SMALL_PROFIT_GIVEBACK; this is a path description, not an identified cause.
2. **What fraction of losers never worked?** 5/28 (17.9%) never reached even a possible +0.5%.
3. **What fraction became materially profitable first?** 11/28 (39.3%) definitely reached +2%; 23/28 (82.1%) reached +0.5%.
4. **Typical loser MFE?** Median known lower bound 1.37%; upper bounds remain in raw labels.
5. **Typical winner MFE?** Median known lower bound 12.29%.
6. **Typical winner MFE peak?** Exact median holding bar 10.5; 1 of 27 peaks ambiguous.
7. **Typical loser MFE peak?** Exact median holding bar 1.0; 0 of 28 peaks ambiguous.
8. **Typical winner giveback?** Median surrendered return 5.96%; median exact-MFE fraction 54.0%.
9. **Typical loser giveback?** Median surrendered return 6.17%; median exact-MFE fraction 414.8%.
10. **How much positive excursion is surrendered?** Across closed independent trades: mean known MFE minus realized return 6.33%; this is not capturable portfolio profit.
11. **Which entry filters appear too strict?** None with fully replicated strictness evidence.
12. **Which accepted regions appear too loose?** No previously frozen region passed the repeated weak-lifecycle discovery screen; unconfirmed associations remain in stage 2.
13. **Best isolated entry intervention?** NONE by discovery expectancy only; this ranking is descriptive and never a production recommendation.
14. **Best lifecycle intervention?** NONE by discovery expectancy only; all tested candidates and failed gates are shown below.
15. **How many losers did the displayed lifecycle candidate rescue?** No candidate: insufficient discovery mechanism sample.
16. **How many winners did it damage?** No new intervention tested.
17. **Effect on WR?** No proposed change.
18. **Effect on PF?** No proposed change.
19. **Effect on expectancy?** No proposed change.
20. **Effect on mean / median winner?** Baseline 7.11%/4.91%.
21. **Effect on mean / median loser?** Baseline -4.22%/-3.62%.
22. **Effect on median trade?** Baseline -0.01%.
23. **Effect on tail dependence?** Small sample; prior interventions did not clear all gates.
24. **Is a combined Strategy V2 candidate justified?** NO COMBINATION: independent discovery screen failed
25. **What remains unresolved?** Causal entry vs management attribution, cost sensitivity, unseen-data replication, intrabar order, and regime stability. MeanRev sample remains limited.

All isolated/combined scenarios; ranking never overrides the frozen screen:

| scenario | status | trades | win_rate | profit_factor | expectancy | median_return | mean_winner | median_winner | mean_loser | median_loser | loser_to_win | winner_damaged | winner_destroyed | large_winner_truncated | a_only_fills | b_only_fills |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |


Threshold crossings by chronological period (conditional outcomes; not executable rescue probabilities):

| partition | threshold | closed | final_win_rate | probability_loss | median_final_return | median_remaining_upside_lower | median_bars_to_next_high | median_giveback_before_next_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ENTRY HOLDOUT / EXIT-USED HISTORY | 0.005 | 9 | 0.33333 | 0.66667 | -0.023304 | 0 | 3 | 2.5396 |
| ENTRY HOLDOUT / EXIT-USED HISTORY | 0.01 | 7 | 0.42857 | 0.57143 | -0.019409 | 0.0090075 | 2.5 | 1.6794 |
| ENTRY HOLDOUT / EXIT-USED HISTORY | 0.02 | 4 | 0.75 | 0.25 | 0.084116 | 0.097993 | 1 | 0.5223 |
| ENTRY HOLDOUT / EXIT-USED HISTORY | 0.03 | 3 | 1 | 0 | 0.12891 | 0.15578 | 1 | 0.5223 |
| ENTRY HOLDOUT / EXIT-USED HISTORY | 0.04 | 3 | 1 | 0 | 0.12891 | 0.12794 | 1 | 0.042401 |
| IN-SAMPLE | 0.005 | 41 | 0.58537 | 0.41463 | 0.0070776 | 0.045478 | 1 | 0.63253 |
| IN-SAMPLE | 0.01 | 36 | 0.66667 | 0.33333 | 0.018321 | 0.048616 | 1 | 0.57194 |
| IN-SAMPLE | 0.02 | 34 | 0.70588 | 0.29412 | 0.021436 | 0.048616 | 1 | 0.33794 |
| IN-SAMPLE | 0.03 | 32 | 0.71875 | 0.28125 | 0.027334 | 0.039384 | 1 | 0.2607 |
| IN-SAMPLE | 0.04 | 28 | 0.82143 | 0.17857 | 0.036636 | 0.056556 | 1 | 0.17688 |
