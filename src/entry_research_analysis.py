"""Finite, observational entry research. No strategy or execution overrides.

All cohort predicates consume existing diagnostics. Module-rule failures are
DESCRIPTIVE: ignoring them would change module identity. Only independent final
filters can be ablated with an unchanged active-module mask. Returns are fractions.
"""
from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pandas as pd

from src.diagnostics_analysis import MODULE_ACTIVATION_COLUMNS
from src.historical_outcomes import (
    DEFAULT_HORIZONS, DEFAULT_TARGET_STOPS, OBSERVATION_SCHEMA,
    calculate_historical_outcomes, _pair_key,
)
from src.strategy_evaluation import MODULE_BITS
from src.exit_research_analysis import trimmed_mean, without_top

MODULES = {"meanrev": "Mean Reversion", "pullback": "Pullback",
           "breakout": "Breakout", "squeeze": "Squeeze"}
PREFIXES = {"meanrev": "mr", "pullback": "pb", "breakout": "bo", "squeeze": "sq"}
KEYS = ["observation_id", "symbol", "timestamp", "direction"]
# Fixed, scale-aware descriptive panel; no feature/threshold search.
NUMERIC_FEATURES = (
    "rsi", "rsi_distance_from_avg", "htf_adx", "adx_margin", "ema_spread_pct",
    "atr_pct", "candle_range_atr", "volume_ratio", "distance_to_breakout_atr",
    "bb_width", "distance_to_squeeze_pct", "distance_to_upper_band_atr",
    "bars_since_rsi_up", "bars_since_oversold", "bars_since_squeeze",
)
FINAL_FILTERS = ("direction", "score", "volatility", "candle", "session", "confirmed")
MIN_SAMPLE = 30
MIN_GROUP = 5


def source_columns(root):
    """Inventory literal diagnostic assignments, including exact source expressions.

    This is provenance, not code execution or extraction of strategy predicates.
    An unknown input column fails closed at the feature boundary.
    """
    found = {}
    for file in ("src/diagnostics_context.py", "src/diagnostics_signals.py"):
        source = (Path(root) / file).read_text()
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if (isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name)
                            and target.value.id == "result" and isinstance(target.slice, ast.Constant)
                            and isinstance(target.slice.value, str)):
                        found[target.slice.value] = (f"{file}:{node.lineno}",
                                                    ast.get_source_segment(source, node.value))
    return found


def feature_manifest(diagnostics, root):
    provenance = source_columns(root)
    unknown = set(diagnostics) - set(provenance)
    if unknown:
        raise ValueError(f"Unreviewed feature columns: {sorted(unknown)}")
    hard = set("allow_long allow_short long_score short_score min_confluence volatility_ok "
               "not_overextended session_ok is_confirmed uptrend downtrend htf_ema_slow "
               "rsi_up_recent rsi_down_recent touched_ema_long reclaimed_long touched_ema_short "
               "reclaimed_short breakout_level breakdown_level volume_strong squeeze_recent "
               "in_squeeze bb_upper bb_lower was_oversold_recently was_overbought_recently "
               "rsi_cross_up rsi_cross_down open close".split())
    hard.update("rsi rsi_avg htf_adx adx_min adx_ok htf_ema_fast atr atr_pct min_atr_pct "
                "candle_range max_candle_atr volume average_volume volume_length use_volume_filter "
                "bars_since_rsi_up bars_since_rsi_down bars_since_oversold bars_since_overbought "
                "confluence_window bb_width bb_width_avg bb_basis bb_dev bb_length bb_mult "
                "bars_since_squeeze squeeze_window breakout_lookback is_swing in_entry_session high low".split())
    rows = []
    for name in diagnostics:
        location, expression = provenance[name]
        modules = [m for m, p in PREFIXES.items() if name.startswith(p + "_")]
        rows.append(dict(name=name, meaning=name.replace("_", " "), source_column=name,
                         source_function=location, source_expression=expression,
                         dtype=str(diagnostics[name].dtype), module_applicability=",".join(modules) or "all/context",
                         available_at="closed input bar close", safe_decision_time_feature=True,
                         currently_used_as_hard_filter=name in hard,
                         diagnostic_only=name not in hard, numeric_shape_panel=name in NUMERIC_FEATURES,
                         note="Hard-filter flag includes upstream gate inputs. htf_* uses Daily input; NaN retained; no event-end metadata"))
    return pd.DataFrame(rows)


def decision_features(diagnostics, symbol, root):
    feature_manifest(diagnostics, root)  # fail closed, never accept joined labels
    result = diagnostics.rename_axis("timestamp").reset_index().copy()
    result.insert(0, "symbol", symbol)
    result.insert(0, "observation_id", [f"{symbol}|{t.isoformat()}|Long" for t in diagnostics.index])
    result.insert(3, "direction", "Long")
    result.insert(4, "available_at", "bar close")
    return result


def requirements(frame, module):
    prefix = PREFIXES[module] + "_long_fail_"
    cols = [c for c in frame if c.startswith(prefix) and c != prefix + "mask"]
    if not cols:
        raise ValueError("Missing module diagnostics")
    return cols


def cohorts(frame, module):
    """Classify bars; do not count the derived score failure twice.

    The strict sole blocker requires every other module requirement AND every
    independent final requirement. Module near misses with mask=0 are never
    called Pure signals. Other active modules are excluded from this envelope.
    """
    bit = MODULE_BITS[MODULES[module]]
    cols = requirements(frame, module)
    module_fail = frame[cols].astype(bool)
    final_cols = [f"long_fail_{f}" for f in FINAL_FILTERS if f != "score"]
    failures = pd.concat([module_fail, frame[final_cols].astype(bool)], axis=1)
    active = frame[MODULE_ACTIVATION_COLUMNS[MODULES[module]] + "_long"].astype(bool)
    if not active.equals(~module_fail.any(axis=1)):
        raise ValueError("Module failure diagnostics disagree with core activation")
    if not (frame.min_confluence == 1).all():
        raise ValueError("Entry V1 requires current min_confluence=1")
    expected_mask = sum(frame[p + "_long"].astype(int) * MODULE_BITS[m]
                        for m, p in MODULE_ACTIVATION_COLUMNS.items())
    if not (expected_mask == frame.long_active_module_mask).all():
        raise ValueError("Module mask disagrees with core")
    pure = frame.long_active_module_mask == bit
    isolated = (frame.long_active_module_mask.astype(int) & ~bit) == 0
    expected_signal = ~frame[[f"long_fail_{f}" for f in FINAL_FILTERS]].any(axis=1)
    if not expected_signal.equals(frame.long_signal.astype(bool)):
        raise ValueError("Final diagnostics disagree with core signal")
    count = failures.sum(axis=1)
    result = pd.DataFrame(index=frame.index)
    result["pure_active"] = pure
    result["approved"] = pure & frame.long_signal
    result["module_opportunity_bar"] = isolated & (module_fail.sum(axis=1) == 1)
    result["candidate_envelope"] = isolated & (module_fail.sum(axis=1) <= 1)
    result["single_blocker"] = isolated & (count == 1)
    result["multi_blocker"] = isolated & (count > 1)
    result["failure_count"] = count
    result["sole_blocker"] = ""
    for c in failures:
        result.loc[result.single_blocker & failures[c], "sole_blocker"] = c
    return result, failures


def ablation(frame, module, filter_column):
    masks, failures = cohorts(frame, module)
    if filter_column not in failures or not filter_column.startswith("long_fail_"):
        raise ValueError("NOT SAFE FOR ABLATION: module identity or derived score")
    added = masks.pure_active & failures[filter_column] & ~failures.drop(columns=filter_column).any(axis=1)
    return masks.approved | added, added


def future_labels(diagnostics, features):
    """Use the existing engine once per anchor, with no event hindsight metadata."""
    rows = []
    for t in features.timestamp:
        row = {c: pd.NA for c in OBSERVATION_SCHEMA}
        row.update(sample_type="Entry Research Bar", direction="Long", module="Unexpanded",
                   anchor_time=t, anchor_price=float(diagnostics.at[t, "close"]),
                   event_start=pd.NaT, event_end=pd.NaT, available_at="anchor bar close")
        rows.append(row)
    observations = pd.DataFrame(rows, columns=OBSERVATION_SCHEMA)
    result = calculate_historical_outcomes(diagnostics, observations)
    labels = features[KEYS].reset_index(drop=True).copy()
    for col in result:
        if col not in OBSERVATION_SCHEMA:
            labels[col] = result[col]
    # Actual bar labels, not an invented intraday timestamp.
    locations = diagnostics.index.get_indexer(features.timestamp)
    for horizon in DEFAULT_HORIZONS:
        labels[f"label_end_{horizon}"] = pd.Series([
            diagnostics.index[p + horizon] if p + horizon < len(diagnostics) else pd.NaT
            for p in locations], dtype=diagnostics.index.dtype)
    return labels


def joined(features, labels):
    if not features.observation_id.is_unique or not labels.observation_id.is_unique:
        raise ValueError("Observation keys must be unique")
    return features.merge(labels, on=KEYS, how="inner", validate="one_to_one")


def metrics(frame, horizon=10):
    values = frame[f"forward_return_{horizon}"].replace([np.inf, -np.inf], np.nan).dropna()
    n = len(values)
    valid = frame.loc[values.index]
    result = dict(observations=len(frame), complete=n, censored=len(frame)-n,
                  symbols=valid.symbol.nunique(), years=pd.to_datetime(valid.timestamp).dt.year.nunique(),
                  mean=float(values.mean()), median=float(values.median()),
                  q10=float(values.quantile(.1)), q90=float(values.quantile(.9)),
                  positive=int((values > 0).sum()), negative=int((values < 0).sum()),
                  positive_rate=float((values > 0).mean()) if n else np.nan,
                  trimmed_mean=trimmed_mean(values),
                  mean_mfe=float(valid[f"mfe_{horizon}"].mean()),
                  median_mfe=float(valid[f"mfe_{horizon}"].median()),
                  mean_mae=float(valid[f"mae_{horizon}"].mean()),
                  median_mae=float(valid[f"mae_{horizon}"].median()))
    for k in (1, 3, 5):
        result[f"mean_without_top_{k}"] = without_top(values, k)
        result[f"mean_without_bottom_{k}"] = -without_top(-values, k)
        result[f"top_{k}_influence"] = result["mean"] - result[f"mean_without_top_{k}"]
    for target, stop in DEFAULT_TARGET_STOPS:
        key = _pair_key(target, stop)
        status = frame[f"{key}_path_status"]
        known = status.isin(["TARGET_BEFORE_STOP", "STOP_BEFORE_TARGET", "NEITHER"])
        result[key + "_resolved"] = int(known.sum())
        for value in ("TARGET_BEFORE_STOP", "STOP_BEFORE_TARGET", "NEITHER", "AMBIGUOUS", "CENSORED"):
            result[key + "_" + value.lower() + "_count"] = int((status == value).sum())
        result[key + "_rate"] = float((status[known] == "TARGET_BEFORE_STOP").mean()) if known.any() else np.nan
    return result


def comparison(a, b, horizon=10):
    """Unpaired B-A descriptive contrast. No causal or significance claim."""
    ma, mb = metrics(a, horizon), metrics(b, horizon)
    out = {f"{arm}_{k}": v for arm, vals in (("a", ma), ("b", mb)) for k, v in vals.items()}
    out.update(delta_mean=mb["mean"]-ma["mean"], delta_median=mb["median"]-ma["median"],
               delta_trimmed=mb["trimmed_mean"]-ma["trimmed_mean"],
               delta_positive_rate=mb["positive_rate"]-ma["positive_rate"])
    sign = np.sign(out["delta_mean"])
    for k in (1, 3, 5):
        # Delete the apparent winner's positive tail, preserving the loser.
        out[f"delta_without_winner_top_{k}"] = (
            mb[f"mean_without_top_{k}"]-ma["mean"] if sign >= 0 else
            mb["mean"]-ma[f"mean_without_top_{k}"])
    for group in ("year", "symbol"):
        aa, bb = a.copy(), b.copy()
        if group == "year":
            aa[group] = pd.to_datetime(aa.timestamp).dt.year
            bb[group] = pd.to_datetime(bb.timestamp).dt.year
        ac = aa.groupby(group)[f"forward_return_{horizon}"].agg(["count", "mean"])
        bc = bb.groupby(group)[f"forward_return_{horizon}"].agg(["count", "mean"])
        both = ac.join(bc, lsuffix="_a", rsuffix="_b", how="inner")
        both = both[(both.count_a >= MIN_GROUP) & (both.count_b >= MIN_GROUP)]
        differences = both.mean_b - both.mean_a
        differences = differences[differences.abs() > 1e-12]
        out[f"informative_{group}s"] = len(differences)
        out[f"{group}_agreement"] = float((differences*sign > 0).mean()) if len(differences) else np.nan
        leave_out = []
        for key in sorted(set(aa[group]) | set(bb[group])):
            va = aa.loc[aa[group] != key, f"forward_return_{horizon}"].mean()
            vb = bb.loc[bb[group] != key, f"forward_return_{horizon}"].mean()
            leave_out.append((vb-va)*sign)
        out[f"one_{group}_dependent"] = bool(leave_out and min(leave_out) <= 0)
    out["tail_dependent"] = bool(sign*out["delta_trimmed"] <= 0 or
                                  sign*out["delta_without_winner_top_5"] <= 0)
    out["low_sample"] = min(ma["complete"], mb["complete"]) < MIN_SAMPLE
    return out


def evidence_label(comp):
    if comp["low_sample"]:
        return "LOW SAMPLE"
    if not np.isfinite(comp["delta_mean"]) or comp["delta_mean"] == 0:
        return "INCONCLUSIVE"
    stable = (comp["informative_years"] >= 2 and comp["informative_symbols"] >= 5
              and comp["year_agreement"] >= .6 and comp["symbol_agreement"] >= .6
              and not comp["tail_dependent"] and not comp["one_year_dependent"]
              and not comp["one_symbol_dependent"]
              and comp["delta_mean"]*comp["delta_median"] > 0)
    if not stable:
        return "MIXED"
    return "SUPPORTED" if comp["delta_mean"] < 0 else "POTENTIALLY TOO STRICT"


def fit_bins(approved):
    # Edges learned from discovery FEATURES only. Duplicates reduce bin count;
    # never force ties into different bins by ranking or use holdout quantiles.
    return {f: sorted(set(float(x) for x in approved[f].dropna().quantile([.2,.4,.6,.8])))
            for f in NUMERIC_FEATURES if approved[f].notna().any()}


def bin_numbers(values, edges):
    return pd.Series(np.searchsorted(edges, values, side="left") + 1, index=values.index).where(values.notna())


def summarize_groups(frame, cohorts_by_name):
    rows = []
    for name, part in cohorts_by_name.items():
        groups = [("all", "all", part)]
        for group in ("year", "symbol", "uptrend"):
            p = part.assign(year=pd.to_datetime(part.timestamp).dt.year) if group == "year" else part
            groups.extend((group, str(key), g) for key, g in p.groupby(group, sort=True))
        for group, key, g in groups:
            for h in DEFAULT_HORIZONS:
                rows.append(dict(cohort=name, group=group, group_value=key, horizon=h, **metrics(g,h)))
    return pd.DataFrame(rows)


def stable_summary_types(table, empty_input):
    """Give empty and populated summary artifacts the same numerical dtypes."""
    metric_types={k: "int64" if isinstance(v,int) else "float64"
                  for k,v in metrics(empty_input).items()}
    ints=set("horizon bin reaching passing failing otherwise_qualified_blocked baseline_overlap "
             "count missing eligible poor input_bars pure_active opportunities signals candidate_envelope "
             "informative_years informative_symbols".split())
    floats=set("blocked_rate extra_signals union_signals median_feature q20 q80 "
               "signal_fraction_of_candidate_envelope final_gate_conversion all_approved_poor_rate enrichment "
               "year_agreement symbol_agreement".split())
    bools={"tail_dependent","one_year_dependent","one_symbol_dependent","low_sample"}
    result=table.copy()
    for col in result:
        bare=col[2:] if col.startswith(("a_","b_")) else col
        dtype=(metric_types.get(bare) or ("int64" if col in ints else
               "float64" if col in floats or col.startswith("delta_") else "bool" if col in bools else "object"))
        result[col]=result[col].astype(dtype)
    return result


def analyze_module(frame, module, *, edges=None):
    masks, failures = cohorts(frame, module)
    baseline = frame.loc[masks.approved]
    edges = fit_bins(baseline) if edges is None else edges
    all_cohorts = {"approved_pure": baseline,
                   "pure_active_before_final": frame.loc[masks.pure_active],
                   "module_opportunity_bars_no_other_active": frame.loc[masks.module_opportunity_bar],
                   "multi_blocker_no_other_active": frame.loc[masks.multi_blocker]}
    funnel, filters, ablations, comparisons = [], [], [], []
    reaching = pd.Series(True, index=frame.index)
    for col in failures:
        passing = reaching & ~failures[col]
        funnel.append(dict(requirement=col, reaching=int(reaching.sum()), passing=int(passing.sum()),
                           failing=int((reaching & failures[col]).sum()),
                           blocked_rate=float(failures.loc[reaching,col].mean()) if reaching.any() else np.nan,
                           otherwise_qualified_blocked=int((masks.single_blocker & failures[col]).sum()),
                           scope="all bars; conjunction display order, not causal priority"))
        reaching = passing
        blocked = frame.loc[masks.single_blocker & failures[col]]
        all_cohorts[col] = blocked
        comp = comparison(baseline, blocked)
        label = evidence_label(comp)
        safe = col.startswith("long_fail_")
        filters.append(dict(filter=col, research_label=label,
                            ablation_status="SAFE FINAL GATE" if safe else "NOT SAFE FOR ABLATION",
                            **comp))
        for h in DEFAULT_HORIZONS:
            comparisons.append(dict(filter=col, horizon=h, **comparison(baseline,blocked,h)))
        if safe:
            union, extra = ablation(frame,module,col)
            ablations.append(dict(filter=col, status="SAFE FINAL GATE", baseline_overlap=int(masks.approved.sum()),
                                  extra_signals=int(extra.sum()), union_signals=int(union.sum()),
                                  **metrics(frame.loc[union])))
        else:
            ablations.append(dict(filter=col, status="NOT SAFE FOR ABLATION", baseline_overlap=len(baseline),
                                  extra_signals=np.nan, union_signals=np.nan, **metrics(frame.iloc[:0])))
    # Explicitly account for score as a derived, unablated gate.
    funnel.append(dict(requirement="long_fail_score", reaching=int(masks.pure_active.sum()),
                       passing=int((masks.pure_active & ~frame.long_fail_score).sum()),
                       failing=int((masks.pure_active & frame.long_fail_score).sum()), blocked_rate=0.0,
                       otherwise_qualified_blocked=0, scope="derived score=1 for pure active; not a second module failure"))
    ablations.append(dict(filter="long_fail_score",status="NOT SAFE FOR ABLATION",
                         baseline_overlap=len(baseline),extra_signals=np.nan,
                         union_signals=np.nan,**metrics(frame.iloc[:0])))
    shape, distributions, poor_rows, bin_groups = [], [], [], []
    for feature in NUMERIC_FEATURES:
        v = baseline[feature].dropna()
        distributions.append(dict(feature=feature,count=len(v),missing=len(baseline)-len(v),
                                  mean=float(v.mean()),median=float(v.median()),q20=float(v.quantile(.2)),
                                  q80=float(v.quantile(.8))))
        if feature not in edges:
            continue
        bins = bin_numbers(baseline[feature], edges[feature])
        for bin_id in range(1, len(edges[feature])+2):
            part = baseline.loc[bins == bin_id]
            for h in DEFAULT_HORIZONS:
                shape.append(dict(feature=feature, bin=bin_id, horizon=h,
                                  median_feature=float(part[feature].median()), **metrics(part,h)))
            for group in ("year", "symbol"):
                source = part.assign(year=pd.to_datetime(part.timestamp).dt.year) if group == "year" else part
                for key, g in source.groupby(group, sort=True):
                    returns = g.forward_return_10.dropna()
                    bin_groups.append(dict(feature=feature,bin=bin_id,group=group,group_value=str(key),
                        observations=len(g),complete=len(returns),median_feature=float(g[feature].median()),
                        mean=float(returns.mean()),median=float(returns.median()),
                        positive_rate=float((returns>0).mean()) if len(returns) else np.nan,
                        mean_mfe=float(g.mfe_10.mean()),mean_mae=float(g.mae_10.mean())))
            views = {
                "negative_return_5": (baseline.forward_return_5 < 0, baseline.complete_5),
                "negative_return_20": (baseline.forward_return_20 < 0, baseline.complete_20),
                "stop_before_target_3_2": (baseline.target_3_stop_2_path_status == "STOP_BEFORE_TARGET",
                    baseline.target_3_stop_2_path_status.isin(["TARGET_BEFORE_STOP","STOP_BEFORE_TARGET","NEITHER"])),
            }
            for view,(poor,eligible) in views.items():
                in_bin = bins == bin_id
                denominator = int((eligible & in_bin).sum())
                overall_rate = float(poor[eligible].mean()) if eligible.any() else np.nan
                rate = float(poor[eligible & in_bin].mean()) if denominator else np.nan
                poor_rows.append(dict(feature=feature,bin=bin_id,outcome_view=view,eligible=denominator,
                                      poor=int((poor & eligible & in_bin).sum()),poor_rate=rate,
                                      all_approved_poor_rate=overall_rate,
                                      enrichment=rate/overall_rate if overall_rate > 0 else np.nan))
    raw_near = frame.loc[masks.single_blocker, KEYS].copy()
    raw_near["sole_blocker"] = masks.loc[masks.single_blocker,"sole_blocker"]
    fn = raw_near.merge(frame.drop(columns=["symbol","timestamp","direction"]), on="observation_id",validate="one_to_one")
    # False negatives use several fixed views, not an optimized barrier.
    fn["positive_5"] = (fn.forward_return_5 > 0).where(fn.complete_5)
    fn["positive_20"] = (fn.forward_return_20 > 0).where(fn.complete_20)
    fn["target_first_3_2"] = fn.target_3_stop_2_target_before_stop
    margin_rows=[]
    for blocker, blocked in fn.groupby("sole_blocker", sort=True):
        for feature, thresholds in edges.items():
            bins=bin_numbers(blocked[feature],thresholds)
            for bin_id in range(1,len(thresholds)+2):
                g=blocked.loc[bins==bin_id]
                values=g.forward_return_10.dropna()
                margin_rows.append(dict(blocker=blocker,feature=feature,bin=bin_id,
                    observations=len(g),complete=len(values),positive=int((values>0).sum()),
                    positive_rate=float((values>0).mean()) if len(values) else np.nan,
                    median_feature=float(g[feature].median()),mean=float(values.mean())))
    empty_shape = ["feature","bin","horizon","median_feature",*metrics(frame.iloc[:0]).keys()]
    tables=dict(baseline_summary=summarize_groups(frame,all_cohorts),
                population=pd.DataFrame([dict(input_bars=len(frame),pure_active=int(masks.pure_active.sum()),
                    opportunities=int(masks.module_opportunity_bar.sum()),signals=len(baseline),
                    candidate_envelope=int(masks.candidate_envelope.sum()),
                    signal_fraction_of_candidate_envelope=len(baseline)/max(1,int(masks.candidate_envelope.sum())),
                    final_gate_conversion=len(baseline)/max(1,int(masks.pure_active.sum())),
                    symbols=baseline.symbol.nunique(),years=pd.to_datetime(baseline.timestamp).dt.year.nunique())]),
                funnel_summary=pd.DataFrame(funnel),filter_summary=pd.DataFrame(filters),
                filter_horizons=pd.DataFrame(comparisons),near_misses=raw_near,
                ablation_summary=pd.DataFrame(ablations),feature_bins=pd.DataFrame(shape,columns=empty_shape),
                feature_distributions=pd.DataFrame(distributions),
                feature_bin_groups=pd.DataFrame(bin_groups,columns=["feature","bin","group","group_value",
                    "observations","complete","median_feature","mean","median","positive_rate","mean_mfe","mean_mae"]),
                false_negative_bins=pd.DataFrame(margin_rows,columns=["blocker","feature","bin","observations",
                    "complete","positive","positive_rate","median_feature","mean"]),
                false_positives=pd.DataFrame(poor_rows,columns=["feature","bin","outcome_view","eligible","poor","poor_rate","all_approved_poor_rate","enrichment"]),
                false_negatives=fn)
    return {name: (table if name in ("near_misses","false_negatives") else
                   stable_summary_types(table,frame.iloc[:0])) for name,table in tables.items()}, edges


def hypothesis_rows(frame,module,tables,edges):
    approved = frame.loc[cohorts(frame,module)[0].approved]
    rows = []
    for r in tables["filter_summary"].to_dict("records"):
        direction = int(np.sign(r["delta_mean"])) if np.isfinite(r["delta_mean"]) else 0
        rows.append(dict(hypothesis_id=f"{module}:filter:{r['filter']}",module=module,kind="filter",feature=r["filter"],
                         observation=r["research_label"],interpretation="Single-blocker minus approved pure mean forward return; observational association",
                         expected_direction=direction,discovery_a_n=r["a_complete"],discovery_b_n=r["b_complete"],
                         discovery_delta=r["delta_mean"],discovery_trimmed_delta=r["delta_trimmed"],
                         action="KEEP CURRENT RULE" if r["research_label"] == "SUPPORTED" else
                         "TEST RELAXATION" if r["research_label"] == "POTENTIALLY TOO STRICT" else "NO ACTION",
                         holdout_test="Same cohorts, 10-bar primary; 1/3/5/20 descriptive; n>=30 each, >=5 shared symbols, >=60% agreement; trim/median/winner top5 agree"))
    for feature, thresholds in edges.items():
        bins = bin_numbers(approved[feature], thresholds)
        a,b = approved.loc[bins == 1],approved.loc[bins == len(thresholds)+1]
        comp = comparison(a,b)
        direction = int(np.sign(comp["delta_mean"])) if np.isfinite(comp["delta_mean"]) else 0
        rows.append(dict(hypothesis_id=f"{module}:feature:{feature}",module=module,kind="feature",feature=feature,
                         observation=evidence_label(comp),interpretation="Fixed discovery highest bin minus lowest bin within approved pure signals",
                         expected_direction=direction,discovery_a_n=comp["a_complete"],discovery_b_n=comp["b_complete"],
                         discovery_delta=comp["delta_mean"],discovery_trimmed_delta=comp["delta_trimmed"],
                         action="TAKE/SKIP FEATURE CANDIDATE" if not comp["low_sample"] else "NO ACTION",
                         holdout_test="Frozen discovery bin edges; highest minus lowest; same 10-bar primary and replication screen as filters"))
    return pd.DataFrame(rows)


def evaluate_hypotheses(frame,hypotheses,edges_by_module):
    rows,group_rows = [],[]
    for hyp in hypotheses.to_dict("records"):
        masks,_ = cohorts(frame,hyp["module"])
        a = frame.loc[masks.approved]
        if hyp["kind"] == "filter":
            b = frame.loc[masks.single_blocker & (masks.sole_blocker == hyp["feature"])]
        else:
            thresholds = edges_by_module[hyp["module"]][hyp["feature"]]
            bins = bin_numbers(a[hyp["feature"]],thresholds)
            a,b = a.loc[bins == 1],a.loc[bins == len(thresholds)+1]
        c = comparison(a,b)
        sign = hyp["expected_direction"]
        replicated = bool(sign*c["delta_mean"] > 0)
        checks = [sign*c[k] > 0 for k in ("delta_mean","delta_trimmed","delta_median","delta_without_winner_top_5")]
        low = c["low_sample"] or min(hyp["discovery_a_n"],hyp["discovery_b_n"]) < MIN_SAMPLE
        stable = (hyp["observation"] in ("SUPPORTED","POTENTIALLY TOO STRICT")
                  and c["informative_symbols"] >= 5 and c["symbol_agreement"] >= .6
                  and not c["one_year_dependent"] and not c["one_symbol_dependent"])
        status = ("LOW SAMPLE" if low else "INCONCLUSIVE" if sign == 0 else
                  "FAILED HOLDOUT" if sign*c["delta_mean"] < 0 else
                  "REPLICATED" if all(checks) and stable else "PARTIAL" if replicated else "INCONCLUSIVE")
        rows.append(dict(**hyp,**c,direction_replicated=replicated,
                         weakened=abs(c["delta_mean"]) < abs(hyp["discovery_delta"]),
                         reversed=sign*c["delta_mean"] < 0,final_status=status))
        for group in ("year","symbol"):
            aa,bb = a.copy(),b.copy()
            if group == "year":
                aa[group]=pd.to_datetime(aa.timestamp).dt.year
                bb[group]=pd.to_datetime(bb.timestamp).dt.year
            for key in sorted(set(aa[group]) | set(bb[group])):
                ma,mb = metrics(aa[aa[group] == key]),metrics(bb[bb[group] == key])
                group_rows.append(dict(hypothesis_id=hyp["hypothesis_id"],group=group,group_value=str(key),
                                       a_n=ma["complete"],b_n=mb["complete"],a_mean=ma["mean"],b_mean=mb["mean"],
                                       delta=mb["mean"]-ma["mean"],expected_direction=sign))
    return pd.DataFrame(rows),pd.DataFrame(group_rows,columns=["hypothesis_id","group","group_value","a_n","b_n","a_mean","b_mean","delta","expected_direction"])
