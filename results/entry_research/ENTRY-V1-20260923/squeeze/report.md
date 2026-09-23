# Pure Squeeze Entry Research V1

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
| discovery | 2244 | 236 | 228 | 0.9661 | 47 | 5 |
| holdout | 658 | 55 | 54 | 0.98182 | 25 | 2 |

Existing module event conversion (includes overlap; conversion is to module activation, not necessarily a final signal; rate in percent):

| partition | opportunity_events | eligible_events | converted_events | conversion_rate | censored_events |
| --- | --- | --- | --- | --- | --- |
| discovery | 1397 | 1377 | 175 | 12.564 | 18 |
| holdout | 425 | 412 | 46 | 11.165 | 13 |

Approved pure future outcomes (fractions; sample counts exclude incomplete horizons):

| partition | horizon | complete | censored | mean | median | positive_rate | mean_mfe | mean_mae |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| discovery | 1 | 228 | 0 | -0.00053934 | -0.00053996 | 0.4693 | 0.01349 | -0.012782 |
| discovery | 3 | 228 | 0 | 0.00063313 | 0.0020427 | 0.52193 | 0.027 | -0.025171 |
| discovery | 5 | 225 | 3 | 0.0016633 | 0.0040323 | 0.55111 | 0.033855 | -0.032502 |
| discovery | 10 | 225 | 3 | 0.0039105 | 0.0022932 | 0.51111 | 0.050637 | -0.047133 |
| discovery | 20 | 225 | 3 | 0.01817 | 0.010749 | 0.56 | 0.086099 | -0.068221 |
| holdout | 1 | 54 | 0 | -0.0051691 | -0.0020575 | 0.44444 | 0.0097659 | -0.020049 |
| holdout | 3 | 54 | 0 | -0.0019862 | 0.00078196 | 0.5 | 0.025386 | -0.033064 |
| holdout | 5 | 54 | 0 | -0.0080092 | -0.012895 | 0.37037 | 0.036421 | -0.043991 |
| holdout | 10 | 52 | 2 | -0.012395 | -0.0013354 | 0.48077 | 0.043184 | -0.061802 |
| holdout | 20 | 49 | 5 | -0.0019034 | -0.0055072 | 0.42857 | 0.072115 | -0.082093 |

Discovery filters; B is the strictly isolated single blocker and A the approved pure cohort:

| filter | research_label | ablation_status | a_complete | b_complete | delta_mean | delta_trimmed | tail_dependent | year_agreement | symbol_agreement |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sq_long_fail_trend | POTENTIALLY TOO STRICT | NOT SAFE FOR ABLATION | 225 | 350 | 0.020139 | 0.015626 | False | 1 | 0.61111 |
| sq_long_fail_recent | MIXED | NOT SAFE FOR ABLATION | 225 | 579 | 0.0051971 | 0.004231 | False | 0.5 | 0.56522 |
| sq_long_fail_release | MIXED | NOT SAFE FOR ABLATION | 225 | 195 | -0.0085333 | -0.0057763 | False | 0.75 | 0.54545 |
| sq_long_fail_price | MIXED | NOT SAFE FOR ABLATION | 225 | 986 | 0.0059964 | 0.0080392 | False | 0.5 | 0.52174 |
| long_fail_direction | LOW SAMPLE | SAFE FINAL GATE | 225 | 0 | NA | NA | False | NA | NA |
| long_fail_volatility | LOW SAMPLE | SAFE FINAL GATE | 225 | 0 | NA | NA | False | NA | NA |
| long_fail_candle | LOW SAMPLE | SAFE FINAL GATE | 225 | 7 | 0.0050885 | 0.0061365 | True | NA | NA |
| long_fail_session | LOW SAMPLE | SAFE FINAL GATE | 225 | 0 | NA | NA | False | NA | NA |
| long_fail_confirmed | LOW SAMPLE | SAFE FINAL GATE | 225 | 0 | NA | NA | False | NA | NA |

Frozen hypotheses and Entry Holdout:

| kind | feature | discovery_a_n | discovery_b_n | a_complete | b_complete | discovery_delta | delta_mean | direction_replicated | final_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| filter | sq_long_fail_trend | 225 | 350 | 52 | 97 | 0.020139 | 0.01465 | True | PARTIAL |
| filter | sq_long_fail_recent | 225 | 579 | 52 | 216 | 0.0051971 | 0.039381 | True | PARTIAL |
| filter | sq_long_fail_release | 225 | 195 | 52 | 39 | -0.0085333 | 0.062223 | False | FAILED HOLDOUT |
| filter | sq_long_fail_price | 225 | 986 | 52 | 270 | 0.0059964 | 0.019436 | True | PARTIAL |
| filter | long_fail_direction | 225 | 0 | 52 | 0 | NA | NA | False | LOW SAMPLE |
| filter | long_fail_volatility | 225 | 0 | 52 | 0 | NA | NA | False | LOW SAMPLE |
| filter | long_fail_candle | 225 | 7 | 52 | 1 | 0.0050885 | -0.010232 | False | LOW SAMPLE |
| filter | long_fail_session | 225 | 0 | 52 | 0 | NA | NA | False | LOW SAMPLE |
| filter | long_fail_confirmed | 225 | 0 | 52 | 0 | NA | NA | False | LOW SAMPLE |
| feature | rsi | 43 | 46 | 20 | 6 | 0.0090441 | -0.020092 | False | LOW SAMPLE |
| feature | rsi_distance_from_avg | 46 | 45 | 9 | 6 | 0.02313 | -0.050049 | False | LOW SAMPLE |
| feature | htf_adx | 46 | 46 | 14 | 6 | -0.030636 | -0.0040499 | True | LOW SAMPLE |
| feature | adx_margin | 46 | 46 | 14 | 6 | -0.030636 | -0.0040499 | True | LOW SAMPLE |
| feature | ema_spread_pct | 46 | 46 | 17 | 17 | -0.032142 | -0.038842 | True | LOW SAMPLE |
| feature | atr_pct | 46 | 46 | 4 | 16 | 0.015171 | -0.017315 | False | LOW SAMPLE |
| feature | candle_range_atr | 46 | 46 | 14 | 7 | 0.039651 | -0.030349 | False | LOW SAMPLE |
| feature | volume_ratio | 45 | 45 | 14 | 6 | 0.0242 | -0.094579 | False | LOW SAMPLE |
| feature | distance_to_breakout_atr | 45 | 45 | 13 | 10 | -0.019368 | -0.011176 | True | LOW SAMPLE |
| feature | bb_width | 46 | 46 | 6 | 10 | 0.010635 | -0.075827 | False | LOW SAMPLE |
| feature | distance_to_squeeze_pct | 45 | 46 | 13 | 4 | -0.014505 | -0.0596 | True | LOW SAMPLE |
| feature | distance_to_upper_band_atr | 45 | 44 | 6 | 12 | -0.02732 | 0.0083055 | False | LOW SAMPLE |
| feature | bars_since_rsi_up | 66 | 40 | 11 | 4 | 0.018867 | 0.04349 | True | LOW SAMPLE |
| feature | bars_since_oversold | 45 | 44 | 8 | 8 | 0.0050597 | -0.044628 | False | LOW SAMPLE |
| feature | bars_since_squeeze | 66 | 0 | 16 | 0 | NA | NA | False | LOW SAMPLE |

See discovery/ and holdout/ CSVs for all five horizons, funnel, near misses, ablations, bins, feature distributions, false-positive enrichment, false-negative margins, and per-hypothesis year/symbol results.
