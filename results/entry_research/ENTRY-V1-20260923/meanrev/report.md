# Pure Mean Reversion Entry Research V1

Behavior change: NO. Existing strategy behavior changed: NO.
Research orchestration only; production calculations and existing outcomes are unchanged.

Pure means current active-module mask equals 1/2/4/8, followed by current final
signal. Module sole blockers with no other active module are a separate
DESCRIPTIVE cohort: they are not pure activated signals. All independent module
and final requirements must otherwise pass; derived score failure is not counted
a second time. All-bar sequential funnels use diagnostic column order, without
claiming causal priority. Safe one-filter ablations preserve the active mask.

Forward returns and MFE/MAE use the existing Historical Outcome Engine, anchored
to signal close (not a fill). Default barriers +3%/-2% and +5%/-3% and horizons
1/3/5/10/20 are unchanged. Ambiguous/censored paths are excluded from resolved
barrier denominators. Horizon incompleteness is not a loss. Discovery labels
never cross the holdout boundary. Event ends and conversion are retrospective.

All four modules' discovery hypotheses and bin edges were frozen before holdout
labels were computed. Entry Holdout is NOT untouched strategy OOS: Exit Research
already used this history. Effects are unpaired observational differences,
confounded by selection, contemporaneous market moves and overlapping windows.
No statistical significance, independence, costs, portfolio return, TradingView
parity, production policy or ML result is claimed. Present-day universe selection,
ARM's shorter history, warm-up and small cohorts limit generalization. A fixed
30 observations per arm is only a reporting screen. No thresholds are optimized.

| partition | opportunities | pure_active | signals | final_gate_conversion | symbols | years |
| --- | --- | --- | --- | --- | --- | --- |
| discovery | 1548 | 53 | 47 | 0.88679 | 31 | 4 |
| holdout | 411 | 12 | 12 | 1 | 11 | 2 |

Existing module event conversion (includes overlap; conversion is to module activation, not necessarily a final signal; rate in percent):

| partition | opportunity_events | eligible_events | converted_events | conversion_rate | censored_events |
| --- | --- | --- | --- | --- | --- |
| discovery | 1837 | 1828 | 26 | 1.4223 | 9 |
| holdout | 505 | 494 | 3 | 0.40486 | 10 |

Approved pure future outcomes (fractions; sample counts exclude incomplete horizons):

| partition | horizon | complete | censored | mean | median | positive_rate | mean_mfe | mean_mae |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| discovery | 1 | 47 | 0 | 0.00041329 | 0.0011832 | 0.53191 | 0.014248 | -0.012758 |
| discovery | 3 | 47 | 0 | 0.011559 | 0.0093705 | 0.59574 | 0.032741 | -0.022003 |
| discovery | 5 | 47 | 0 | 0.02123 | 0.02146 | 0.65957 | 0.047173 | -0.028409 |
| discovery | 10 | 47 | 0 | 0.027298 | 0.026956 | 0.65957 | 0.070249 | -0.036043 |
| discovery | 20 | 47 | 0 | 0.035975 | 0.031831 | 0.65957 | 0.095624 | -0.060064 |
| holdout | 1 | 11 | 1 | -0.01184 | -0.001933 | 0.45455 | 0.024679 | -0.0192 |
| holdout | 3 | 11 | 1 | -0.024249 | 0.0080418 | 0.54545 | 0.026694 | -0.04283 |
| holdout | 5 | 10 | 2 | -0.012274 | 0.0086489 | 0.6 | 0.043091 | -0.058883 |
| holdout | 10 | 10 | 2 | 0.0087286 | 0.029436 | 0.6 | 0.061519 | -0.064893 |
| holdout | 20 | 10 | 2 | -0.034187 | -0.041215 | 0.3 | 0.079822 | -0.10165 |

Discovery filters; B is the strictly isolated single blocker and A the approved pure cohort:

| filter | research_label | ablation_status | a_complete | b_complete | delta_mean | delta_trimmed | tail_dependent | year_agreement | symbol_agreement |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mr_long_fail_trend | LOW SAMPLE | NOT SAFE FOR ABLATION | 47 | 2 | 0.048076 | 0.050201 | False | NA | NA |
| mr_long_fail_slow_ema | MIXED | NOT SAFE FOR ABLATION | 47 | 78 | -0.003924 | -0.0021688 | True | 0.5 | NA |
| mr_long_fail_oversold | MIXED | NOT SAFE FOR ABLATION | 47 | 1281 | -0.022523 | -0.022381 | False | 1 | NA |
| mr_long_fail_rsi_cross | MIXED | NOT SAFE FOR ABLATION | 47 | 151 | -0.0067996 | -0.0028641 | True | 1 | NA |
| mr_long_fail_candle | LOW SAMPLE | NOT SAFE FOR ABLATION | 47 | 10 | -0.015759 | -0.0034459 | False | 1 | NA |
| long_fail_direction | LOW SAMPLE | SAFE FINAL GATE | 47 | 0 | NA | NA | False | NA | NA |
| long_fail_volatility | LOW SAMPLE | SAFE FINAL GATE | 47 | 0 | NA | NA | False | NA | NA |
| long_fail_candle | LOW SAMPLE | SAFE FINAL GATE | 47 | 6 | -0.013409 | -0.011284 | True | 0 | NA |
| long_fail_session | LOW SAMPLE | SAFE FINAL GATE | 47 | 0 | NA | NA | False | NA | NA |
| long_fail_confirmed | LOW SAMPLE | SAFE FINAL GATE | 47 | 0 | NA | NA | False | NA | NA |

Frozen hypotheses and Entry Holdout:

| kind | feature | discovery_a_n | discovery_b_n | a_complete | b_complete | discovery_delta | delta_mean | direction_replicated | final_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| filter | mr_long_fail_trend | 47 | 2 | 10 | 0 | 0.048076 | NA | False | LOW SAMPLE |
| filter | mr_long_fail_slow_ema | 47 | 78 | 10 | 28 | -0.003924 | -0.0097768 | True | LOW SAMPLE |
| filter | mr_long_fail_oversold | 47 | 1281 | 10 | 334 | -0.022523 | 0.0062927 | False | LOW SAMPLE |
| filter | mr_long_fail_rsi_cross | 47 | 151 | 10 | 30 | -0.0067996 | 0.0011209 | False | LOW SAMPLE |
| filter | mr_long_fail_candle | 47 | 10 | 10 | 2 | -0.015759 | -0.082076 | True | LOW SAMPLE |
| filter | long_fail_direction | 47 | 0 | 10 | 0 | NA | NA | False | LOW SAMPLE |
| filter | long_fail_volatility | 47 | 0 | 10 | 0 | NA | NA | False | LOW SAMPLE |
| filter | long_fail_candle | 47 | 6 | 10 | 0 | -0.013409 | NA | False | LOW SAMPLE |
| filter | long_fail_session | 47 | 0 | 10 | 0 | NA | NA | False | LOW SAMPLE |
| filter | long_fail_confirmed | 47 | 0 | 10 | 0 | NA | NA | False | LOW SAMPLE |
| feature | rsi | 10 | 10 | 1 | 1 | 0.013141 | -0.0028335 | False | LOW SAMPLE |
| feature | rsi_distance_from_avg | 10 | 10 | 1 | 5 | -0.020067 | -0.070114 | True | LOW SAMPLE |
| feature | htf_adx | 10 | 10 | 2 | 1 | 0.0064423 | -0.04148 | False | LOW SAMPLE |
| feature | adx_margin | 10 | 10 | 2 | 1 | 0.0064423 | -0.04148 | False | LOW SAMPLE |
| feature | ema_spread_pct | 10 | 10 | 1 | 2 | 0.024045 | 0.011346 | True | LOW SAMPLE |
| feature | atr_pct | 10 | 10 | 2 | 3 | 0.020249 | -0.10742 | False | LOW SAMPLE |
| feature | candle_range_atr | 10 | 10 | 2 | 5 | 0.018952 | -0.011765 | False | LOW SAMPLE |
| feature | volume_ratio | 10 | 10 | 1 | 3 | 0.049142 | -0.084846 | False | LOW SAMPLE |
| feature | distance_to_breakout_atr | 10 | 10 | 3 | 1 | -0.037128 | -0.017695 | True | LOW SAMPLE |
| feature | bb_width | 10 | 10 | 2 | 2 | 0.025422 | -0.1747 | False | LOW SAMPLE |
| feature | distance_to_squeeze_pct | 10 | 10 | 2 | 3 | 0.0075242 | -0.061758 | False | LOW SAMPLE |
| feature | distance_to_upper_band_atr | 10 | 10 | 3 | 1 | 0.0037204 | -0.050073 | False | LOW SAMPLE |
| feature | bars_since_rsi_up | 47 | 0 | 10 | 0 | NA | NA | False | LOW SAMPLE |
| feature | bars_since_oversold | 20 | 8 | 5 | 0 | 0.045438 | NA | False | LOW SAMPLE |
| feature | bars_since_squeeze | 9 | 8 | 2 | 1 | -0.031099 | 0.084131 | False | LOW SAMPLE |

See discovery/ and holdout/ CSVs for all five horizons, funnel, near misses, ablations, bins, feature distributions, false-positive enrichment, false-negative margins, and per-hypothesis year/symbol results.
