# meanrev: Win Rate V1

| module | baseline_wr | baseline_trades | bad_entry_like_fraction | giveback_fraction | dead_fraction | uncertain_fraction | largest_category | highest_observed_scenario | highest_observed_wr | trades | pf | expectancy | status | robust_supported_wr |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| meanrev | 0.49091 | 55 | 0.17857 | 0.82143 | 0 | 0 | SMALL_PROFIT_GIVEBACK | lock25_2 | 0.56364 | 55 | 0.9089 | -0.0017379 | LOW SAMPLE | NA |

All predefined scenarios, without selecting a production policy:

| scenario | status | trades | win_rate | mean_winner | mean_loser | profit_factor | expectancy | year_wr_min | year_wr_max | year_wr_std | symbol_wr_std | discovery_failed | holdout_failed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | LOW SAMPLE | 55 | 0.49091 | 0.07108 | -0.042199 | 1.6243 | 0.013411 | 0.28571 | 0.625 | 0.12557 | NA | sample,wr,symbol,tail | sample,wr,symbol,year,tail |
| breakeven_1 | LOW SAMPLE | 56 | 0.28571 | 0.069887 | -0.036961 | 1.2101 | 0.0034671 | 0 | 0.42105 | 0.13935 | NA | sample,wr,expectancy,symbol,year,tail | sample,wr,expectancy,pf,winner_size,symbol,year,tail |
| breakeven_2 | LOW SAMPLE | 55 | 0.38182 | 0.06107 | -0.043719 | 1.2223 | 0.0042402 | 0.125 | 0.52632 | 0.13198 | NA | sample,wr,expectancy,symbol,year,tail | sample,wr,expectancy,pf,winner_size,symbol,year,tail |
| breakeven_3 | LOW SAMPLE | 55 | 0.41818 | 0.061859 | -0.044515 | 1.2784 | 0.0056341 | 0.125 | 0.625 | 0.17603 | NA | sample,wr,symbol,year,tail | sample,wr,expectancy,pf,winner_size,symbol,year,tail |
| breakeven_4 | LOW SAMPLE | 55 | 0.47273 | 0.068856 | -0.044353 | 1.5525 | 0.011583 | 0.25 | 0.625 | 0.15093 | NA | sample,wr,symbol,tail | sample,wr,expectancy,pf,symbol,year,tail |
| early_3 | LOW SAMPLE | 55 | 0.45455 | 0.073684 | -0.039985 | 1.5357 | 0.011683 | 0.28571 | 0.52632 | 0.088334 | NA | sample,wr,expectancy,pf,symbol,year,tail | sample,wr,symbol,year,tail |
| lock25_1 | LOW SAMPLE | 56 | 0.55357 | 0.027775 | -0.036961 | 0.93181 | -0.0011252 | 0.125 | 0.71429 | 0.21303 | NA | sample,expectancy,pf,winner_size,symbol,year,tail | sample,wr,expectancy,pf,winner_size,symbol,year,tail |
| lock25_2 | LOW SAMPLE | 55 | 0.56364 | 0.030764 | -0.043719 | 0.9089 | -0.0017379 | 0.25 | 0.75 | 0.17699 | NA | sample,expectancy,pf,winner_size,symbol,year,tail | sample,wr,expectancy,pf,winner_size,symbol,year,tail |
| lock25_3 | LOW SAMPLE | 55 | 0.54545 | 0.03677 | -0.044515 | 0.9912 | -0.00017802 | 0.25 | 0.75 | 0.18202 | NA | sample,expectancy,pf,winner_size,symbol,year,tail | sample,wr,expectancy,pf,winner_size,symbol,year,tail |
| lock25_4 | LOW SAMPLE | 55 | 0.52727 | 0.052239 | -0.044353 | 1.3137 | 0.0065775 | 0.375 | 0.625 | 0.091169 | NA | sample,expectancy,pf,winner_size,symbol,year,tail | sample,wr,expectancy,pf,symbol,year,tail |
| time_10 | LOW SAMPLE | 55 | 0.47273 | 0.073652 | -0.041025 | 1.6096 | 0.013186 | 0.28571 | 0.625 | 0.11755 | NA | sample,wr,symbol,year,tail | sample,wr,symbol,year,tail |
| time_15 | LOW SAMPLE | 55 | 0.49091 | 0.07108 | -0.042199 | 1.6243 | 0.013411 | 0.28571 | 0.625 | 0.12557 | NA | sample,wr,symbol,tail | sample,wr,symbol,year,tail |
| time_5 | LOW SAMPLE | 55 | 0.47273 | 0.073652 | -0.040444 | 1.6327 | 0.013492 | 0.28571 | 0.625 | 0.11755 | NA | sample,wr,symbol,year,tail | sample,wr,symbol,year,tail |

Winner stop tolerance (bounds, fractions):

| module | adverse_threshold | winners | definitely_touched | possibly_touched | fraction_definite | fraction_possible |
| --- | --- | --- | --- | --- | --- | --- |
| meanrev | -0.01 | 27 | 17 | 17 | 0.62963 | 0.62963 |
| meanrev | -0.02 | 27 | 10 | 10 | 0.37037 | 0.37037 |
| meanrev | -0.03 | 27 | 5 | 5 | 0.18519 | 0.18519 |
