# Entry Research Matrix V1

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

Snapshot: `EXIT-V1-20260923-CLOSED`; hash `b3208fa046c8a09e6067f5dbfa8ffafd11b1d4855662d79b9e42b5cc8d5300d3`. Discovery < 2025-09-21; Entry Holdout >= 2025-09-21, through 2026-09-21. All 50 symbols; original warm-up retained. Rows are daily bar labels, not exact close-clock timestamps.

| module | opportunity_bars | pure_signals | supported_discovery | too_strict_discovery | potentially_loose_exploratory | inconclusive_or_mixed | replicated | failed_holdout | take_skip_candidates | low_sample | holdout_approved |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| meanrev | 1959 | 59 | None | None | LOW SAMPLE / no enrichment | mr_long_fail_trend, mr_long_fail_slow_ema, mr_long_fail_oversold, mr_long_fail_rsi_cross, mr_long_fail_candle, long_fail_direction, long_fail_volatility, long_fail_candle, long_fail_session, long_fail_confirmed | None | 0 | None validated | 25 | 12 |
| pullback | 4218 | 375 | pb_long_fail_trend | None | bb_width bin 5: 31/56 negative20; rsi_distance_from_avg bin 2: 30/57 negative20; candle_range_atr bin 4: 28/55 negative20 | pb_long_fail_slow_ema, pb_long_fail_rsi, pb_long_fail_touch, pb_long_fail_reclaim, long_fail_direction, long_fail_volatility, long_fail_candle, long_fail_session, long_fail_confirmed | None | 3 | None validated | 22 | 84 |
| breakout | 6855 | 1013 | bo_long_fail_volume | bo_long_fail_price | bars_since_rsi_up bin 5: 41/79 negative20; distance_to_upper_band_atr bin 1: 77/155 negative20; candle_range_atr bin 3: 77/155 negative20 | bo_long_fail_trend, bo_long_fail_rsi, long_fail_direction, long_fail_volatility, long_fail_candle, long_fail_session, long_fail_confirmed | bo_long_fail_price | 5 | None validated | 11 | 216 |
| squeeze | 2902 | 282 | None | sq_long_fail_trend | bars_since_oversold bin 4: 29/44 negative20; bars_since_rsi_up bin 5: 24/40 negative20; candle_range_atr bin 2: 26/45 negative20 | sq_long_fail_recent, sq_long_fail_release, sq_long_fail_price, long_fail_direction, long_fail_volatility, long_fail_candle, long_fail_session, long_fail_confirmed | None | 1 | None validated | 20 | 54 |

Holdout poor-approved views (multiple definitions; neither a trade loss nor profitability):

| module | view | eligible | poor | rate |
| --- | --- | --- | --- | --- |
| meanrev | negative_return_5 | 10 | 4 | 0.4 |
| meanrev | negative_return_20 | 10 | 7 | 0.7 |
| meanrev | stop_before_target_3_2 | 10 | 6 | 0.6 |
| pullback | negative_return_5 | 83 | 42 | 0.50602 |
| pullback | negative_return_20 | 83 | 42 | 0.50602 |
| pullback | stop_before_target_3_2 | 81 | 52 | 0.64198 |
| breakout | negative_return_5 | 211 | 110 | 0.52133 |
| breakout | negative_return_20 | 201 | 89 | 0.44279 |
| breakout | stop_before_target_3_2 | 213 | 129 | 0.60563 |
| squeeze | negative_return_5 | 54 | 34 | 0.62963 |
| squeeze | negative_return_20 | 49 | 28 | 0.57143 |
| squeeze | stop_before_target_3_2 | 52 | 28 | 0.53846 |

All replicated hypotheses with sample context:

| module | kind | feature | a_complete | b_complete | discovery_delta | delta_mean | delta_trimmed | symbol_agreement |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| breakout | filter | bo_long_fail_price | 211 | 845 | 0.0075697 | 0.0083721 | 0.0088274 | 0.85714 |

Interpretation and cross-module comparison

- meanrev: Largest adequately sampled favorable blocked cohort: mr_long_fail_oversold, 186/334 positive 10-bar observations, blocked-minus-approved mean 0.6293%. 10/25 holdout contrasts show tail, single-year or single-symbol sensitivity; 0 fully replicated, 0 partial.
- pullback: Largest adequately sampled favorable blocked cohort: pb_long_fail_reclaim, 387/722 positive 10-bar observations, blocked-minus-approved mean 1.1944%. 16/25 holdout contrasts show tail, single-year or single-symbol sensitivity; 0 fully replicated, 0 partial.
- breakout: Largest adequately sampled favorable blocked cohort: bo_long_fail_price, 474/845 positive 10-bar observations, blocked-minus-approved mean 0.8372%. 15/24 holdout contrasts show tail, single-year or single-symbol sensitivity; 1 fully replicated, 7 partial.
- squeeze: Largest adequately sampled favorable blocked cohort: sq_long_fail_price, 135/270 positive 10-bar observations, blocked-minus-approved mean 1.9436%. 9/24 holdout contrasts show tail, single-year or single-symbol sensitivity; 0 fully replicated, 3 partial.

Features with replicated contrasts in multiple modules: None. Module-specific replicated effects are enumerated above; empty tables mean no finding passed the fixed screen. The highest poor-approved rate can differ by outcome view; the table supplies its exact denominator. No module is declared to have validated TAKE/SKIP separation. Positive false-negative counts alone do not justify relaxation. Potentially loose regions are the discovery-bin false-positive enrichments (enrichment >1); they remain exploratory unless the frozen feature contrast replicates. Inconclusive filters and individual tail/year/symbol flags remain in the module reports and CSVs.

Exit context: MeanRev Trend OFF/Dynamic 2.0 PROVISIONAL; Pullback Trend ON/Dynamic 1.5 RESEARCH BASELINE; Breakout/Squeeze INCONCLUSIVE. No secondary trade replay is needed or used for entry conclusions.

Storage: `datasets/features/decision_time_features.csv` and `published/future_outcome_labels.csv` are separate, with observation_id/symbol/timestamp/direction keys. Partition is research metadata in labels only. `datasets/{discovery,holdout}/opportunity_conversion.csv` contains existing retrospective events, including overlap and boundary censoring; it is not a decision feature or a pure signal denominator. A separate `results/entry_research_registry.csv` avoids overloading the exit registry's A/B execution-configuration schema.
