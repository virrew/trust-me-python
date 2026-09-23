# Pure Squeeze exit research



**INCONCLUSIVE** — No multiplier coherently beats its adjacent grid values and 2.5 baseline under the preregistered robustness screen



Final Long signal AND long_active_module_mask == 4. Other modules excluded before replay; all bars retained.

Snapshot `EXIT-V1-20260923-CLOSED`, SHA256 `b3208fa046c8a09e6067f5dbfa8ffafd11b1d4855662d79b9e42b5cc8d5300d3`; 5y / daily, Swing, Long only.

Snapshot cutoff: strictly before 2026-09-22; 50/50 symbols available. See `../../../research_data/EXIT-V1-20260923-CLOSED/manifest.csv` for each symbol's dates, rows, download time and checksums.

Number of pure signals: 282.



## Trend test (Dynamic ATR 2.5)

`EXIT-V1-20260923-CLOSED-PURE-SQUEEZE-ATR2.5-DYNAMIC-TRENDON-VS-ATR2.5-DYNAMIC-TRENDOFF`

194 pairs; A/B wins/ties 5/0/189; fill-status changes 0 (0 one-sided fills). Mean delta -0.000644; median 0.000000; 10% trimmed 0.000000; without top 1/3/5 -0.000648/-0.000654/-0.000661. Label: TAIL-SENSITIVE; supported winner: INCONCLUSIVE.

Decision: {'value': True, 'evidence': 'INCONCLUSIVE; historical Trend ON convention'}



## ATR mode test (2.5)

`EXIT-V1-20260923-CLOSED-PURE-SQUEEZE-ATR2.5-DYNAMIC-TRENDON-VS-ATR2.5-LOCKED-TRENDON`

192 pairs; A/B wins/ties 79/85/28; fill-status changes 4 (3 one-sided fills). Mean delta 0.001248; median 0.000000; 10% trimmed 0.000714; without top 1/3/5 0.000579/-0.000563/-0.001267. Label: TAIL-SENSITIVE; supported winner: INCONCLUSIVE.

Decision: {'value': False, 'evidence': 'INCONCLUSIVE; historical Dynamic convention'}



## Predefined ATR grid

All return values below are fractions; win rates are fractions. PF is return-based, without costs.

| atr_multiplier | trades | win_rate | mean_return | median_return | profit_factor | mean_R | median_R | average_bars_held | mean_without_top_5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1.5 | 205 | 0.321951 | -0.00220725 | -0.00910524 | 0.861422 | -0.0770177 | -0.266313 | 5.45366 | -0.00693983 |
| 1.75 | 203 | 0.339901 | 0.000505988 | -0.0121324 | 1.02754 | -0.0555305 | -0.304661 | 6.97044 | -0.00526154 |
| 2 | 201 | 0.323383 | -0.00147699 | -0.0152947 | 0.930027 | -0.0756025 | -0.338582 | 8.18905 | -0.006958 |
| 2.25 | 199 | 0.336683 | -0.00148942 | -0.0173176 | 0.936329 | -0.0611618 | -0.319529 | 9.74372 | -0.00829705 |
| 2.5 | 194 | 0.340206 | 0.0034972 | -0.0192629 | 1.14375 | -0.00323433 | -0.350948 | 11.9536 | -0.00515257 |
| 3 | 186 | 0.38172 | 0.0108318 | -0.0207154 | 1.37778 | 0.116681 | -0.296679 | 18.4946 | 0.00114062 |



Paired grid evidence (B minus A); full symbol/year/tail/exit tables are in each canonical experiment directory.

### C-grid-1.5-1.75

`EXIT-V1-20260923-CLOSED-PURE-SQUEEZE-ATR1.5-DYNAMIC-TRENDON-VS-ATR1.75-DYNAMIC-TRENDON`

203 pairs; A/B wins/ties 150/27/26; fill-status changes 2 (2 one-sided fills). Mean delta 0.002745; median -0.004658; 10% trimmed -0.004129; without top 1/3/5 0.000565/-0.001273/-0.002380. Label: TAIL-SENSITIVE; supported winner: INCONCLUSIVE.

### C-grid-1.5-2.5

`EXIT-V1-20260923-CLOSED-PURE-SQUEEZE-ATR1.5-DYNAMIC-TRENDON-VS-ATR2.5-DYNAMIC-TRENDON`

194 pairs; A/B wins/ties 136/50/8; fill-status changes 11 (10 one-sided fills). Mean delta 0.005402; median -0.016281; 10% trimmed -0.007644; without top 1/3/5 0.003261/-0.000122/-0.002392. Label: TAIL-SENSITIVE; supported winner: INCONCLUSIVE.

### C-grid-1.75-2

`EXIT-V1-20260923-CLOSED-PURE-SQUEEZE-ATR1.75-DYNAMIC-TRENDON-VS-ATR2-DYNAMIC-TRENDON`

201 pairs; A/B wins/ties 158/17/26; fill-status changes 2 (2 one-sided fills). Mean delta -0.002225; median -0.004949; 10% trimmed -0.004742; without top 1/3/5 -0.002659/-0.003444/-0.004171. Label: ROBUST; supported winner: A.

### C-grid-1.75-2.5

`EXIT-V1-20260923-CLOSED-PURE-SQUEEZE-ATR1.75-DYNAMIC-TRENDON-VS-ATR2.5-DYNAMIC-TRENDON`

194 pairs; A/B wins/ties 143/42/9; fill-status changes 9 (8 one-sided fills). Mean delta 0.001186; median -0.013470; 10% trimmed -0.008650; without top 1/3/5 -0.001019/-0.003367/-0.005156. Label: TAIL-SENSITIVE; supported winner: INCONCLUSIVE.

### C-grid-2-2.25

`EXIT-V1-20260923-CLOSED-PURE-SQUEEZE-ATR2-DYNAMIC-TRENDON-VS-ATR2.25-DYNAMIC-TRENDON`

199 pairs; A/B wins/ties 158/16/25; fill-status changes 2 (1 one-sided fills). Mean delta -0.000239; median -0.005088; 10% trimmed -0.004798; without top 1/3/5 -0.001249/-0.002814/-0.003750. Label: TAIL-SENSITIVE; supported winner: INCONCLUSIVE.

### C-grid-2-2.5

`EXIT-V1-20260923-CLOSED-PURE-SQUEEZE-ATR2-DYNAMIC-TRENDON-VS-ATR2.5-DYNAMIC-TRENDON`

194 pairs; A/B wins/ties 147/32/15; fill-status changes 7 (6 one-sided fills). Mean delta 0.003393; median -0.009759; 10% trimmed -0.007397; without top 1/3/5 0.001168/-0.001269/-0.003128. Label: TAIL-SENSITIVE; supported winner: INCONCLUSIVE.

### C-grid-2.25-2.5

`EXIT-V1-20260923-CLOSED-PURE-SQUEEZE-ATR2.25-DYNAMIC-TRENDON-VS-ATR2.5-DYNAMIC-TRENDON`

194 pairs; A/B wins/ties 150/20/24; fill-status changes 5 (5 one-sided fills). Mean delta 0.003599; median -0.004860; 10% trimmed -0.004481; without top 1/3/5 0.001372/-0.000845/-0.002052. Label: TAIL-SENSITIVE; supported winner: INCONCLUSIVE.

### C-grid-2.5-3

`EXIT-V1-20260923-CLOSED-PURE-SQUEEZE-ATR2.5-DYNAMIC-TRENDON-VS-ATR3-DYNAMIC-TRENDON`

186 pairs; A/B wins/ties 125/43/18; fill-status changes 8 (8 one-sided fills). Mean delta 0.006249; median -0.008373; 10% trimmed -0.002765; without top 1/3/5 0.004544/0.002280/0.000512. Label: TAIL-SENSITIVE; supported winner: INCONCLUSIVE.



## Final interaction tests

not applicable: no candidate passed grid screen

Both Trend and ATR-mode tests at the selected multiplier must pass before promotion. No additional multiplier search is permitted.



## Interpretation and limitations

Paired statistics use finite closed trades filled in BOTH arms. One-sided fills and censored outcomes are excluded from paired deltas and retained separately. Aggregate arm metrics can reflect changed trade sequences.

R has a different initial-risk denominator across multipliers; raw return, PF, medians, stability and fill behavior govern the screen. R never chooses the candidate.

LOW SAMPLE, MIXED and TAIL-SENSITIVE are descriptive labels, not significance tests. A failed conservative gate is insufficient support, not proof an exit has no value.

This is in-sample research on a present-day stock universe, with survivorship/selection bias, unequal IPO histories, Yahoo revisions and no transaction costs, sizing or portfolio constraints. No TradingView parity or OOS validation is claimed.

Additional evidence required: a frozen later or walk-forward sample with sufficient independent trades across years/symbols, plus cost-aware evaluation under an explicitly approved execution contract.



## Adaptive hypotheses (not implemented)

Study whether signal-time ATR regime or trend context explains tail-sensitive exits, using separately preregistered hypotheses and untouched validation data. No adaptive rules or entry filters were changed.

