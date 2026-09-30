| topic | result | source |
| --- | --- | --- |
| Win rates | Verified from checked WR baseline | stage_1_baseline/by_module.csv |
| Giveback losers | Verified from checked WR taxonomy | stage_2_loser_taxonomy/taxonomy.csv |
| Aggressive profit locking / break-even | No prior scenario passed every historical screen; inspect full payoff tradeoff | stage_7_robustness/assessment.csv |
| Winner adverse excursions | Verified bounded stop-touch counts | stage_3_winner_survival/stop_tolerance.csv |
| Entry price blocker | Only fully replicated filter; observational, not realized execution benefit | Entry V1 holdout_results.csv |
| Exit policy | Breakout/Squeeze INCONCLUSIVE; MeanRev PROVISIONAL and low sample | EXIT_POLICY_MATRIX_V1.md |
| Causality | Next-open research semantics differ deliberately from Pine broker emulator | reference/RESEARCH_EXECUTION_CONTRACT.md |

ALL CURRENT HISTORY HAS ALREADY BEEN TOUCHED BY PREVIOUS RESEARCH. No untouched OOS or confirmatory data.