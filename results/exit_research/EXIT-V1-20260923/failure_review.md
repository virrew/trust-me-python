# Initial snapshot rejected before research

The existing Yahoo pipeline (`auto_adjust=False`) returned a missing close on
AAPL 2026-09-22; its preceding 1,253 daily rows were finite. The first 12
symbols failed OHLCV validation (two attempts each). The batch was interrupted
before any backtest or registry write. No OHLCV was imputed or used.

The replacement session EXIT-V1-20260923-CLOSED fixes a common exclusive
cutoff of 2026-09-22 for every symbol, chosen before any backtests. It preserves
all returned bars inside that window and rejects any remaining invalid data.
The original failure manifest and errors are retained in
`results/research_data/EXIT-V1-20260923/manifest.json`.
