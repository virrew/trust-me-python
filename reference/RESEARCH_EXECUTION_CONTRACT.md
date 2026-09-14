# Research Execution Contract — deterministic Swing backtest

This contract defines deliberate Python **research assumptions**. It is not a
claim of TradingView broker-emulator parity. Pine remains authoritative for
Trust Me v2.0 signal, module, direction, ATR parameter, and trend-exit intent;
this document is authoritative only for research execution timing and fills.

## Scope and availability

Only Swing is modeled. Intraday session exits, `timenow`, `immediately=true`,
commissions, slippage, sizing, leverage, and an assumed intrabar OHLC path are
outside scope. A final diagnostic signal on bar *t* becomes available at bar
*t* close (`signal_available_at = signal bar close`). It may use no information
from *t+1*. The market entry occurs at *t+1* open at that open price. A final-bar
signal has no fill.

Only one position may be active, with no pyramiding. Signals while a position
is active are ignored. Both long and short final diagnostic signals are
supported. Simultaneous opposing signals are explicitly treated as conflicting
and skipped; neither direction receives arbitrary priority.

## ATR stop lifecycle

Swing defaults are ATR length 14 (provided by diagnostics), multiplier 2.5,
and `use_locked_atr = false`. Because the entry bar is incomplete at its open,
the initial and locked value is `ATR[t]`, the signal bar's last fully known ATR:

* Long: `initial_stop = entry_open - ATR[t] * multiplier`.
* Short: `initial_stop = entry_open + ATR[t] * multiplier`.

That stop is active throughout the entry bar. In locked mode `ATR[t]` remains
in use. In dynamic mode, each completed bar's ATR may update the stop only for
the **next** bar. At every bar the engine first checks the stop already active
at bar start. Only if the trade survives does it incorporate the completed high
(long) or low (short), then calculate the next stop:

* Long: `extreme=max(previous,current high)` and
  `next_stop=max(previous stop, extreme-ATR*multiplier)`.
* Short: `extreme=min(previous,current low)` and
  `next_stop=min(previous stop, extreme+ATR*multiplier)`.

Thus stops never loosen and a current bar's future high/low cannot protect that
same bar.

## Stop fills and close decisions

For a long, an open at or below the active stop fills at the open; otherwise a
low at or below it fills at the stop. For a short, an open at or above the stop
fills at the open; otherwise a high at or above it fills at the stop. No
invented intrabar path is used.

The Pine-derived Swing trend decision is evaluated on a confirmed close: long
when `close < htf_ema_fast`, short when `close > htf_ema_fast`. The resulting
market exit fills at the next bar's open. If that same open gaps through the
active stop, the price is still that open and the non-arbitrary reason is
`TREND_AND_STOP_AT_OPEN`. Otherwise the reason is `TREND_EXIT`.

## Dataset end and accounting

If no next open exists for a scheduled trend exit, or any position remains open
at dataset end, it is recorded as `closed = false`,
`censored_at_end = true`, with no invented exit price or return. `bars_held`
counts active bars including entry and exit bars. Direction-adjusted
`return_pct` is calculated only for closed trades and excludes costs.

The ledger preserves signal time, entry/exit timing, ATR/stop values, direction,
module mask and score provenance copied from diagnostics. A separate state table
records the stop and extreme before and after each active bar. Empty outputs
retain their schemas, dtypes, and the input index timezone. Summary statistics
use closed trades only; zero returns are neither wins nor losses, and profit
factor is gross positive return divided by absolute gross negative return.
