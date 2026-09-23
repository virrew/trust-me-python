# Win Rate Research Matrix V1

Behavior change: NO. Existing strategy behavior changed: NO. Research-only interventions; production code and authoritative references unchanged.

Frozen 50-symbol Daily snapshot `EXIT-V1-20260923-CLOSED`. Pure Long modules, one position per symbol/module; pooled modules are not a portfolio or the broad strategy. Entry Holdout starts 2025-09-21; discovery excludes trades whose exits cross the boundary. ALL history was previously used by Exit V1; Entry Holdout has already been examined by Entry V1. **No untouched CONFIRMATORY DATA is available.**

The premise of approximately 40% WR must be checked against the cohort and exit policy. MeanRev uses provisional Dynamic ATR 2 / Trend OFF; Pullback Dynamic 1.5 / Trend ON; Breakout and Squeeze use unresolved reference Dynamic 2.5 / Trend ON. Their full existing predefined configuration sensitivity is retained. Returns are raw fractions with no costs, sizing or portfolio aggregation. Break-even is not a win.

| module | trades | censored | winners | losers | ties | win_rate | mean_winner | median_winner | mean_loser | median_loser | average_return | median_return | expectancy | profit_factor | average_holding | median_holding | worst_return | p05_return | expected_shortfall05 | top5_share_gross_profit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| breakout | 547 | 2 | 223 | 324 | 0 | 0.40768 | 0.070512 | 0.038785 | -0.043581 | -0.040125 | 0.0029321 | -0.013198 | 0.0029321 | 1.1136 | 12.068 | 10 | -0.21954 | -0.083775 | -0.11096 | 0.14031 |
| meanrev | 55 | 1 | 27 | 28 | 0 | 0.49091 | 0.07108 | 0.049076 | -0.042199 | -0.036176 | 0.013411 | -0.00011655 | 0.013411 | 1.6243 | 11.491 | 10 | -0.10417 | -0.076553 | -0.090049 | 0.50065 |
| pullback | 363 | 0 | 155 | 208 | 0 | 0.427 | 0.059225 | 0.029505 | -0.027289 | -0.021542 | 0.0096519 | -0.0067863 | 0.0096519 | 1.6172 | 5.8567 | 4 | -0.12456 | -0.066761 | -0.08322 | 0.17721 |
| squeeze | 194 | 1 | 66 | 128 | 0 | 0.34021 | 0.081789 | 0.053582 | -0.036872 | -0.031667 | 0.0034972 | -0.019263 | 0.0034972 | 1.1438 | 11.954 | 8 | -0.1488 | -0.075071 | -0.09352 | 0.30609 |

Cross-module pooled independent research trades (NOT a portfolio or a deduplicated broad-strategy WR):

| trades | censored | winners | losers | ties | win_rate | mean_winner | median_winner | mean_loser | median_loser | average_return | median_return | expectancy | profit_factor | average_holding | median_holding | worst_return | p05_return | expected_shortfall05 | top5_share_gross_profit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1159 | 4 | 471 | 688 | 0 | 0.40638 | 0.06841 | 0.038427 | -0.037351 | -0.031667 | 0.0056286 | -0.010634 | 0.0056286 | 1.2539 | 10.076 | 7 | -0.21954 | -0.077713 | -0.10053 | 0.073916 |

Loss taxonomy (mutually exclusive, fractions of ALL losses; uncertainty retained):

| module | category | count | total_losses | fraction |
| --- | --- | --- | --- | --- |
| meanrev | GIVEBACK_LOSER | 11 | 28 | 0.39286 |
| meanrev | SMALL_PROFIT_GIVEBACK | 12 | 28 | 0.42857 |
| meanrev | DEAD_TRADE | 0 | 28 | 0 |
| meanrev | IMMEDIATE_FAILURE | 5 | 28 | 0.17857 |
| meanrev | NEVER_WORKED | 0 | 28 | 0 |
| meanrev | STOP_TIMING_OTHER | 0 | 28 | 0 |
| meanrev | UNCERTAIN_PATH | 0 | 28 | 0 |
| pullback | GIVEBACK_LOSER | 60 | 208 | 0.28846 |
| pullback | SMALL_PROFIT_GIVEBACK | 84 | 208 | 0.40385 |
| pullback | DEAD_TRADE | 0 | 208 | 0 |
| pullback | IMMEDIATE_FAILURE | 49 | 208 | 0.23558 |
| pullback | NEVER_WORKED | 10 | 208 | 0.048077 |
| pullback | STOP_TIMING_OTHER | 0 | 208 | 0 |
| pullback | UNCERTAIN_PATH | 5 | 208 | 0.024038 |
| breakout | GIVEBACK_LOSER | 169 | 324 | 0.5216 |
| breakout | SMALL_PROFIT_GIVEBACK | 107 | 324 | 0.33025 |
| breakout | DEAD_TRADE | 0 | 324 | 0 |
| breakout | IMMEDIATE_FAILURE | 44 | 324 | 0.1358 |
| breakout | NEVER_WORKED | 3 | 324 | 0.0092593 |
| breakout | STOP_TIMING_OTHER | 0 | 324 | 0 |
| breakout | UNCERTAIN_PATH | 1 | 324 | 0.0030864 |
| squeeze | GIVEBACK_LOSER | 73 | 128 | 0.57031 |
| squeeze | SMALL_PROFIT_GIVEBACK | 30 | 128 | 0.23438 |
| squeeze | DEAD_TRADE | 0 | 128 | 0 |
| squeeze | IMMEDIATE_FAILURE | 18 | 128 | 0.14062 |
| squeeze | NEVER_WORKED | 4 | 128 | 0.03125 |
| squeeze | STOP_TIMING_OTHER | 0 | 128 | 0 |
| squeeze | UNCERTAIN_PATH | 3 | 128 | 0.023438 |

Bad-entry-like is IMMEDIATE_FAILURE + NEVER_WORKED, a descriptive proxy, not a causal percentage. A failed path does not prove an entry defect. STOP_TIMING_OTHER is not assigned merely because a trade hit a stop. Uncertain stop-bar ordering prevents attributing some losses. DEAD_TRADE is a deliberately narrow, preregistered near-flat-first-10-bars definition.

## Module matrix

| module | baseline_wr | baseline_trades | bad_entry_like_fraction | giveback_fraction | dead_fraction | uncertain_fraction | largest_category | highest_observed_scenario | highest_observed_wr | trades | pf | expectancy | status | robust_supported_wr |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| meanrev | 0.49091 | 55 | 0.17857 | 0.82143 | 0 | 0 | SMALL_PROFIT_GIVEBACK | lock25_2 | 0.56364 | 55 | 0.9089 | -0.0017379 | LOW SAMPLE | NA |
| pullback | 0.427 | 363 | 0.28365 | 0.69231 | 0 | 0.024038 | SMALL_PROFIT_GIVEBACK | lock25_1 | 0.56712 | 365 | 1.4258 | 0.0050357 | MIXED | NA |
| breakout | 0.40768 | 547 | 0.14506 | 0.85185 | 0 | 0.0030864 | GIVEBACK_LOSER | lock25_1 | 0.62774 | 685 | 1.025 | 0.00032224 | TAIL-SENSITIVE | NA |
| squeeze | 0.34021 | 194 | 0.17188 | 0.80469 | 0 | 0.023438 | GIVEBACK_LOSER | lock25_1 | 0.59716 | 211 | 1.0128 | 0.00015311 | TAIL-SENSITIVE | NA |

## WIN RATE FRONTIER

| module | scenario | status | trades | fraction_trades_removed | win_rate | mean_winner | median_winner | mean_loser | median_loser | profit_factor | expectancy | median_return | worst_return | top5_share_gross_profit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| breakout | baseline | TAIL-SENSITIVE | 547 | 0 | 0.40768 | 0.070512 | 0.038785 | -0.043581 | -0.040125 | 1.1136 | 0.0029321 | -0.013198 | -0.21954 | 0.14031 |
| breakout | breakeven_1 | TAIL-SENSITIVE | 647 | -0.18282 | 0.21175 | 0.066365 | 0.034813 | -0.033492 | -0.024356 | 1.0206 | 0.00028315 | 0 | -0.21954 | 0.19285 |
| breakout | breakeven_2 | TAIL-SENSITIVE | 598 | -0.093236 | 0.29431 | 0.06832 | 0.034879 | -0.040971 | -0.037785 | 1.1033 | 0.001883 | 0 | -0.21954 | 0.1556 |
| breakout | breakeven_3 | TAIL-SENSITIVE | 579 | -0.058501 | 0.32988 | 0.067903 | 0.034945 | -0.043403 | -0.040125 | 1.0672 | 0.0014104 | 0 | -0.21954 | 0.14426 |
| breakout | breakeven_4 | TAIL-SENSITIVE | 570 | -0.042048 | 0.34912 | 0.068014 | 0.035923 | -0.044016 | -0.040235 | 1.0495 | 0.0011194 | -0.0030481 | -0.21954 | 0.14001 |
| breakout | early_3 | TAIL-SENSITIVE | 561 | -0.025594 | 0.38324 | 0.071868 | 0.040019 | -0.040737 | -0.035759 | 1.0962 | 0.0024178 | -0.014149 | -0.21954 | 0.14278 |
| breakout | lock25_1 | TAIL-SENSITIVE | 685 | -0.25229 | 0.62774 | 0.021083 | 0.0070871 | -0.034823 | -0.028701 | 1.025 | 0.00032224 | 0.0034924 | -0.21954 | 0.1911 |
| breakout | lock25_2 | TAIL-SENSITIVE | 628 | -0.14808 | 0.6035 | 0.032244 | 0.012119 | -0.044533 | -0.041329 | 1.102 | 0.0018018 | 0.0060228 | -0.21954 | 0.15311 |
| breakout | lock25_3 | TAIL-SENSITIVE | 603 | -0.10238 | 0.56053 | 0.040036 | 0.016859 | -0.045966 | -0.041442 | 1.1109 | 0.002241 | 0.007946 | -0.21954 | 0.13826 |
| breakout | lock25_4 | TAIL-SENSITIVE | 589 | -0.076782 | 0.51613 | 0.047045 | 0.019922 | -0.045255 | -0.040545 | 1.1088 | 0.0023835 | 0.0062222 | -0.21954 | 0.13251 |
| breakout | skip_bars_since_rsi_up_5 | TAIL-SENSITIVE | 517 | 0.054845 | 0.39458 | 0.072989 | 0.041684 | -0.043948 | -0.040235 | 1.0824 | 0.0021934 | -0.01434 | -0.21954 | 0.16728 |
| breakout | skip_candle_range_atr_3 | TAIL-SENSITIVE | 483 | 0.117 | 0.39959 | 0.073571 | 0.040019 | -0.04326 | -0.039237 | 1.1318 | 0.0034244 | -0.013198 | -0.21954 | 0.15538 |
| breakout | skip_distance_to_upper_band_atr_1 | MIXED | 479 | 0.12431 | 0.40919 | 0.072164 | 0.040754 | -0.042805 | -0.037844 | 1.1676 | 0.0042384 | -0.012918 | -0.21954 | 0.15075 |
| breakout | time_10 | TAIL-SENSITIVE | 547 | 0 | 0.40768 | 0.070512 | 0.038785 | -0.043581 | -0.040125 | 1.1136 | 0.0029321 | -0.013198 | -0.21954 | 0.14031 |
| breakout | time_15 | TAIL-SENSITIVE | 547 | 0 | 0.40768 | 0.070512 | 0.038785 | -0.043581 | -0.040125 | 1.1136 | 0.0029321 | -0.013198 | -0.21954 | 0.14031 |
| breakout | time_5 | TAIL-SENSITIVE | 557 | -0.018282 | 0.40395 | 0.069247 | 0.037687 | -0.042742 | -0.037915 | 1.098 | 0.0024964 | -0.01279 | -0.21954 | 0.1416 |
| meanrev | baseline | LOW SAMPLE | 55 | 0 | 0.49091 | 0.07108 | 0.049076 | -0.042199 | -0.036176 | 1.6243 | 0.013411 | -0.00011655 | -0.10417 | 0.50065 |
| meanrev | breakeven_1 | LOW SAMPLE | 56 | -0.018182 | 0.28571 | 0.069887 | 0.061913 | -0.036961 | -0.032269 | 1.2101 | 0.0034671 | 0 | -0.10417 | 0.62455 |
| meanrev | breakeven_2 | LOW SAMPLE | 55 | 0 | 0.38182 | 0.06107 | 0.049076 | -0.043719 | -0.041365 | 1.2223 | 0.0042402 | 0 | -0.10417 | 0.54524 |
| meanrev | breakeven_3 | LOW SAMPLE | 55 | 0 | 0.41818 | 0.061859 | 0.049076 | -0.044515 | -0.042988 | 1.2784 | 0.0056341 | 0 | -0.10417 | 0.50638 |
| meanrev | breakeven_4 | LOW SAMPLE | 55 | 0 | 0.47273 | 0.068856 | 0.04627 | -0.044353 | -0.039866 | 1.5525 | 0.011583 | 0 | -0.10417 | 0.52243 |
| meanrev | early_3 | LOW SAMPLE | 55 | 0 | 0.45455 | 0.073684 | 0.049076 | -0.039985 | -0.035454 | 1.5357 | 0.011683 | -0.0097316 | -0.10417 | 0.5216 |
| meanrev | lock25_1 | LOW SAMPLE | 56 | -0.018182 | 0.55357 | 0.027775 | 0.0089718 | -0.036961 | -0.032269 | 0.93181 | -0.0011252 | 0.0037808 | -0.10417 | 0.64766 |
| meanrev | lock25_2 | LOW SAMPLE | 55 | 0 | 0.56364 | 0.030764 | 0.01169 | -0.043719 | -0.041365 | 0.9089 | -0.0017379 | 0.0057241 | -0.10417 | 0.58566 |
| meanrev | lock25_3 | LOW SAMPLE | 55 | 0 | 0.54545 | 0.03677 | 0.016901 | -0.044515 | -0.042988 | 0.9912 | -0.00017802 | 0.0082374 | -0.10417 | 0.53582 |
| meanrev | lock25_4 | LOW SAMPLE | 55 | 0 | 0.52727 | 0.052239 | 0.021779 | -0.044353 | -0.039866 | 1.3137 | 0.0065775 | 0.010351 | -0.10417 | 0.54957 |
| meanrev | time_10 | LOW SAMPLE | 55 | 0 | 0.47273 | 0.073652 | 0.051566 | -0.041025 | -0.035609 | 1.6096 | 0.013186 | -0.0037254 | -0.10417 | 0.50176 |
| meanrev | time_15 | LOW SAMPLE | 55 | 0 | 0.49091 | 0.07108 | 0.049076 | -0.042199 | -0.036176 | 1.6243 | 0.013411 | -0.00011655 | -0.10417 | 0.50065 |
| meanrev | time_5 | LOW SAMPLE | 55 | 0 | 0.47273 | 0.073652 | 0.051566 | -0.040444 | -0.035299 | 1.6327 | 0.013492 | -0.0037254 | -0.10417 | 0.50176 |
| pullback | baseline | INCONCLUSIVE | 363 | 0 | 0.427 | 0.059225 | 0.029505 | -0.027289 | -0.021542 | 1.6172 | 0.0096519 | -0.0067863 | -0.12456 | 0.17721 |
| pullback | breakeven_1 | MIXED | 365 | -0.0055096 | 0.29863 | 0.055888 | 0.025333 | -0.026614 | -0.020272 | 1.4043 | 0.0048049 | 0 | -0.1126 | 0.24734 |
| pullback | breakeven_2 | MIXED | 364 | -0.0027548 | 0.3544 | 0.055014 | 0.026737 | -0.027461 | -0.021562 | 1.4278 | 0.0058417 | 0 | -0.1126 | 0.22923 |
| pullback | breakeven_3 | MIXED | 363 | 0 | 0.39669 | 0.056936 | 0.027423 | -0.027681 | -0.021542 | 1.5426 | 0.0079448 | -0.0036142 | -0.12456 | 0.19842 |
| pullback | breakeven_4 | MIXED | 363 | 0 | 0.41598 | 0.05887 | 0.029164 | -0.027365 | -0.021522 | 1.6324 | 0.0094868 | -0.0050093 | -0.12456 | 0.18301 |
| pullback | early_3 | MIXED | 363 | 0 | 0.427 | 0.059225 | 0.029505 | -0.027289 | -0.021542 | 1.6172 | 0.0096519 | -0.0067863 | -0.12456 | 0.17721 |
| pullback | lock25_1 | MIXED | 365 | -0.0055096 | 0.56712 | 0.029733 | 0.0074054 | -0.027321 | -0.021187 | 1.4258 | 0.0050357 | 0.0028058 | -0.1126 | 0.24481 |
| pullback | lock25_2 | MIXED | 364 | -0.0027548 | 0.51923 | 0.037824 | 0.010843 | -0.028265 | -0.022085 | 1.4452 | 0.0060505 | 0.0018934 | -0.1126 | 0.22756 |
| pullback | lock25_3 | MIXED | 363 | 0 | 0.47934 | 0.046376 | 0.020046 | -0.02807 | -0.02166 | 1.521 | 0.0076147 | -0.0027228 | -0.12456 | 0.2016 |
| pullback | lock25_4 | MIXED | 363 | 0 | 0.45455 | 0.051904 | 0.023876 | -0.027485 | -0.021542 | 1.5737 | 0.0086008 | -0.0050093 | -0.12456 | 0.18996 |
| pullback | skip_bb_width_5 | MIXED | 289 | 0.20386 | 0.44291 | 0.054443 | 0.0296 | -0.021064 | -0.017143 | 2.0549 | 0.012379 | -0.0050663 | -0.089444 | 0.20283 |
| pullback | skip_candle_range_atr_4 | MIXED | 299 | 0.17631 | 0.43144 | 0.062267 | 0.032795 | -0.026589 | -0.020258 | 1.7771 | 0.011747 | -0.0068125 | -0.12456 | 0.19322 |
| pullback | skip_rsi_distance_from_avg_2 | MIXED | 282 | 0.22314 | 0.42908 | 0.063213 | 0.029505 | -0.027909 | -0.021169 | 1.7023 | 0.01119 | -0.0060234 | -0.12456 | 0.21269 |
| pullback | time_10 | MIXED | 363 | 0 | 0.427 | 0.059225 | 0.029505 | -0.027289 | -0.021542 | 1.6172 | 0.0096519 | -0.0067863 | -0.12456 | 0.17721 |
| pullback | time_15 | MIXED | 363 | 0 | 0.427 | 0.059225 | 0.029505 | -0.027289 | -0.021542 | 1.6172 | 0.0096519 | -0.0067863 | -0.12456 | 0.17721 |
| pullback | time_5 | MIXED | 363 | 0 | 0.427 | 0.059225 | 0.029505 | -0.027289 | -0.021542 | 1.6172 | 0.0096519 | -0.0067863 | -0.12456 | 0.17721 |
| squeeze | baseline | TAIL-SENSITIVE | 194 | 0 | 0.34021 | 0.081789 | 0.053582 | -0.036872 | -0.031667 | 1.1438 | 0.0034972 | -0.019263 | -0.1488 | 0.30609 |
| squeeze | breakeven_1 | TAIL-SENSITIVE | 209 | -0.07732 | 0.15311 | 0.076079 | 0.040944 | -0.030754 | -0.019741 | 0.83327 | -0.0023308 | 0 | -0.23368 | 0.53385 |
| squeeze | breakeven_2 | TAIL-SENSITIVE | 202 | -0.041237 | 0.22772 | 0.073097 | 0.044442 | -0.038501 | -0.035299 | 0.99243 | -0.0001269 | 0 | -0.1488 | 0.38652 |
| squeeze | breakeven_3 | TAIL-SENSITIVE | 198 | -0.020619 | 0.27778 | 0.071672 | 0.051502 | -0.038825 | -0.034149 | 1.0256 | 0.00049634 | -8.8075e-05 | -0.1488 | 0.3297 |
| squeeze | breakeven_4 | TAIL-SENSITIVE | 196 | -0.010309 | 0.31633 | 0.069813 | 0.047544 | -0.038503 | -0.03298 | 1.0506 | 0.001064 | -0.0085449 | -0.1488 | 0.32126 |
| squeeze | early_3 | TAIL-SENSITIVE | 194 | 0 | 0.33505 | 0.082322 | 0.054519 | -0.034649 | -0.030822 | 1.1972 | 0.0045426 | -0.016838 | -0.1488 | 0.30879 |
| squeeze | lock25_1 | TAIL-SENSITIVE | 211 | -0.087629 | 0.59716 | 0.020268 | 0.0056799 | -0.029664 | -0.020605 | 1.0128 | 0.00015311 | 0.0031502 | -0.1488 | 0.49365 |
| squeeze | lock25_2 | TAIL-SENSITIVE | 206 | -0.061856 | 0.59223 | 0.027642 | 0.0086275 | -0.040429 | -0.037434 | 0.99303 | -0.00011483 | 0.0052743 | -0.1488 | 0.37972 |
| squeeze | lock25_3 | TAIL-SENSITIVE | 201 | -0.036082 | 0.52239 | 0.037663 | 0.013012 | -0.040125 | -0.03539 | 1.0266 | 0.00051041 | 0.0060949 | -0.1488 | 0.32382 |
| squeeze | lock25_4 | TAIL-SENSITIVE | 198 | -0.020619 | 0.46465 | 0.048627 | 0.018653 | -0.038856 | -0.033231 | 1.0862 | 0.0017926 | -0.0078469 | -0.1488 | 0.29051 |
| squeeze | skip_bars_since_oversold_4 | MIXED | 147 | 0.24227 | 0.38776 | 0.085141 | 0.052645 | -0.037303 | -0.031992 | 1.4455 | 0.010175 | -0.015049 | -0.1488 | 0.34047 |
| squeeze | skip_bars_since_rsi_up_5 | TAIL-SENSITIVE | 170 | 0.12371 | 0.35882 | 0.075214 | 0.051502 | -0.036016 | -0.031503 | 1.1687 | 0.0038959 | -0.018666 | -0.1488 | 0.29799 |
| squeeze | skip_candle_range_atr_2 | TAIL-SENSITIVE | 162 | 0.16495 | 0.3642 | 0.085887 | 0.058159 | -0.034976 | -0.031503 | 1.4066 | 0.0090419 | -0.015459 | -0.12012 | 0.30814 |
| squeeze | time_10 | TAIL-SENSITIVE | 194 | 0 | 0.34021 | 0.081789 | 0.053582 | -0.036872 | -0.031667 | 1.1438 | 0.0034972 | -0.019263 | -0.1488 | 0.30609 |
| squeeze | time_15 | TAIL-SENSITIVE | 194 | 0 | 0.34021 | 0.081789 | 0.053582 | -0.036872 | -0.031667 | 1.1438 | 0.0034972 | -0.019263 | -0.1488 | 0.30609 |
| squeeze | time_5 | TAIL-SENSITIVE | 194 | 0 | 0.3299 | 0.082622 | 0.055107 | -0.035138 | -0.029792 | 1.1576 | 0.003711 | -0.017712 | -0.1488 | 0.31247 |

Historical stability (eligible groups have >=5 trades):

| module | scenario | year_eligible_groups | year_wr_min | year_wr_max | year_wr_std | symbol_eligible_groups | symbol_wr_min | symbol_wr_max | symbol_wr_std |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| breakout | baseline | 6 | 0.24 | 0.47305 | 0.071145 | 48 | 0.076923 | 0.71429 | 0.13292 |
| breakout | breakeven_1 | 6 | 0.11905 | 0.25926 | 0.044959 | 49 | 0 | 0.44444 | 0.098358 |
| breakout | breakeven_2 | 6 | 0.18919 | 0.35556 | 0.060839 | 49 | 0.066667 | 0.71429 | 0.12903 |
| breakout | breakeven_3 | 6 | 0.21622 | 0.38793 | 0.067149 | 49 | 0.076923 | 0.71429 | 0.12479 |
| breakout | breakeven_4 | 6 | 0.22222 | 0.42197 | 0.074999 | 49 | 0.076923 | 0.71429 | 0.12741 |
| breakout | early_3 | 6 | 0.24 | 0.45882 | 0.068484 | 48 | 0.076923 | 0.71429 | 0.13078 |
| breakout | lock25_1 | 6 | 0.52 | 0.66667 | 0.050713 | 49 | 0.33333 | 0.88889 | 0.12358 |
| breakout | lock25_2 | 6 | 0.4 | 0.64865 | 0.085759 | 49 | 0.33333 | 1 | 0.1344 |
| breakout | lock25_3 | 6 | 0.4 | 0.61453 | 0.065667 | 49 | 0.27273 | 1 | 0.1411 |
| breakout | lock25_4 | 6 | 0.44 | 0.55172 | 0.03499 | 49 | 0.21429 | 0.85714 | 0.15108 |
| breakout | skip_bars_since_rsi_up_5 | 6 | 0.24 | 0.46203 | 0.070354 | 48 | 0.083333 | 0.71429 | 0.13307 |
| breakout | skip_candle_range_atr_3 | 6 | 0.22727 | 0.46309 | 0.07882 | 46 | 0.1 | 0.71429 | 0.13764 |
| breakout | skip_distance_to_upper_band_atr_1 | 6 | 0.15789 | 0.48667 | 0.10212 | 46 | 0.090909 | 0.83333 | 0.14893 |
| breakout | time_10 | 6 | 0.24 | 0.47305 | 0.071145 | 48 | 0.076923 | 0.71429 | 0.13292 |
| breakout | time_15 | 6 | 0.24 | 0.47305 | 0.071145 | 48 | 0.076923 | 0.71429 | 0.13292 |
| breakout | time_5 | 6 | 0.24 | 0.47337 | 0.075074 | 48 | 0.076923 | 0.71429 | 0.13087 |
| meanrev | baseline | 5 | 0.28571 | 0.625 | 0.12557 | 0 | NA | NA | NA |
| meanrev | breakeven_1 | 5 | 0 | 0.42105 | 0.13935 | 0 | NA | NA | NA |
| meanrev | breakeven_2 | 5 | 0.125 | 0.52632 | 0.13198 | 0 | NA | NA | NA |
| meanrev | breakeven_3 | 5 | 0.125 | 0.625 | 0.17603 | 0 | NA | NA | NA |
| meanrev | breakeven_4 | 5 | 0.25 | 0.625 | 0.15093 | 0 | NA | NA | NA |
| meanrev | early_3 | 5 | 0.28571 | 0.52632 | 0.088334 | 0 | NA | NA | NA |
| meanrev | lock25_1 | 5 | 0.125 | 0.71429 | 0.21303 | 0 | NA | NA | NA |
| meanrev | lock25_2 | 5 | 0.25 | 0.75 | 0.17699 | 0 | NA | NA | NA |
| meanrev | lock25_3 | 5 | 0.25 | 0.75 | 0.18202 | 0 | NA | NA | NA |
| meanrev | lock25_4 | 5 | 0.375 | 0.625 | 0.091169 | 0 | NA | NA | NA |
| meanrev | time_10 | 5 | 0.28571 | 0.625 | 0.11755 | 0 | NA | NA | NA |
| meanrev | time_15 | 5 | 0.28571 | 0.625 | 0.12557 | 0 | NA | NA | NA |
| meanrev | time_5 | 5 | 0.28571 | 0.625 | 0.11755 | 0 | NA | NA | NA |
| pullback | baseline | 6 | 0.29412 | 0.47619 | 0.077248 | 41 | 0.11111 | 0.83333 | 0.16692 |
| pullback | breakeven_1 | 6 | 0.23333 | 0.33333 | 0.034571 | 41 | 0 | 0.66667 | 0.16244 |
| pullback | breakeven_2 | 6 | 0.26667 | 0.4127 | 0.052558 | 41 | 0 | 0.83333 | 0.16421 |
| pullback | breakeven_3 | 6 | 0.27119 | 0.44444 | 0.070043 | 41 | 0.11111 | 0.83333 | 0.15745 |
| pullback | breakeven_4 | 6 | 0.28814 | 0.46032 | 0.07569 | 41 | 0.11111 | 0.83333 | 0.16399 |
| pullback | early_3 | 6 | 0.29412 | 0.47619 | 0.077248 | 41 | 0.11111 | 0.83333 | 0.16692 |
| pullback | lock25_1 | 6 | 0.47059 | 0.61905 | 0.055277 | 41 | 0.22222 | 1 | 0.16687 |
| pullback | lock25_2 | 6 | 0.35294 | 0.54762 | 0.067142 | 41 | 0 | 0.83333 | 0.19281 |
| pullback | lock25_3 | 6 | 0.35294 | 0.52381 | 0.061953 | 41 | 0.11111 | 0.83333 | 0.1847 |
| pullback | lock25_4 | 6 | 0.35294 | 0.49206 | 0.060254 | 41 | 0.11111 | 0.83333 | 0.17819 |
| pullback | skip_bb_width_5 | 6 | 0.22222 | 0.49254 | 0.099591 | 35 | 0 | 0.83333 | 0.17885 |
| pullback | skip_candle_range_atr_4 | 6 | 0.23077 | 0.48148 | 0.093618 | 35 | 0.125 | 0.83333 | 0.15729 |
| pullback | skip_rsi_distance_from_avg_2 | 6 | 0.30233 | 0.5 | 0.069465 | 33 | 0 | 0.8 | 0.16099 |
| pullback | time_10 | 6 | 0.29412 | 0.47619 | 0.077248 | 41 | 0.11111 | 0.83333 | 0.16692 |
| pullback | time_15 | 6 | 0.29412 | 0.47619 | 0.077248 | 41 | 0.11111 | 0.83333 | 0.16692 |
| pullback | time_5 | 6 | 0.29412 | 0.47619 | 0.077248 | 41 | 0.11111 | 0.83333 | 0.16692 |
| squeeze | baseline | 5 | 0.25581 | 0.39535 | 0.049034 | 17 | 0 | 0.6 | 0.17638 |
| squeeze | breakeven_1 | 5 | 0.071429 | 0.20455 | 0.048512 | 21 | 0 | 0.4 | 0.127 |
| squeeze | breakeven_2 | 5 | 0.14286 | 0.30769 | 0.063651 | 21 | 0 | 0.6 | 0.15382 |
| squeeze | breakeven_3 | 5 | 0.15385 | 0.34091 | 0.070363 | 19 | 0 | 0.6 | 0.16527 |
| squeeze | breakeven_4 | 5 | 0.23077 | 0.37209 | 0.054159 | 18 | 0 | 0.6 | 0.17609 |
| squeeze | early_3 | 5 | 0.25581 | 0.39535 | 0.04782 | 17 | 0 | 0.6 | 0.17638 |
| squeeze | lock25_1 | 5 | 0.5 | 0.65909 | 0.054464 | 22 | 0.2 | 1 | 0.17735 |
| squeeze | lock25_2 | 5 | 0.55319 | 0.63014 | 0.026668 | 22 | 0.25 | 0.8 | 0.16035 |
| squeeze | lock25_3 | 5 | 0.30769 | 0.57746 | 0.095081 | 19 | 0.16667 | 1 | 0.21104 |
| squeeze | lock25_4 | 5 | 0.30769 | 0.50704 | 0.071615 | 18 | 0 | 1 | 0.22785 |
| squeeze | skip_bars_since_oversold_4 | 5 | 0.25 | 0.42857 | 0.064797 | 5 | 0.2 | 0.33333 | 0.048711 |
| squeeze | skip_bars_since_rsi_up_5 | 5 | 0.28571 | 0.39683 | 0.038459 | 14 | 0 | 0.6 | 0.16688 |
| squeeze | skip_candle_range_atr_2 | 5 | 0.27273 | 0.41379 | 0.057607 | 11 | 0 | 0.4 | 0.14096 |
| squeeze | time_10 | 5 | 0.25581 | 0.39535 | 0.049034 | 17 | 0 | 0.6 | 0.17638 |
| squeeze | time_15 | 5 | 0.25581 | 0.39535 | 0.049034 | 17 | 0 | 0.6 | 0.17638 |
| squeeze | time_5 | 5 | 0.25581 | 0.39535 | 0.04729 | 17 | 0 | 0.6 | 0.17638 |

## Targets under the fixed robustness constraints

| module | target | any_predefined_reached | robust_reached | scenario | trades | expectancy | profit_factor |
| --- | --- | --- | --- | --- | --- | --- | --- |
| meanrev | 0.5 | True | False | UNSUPPORTED | 0 | NA | NA |
| meanrev | 0.6 | False | False | UNSUPPORTED | 0 | NA | NA |
| meanrev | 0.7 | False | False | UNSUPPORTED | 0 | NA | NA |
| meanrev | 0.75 | False | False | UNSUPPORTED | 0 | NA | NA |
| pullback | 0.5 | True | False | UNSUPPORTED | 0 | NA | NA |
| pullback | 0.6 | False | False | UNSUPPORTED | 0 | NA | NA |
| pullback | 0.7 | False | False | UNSUPPORTED | 0 | NA | NA |
| pullback | 0.75 | False | False | UNSUPPORTED | 0 | NA | NA |
| breakout | 0.5 | True | False | UNSUPPORTED | 0 | NA | NA |
| breakout | 0.6 | True | False | UNSUPPORTED | 0 | NA | NA |
| breakout | 0.7 | False | False | UNSUPPORTED | 0 | NA | NA |
| breakout | 0.75 | False | False | UNSUPPORTED | 0 | NA | NA |
| squeeze | 0.5 | True | False | UNSUPPORTED | 0 | NA | NA |
| squeeze | 0.6 | False | False | UNSUPPORTED | 0 | NA | NA |
| squeeze | 0.7 | False | False | UNSUPPORTED | 0 | NA | NA |
| squeeze | 0.75 | False | False | UNSUPPORTED | 0 | NA | NA |

## Existing exit-policy uncertainty

| module | configuration | trades | win_rate | profit_factor | expectancy |
| --- | --- | --- | --- | --- | --- |
| breakout | ATR1.5-DYNAMIC-TRENDON | 673 | 0.37741 | 0.97116 | -0.0005028 |
| breakout | ATR1.75-DYNAMIC-TRENDON | 644 | 0.3882 | 0.98964 | -0.00020372 |
| breakout | ATR2-DYNAMIC-TRENDON | 614 | 0.40391 | 1.0184 | 0.00039513 |
| breakout | ATR2.25-DYNAMIC-TRENDON | 581 | 0.40448 | 1.0857 | 0.0019633 |
| breakout | ATR2.5-DYNAMIC-TRENDOFF | 545 | 0.41651 | 1.1227 | 0.0032511 |
| breakout | ATR2.5-DYNAMIC-TRENDON | 547 | 0.40768 | 1.1136 | 0.0029321 |
| breakout | ATR2.5-LOCKED-TRENDON | 531 | 0.41243 | 1.263 | 0.0070891 |
| breakout | ATR3-DYNAMIC-TRENDON | 485 | 0.38969 | 1.2125 | 0.0064152 |
| squeeze | ATR1.5-DYNAMIC-TRENDON | 205 | 0.32195 | 0.86142 | -0.0022073 |
| squeeze | ATR1.75-DYNAMIC-TRENDON | 203 | 0.3399 | 1.0275 | 0.00050599 |
| squeeze | ATR2-DYNAMIC-TRENDON | 201 | 0.32338 | 0.93003 | -0.001477 |
| squeeze | ATR2.25-DYNAMIC-TRENDON | 199 | 0.33668 | 0.93633 | -0.0014894 |
| squeeze | ATR2.5-DYNAMIC-TRENDOFF | 194 | 0.34021 | 1.1142 | 0.0028529 |
| squeeze | ATR2.5-DYNAMIC-TRENDON | 194 | 0.34021 | 1.1438 | 0.0034972 |
| squeeze | ATR2.5-LOCKED-TRENDON | 194 | 0.37629 | 1.153 | 0.0036791 |
| squeeze | ATR3-DYNAMIC-TRENDON | 186 | 0.38172 | 1.3778 | 0.010832 |

## Explicit research answers

### meanrev

1. Current pure-cohort WR is 49.09%: 27 wins, 28 losses, 0 ties from 55 closed trades. Mean winner 7.11%, mean loser -4.22%; this payoff asymmetry explains why WR alone is inadequate.
2. Largest observed loss category: SMALL_PROFIT_GIVEBACK, 42.86% of losses.
3. 5 bad-from-start-like versus 23 known-giveback losses; 0 cannot be unambiguously categorized.
4. 16–16 of 28 losses reached +1% before exit (retrospective bounds, not tradable rescue counts). Best actual matched loser-to-win rescue among fixed exits: 7; matched rescue and winner destruction for every rule are in the paired-effect table.
5. 5 losses had <0.5% possible lifetime favorable excursion and look more like entry-selection candidates. This does not prove they require a different entry; random variation and execution also matter.
6. Largest adequately sampled fixed-bin WR spreads: bars_since_rsi_up (0.0%). These are associations selected for description, not new tested filters; year/symbol/partition detail and frozen edges remain in CSVs.
7. Highest observed fixed-exit WR: lock25_2, 56.36%, n=55, PF=0.909, expectancy=-0.17%, mean winner=3.08%. This is a descriptive maximum, not a recommendation.
8. Entry V1 supplied no sufficiently sampled enriched region for the preregistered skip family; no entry threshold was invented.
9. Combined research: NO COMBINATION: one or both families failed discovery screen. No Cartesian search is allowed.
10. No intervention satisfies every predefined historical robustness gate; a higher robust WR is not established.
11. 0 predefined scenarios reach 75% in pooled history; none should be interpreted without count, winner-size, tail and year/symbol gates. Failed checks are explicit in stage 7.
12. Robust 75% is not supported by this finite study. This is not a mathematical impossibility result; searching until 75% appears would add selection bias and may remove most trades or truncate winners.
13. Freeze any surviving hypothesis and test it on genuinely later, unseen bars, with costs and a stable universe. For unresolved modules, first resolve exit-policy uncertainty; do not deploy the descriptive maximum.

### pullback

1. Current pure-cohort WR is 42.70%: 155 wins, 208 losses, 0 ties from 363 closed trades. Mean winner 5.92%, mean loser -2.73%; this payoff asymmetry explains why WR alone is inadequate.
2. Largest observed loss category: SMALL_PROFIT_GIVEBACK, 40.38% of losses.
3. 59 bad-from-start-like versus 144 known-giveback losses; 5 cannot be unambiguously categorized.
4. 113–115 of 208 losses reached +1% before exit (retrospective bounds, not tradable rescue counts). Best actual matched loser-to-win rescue among fixed exits: 66; matched rescue and winner destruction for every rule are in the paired-effect table.
5. 59 losses had <0.5% possible lifetime favorable excursion and look more like entry-selection candidates. This does not prove they require a different entry; random variation and execution also matter.
6. Largest adequately sampled fixed-bin WR spreads: atr_pct (31.0%), adx_margin (21.4%), htf_adx (21.4%). These are associations selected for description, not new tested filters; year/symbol/partition detail and frozen edges remain in CSVs.
7. Highest observed fixed-exit WR: lock25_1, 56.71%, n=365, PF=1.426, expectancy=0.50%, mean winner=2.97%. This is a descriptive maximum, not a recommendation.
8. Highest observed predefined entry-skip WR: skip_bb_width_5, 44.29%, n=289 (20.4% fewer), PF=2.055, expectancy=1.24%.
9. Combined research: NO COMBINATION: one or both families failed discovery screen. No Cartesian search is allowed.
10. No intervention satisfies every predefined historical robustness gate; a higher robust WR is not established.
11. 0 predefined scenarios reach 75% in pooled history; none should be interpreted without count, winner-size, tail and year/symbol gates. Failed checks are explicit in stage 7.
12. Robust 75% is not supported by this finite study. This is not a mathematical impossibility result; searching until 75% appears would add selection bias and may remove most trades or truncate winners.
13. Freeze any surviving hypothesis and test it on genuinely later, unseen bars, with costs and a stable universe. For unresolved modules, first resolve exit-policy uncertainty; do not deploy the descriptive maximum.

### breakout

1. Current pure-cohort WR is 40.77%: 223 wins, 324 losses, 0 ties from 547 closed trades. Mean winner 7.05%, mean loser -4.36%; this payoff asymmetry explains why WR alone is inadequate.
2. Largest observed loss category: GIVEBACK_LOSER, 52.16% of losses.
3. 47 bad-from-start-like versus 276 known-giveback losses; 1 cannot be unambiguously categorized.
4. 236–236 of 324 losses reached +1% before exit (retrospective bounds, not tradable rescue counts). Best actual matched loser-to-win rescue among fixed exits: 157; matched rescue and winner destruction for every rule are in the paired-effect table.
5. 47 losses had <0.5% possible lifetime favorable excursion and look more like entry-selection candidates. This does not prove they require a different entry; random variation and execution also matter.
6. Largest adequately sampled fixed-bin WR spreads: bars_since_rsi_up (17.7%), bars_since_oversold (17.6%), atr_pct (17.2%). These are associations selected for description, not new tested filters; year/symbol/partition detail and frozen edges remain in CSVs.
7. Highest observed fixed-exit WR: lock25_1, 62.77%, n=685, PF=1.025, expectancy=0.03%, mean winner=2.11%. This is a descriptive maximum, not a recommendation.
8. Highest observed predefined entry-skip WR: skip_distance_to_upper_band_atr_1, 40.92%, n=479 (12.4% fewer), PF=1.168, expectancy=0.42%.
9. Combined research: NO COMBINATION: one or both families failed discovery screen. No Cartesian search is allowed.
10. No intervention satisfies every predefined historical robustness gate; a higher robust WR is not established.
11. 0 predefined scenarios reach 75% in pooled history; none should be interpreted without count, winner-size, tail and year/symbol gates. Failed checks are explicit in stage 7.
12. Robust 75% is not supported by this finite study. This is not a mathematical impossibility result; searching until 75% appears would add selection bias and may remove most trades or truncate winners.
13. Freeze any surviving hypothesis and test it on genuinely later, unseen bars, with costs and a stable universe. For unresolved modules, first resolve exit-policy uncertainty; do not deploy the descriptive maximum.

### squeeze

1. Current pure-cohort WR is 34.02%: 66 wins, 128 losses, 0 ties from 194 closed trades. Mean winner 8.18%, mean loser -3.69%; this payoff asymmetry explains why WR alone is inadequate.
2. Largest observed loss category: GIVEBACK_LOSER, 57.03% of losses.
3. 22 bad-from-start-like versus 103 known-giveback losses; 3 cannot be unambiguously categorized.
4. 96–96 of 128 losses reached +1% before exit (retrospective bounds, not tradable rescue counts). Best actual matched loser-to-win rescue among fixed exits: 63; matched rescue and winner destruction for every rule are in the paired-effect table.
5. 22 losses had <0.5% possible lifetime favorable excursion and look more like entry-selection candidates. This does not prove they require a different entry; random variation and execution also matter.
6. Largest adequately sampled fixed-bin WR spreads: distance_to_squeeze_pct (28.1%), bars_since_oversold (28.1%), rsi (24.0%). These are associations selected for description, not new tested filters; year/symbol/partition detail and frozen edges remain in CSVs.
7. Highest observed fixed-exit WR: lock25_1, 59.72%, n=211, PF=1.013, expectancy=0.02%, mean winner=2.03%. This is a descriptive maximum, not a recommendation.
8. Highest observed predefined entry-skip WR: skip_bars_since_oversold_4, 38.78%, n=147 (24.2% fewer), PF=1.446, expectancy=1.02%.
9. Combined research: NO COMBINATION: one or both families failed discovery screen. No Cartesian search is allowed.
10. No intervention satisfies every predefined historical robustness gate; a higher robust WR is not established.
11. 0 predefined scenarios reach 75% in pooled history; none should be interpreted without count, winner-size, tail and year/symbol gates. Failed checks are explicit in stage 7.
12. Robust 75% is not supported by this finite study. This is not a mathematical impossibility result; searching until 75% appears would add selection bias and may remove most trades or truncate winners.
13. Freeze any surviving hypothesis and test it on genuinely later, unseen bars, with costs and a stable universe. For unresolved modules, first resolve exit-policy uncertainty; do not deploy the descriptive maximum.

## Interpretation and limits

Full-stream replays include changed position occupancy and subsequent fills; rescue/destruction pairs match symbol/module/signal_time only. One-sided fills and censored pairs are retained separately. A higher WR from break-even exits cannot count zero returns as wins. Stop threshold sensitivity is not an optimized tighter-stop policy. Winner time-to-threshold quantiles are conditional on known hits; not-hit/unknown counts are exported. MAE-before-positive uses completed bars before first positive close; intrabar ordering within that first-positive bar is unknown.

Stage 7 includes every year/symbol, leave-one-year/symbol-out and removal of top 1/3/5 positive trades. ROBUST would be a descriptive historical status only, not statistical significance or independent OOS confirmation. Present-day universe selection, correlated trades, multiple comparisons, shorter IPO histories and unmodeled transaction costs remain material. Historical Outcome labels were already produced by Entry V1 and are reused only to preregister entry hypotheses; they are never joined as decision features. No ML, parameter optimization or production strategy changes were made.
