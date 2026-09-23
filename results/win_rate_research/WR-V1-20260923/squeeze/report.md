# squeeze: Win Rate V1

| module | baseline_wr | baseline_trades | bad_entry_like_fraction | giveback_fraction | dead_fraction | uncertain_fraction | largest_category | highest_observed_scenario | highest_observed_wr | trades | pf | expectancy | status | robust_supported_wr |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| squeeze | 0.34021 | 194 | 0.17188 | 0.80469 | 0 | 0.023438 | GIVEBACK_LOSER | lock25_1 | 0.59716 | 211 | 1.0128 | 0.00015311 | TAIL-SENSITIVE | NA |

All predefined scenarios, without selecting a production policy:

| scenario | status | trades | win_rate | mean_winner | mean_loser | profit_factor | expectancy | year_wr_min | year_wr_max | year_wr_std | symbol_wr_std | discovery_failed | holdout_failed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | TAIL-SENSITIVE | 194 | 0.34021 | 0.081789 | -0.036872 | 1.1438 | 0.0034972 | 0.25581 | 0.39535 | 0.049034 | 0.17638 | wr,tail | sample,wr,expectancy,pf,symbol,year,tail |
| breakeven_1 | TAIL-SENSITIVE | 209 | 0.15311 | 0.076079 | -0.030754 | 0.83327 | -0.0023308 | 0.071429 | 0.20455 | 0.048512 | 0.127 | wr,expectancy,pf,symbol,year,tail | sample,wr,expectancy,pf,winner_size,symbol,year,tail |
| breakeven_2 | TAIL-SENSITIVE | 202 | 0.22772 | 0.073097 | -0.038501 | 0.99243 | -0.0001269 | 0.14286 | 0.30769 | 0.063651 | 0.15382 | wr,expectancy,pf,symbol,year,tail | sample,wr,expectancy,pf,symbol,year,tail |
| breakeven_3 | TAIL-SENSITIVE | 198 | 0.27778 | 0.071672 | -0.038825 | 1.0256 | 0.00049634 | 0.15385 | 0.34091 | 0.070363 | 0.16527 | wr,expectancy,pf,year,tail | sample,wr,expectancy,pf,symbol,year,tail |
| breakeven_4 | TAIL-SENSITIVE | 196 | 0.31633 | 0.069813 | -0.038503 | 1.0506 | 0.001064 | 0.23077 | 0.37209 | 0.054159 | 0.17609 | wr,expectancy,pf,year,tail | sample,wr,expectancy,pf,symbol,year,tail |
| early_3 | TAIL-SENSITIVE | 194 | 0.33505 | 0.082322 | -0.034649 | 1.1972 | 0.0045426 | 0.25581 | 0.39535 | 0.04782 | 0.17638 | wr,year,tail | sample,wr,expectancy,pf,symbol,year,tail |
| lock25_1 | TAIL-SENSITIVE | 211 | 0.59716 | 0.020268 | -0.029664 | 1.0128 | 0.00015311 | 0.5 | 0.65909 | 0.054464 | 0.17735 | expectancy,pf,winner_size,symbol,year,tail | sample,expectancy,pf,winner_size,symbol,year,tail |
| lock25_2 | TAIL-SENSITIVE | 206 | 0.59223 | 0.027642 | -0.040429 | 0.99303 | -0.00011483 | 0.55319 | 0.63014 | 0.026668 | 0.16035 | expectancy,pf,winner_size,year,tail | sample,expectancy,pf,winner_size,symbol,year,tail |
| lock25_3 | TAIL-SENSITIVE | 201 | 0.52239 | 0.037663 | -0.040125 | 1.0266 | 0.00051041 | 0.30769 | 0.57746 | 0.095081 | 0.21104 | expectancy,pf,winner_size,year,tail | sample,expectancy,pf,winner_size,symbol,year,tail |
| lock25_4 | TAIL-SENSITIVE | 198 | 0.46465 | 0.048627 | -0.038856 | 1.0862 | 0.0017926 | 0.30769 | 0.50704 | 0.071615 | 0.22785 | expectancy,winner_size,year,tail | sample,expectancy,pf,winner_size,symbol,year,tail |
| skip_bars_since_oversold_4 | MIXED | 147 | 0.38776 | 0.085141 | -0.037303 | 1.4455 | 0.010175 | 0.25 | 0.42857 | 0.064797 | 0.048711 | symbol | sample,count,expectancy,pf,symbol,year,tail |
| skip_bars_since_rsi_up_5 | TAIL-SENSITIVE | 170 | 0.35882 | 0.075214 | -0.036016 | 1.1687 | 0.0038959 | 0.28571 | 0.39683 | 0.038459 | 0.16688 | symbol,tail | sample,wr,expectancy,pf,symbol,year,tail |
| skip_candle_range_atr_2 | TAIL-SENSITIVE | 162 | 0.3642 | 0.085887 | -0.034976 | 1.4066 | 0.0090419 | 0.27273 | 0.41379 | 0.057607 | 0.14096 | wr,symbol,year,tail | sample,expectancy,pf,symbol,year,tail |
| time_10 | TAIL-SENSITIVE | 194 | 0.34021 | 0.081789 | -0.036872 | 1.1438 | 0.0034972 | 0.25581 | 0.39535 | 0.049034 | 0.17638 | wr,tail | sample,wr,expectancy,pf,symbol,year,tail |
| time_15 | TAIL-SENSITIVE | 194 | 0.34021 | 0.081789 | -0.036872 | 1.1438 | 0.0034972 | 0.25581 | 0.39535 | 0.049034 | 0.17638 | wr,tail | sample,wr,expectancy,pf,symbol,year,tail |
| time_5 | TAIL-SENSITIVE | 194 | 0.3299 | 0.082622 | -0.035138 | 1.1576 | 0.003711 | 0.25581 | 0.39535 | 0.04729 | 0.17638 | wr,tail | sample,wr,expectancy,pf,symbol,year,tail |

Winner stop tolerance (bounds, fractions):

| module | adverse_threshold | winners | definitely_touched | possibly_touched | fraction_definite | fraction_possible |
| --- | --- | --- | --- | --- | --- | --- |
| squeeze | -0.01 | 66 | 43 | 45 | 0.65152 | 0.68182 |
| squeeze | -0.02 | 66 | 29 | 31 | 0.43939 | 0.4697 |
| squeeze | -0.03 | 66 | 14 | 14 | 0.21212 | 0.21212 |
