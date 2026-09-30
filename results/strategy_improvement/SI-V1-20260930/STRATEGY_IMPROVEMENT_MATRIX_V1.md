# Strategy Improvement / Trade Lifecycle Research V1

Behavior change: NO. Existing strategy behavior changed: NO. Existing production functions, defaults, references and earlier research artifacts are unchanged. Alternative behavior exists only in explicitly isolated research arms.

Git commit studied: `14dc1659a824ad7142693e3ed55de879077881a3`. Frozen snapshot: `EXIT-V1-20260923-CLOSED` (`b3208fa046c8a09e6067f5dbfa8ffafd11b1d4855662d79b9e42b5cc8d5300d3`). 1163 lifecycle trades, 1159 closed, 4 censored. 50 symbols, Long only, independent module streams; this is not a combined portfolio.

**ALL CURRENT HISTORY HAS ALREADY BEEN TOUCHED BY PREVIOUS RESEARCH. No untouched OOS or confirmatory data.** Discovery is strictly closed before 2025-09-21; boundary-crossing outcomes cannot select candidates. Entry Holdout begins at that boundary. Earlier Entry/Exit/WR studies used the history, including holdout.

Reference exits: MeanRev Dynamic ATR 2 / Trend OFF (PROVISIONAL), Pullback Dynamic 1.5 / Trend ON (RESEARCH BASELINE), Breakout and Squeeze Dynamic 2.5 / Trend ON (INCONCLUSIVE). No transaction costs, sizing or portfolio effects. All returns and rates in CSVs/tables are fractions; peak ages are one-based holding bars. Exact-peak summaries exclude intrabar-ambiguous peaks and export their missing counts.

## Baseline

| module | trades | winners | losers | win_rate | profit_factor | expectancy | mean_winner | mean_loser |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| breakout | 547 | 223 | 324 | 0.40768 | 1.1136 | 0.0029321 | 0.070512 | -0.043581 |
| meanrev | 55 | 27 | 28 | 0.49091 | 1.6243 | 0.013411 | 0.07108 | -0.042199 |
| pullback | 363 | 155 | 208 | 0.427 | 1.6172 | 0.0096519 | 0.059225 | -0.027289 |
| squeeze | 194 | 66 | 128 | 0.34021 | 1.1438 | 0.0034972 | 0.081789 | -0.036872 |

## Main research questions

**Why is current win rate low?**

688 closed losses versus 471 wins; 548 losses first achieved known +0.5% and 313 achieved +2%. Loose return retention and noisy entries both contribute descriptively; expectancy also depends on the larger winners.

**Poor entries or poor lifecycle management?**

Only 133/688 losers definitely never reached +0.5%. Worked-then-failed paths dominate, but this does not prove an exit fix can rescue them without harming winners. Intrabar ambiguity and selection prevent causal attribution.

**Which current filters block historically good opportunities?**

bo_long_fail_price is the sole fully replicated Entry V1 strictness hypothesis. Forward returns were observational. Its isolated realized replay, original-mask provenance, occupancy changes and failed/passed gates appear in the Breakout section.

**Which filters fail to exclude bad opportunities?**

Passing rules cannot establish causal false positives. Stage 2 reports every current filter and frozen accepted bin; stage 6 applies the preregistered repeated-weak-region screen. No arbitrary new feature bins or early-failure filter were invented.

**How much MFE makes a winner durable?**

No guaranteed threshold. Stage 3 gives +0.5/1/2/3/4% first-crossing win/loss probabilities, remaining MFE bounds and missing counts separately by module/period. Even +4% can precede a loss; final MFE never enters a decision feature.

**When does a runner resemble a future giveback loser?**

The empirical state curves stratify known running MFE, close giveback and time since a strict new high. Repeated rows are dependent. Candidate boundaries came only from discovery winner tolerance and loser MFE, then were frozen before replay; there is no universally demonstrated decay boundary.

**How much MFE can safely be given back?**

No safety guarantee. Large (>=10%) winners have median maximum close giveback after +2% MFE of 55.5%, q75 95.1%; missing=0. A tight fractional lock can interrupt normal winners; actual truncation counts determine acceptance.

**How long do winners create new highs?**

Median last survived strict high is holding bar 10.0; median total holding 13.0; large-winner last high median 19.0. Exact peak timing and gaps between highs are exported per module and period.

**How long do material giveback losers stall before failing?**

Median exact peak-to-exit interval 3.0 bars; 6/313 exact timings unavailable. A stalled state is not by itself a causal failure signal.

**What fraction of losses can be rescued without excessive winner destruction?**

No fraction is established beyond the finite causal replays. Each scenario exports matched and all-baseline loser denominators, winner damage/destruction, large-winner truncation and one-sided fills. Scenarios passing both chronological multi-objective screens: none.

**Can WR rise without collapsing winner size?**

Compare actual deltas and the >=90% mean/median winner preservation screen, not just WR. Passing both complete screens: none. Previously aggressive lock25 remains a caution, not an adopted policy.

**Can PF and expectancy improve together?**

Observed full-history increases in both: pullback/adaptive, breakout/adaptive, breakout/relax_price. This is descriptive; discovery, tail, year/symbol, count and holdout failures remain binding.

**Can median trade improve?**

Observed positive median-trade changes: pullback/giveback, pullback/adaptive, breakout/giveback, breakout/stalled, breakout/adaptive, squeeze/giveback, breakout/relax_price. The same winner-preservation and robustness requirements apply.

**Which module has the clearest improvement opportunity?**

Breakout has the clearest replicated entry-filter hypothesis and many material giveback losses. That identifies a research mechanism, not a supported production change; its exit policy is still unresolved. Candidate-specific evidence is enumerated without picking a full-history winner.

**Which module should remain mostly unchanged?**

MeanRev: only 55 closed reference trades and a provisional exit policy. Other modules also retain their current production behavior regardless of isolated research results.

**Is there enough evidence for a combined Strategy V2?**

meanrev: NO COMBINATION: independent discovery screen failed; pullback: NO COMBINATION: independent discovery screen failed; breakout: NO COMBINATION: independent discovery screen failed; squeeze: NO COMBINATION: independent discovery screen failed. No combination is constructed when either independent family fails.

**Exact next research step?**

Keep these candidate definitions and hashes fixed. First resolve the documented Breakout/Squeeze reference-exit uncertainty under a preregistered cost-aware protocol; then evaluate any surviving fixed hypothesis on genuinely later unseen bars with a prospectively fixed universe. Collect more MeanRev observations. Do not retune on this snapshot, deploy a descriptive maximum, train ML or start another phase automatically.

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

## Interpretation and recovery

State-curve rows are dependent bar observations, with unique-trade counts and eligible denominators. Exit is a competing event for the next-high horizon; unknown stop-bar ordering and unresolved censoring stay missing. Threshold crossing on an exit endpoint cannot trigger protection retroactively. More MFE is not a causal treatment and cannot guarantee a durable winner. Original-path trigger exposure is separate from actual replay rescue and damage. All scenarios replay their full signal streams, so changed occupancy and re-entry affect counts; pairing uses module/symbol/signal time, never ledger order.

The price-relaxation arm adds strict sole-price-blocker opportunities while retaining original diagnostic masks/scores (normally zero); these are experimental entries, not Pure activations. None of the prior broad-entry or observational conclusions is upgraded to execution evidence without its explicit replay table. No randomized intervention, economic significance, costs, untouched OOS, ML, scanner, or production Strategy V2 is claimed.

Every stage has CSV/schema outputs, a hashed completion marker and atomic research state. The plan pins source/runtime/snapshot/prior-artifact identity. Corruption fails closed; valid completed stages are reused. Resume: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m src.strategy_improvement_runner --resume`.
