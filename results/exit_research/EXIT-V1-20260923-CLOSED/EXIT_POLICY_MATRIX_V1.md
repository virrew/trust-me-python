# Exit Policy Matrix V1

Behavior change: NO. Existing strategy behavior changed: NO. Research candidates only; no production policy or entry rule changed.

| module | trend_exit | atr_mode | atr_multiplier | research_status | sample_size | major_caveats | adaptive_candidates | OOS_status | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MeanRev | OFF | Dynamic | 2 | PROVISIONAL | 57 historical signals | 57 historical signals; final interaction completion not recorded | Signal-time volatility/trend interaction (unimplemented) | PENDING OOS | 5 existing experiments reused; see existing_experiments.csv |
| Pure Pullback | ON | Dynamic | 1.5 | RESEARCH BASELINE | 380–382 historical signals | 380–382 historical signals; final interactions stored; tail sensitivity remains | Signal-time volatility/trend interaction (unimplemented) | PENDING OOS | 10 existing experiments reused; see existing_experiments.csv |
| Pure Breakout | Unresolved | Unresolved | Unresolved | INCONCLUSIVE | 1013 signals; 485–643 pairs | No multiplier coherently beats its adjacent grid values and 2.5 baseline under the preregistered robustness screen | Signal-time volatility/trend interaction (unimplemented) | PENDING OOS | exit_research/EXIT-V1-20260923-CLOSED/breakout/report.md |
| Pure Squeeze | Unresolved | Unresolved | Unresolved | INCONCLUSIVE | 282 signals; 186–203 pairs | No multiplier coherently beats its adjacent grid values and 2.5 baseline under the preregistered robustness screen | Signal-time volatility/trend interaction (unimplemented) | PENDING OOS | exit_research/EXIT-V1-20260923-CLOSED/squeeze/report.md |

Historical MeanRev/Pullback evidence is reused without rerunning or rewriting artifacts. The old broad Breakout/Squeeze cohorts are context only: other modules affected fills, and no frozen data permits exact equivalence. The new pure-only replay uses one shared frozen Yahoo snapshot. All results are in sample, without costs or portfolio sizing.

Next phase: ENTRY RESEARCH, with exit uncertainty retained explicitly and hypotheses preregistered. Do not treat entry research as validation of these exits. Walk-forward/OOS confirmation remains pending.
