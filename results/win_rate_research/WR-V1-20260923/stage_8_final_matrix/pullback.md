# pullback: Win Rate V1

| module | baseline_wr | baseline_trades | bad_entry_like_fraction | giveback_fraction | dead_fraction | uncertain_fraction | largest_category | highest_observed_scenario | highest_observed_wr | trades | pf | expectancy | status | robust_supported_wr |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pullback | 0.427 | 363 | 0.28365 | 0.69231 | 0 | 0.024038 | SMALL_PROFIT_GIVEBACK | lock25_1 | 0.56712 | 365 | 1.4258 | 0.0050357 | MIXED | NA |

All predefined scenarios, without selecting a production policy:

| scenario | status | trades | win_rate | mean_winner | mean_loser | profit_factor | expectancy | year_wr_min | year_wr_max | year_wr_std | symbol_wr_std | discovery_failed | holdout_failed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | INCONCLUSIVE | 363 | 0.427 | 0.059225 | -0.027289 | 1.6172 | 0.0096519 | 0.29412 | 0.47619 | 0.077248 | 0.16692 | wr | sample,wr,symbol,year,tail |
| breakeven_1 | MIXED | 365 | 0.29863 | 0.055888 | -0.026614 | 1.4043 | 0.0048049 | 0.23333 | 0.33333 | 0.034571 | 0.16244 | wr,expectancy,pf,symbol,year | sample,wr,symbol,year,tail |
| breakeven_2 | MIXED | 364 | 0.3544 | 0.055014 | -0.027461 | 1.4278 | 0.0058417 | 0.26667 | 0.4127 | 0.052558 | 0.16421 | wr,expectancy,pf,symbol,year | sample,wr,symbol,year,tail |
| breakeven_3 | MIXED | 363 | 0.39669 | 0.056936 | -0.027681 | 1.5426 | 0.0079448 | 0.27119 | 0.44444 | 0.070043 | 0.15745 | wr,expectancy,symbol,year | sample,wr,symbol,year,tail |
| breakeven_4 | MIXED | 363 | 0.41598 | 0.05887 | -0.027365 | 1.6324 | 0.0094868 | 0.28814 | 0.46032 | 0.07569 | 0.16399 | wr,year | sample,wr,symbol,year,tail |
| early_3 | MIXED | 363 | 0.427 | 0.059225 | -0.027289 | 1.6172 | 0.0096519 | 0.29412 | 0.47619 | 0.077248 | 0.16692 | wr | sample,wr,symbol,year,tail |
| lock25_1 | MIXED | 365 | 0.56712 | 0.029733 | -0.027321 | 1.4258 | 0.0050357 | 0.47059 | 0.61905 | 0.055277 | 0.16687 | expectancy,pf,winner_size,symbol,year | sample,winner_size,symbol,year,tail |
| lock25_2 | MIXED | 364 | 0.51923 | 0.037824 | -0.028265 | 1.4452 | 0.0060505 | 0.35294 | 0.54762 | 0.067142 | 0.19281 | expectancy,pf,winner_size,symbol,year | sample,winner_size,symbol,year,tail |
| lock25_3 | MIXED | 363 | 0.47934 | 0.046376 | -0.02807 | 1.521 | 0.0076147 | 0.35294 | 0.52381 | 0.061953 | 0.1847 | expectancy,symbol | sample,expectancy,pf,winner_size,symbol,year,tail |
| lock25_4 | MIXED | 363 | 0.45455 | 0.051904 | -0.027485 | 1.5737 | 0.0086008 | 0.35294 | 0.49206 | 0.060254 | 0.17819 | symbol | sample,expectancy,pf,symbol,year,tail |
| skip_bb_width_5 | MIXED | 289 | 0.44291 | 0.054443 | -0.021064 | 2.0549 | 0.012379 | 0.22222 | 0.49254 | 0.099591 | 0.17885 | wr | sample,wr,symbol,year,tail |
| skip_candle_range_atr_4 | MIXED | 299 | 0.43144 | 0.062267 | -0.026589 | 1.7771 | 0.011747 | 0.23077 | 0.48148 | 0.093618 | 0.15729 | wr,symbol,year | sample,wr,symbol,year,tail |
| skip_rsi_distance_from_avg_2 | MIXED | 282 | 0.42908 | 0.063213 | -0.027909 | 1.7023 | 0.01119 | 0.30233 | 0.5 | 0.069465 | 0.16099 | wr,symbol,year | sample,wr,symbol,year,tail |
| time_10 | MIXED | 363 | 0.427 | 0.059225 | -0.027289 | 1.6172 | 0.0096519 | 0.29412 | 0.47619 | 0.077248 | 0.16692 | wr | sample,wr,symbol,year,tail |
| time_15 | MIXED | 363 | 0.427 | 0.059225 | -0.027289 | 1.6172 | 0.0096519 | 0.29412 | 0.47619 | 0.077248 | 0.16692 | wr | sample,wr,symbol,year,tail |
| time_5 | MIXED | 363 | 0.427 | 0.059225 | -0.027289 | 1.6172 | 0.0096519 | 0.29412 | 0.47619 | 0.077248 | 0.16692 | wr | sample,wr,symbol,year,tail |

Winner stop tolerance (bounds, fractions):

| module | adverse_threshold | winners | definitely_touched | possibly_touched | fraction_definite | fraction_possible |
| --- | --- | --- | --- | --- | --- | --- |
| pullback | -0.01 | 155 | 66 | 72 | 0.42581 | 0.46452 |
| pullback | -0.02 | 155 | 23 | 27 | 0.14839 | 0.17419 |
| pullback | -0.03 | 155 | 7 | 8 | 0.045161 | 0.051613 |
