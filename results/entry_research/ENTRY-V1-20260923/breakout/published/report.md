# Pure Breakout Entry Research V1

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
| discovery | 5388 | 850 | 797 | 0.93765 | 50 | 5 |
| holdout | 1467 | 239 | 216 | 0.90377 | 40 | 2 |

Existing module event conversion (includes overlap; conversion is to module activation, not necessarily a final signal; rate in percent):

| partition | opportunity_events | eligible_events | converted_events | conversion_rate | censored_events |
| --- | --- | --- | --- | --- | --- |
| discovery | 3522 | 3480 | 652 | 18.534 | 35 |
| holdout | 950 | 925 | 181 | 19.459 | 24 |

Approved pure future outcomes (fractions; sample counts exclude incomplete horizons):

| partition | horizon | complete | censored | mean | median | positive_rate | mean_mfe | mean_mae |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| discovery | 1 | 792 | 5 | 0.00049156 | 0.0017987 | 0.53788 | 0.015352 | -0.013416 |
| discovery | 3 | 787 | 10 | 0.0027679 | 0.0020757 | 0.5324 | 0.02962 | -0.025526 |
| discovery | 5 | 787 | 10 | 0.0039661 | 0.0028291 | 0.53367 | 0.039858 | -0.033261 |
| discovery | 10 | 780 | 17 | 0.010032 | 0.007929 | 0.57308 | 0.058854 | -0.04608 |
| discovery | 20 | 773 | 24 | 0.020034 | 0.01804 | 0.57827 | 0.087766 | -0.064783 |
| holdout | 1 | 215 | 1 | -0.0011903 | -0.0013663 | 0.46047 | 0.01736 | -0.017198 |
| holdout | 3 | 214 | 2 | -0.0025266 | -0.0067016 | 0.44393 | 0.033429 | -0.036901 |
| holdout | 5 | 211 | 5 | -0.0030731 | -0.0064433 | 0.47867 | 0.044243 | -0.046782 |
| holdout | 10 | 211 | 5 | 0.0058413 | 0.0023217 | 0.50711 | 0.066581 | -0.063987 |
| holdout | 20 | 201 | 15 | 0.017478 | 0.0081349 | 0.55721 | 0.1041 | -0.083222 |

Discovery filters; B is the strictly isolated single blocker and A the approved pure cohort:

| filter | research_label | ablation_status | a_complete | b_complete | delta_mean | delta_trimmed | tail_dependent | year_agreement | symbol_agreement |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bo_long_fail_trend | MIXED | NOT SAFE FOR ABLATION | 780 | 1007 | 0.0036522 | 0.0030219 | False | 0.6 | 0.68085 |
| bo_long_fail_price | POTENTIALLY TOO STRICT | NOT SAFE FOR ABLATION | 780 | 2992 | 0.0075697 | 0.0059705 | False | 1 | 0.61702 |
| bo_long_fail_volume | SUPPORTED | NOT SAFE FOR ABLATION | 780 | 572 | -0.011469 | -0.007733 | False | 0.8 | 0.625 |
| bo_long_fail_rsi | MIXED | NOT SAFE FOR ABLATION | 780 | 474 | 0.0020749 | 0.0024253 | True | 0.8 | 0.46341 |
| long_fail_direction | LOW SAMPLE | SAFE FINAL GATE | 780 | 0 | NA | NA | False | NA | NA |
| long_fail_volatility | LOW SAMPLE | SAFE FINAL GATE | 780 | 0 | NA | NA | False | NA | NA |
| long_fail_candle | MIXED | SAFE FINAL GATE | 780 | 52 | 0.032121 | 0.015794 | False | 0.75 | NA |
| long_fail_session | LOW SAMPLE | SAFE FINAL GATE | 780 | 0 | NA | NA | False | NA | NA |
| long_fail_confirmed | LOW SAMPLE | SAFE FINAL GATE | 780 | 0 | NA | NA | False | NA | NA |

Frozen hypotheses and Entry Holdout:

| kind | feature | discovery_a_n | discovery_b_n | a_complete | b_complete | discovery_delta | delta_mean | direction_replicated | final_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| filter | bo_long_fail_trend | 780 | 1007 | 211 | 237 | 0.0036522 | 0.012495 | True | PARTIAL |
| filter | bo_long_fail_price | 780 | 2992 | 211 | 845 | 0.0075697 | 0.0083721 | True | REPLICATED |
| filter | bo_long_fail_volume | 780 | 572 | 211 | 142 | -0.011469 | 0.0095883 | False | FAILED HOLDOUT |
| filter | bo_long_fail_rsi | 780 | 474 | 211 | 125 | 0.0020749 | 0.040666 | True | PARTIAL |
| filter | long_fail_direction | 780 | 0 | 211 | 0 | NA | NA | False | LOW SAMPLE |
| filter | long_fail_volatility | 780 | 0 | 211 | 0 | NA | NA | False | LOW SAMPLE |
| filter | long_fail_candle | 780 | 52 | 211 | 23 | 0.032121 | 0.01494 | True | LOW SAMPLE |
| filter | long_fail_session | 780 | 0 | 211 | 0 | NA | NA | False | LOW SAMPLE |
| filter | long_fail_confirmed | 780 | 0 | 211 | 0 | NA | NA | False | LOW SAMPLE |
| feature | rsi | 157 | 158 | 54 | 37 | -0.0029662 | -0.0034741 | True | PARTIAL |
| feature | rsi_distance_from_avg | 158 | 155 | 37 | 46 | 0.013555 | -0.035705 | False | FAILED HOLDOUT |
| feature | htf_adx | 148 | 159 | 48 | 23 | -0.015079 | 0.010707 | False | LOW SAMPLE |
| feature | adx_margin | 148 | 159 | 48 | 23 | -0.015079 | 0.010707 | False | LOW SAMPLE |
| feature | ema_spread_pct | 156 | 155 | 34 | 73 | 0.012668 | -0.017039 | False | FAILED HOLDOUT |
| feature | atr_pct | 156 | 157 | 4 | 61 | -0.0032837 | -0.032228 | True | LOW SAMPLE |
| feature | candle_range_atr | 153 | 157 | 45 | 53 | -0.00094932 | 0.027338 | False | FAILED HOLDOUT |
| feature | volume_ratio | 158 | 154 | 49 | 39 | -0.00341 | -0.0037707 | True | PARTIAL |
| feature | distance_to_breakout_atr | 156 | 156 | 51 | 40 | -0.0093703 | -0.0041374 | True | PARTIAL |
| feature | bb_width | 155 | 158 | 18 | 64 | 0.0028977 | 0.0067131 | True | LOW SAMPLE |
| feature | distance_to_squeeze_pct | 151 | 149 | 33 | 66 | 0.010619 | -0.0033606 | False | FAILED HOLDOUT |
| feature | distance_to_upper_band_atr | 155 | 159 | 46 | 48 | 0.012635 | 0.0003321 | True | PARTIAL |
| feature | bars_since_rsi_up | 187 | 80 | 49 | 18 | -0.0057376 | 0.038204 | False | LOW SAMPLE |
| feature | bars_since_oversold | 148 | 147 | 29 | 3 | 0.019091 | -0.080322 | False | LOW SAMPLE |
| feature | bars_since_squeeze | 239 | 148 | 53 | 69 | -0.0034706 | -0.001777 | True | PARTIAL |

See discovery/ and holdout/ CSVs for all five horizons, funnel, near misses, ablations, bins, feature distributions, false-positive enrichment, false-negative margins, and per-hypothesis year/symbol results.
