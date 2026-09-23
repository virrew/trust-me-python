# breakout: Win Rate V1

| module | baseline_wr | baseline_trades | bad_entry_like_fraction | giveback_fraction | dead_fraction | uncertain_fraction | largest_category | highest_observed_scenario | highest_observed_wr | trades | pf | expectancy | status | robust_supported_wr |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| breakout | 0.40768 | 547 | 0.14506 | 0.85185 | 0 | 0.0030864 | GIVEBACK_LOSER | lock25_1 | 0.62774 | 685 | 1.025 | 0.00032224 | TAIL-SENSITIVE | NA |

All predefined scenarios, without selecting a production policy:

| scenario | status | trades | win_rate | mean_winner | mean_loser | profit_factor | expectancy | year_wr_min | year_wr_max | year_wr_std | symbol_wr_std | discovery_failed | holdout_failed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | TAIL-SENSITIVE | 547 | 0.40768 | 0.070512 | -0.043581 | 1.1136 | 0.0029321 | 0.24 | 0.47305 | 0.071145 | 0.13292 | wr,tail | wr,expectancy,pf,symbol,year,tail |
| breakeven_1 | TAIL-SENSITIVE | 647 | 0.21175 | 0.066365 | -0.033492 | 1.0206 | 0.00028315 | 0.11905 | 0.25926 | 0.044959 | 0.098358 | wr,expectancy,symbol,year,tail | wr,expectancy,pf,symbol,year,tail |
| breakeven_2 | TAIL-SENSITIVE | 598 | 0.29431 | 0.06832 | -0.040971 | 1.1033 | 0.001883 | 0.18919 | 0.35556 | 0.060839 | 0.12903 | wr,expectancy,symbol,year,tail | wr,expectancy,pf,symbol,year,tail |
| breakeven_3 | TAIL-SENSITIVE | 579 | 0.32988 | 0.067903 | -0.043403 | 1.0672 | 0.0014104 | 0.21622 | 0.38793 | 0.067149 | 0.12479 | wr,expectancy,symbol,year,tail | wr,expectancy,pf,symbol,year,tail |
| breakeven_4 | TAIL-SENSITIVE | 570 | 0.34912 | 0.068014 | -0.044016 | 1.0495 | 0.0011194 | 0.22222 | 0.42197 | 0.074999 | 0.12741 | wr,expectancy,symbol,year,tail | wr,expectancy,pf,symbol,year,tail |
| early_3 | TAIL-SENSITIVE | 561 | 0.38324 | 0.071868 | -0.040737 | 1.0962 | 0.0024178 | 0.24 | 0.45882 | 0.068484 | 0.13078 | wr,year,tail | wr,expectancy,pf,symbol,year,tail |
| lock25_1 | TAIL-SENSITIVE | 685 | 0.62774 | 0.021083 | -0.034823 | 1.025 | 0.00032224 | 0.52 | 0.66667 | 0.050713 | 0.12358 | expectancy,winner_size,symbol,year,tail | expectancy,pf,winner_size,symbol,year,tail |
| lock25_2 | TAIL-SENSITIVE | 628 | 0.6035 | 0.032244 | -0.044533 | 1.102 | 0.0018018 | 0.4 | 0.64865 | 0.085759 | 0.1344 | expectancy,winner_size,symbol,tail | expectancy,pf,winner_size,symbol,year,tail |
| lock25_3 | TAIL-SENSITIVE | 603 | 0.56053 | 0.040036 | -0.045966 | 1.1109 | 0.002241 | 0.4 | 0.61453 | 0.065667 | 0.1411 | expectancy,winner_size,symbol,tail | expectancy,pf,winner_size,symbol,year,tail |
| lock25_4 | TAIL-SENSITIVE | 589 | 0.51613 | 0.047045 | -0.045255 | 1.1088 | 0.0023835 | 0.44 | 0.55172 | 0.03499 | 0.15108 | expectancy,winner_size,symbol,tail | expectancy,pf,winner_size,symbol,year,tail |
| skip_bars_since_rsi_up_5 | TAIL-SENSITIVE | 517 | 0.39458 | 0.072989 | -0.043948 | 1.0824 | 0.0021934 | 0.24 | 0.46203 | 0.070354 | 0.13307 | wr,expectancy,symbol,year,tail | wr,expectancy,pf,symbol,year,tail |
| skip_candle_range_atr_3 | TAIL-SENSITIVE | 483 | 0.39959 | 0.073571 | -0.04326 | 1.1318 | 0.0034244 | 0.22727 | 0.46309 | 0.07882 | 0.13764 | wr,symbol,year,tail | wr,expectancy,pf,symbol,year,tail |
| skip_distance_to_upper_band_atr_1 | MIXED | 479 | 0.40919 | 0.072164 | -0.042805 | 1.1676 | 0.0042384 | 0.15789 | 0.48667 | 0.10212 | 0.14893 | wr,symbol,year | wr,expectancy,pf,symbol,year,tail |
| time_10 | TAIL-SENSITIVE | 547 | 0.40768 | 0.070512 | -0.043581 | 1.1136 | 0.0029321 | 0.24 | 0.47305 | 0.071145 | 0.13292 | wr,tail | wr,expectancy,pf,symbol,year,tail |
| time_15 | TAIL-SENSITIVE | 547 | 0.40768 | 0.070512 | -0.043581 | 1.1136 | 0.0029321 | 0.24 | 0.47305 | 0.071145 | 0.13292 | wr,tail | wr,expectancy,pf,symbol,year,tail |
| time_5 | TAIL-SENSITIVE | 557 | 0.40395 | 0.069247 | -0.042742 | 1.098 | 0.0024964 | 0.24 | 0.47337 | 0.075074 | 0.13087 | wr,symbol,tail | wr,expectancy,pf,symbol,year,tail |

Winner stop tolerance (bounds, fractions):

| module | adverse_threshold | winners | definitely_touched | possibly_touched | fraction_definite | fraction_possible |
| --- | --- | --- | --- | --- | --- | --- |
| breakout | -0.01 | 223 | 123 | 127 | 0.55157 | 0.56951 |
| breakout | -0.02 | 223 | 81 | 83 | 0.36323 | 0.3722 |
| breakout | -0.03 | 223 | 50 | 52 | 0.22422 | 0.23318 |
