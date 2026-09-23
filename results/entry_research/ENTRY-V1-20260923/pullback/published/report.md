# Pure Pullback Entry Research V1

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
| discovery | 3231 | 298 | 291 | 0.97651 | 49 | 5 |
| holdout | 987 | 86 | 84 | 0.97674 | 36 | 2 |

Existing module event conversion (includes overlap; conversion is to module activation, not necessarily a final signal; rate in percent):

| partition | opportunity_events | eligible_events | converted_events | conversion_rate | censored_events |
| --- | --- | --- | --- | --- | --- |
| discovery | 1639 | 1628 | 298 | 18.243 | 10 |
| holdout | 540 | 525 | 98 | 18.476 | 14 |

Approved pure future outcomes (fractions; sample counts exclude incomplete horizons):

| partition | horizon | complete | censored | mean | median | positive_rate | mean_mfe | mean_mae |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| discovery | 1 | 291 | 0 | -1.9134e-05 | 0.00061974 | 0.51203 | 0.015834 | -0.015242 |
| discovery | 3 | 290 | 1 | 0.0040998 | 0.0063521 | 0.58621 | 0.032855 | -0.029512 |
| discovery | 5 | 290 | 1 | 0.0064461 | 0.0086782 | 0.58621 | 0.043867 | -0.036769 |
| discovery | 10 | 288 | 3 | 0.019278 | 0.011467 | 0.57292 | 0.065884 | -0.049124 |
| discovery | 20 | 284 | 7 | 0.030642 | 0.013486 | 0.60563 | 0.095771 | -0.071382 |
| holdout | 1 | 83 | 1 | 0.0012834 | 0.001175 | 0.53012 | 0.015951 | -0.017064 |
| holdout | 3 | 83 | 1 | -0.0039196 | -0.0022435 | 0.46988 | 0.027734 | -0.032324 |
| holdout | 5 | 83 | 1 | -0.00023987 | -0.00041933 | 0.49398 | 0.04176 | -0.045732 |
| holdout | 10 | 83 | 1 | -0.0016036 | 0.0051709 | 0.51807 | 0.057724 | -0.064538 |
| holdout | 20 | 83 | 1 | 0.008886 | -0.0051971 | 0.49398 | 0.088899 | -0.087487 |

Discovery filters; B is the strictly isolated single blocker and A the approved pure cohort:

| filter | research_label | ablation_status | a_complete | b_complete | delta_mean | delta_trimmed | tail_dependent | year_agreement | symbol_agreement |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pb_long_fail_trend | SUPPORTED | NOT SAFE FOR ABLATION | 288 | 460 | -0.011517 | -0.0057186 | False | 0.6 | 0.62069 |
| pb_long_fail_slow_ema | LOW SAMPLE | NOT SAFE FOR ABLATION | 288 | 0 | NA | NA | False | NA | NA |
| pb_long_fail_rsi | MIXED | NOT SAFE FOR ABLATION | 288 | 190 | -0.030003 | -0.02156 | False | 0.8 | 0.58333 |
| pb_long_fail_touch | LOW SAMPLE | NOT SAFE FOR ABLATION | 288 | 0 | NA | NA | False | NA | NA |
| pb_long_fail_reclaim | MIXED | NOT SAFE FOR ABLATION | 288 | 2463 | -0.0026549 | 0.0010261 | True | 0.6 | 0.41935 |
| long_fail_direction | LOW SAMPLE | SAFE FINAL GATE | 288 | 0 | NA | NA | False | NA | NA |
| long_fail_volatility | LOW SAMPLE | SAFE FINAL GATE | 288 | 0 | NA | NA | False | NA | NA |
| long_fail_candle | LOW SAMPLE | SAFE FINAL GATE | 288 | 7 | 0.015342 | 0.02061 | True | 1 | NA |
| long_fail_session | LOW SAMPLE | SAFE FINAL GATE | 288 | 0 | NA | NA | False | NA | NA |
| long_fail_confirmed | LOW SAMPLE | SAFE FINAL GATE | 288 | 0 | NA | NA | False | NA | NA |

Frozen hypotheses and Entry Holdout:

| kind | feature | discovery_a_n | discovery_b_n | a_complete | b_complete | discovery_delta | delta_mean | direction_replicated | final_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| filter | pb_long_fail_trend | 288 | 460 | 83 | 169 | -0.011517 | 0.0027921 | False | FAILED HOLDOUT |
| filter | pb_long_fail_slow_ema | 288 | 0 | 83 | 0 | NA | NA | False | LOW SAMPLE |
| filter | pb_long_fail_rsi | 288 | 190 | 83 | 48 | -0.030003 | 0.0032849 | False | FAILED HOLDOUT |
| filter | pb_long_fail_touch | 288 | 0 | 83 | 0 | NA | NA | False | LOW SAMPLE |
| filter | pb_long_fail_reclaim | 288 | 2463 | 83 | 722 | -0.0026549 | 0.011944 | False | FAILED HOLDOUT |
| filter | long_fail_direction | 288 | 0 | 83 | 0 | NA | NA | False | LOW SAMPLE |
| filter | long_fail_volatility | 288 | 0 | 83 | 0 | NA | NA | False | LOW SAMPLE |
| filter | long_fail_candle | 288 | 7 | 83 | 2 | 0.015342 | 0.088514 | True | LOW SAMPLE |
| filter | long_fail_session | 288 | 0 | 83 | 0 | NA | NA | False | LOW SAMPLE |
| filter | long_fail_confirmed | 288 | 0 | 83 | 0 | NA | NA | False | LOW SAMPLE |
| feature | rsi | 58 | 58 | 18 | 22 | -0.012661 | 0.0018199 | False | LOW SAMPLE |
| feature | rsi_distance_from_avg | 58 | 58 | 14 | 15 | -0.034137 | -0.0058918 | True | LOW SAMPLE |
| feature | htf_adx | 59 | 58 | 16 | 6 | -0.0038363 | -0.01357 | True | LOW SAMPLE |
| feature | adx_margin | 59 | 58 | 16 | 6 | -0.0038363 | -0.01357 | True | LOW SAMPLE |
| feature | ema_spread_pct | 59 | 56 | 20 | 19 | 0.01903 | 0.0017437 | True | LOW SAMPLE |
| feature | atr_pct | 58 | 57 | 7 | 19 | 0.015874 | -0.037856 | False | LOW SAMPLE |
| feature | candle_range_atr | 58 | 58 | 28 | 6 | -0.0065765 | 0.054061 | False | LOW SAMPLE |
| feature | volume_ratio | 58 | 58 | 32 | 8 | 0.014253 | -0.0027156 | False | LOW SAMPLE |
| feature | distance_to_breakout_atr | 58 | 58 | 19 | 9 | 0.020279 | -0.0013935 | False | LOW SAMPLE |
| feature | bb_width | 58 | 57 | 15 | 19 | 0.0027982 | -0.025598 | False | LOW SAMPLE |
| feature | distance_to_squeeze_pct | 57 | 57 | 15 | 12 | -0.01794 | 0.013821 | False | LOW SAMPLE |
| feature | distance_to_upper_band_atr | 58 | 57 | 21 | 10 | 0.0021073 | -0.0024149 | False | LOW SAMPLE |
| feature | bars_since_rsi_up | 118 | 50 | 35 | 18 | 0.019344 | 0.013949 | True | LOW SAMPLE |
| feature | bars_since_oversold | 54 | 52 | 11 | 12 | 0.0026719 | -0.0052577 | False | LOW SAMPLE |
| feature | bars_since_squeeze | 55 | 53 | 11 | 23 | -0.0061126 | 0.018784 | False | LOW SAMPLE |

See discovery/ and holdout/ CSVs for all five horizons, funnel, near misses, ablations, bins, feature distributions, false-positive enrichment, false-negative margins, and per-hypothesis year/symbol results.
