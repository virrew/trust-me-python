"""Frozen descriptive accounting for paper evidence, never execution or selection."""
from __future__ import annotations

import math
import numpy as np
import pandas as pd


COSTS = {
    "primary": {"commission_bps_per_side": 10., "slippage_bps_per_side": 5.},
    "stress": {"commission_bps_per_side": 10., "slippage_bps_per_side": 15.},
}
EVIDENCE = ("TEMPORAL_OOS_LATER_UNSEEN", "PROSPECTIVE_PAPER")
METRIC_DEFINITION = {
    "denominator": "closed finite trades only; exact zeros remain in WR denominator",
    "costs": "return debit = (commission+slippage)/10000 * (1+exit_price/entry_price); "
             "one share equivalent, entry-notional denominator; no fill modification",
    "tail": "mean of worst ceil(0.05*N) closed returns, minimum one if N>0",
    "top_winners": "top 1/3/5 positive returns share of positive sum and expectancy after deletion",
    "excursions": "existing lifecycle exact estimates and lower/upper bounds; exact denominators",
    "sample": "LOW SAMPLE if fewer than 100 closed trades; otherwise DESCRIPTIVE ONLY",
    "groups": "evidence class / arm / cost; separate symbol and exact module mask distributions",
    "promotion": "none; no retuning, automatic acceptance or pooled portfolio inference",
}


def account(trades, costs=COSTS):
    """Costs are retrospective accounting on closed fills, not new fill semantics."""
    t = trades.copy()
    for name, cost in costs.items():
        rate = (cost["commission_bps_per_side"] + cost["slippage_bps_per_side"]) / 10000
        t[f"cost_{name}"] = (rate * (1 + t.exit_price / t.entry_price)).where(t.closed)
        t[f"net_return_{name}"] = t.return_pct - t[f"cost_{name}"]
    return t


def return_metrics(values):
    x = pd.Series(values, dtype=float).dropna()
    winners, losers = x[x > 0], x[x < 0]
    profit, loss = float(winners.sum()), float(-losers.sum())
    row = dict(trade_count=len(x), winners=len(winners), losers=len(losers),
               ties=int(x.eq(0).sum()), non_losses=int(x.ge(0).sum()),
               win_rate=float(x.gt(0).mean()), expectancy=float(x.mean()),
               profit_factor=profit/loss if loss else np.inf if profit else np.nan,
               mean_winner=float(winners.mean()), median_winner=float(winners.median()),
               mean_loser=float(losers.mean()), median_loser=float(losers.median()),
               median_trade=float(x.median()), worst_trade=float(x.min()),
               expected_shortfall_05=float(x.nsmallest(max(1, math.ceil(.05*len(x)))).mean()))
    for n in (1, 3, 5):
        top = winners.nlargest(n)
        row[f"top_{n}_winner_share"] = float(top.sum()/profit) if profit else np.nan
        row[f"expectancy_without_top_{n}"] = float(x.drop(top.index).mean())
    return row


def metrics(trades, cost):
    closed = trades.loc[trades.closed & np.isfinite(trades.return_pct)]
    row = dict(fills=len(trades), open_trades=int((~trades.closed).sum()),
               sample_status="LOW SAMPLE" if len(closed) < 100 else "DESCRIPTIVE ONLY")
    for prefix, column in (("gross", "return_pct"), ("net", f"net_return_{cost}")):
        row.update({f"{prefix}_{k}": v for k, v in return_metrics(closed[column]).items()})
    for col in ("bars_held", "in_trade_mfe", "in_trade_mae", "in_trade_mfe_lower",
                "in_trade_mfe_upper", "in_trade_mae_lower", "in_trade_mae_upper",
                "realized_to_in_trade_mfe"):
        values = closed[col].dropna()
        row.update({f"{col}_count": len(values), f"{col}_mean": float(values.mean()),
                    f"{col}_median": float(values.median())})
    return row


def evaluation(trades, arms, costs=COSTS):
    """Always publish zero-sample arm/class rows; never pool evidence classes."""
    rows, groups = [], []
    for evidence in EVIDENCE:
        for arm in arms:
            t = trades.loc[trades.evidence_class.eq(evidence) & trades.arm.eq(arm)]
            for cost in costs:
                base = dict(evidence_class=evidence, arm=arm, cost=cost)
                rows.append({**base, **metrics(t, cost)})
                for dimension in ("symbol", "active_module_mask"):
                    for value, subset in t.groupby(dimension, sort=True):
                        groups.append({**base, "dimension": dimension, "value": str(value),
                                       **metrics(subset, cost)})
    columns = ["evidence_class", "arm", "cost", *metrics(trades.iloc[:0], next(iter(costs)))]
    return {
        "evaluation": pd.DataFrame(rows, columns=columns),
        "distributions": pd.DataFrame(groups, columns=columns[:3] +
                                     ["dimension", "value"] + columns[3:]),
    }
