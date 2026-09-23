"""Descriptive exit research statistics; never alters signals or executions.

Returns and deltas are fractions, rates are fractions, and delta means B - A.
Only finite, closed outcomes in BOTH arms are comparable. A one-sided fill
remains in arm performance but never enters paired performance.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.strategy_evaluation import _metrics

EPS = 1e-12


def trimmed_mean(values, fraction=0.10):
    x = np.sort(np.asarray(pd.Series(values).dropna(), dtype=float))
    k = int(len(x) * fraction)
    return float(np.mean(x[k:len(x)-k])) if len(x) else np.nan


def without_top(values, count):
    x = np.sort(np.asarray(pd.Series(values).dropna(), dtype=float))
    return float(x[:-count].mean()) if len(x) > count else np.nan


def comparable(frame):
    return frame.loc[(frame.pair_status == "MATCHED_SIGNAL")
                     & np.isfinite(frame.return_a) & np.isfinite(frame.return_b)].copy()


def arm_metrics(frame, arm):
    values = frame[f"return_{arm}"].where(frame[f"resolution_{arm}"] == "FILLED").dropna()
    row = _metrics(values)
    row["trades"] = row.pop("number_of_trades")
    row["fills"] = int(frame[f"resolution_{arm}"].str.startswith("FILLED", na=False).sum())
    row["censored"] = int((frame[f"resolution_{arm}"] == "FILLED_BUT_CENSORED_AT_END").sum())
    valid = frame[f"resolution_{arm}"] == "FILLED"
    risk = frame.loc[valid, f"realized_R_{arm}"].replace([np.inf, -np.inf], np.nan).dropna()
    row.update(mean_R=float(risk.mean()), median_R=float(risk.median()), valid_R=len(risk),
               average_bars_held=float(frame.loc[valid, f"bars_held_{arm}"].astype(float).mean()),
               trimmed_mean_return=trimmed_mean(values))
    for n in (1, 3, 5):
        row[f"mean_without_top_{n}"] = without_top(values, n)
    return row


def summarize(frame):
    p = comparable(frame)
    delta = p.return_b - p.return_a
    dr = (p.realized_R_b - p.realized_R_a).replace([np.inf, -np.inf], np.nan).dropna()
    a_wins, b_wins = int((delta < -EPS).sum()), int((delta > EPS).sum())
    row = dict(total_signals=len(frame), comparable_pairs=len(p),
               fill_status_changes=int((frame.resolution_a != frame.resolution_b).sum()),
               one_sided_fills=int(frame.pair_status.isin(["A_ONLY_FILL", "B_ONLY_FILL"]).sum()),
               a_only_fills=int((frame.pair_status == "A_ONLY_FILL").sum()),
               b_only_fills=int((frame.pair_status == "B_ONLY_FILL").sum()),
               a_wins=a_wins, b_wins=b_wins, ties=len(p)-a_wins-b_wins,
               b_win_rate_excluding_ties=b_wins/(a_wins+b_wins) if a_wins+b_wins else np.nan,
               a_win_rate_excluding_ties=a_wins/(a_wins+b_wins) if a_wins+b_wins else np.nan,
               mean_paired_delta=float(delta.mean()), median_paired_delta=float(delta.median()),
               trimmed_mean_paired_delta=trimmed_mean(delta),
               mean_paired_delta_R=float(dr.mean()), median_paired_delta_R=float(dr.median()),
               comparable_R_pairs=len(dr), symbols_with_pairs=p.symbol.nunique(),
               years_with_pairs=pd.to_datetime(p.signal_time).dt.year.nunique())
    for arm in ("a", "b"):
        row.update({f"{key}_{arm}": value for key, value in arm_metrics(frame, arm).items()})
    total = float(delta.sum())
    positive_sum = float(delta.clip(lower=0).sum())
    for n in (1, 3, 5):
        row[f"paired_mean_without_top_{n}"] = without_top(delta, n)
        row[f"paired_mean_without_bottom_{n}"] = -without_top(-delta, n)
        top_sum = float(delta.nlargest(n).sum())
        row[f"top_{n}_delta_share_of_net"] = top_sum/total if abs(total) > EPS else np.nan
        row[f"top_{n}_delta_share_of_positive"] = float(delta.clip(lower=0).nlargest(n).sum())/positive_sum if positive_sum > EPS else np.nan
    yearly = delta.groupby(pd.to_datetime(p.signal_time).dt.year).sum()
    row["largest_year_share_of_net"] = float(yearly.max()/total) if total > EPS else np.nan
    oriented = yearly if total >= 0 else -yearly
    positive_years = oriented.clip(lower=0)
    row["largest_year_share_of_positive_advantage"] = (float(positive_years.max()/positive_years.sum())
                                                       if positive_years.sum() > EPS else np.nan)
    row["year_concentrated"] = bool(row["largest_year_share_of_positive_advantage"] > .6)
    row["mean_trim_disagree"] = bool(row["mean_paired_delta"] * row["trimmed_mean_paired_delta"] < -EPS)
    row["top5_reverse_advantage"] = bool(
        (row["mean_paired_delta"] > EPS and row["paired_mean_without_top_5"] <= 0)
        or (row["mean_paired_delta"] < -EPS and row["paired_mean_without_bottom_5"] >= 0))
    row["majority_mean_disagree"] = bool((b_wins-a_wins)*row["mean_paired_delta"] < -EPS)
    row["label"] = ("LOW SAMPLE" if len(p) < 100 else "TAIL-SENSITIVE"
                    if row["mean_trim_disagree"] or row["top5_reverse_advantage"]
                    or row["majority_mean_disagree"] or row["year_concentrated"] else "MIXED")
    return row


def grouped_summary(frame, group):
    source = frame.copy()
    if group == "year":
        source["year"] = pd.to_datetime(source.signal_time).dt.year
    rows = [{group: key, **summarize(part)} for key, part in source.groupby(group, sort=True)]
    return pd.DataFrame(rows, columns=[group, *summarize(frame.iloc[:0]).keys()])


def supported_winner(frame):
    """Conservative preregistered descriptive screen, NOT significance/OOS.

    Require >=100 pairs, >=20 non-ties, >=10 symbols, >=3 years with >=10
    pairs; mean, symmetric trim, winner-tail deletion and paired majority agree;
    >=60% informative years/symbols agree; >=2 of WR/median/PF do not worsen;
    no year contributes >60% of positive directional gain; <=10% one-sided fills.
    """
    s = summarize(frame)
    if s["comparable_pairs"] < 100 or s["a_wins"] + s["b_wins"] < 20 or s["symbols_with_pairs"] < 10:
        return None
    sign = 1 if s["mean_paired_delta"] > EPS else -1
    winner, loser = ("b", "a") if sign == 1 else ("a", "b")
    p = comparable(frame)
    d = sign * (p.return_b - p.return_a)
    if not (d.mean() > EPS and trimmed_mean(d) > EPS and without_top(d, 5) > EPS
            and (d > EPS).sum() > (d < -EPS).sum()):
        return None
    eligible = p.assign(year=pd.to_datetime(p.signal_time).dt.year, gain=d)
    years = eligible.groupby("year").gain.agg(["count", "sum", "mean"])
    years = years[years["count"] >= 10]
    symbols = eligible.groupby("symbol").gain.mean()
    symbols = symbols[symbols.abs() > EPS]
    positive_years = eligible.groupby("year").gain.sum().clip(lower=0)
    if (len(years) < 3 or (years["mean"] > EPS).mean() < .6 or len(symbols) < 10
            or (symbols > EPS).mean() < .6 or positive_years.sum() <= EPS
            or positive_years.max()/positive_years.sum() > .6):
        return None
    if sum(s[f"{metric}_{winner}"] >= s[f"{metric}_{loser}"] for metric in
           ("win_rate", "median_return", "profit_factor")) < 2:
        return None
    if s["one_sided_fills"] / max(1, s["total_signals"]) > .1:
        return None
    return winner.upper()


def comparison_tables(frame):
    summary = summarize(frame)
    winner = supported_winner(frame)
    if winner:
        summary["label"] = "ROBUST"
    summary["supported_winner"] = winner or "INCONCLUSIVE"
    p = comparable(frame)
    reasons = []
    for arm in ("a", "b"):
        filled = frame[frame[f"resolution_{arm}"].str.startswith("FILLED", na=False)]
        for reason, count in filled[f"exit_reason_{arm}"].value_counts().items():
            reasons.append(dict(arm=arm.upper(), exit_reason=reason, count=count))
    return {
        "robustness_summary": pd.DataFrame([summary]),
        "symbol_summary": grouped_summary(frame, "symbol"),
        "year_summary": grouped_summary(frame, "year"),
        "exit_reason_distribution": pd.DataFrame(reasons, columns=["arm", "exit_reason", "count"]),
        "largest_positive_deltas": p.nlargest(10, "delta_return"),
        "largest_negative_deltas": p.nsmallest(10, "delta_return"),
    }
