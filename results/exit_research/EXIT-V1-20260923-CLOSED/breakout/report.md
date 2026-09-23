# Pure Breakout exit research



**INCONCLUSIVE** — No multiplier coherently beats its adjacent grid values and 2.5 baseline under the preregistered robustness screen



Final Long signal AND long_active_module_mask == 2. Other modules excluded before replay; all bars retained.

Snapshot `EXIT-V1-20260923-CLOSED`, SHA256 `b3208fa046c8a09e6067f5dbfa8ffafd11b1d4855662d79b9e42b5cc8d5300d3`; 5y / daily, Swing, Long only.

Snapshot cutoff: strictly before 2026-09-22; 50/50 symbols available. See `../../../research_data/EXIT-V1-20260923-CLOSED/manifest.csv` for each symbol's dates, rows, download time and checksums.

Number of pure signals: 1013.



## Trend test (Dynamic ATR 2.5)

`EXIT-V1-20260923-CLOSED-PURE-BREAKOUT-ATR2.5-DYNAMIC-TRENDON-VS-ATR2.5-DYNAMIC-TRENDOFF`

545 pairs; A/B wins/ties 23/9/513; fill-status changes 2 (2 one-sided fills). Mean delta 0.000314; median 0.000000; 10% trimmed 0.000000; without top 1/3/5 -0.000185/-0.000742/-0.000925. Label: TAIL-SENSITIVE; supported winner: INCONCLUSIVE.

Decision: {'value': True, 'evidence': 'INCONCLUSIVE; historical Trend ON convention'}



## ATR mode test (2.5)

`EXIT-V1-20260923-CLOSED-PURE-BREAKOUT-ATR2.5-DYNAMIC-TRENDON-VS-ATR2.5-LOCKED-TRENDON`

518 pairs; A/B wins/ties 210/216/92; fill-status changes 42 (41 one-sided fills). Mean delta 0.005030; median 0.000000; 10% trimmed 0.000483; without top 1/3/5 0.003110/0.001687/0.000700. Label: MIXED; supported winner: INCONCLUSIVE.

Decision: {'value': False, 'evidence': 'INCONCLUSIVE; historical Dynamic convention'}



## Predefined ATR grid

All return values below are fractions; win rates are fractions. PF is return-based, without costs.

| atr_multiplier | trades | win_rate | mean_return | median_return | profit_factor | mean_R | median_R | average_bars_held | mean_without_top_5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1.5 | 673 | 0.377415 | -0.000502798 | -0.0118767 | 0.971159 | 0.0205503 | -0.306793 | 5.48588 | -0.00256248 |
| 1.75 | 644 | 0.388199 | -0.000203716 | -0.0133214 | 0.989642 | 0.025434 | -0.277637 | 6.79814 | -0.00302226 |
| 2 | 614 | 0.403909 | 0.000395126 | -0.0126673 | 1.01844 | 0.0317858 | -0.272137 | 8.42345 | -0.00251614 |
| 2.25 | 581 | 0.404475 | 0.00196331 | -0.012009 | 1.08572 | 0.0577833 | -0.230356 | 10.0998 | -0.00122475 |
| 2.5 | 547 | 0.407678 | 0.00293213 | -0.0131976 | 1.11359 | 0.0722073 | -0.216751 | 12.0676 | -0.00111135 |
| 3 | 485 | 0.389691 | 0.00641521 | -0.0172813 | 1.21249 | 0.109065 | -0.224269 | 16.8742 | 0.000169815 |



Paired grid evidence (B minus A); full symbol/year/tail/exit tables are in each canonical experiment directory.

### C-grid-1.5-1.75

`EXIT-V1-20260923-CLOSED-PURE-BREAKOUT-ATR1.5-DYNAMIC-TRENDON-VS-ATR1.75-DYNAMIC-TRENDON`

643 pairs; A/B wins/ties 482/71/90; fill-status changes 31 (30 one-sided fills). Mean delta 0.000052; median -0.004953; 10% trimmed -0.004707; without top 1/3/5 -0.000602/-0.001405/-0.001982. Label: TAIL-SENSITIVE; supported winner: INCONCLUSIVE.

### C-grid-1.5-2.5

`EXIT-V1-20260923-CLOSED-PURE-BREAKOUT-ATR1.5-DYNAMIC-TRENDON-VS-ATR2.5-DYNAMIC-TRENDON`

547 pairs; A/B wins/ties 382/134/31; fill-status changes 126 (124 one-sided fills). Mean delta 0.001871; median -0.015577; 10% trimmed -0.009525; without top 1/3/5 0.000691/-0.000838/-0.001849. Label: TAIL-SENSITIVE; supported winner: INCONCLUSIVE.

### C-grid-1.75-2

`EXIT-V1-20260923-CLOSED-PURE-BREAKOUT-ATR1.75-DYNAMIC-TRENDON-VS-ATR2-DYNAMIC-TRENDON`

614 pairs; A/B wins/ties 476/63/75; fill-status changes 30 (30 one-sided fills). Mean delta 0.000189; median -0.004928; 10% trimmed -0.004755; without top 1/3/5 -0.000242/-0.000931/-0.001416. Label: TAIL-SENSITIVE; supported winner: INCONCLUSIVE.

### C-grid-1.75-2.5

`EXIT-V1-20260923-CLOSED-PURE-BREAKOUT-ATR1.75-DYNAMIC-TRENDON-VS-ATR2.5-DYNAMIC-TRENDON`

547 pairs; A/B wins/ties 399/109/39; fill-status changes 98 (96 one-sided fills). Mean delta 0.001160; median -0.013137; 10% trimmed -0.009636; without top 1/3/5 -0.000040/-0.001232/-0.002095. Label: TAIL-SENSITIVE; supported winner: INCONCLUSIVE.

### C-grid-2-2.25

`EXIT-V1-20260923-CLOSED-PURE-BREAKOUT-ATR2-DYNAMIC-TRENDON-VS-ATR2.25-DYNAMIC-TRENDON`

581 pairs; A/B wins/ties 447/64/70; fill-status changes 33 (33 one-sided fills). Mean delta 0.000806; median -0.005036; 10% trimmed -0.004806; without top 1/3/5 0.000498/-0.000070/-0.000621. Label: TAIL-SENSITIVE; supported winner: INCONCLUSIVE.

### C-grid-2-2.5

`EXIT-V1-20260923-CLOSED-PURE-BREAKOUT-ATR2-DYNAMIC-TRENDON-VS-ATR2.5-DYNAMIC-TRENDON`

547 pairs; A/B wins/ties 411/87/49; fill-status changes 68 (66 one-sided fills). Mean delta 0.001897; median -0.009656; 10% trimmed -0.008303; without top 1/3/5 0.000680/-0.000528/-0.001386. Label: TAIL-SENSITIVE; supported winner: INCONCLUSIVE.

### C-grid-2.25-2.5

`EXIT-V1-20260923-CLOSED-PURE-BREAKOUT-ATR2.25-DYNAMIC-TRENDON-VS-ATR2.5-DYNAMIC-TRENDON`

547 pairs; A/B wins/ties 425/45/77; fill-status changes 35 (33 one-sided fills). Mean delta 0.001142; median -0.005179; 10% trimmed -0.005193; without top 1/3/5 0.000220/-0.001007/-0.001889. Label: TAIL-SENSITIVE; supported winner: INCONCLUSIVE.

### C-grid-2.5-3

`EXIT-V1-20260923-CLOSED-PURE-BREAKOUT-ATR2.5-DYNAMIC-TRENDON-VS-ATR3-DYNAMIC-TRENDON`

485 pairs; A/B wins/ties 361/64/60; fill-status changes 62 (61 one-sided fills). Mean delta 0.003419; median -0.009955; 10% trimmed -0.009148; without top 1/3/5 0.001288/-0.000818/-0.002525. Label: TAIL-SENSITIVE; supported winner: INCONCLUSIVE.



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

