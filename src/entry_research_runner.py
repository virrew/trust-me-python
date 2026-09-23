"""Checkpointed Entry Research V1 on the existing, immutable Exit V1 snapshot.

No network, parameter search, production override, ML or scheduler. All four
modules finish discovery and freeze together before ANY holdout labels exist.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import inspect
import json
import sys
import traceback
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from src.diagnostics_signals import signal_diagnostics
from src.diagnostics_analysis import opportunity_signal_conversion, opportunity_conversion_summary
from src.exit_research_runner import (
    ROOT, UNIVERSE, DEFAULT_SESSION as SNAPSHOT_SESSION, atomic_bytes, digest,
    load_frame, store_frame, save_csv, save_json, validate_ohlcv, now,
)
from src.entry_research_analysis import (
    MODULES, MODULE_BITS, KEYS, NUMERIC_FEATURES, MIN_SAMPLE, MIN_GROUP,
    feature_manifest, decision_features, cohorts, future_labels, joined,
    analyze_module, hypothesis_rows, evaluate_hypotheses, metrics,
)
from src.historical_outcomes import DEFAULT_HORIZONS, DEFAULT_TARGET_STOPS

DEFAULT_SESSION = "ENTRY-V1-20260923"
SOURCES = ("src/entry_research_runner.py", "src/entry_research_analysis.py",
           "src/trust_me_core.py", "src/diagnostics_context.py", "src/diagnostics_signals.py",
           "src/diagnostics_analysis.py", "src/historical_outcomes.py", "src/strategy_evaluation.py",
           "src/exit_research_runner.py", "src/exit_research_analysis.py",
           "reference/trust_me_strategy.pine", "reference/RESEARCH_EXECUTION_CONTRACT.md")
FAILURES = ["symbol","module","stage","error","retry_attempt","excluded"]


def read_json(path):
    return json.loads(Path(path).read_text())


def verify_marker(folder, identity):
    marker = Path(folder)/"completed.json"
    if not marker.exists():
        return False
    record = read_json(marker)
    if record["identity"] != identity:
        raise ValueError(f"Checkpoint identity changed: {folder}")
    for name,sha in record["hashes"].items():
        if not (Path(folder)/name).exists() or digest(Path(folder)/name) != sha:
            raise ValueError(f"Checkpoint checksum mismatch: {folder}/{name}")
    return True


def checkpoint(folder, identity, action):
    folder = Path(folder)
    if verify_marker(folder,identity):
        return "REUSED"
    folder.mkdir(parents=True,exist_ok=True)
    action(folder)
    hashes = {str(f.relative_to(folder)):digest(f) for f in sorted(folder.rglob("*"))
              if f.is_file() and f.name != "completed.json" and not f.name.startswith(".pending-")}
    save_json(folder/"completed.json",dict(identity=identity,hashes=hashes,completed_at=now()))
    return "COMPLETED"


def markdown(frame, columns):
    def fmt(v):
        if isinstance(v,float):
            return "NA" if not np.isfinite(v) else f"{v:.5g}"
        return str(v).replace("|","/").replace("\n"," ")
    return "| " + " | ".join(columns) + " |\n| " + " | ".join("---" for _ in columns) + " |\n" + "\n".join(
        "| " + " | ".join(fmt(r[c]) for c in columns) + " |" for r in frame.to_dict("records")) + "\n"


class EntryRunner:
    def __init__(self, root=ROOT, session=DEFAULT_SESSION):
        import re
        if not re.fullmatch(r"[A-Za-z0-9-]+",session):
            raise ValueError("Invalid session name")
        self.root,self.session = Path(root),session
        self.base = self.root/"results/entry_research"/session
        self.base.mkdir(parents=True,exist_ok=True)
        self.snapshot = self.root/"results/research_data"/SNAPSHOT_SESSION
        snapshot = read_json(self.snapshot/"manifest.json")
        if snapshot["status"] != "completed" or set(snapshot["symbols"]) != set(UNIVERSE):
            raise ValueError("Entry V1 requires the complete canonical frozen 50-symbol snapshot")
        expected = hashlib.sha256(json.dumps(snapshot["symbols"],sort_keys=True).encode()).hexdigest()
        if snapshot["snapshot_id"] != expected:
            raise ValueError("Snapshot manifest integrity compromised")
        for symbol,item in snapshot["symbols"].items():
            if item["status"] != "completed" or item["interval"] != "1d":
                raise ValueError(f"Incomplete/incompatible frozen snapshot: {symbol}")
            for suffix,key in ((".csv","sha256"),(".schema.json","schema_sha256")):
                if digest(self.snapshot/(symbol+suffix)) != item[key]:
                    raise ValueError(f"Snapshot integrity compromised: {symbol}")
        end = min(pd.Timestamp(s["last_timestamp"]) for s in snapshot["symbols"].values())
        start = min(pd.Timestamp(s["first_timestamp"]) for s in snapshot["symbols"].values())
        self.split = end - pd.DateOffset(years=1)
        identity = dict(version=1,snapshot_session=SNAPSHOT_SESSION,snapshot_hash=expected,
                        snapshot_manifest_sha256=digest(self.snapshot/"manifest.json"),
                        source_hashes={f:digest(ROOT/f) for f in SOURCES},
                        environment=dict(python=sys.version,pandas=pd.__version__,numpy=np.__version__),
                        exit_matrix_sha256=digest(self.root/"results/EXIT_POLICY_MATRIX_V1.md"),
                        holdout_start=str(self.split),start=str(start),end=str(end))
        self.identity = hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()
        path = self.base/"research_plan.json"
        if path.exists():
            self.plan = read_json(path)
            if self.plan["identity"] != identity:
                raise ValueError("Source/runtime/snapshot/plan changed; refusing to mix research versions")
        else:
            self.plan = dict(identity=identity,created_at=now(),session=session,
                universe=list(UNIVERSE),mode="Daily Swing Long only",horizons=list(DEFAULT_HORIZONS),
                target_stops=list(DEFAULT_TARGET_STOPS),path_horizon=20,primary_horizon=10,
                feature_panel=list(NUMERIC_FEATURES),bins="discovery-approved quintiles; duplicate edges collapse; missing retained",
                diagnostics_defaults={k:v.default for k,v in inspect.signature(signal_diagnostics).parameters.items()
                                      if v.default is not inspect.Parameter.empty},
                split="Discovery anchors strictly before holdout_start; truncate discovery price paths at boundary; holdout >= start",
                holdout_caveat="Entry holdout only; previous Exit Research already used this history; not untouched strategy OOS",
                observations="Every bar at close; pure active mask equals module bit; no-other-active module near misses separately",
                opportunities="Existing module sole-blocker bars/events; event conversion is retrospective and separate from features",
                ablations="Independent final gates only; score/module predicates NOT SAFE FOR ABLATION",
                hypothesis_family="Every filter sole-blocker contrast and each fixed feature highest-vs-lowest bin; no threshold search",
                descriptive_screen=dict(min_per_arm=MIN_SAMPLE,min_per_year_or_symbol=MIN_GROUP,
                    discovery_min_informative_years=2,min_informative_symbols=5,agreement=.6,
                    require_mean_trim_median_winner_top5=True),
                robustness="Unpaired differences; all horizons, year/symbol tables, leave-one-year/symbol-out and top1/3/5; no significance claims",
                false_positive_views=["negative 5-bar return","negative 20-bar return","stop before target +3%/-2%"],
                failure_policy="Fail closed on any symbol; retain failure log and valid checkpoints; never publish incomplete universe",
                behavior_change="NO",existing_strategy_behavior_changed="NO")
            save_json(path,self.plan)  # BEFORE any feature/outcome computation
            save_json(self.base/"snapshot_reference.json",snapshot)
        self.plan_hash = digest(path)
        self.identity = hashlib.sha256((self.identity+self.plan_hash).encode()).hexdigest()
        self.state_path = self.base/"research_state.json"
        self.state = read_json(self.state_path) if self.state_path.exists() else dict(status="PENDING",stages={})

    def stage(self,name,action):
        folder=self.base/name
        self.state["stages"][name]="RUNNING"
        save_json(self.state_path,self.state)
        try:
            status=checkpoint(folder,self.identity,action)
        except Exception:
            self.state["stages"][name]="FAILED"
            self.state["status"]="FAILED"
            save_json(self.state_path,self.state)
            path=self.base/"failures.csv"
            old=pd.read_csv(path) if path.exists() else pd.DataFrame(columns=FAILURES)
            parts=name.split("/")
            row=dict(symbol=parts[-1] if parts[-1] in UNIVERSE else "ALL",
                     module=parts[0] if parts[0] in MODULES else "ALL",stage=name,
                     error=traceback.format_exc(),retry_attempt=int((old.stage==name).sum())+1,excluded=False)
            save_csv(path,pd.concat([old,pd.DataFrame([row])],ignore_index=True))
            raise
        self.state["stages"][name]=status
        save_json(self.state_path,self.state)
        return status

    def prepare_features(self):
        def one(folder,symbol):
            ohlcv=load_frame(self.snapshot/f"{symbol}.csv").set_index("timestamp")
            validate_ohlcv(ohlcv)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore",pd.errors.PerformanceWarning)
                diag=signal_diagnostics(ohlcv,is_swing=True,allow_long=True,allow_short=False)
            for module in MODULES:
                cohorts(diag,module)
            features=decision_features(diag,symbol,ROOT)
            store_frame(folder/"features.csv",features)
            store_frame(folder/"feature_manifest.csv",feature_manifest(diag,ROOT))
        for symbol in UNIVERSE:
            self.stage(f"cache/features/{symbol}",lambda folder,s=symbol:one(folder,s))
        def aggregate(folder):
            pieces=[load_frame(self.base/f"cache/features/{s}/features.csv") for s in UNIVERSE]
            store_frame(folder/"decision_time_features.csv",pd.concat(pieces,ignore_index=True))
            store_frame(folder/"feature_manifest.csv",load_frame(self.base/f"cache/features/{UNIVERSE[0]}/feature_manifest.csv"))
        self.stage("datasets/features",aggregate)
        print("Features: 50 frozen symbols verified",flush=True)

    def labels(self,partition):
        if partition == "holdout":
            if not verify_marker(self.base/"hypothesis_freeze",self.identity):
                raise ValueError("Holdout is sealed until ALL discovery hypotheses are frozen")
            frozen=read_json(self.base/"hypothesis_freeze/freeze.json")
            if digest(self.base/"candidate_entry_hypotheses.csv") != frozen["hypotheses_sha256"]:
                raise ValueError("Frozen hypothesis checksum mismatch")
        def one(folder,symbol):
            f=load_frame(self.base/f"cache/features/{symbol}/features.csv")
            if partition == "discovery":
                f=f.loc[f.timestamp < self.split].reset_index(drop=True)
            else:
                f=f.loc[f.timestamp >= self.split].reset_index(drop=True)
            d=f.drop(columns=["observation_id","symbol","direction","available_at"]).set_index("timestamp")
            store_frame(folder/"labels.csv",future_labels(d,f))
            events=opportunity_signal_conversion(d,max_followup_bars=5)
            events=events.loc[events.direction == "Long"].copy()
            events.insert(0,"symbol",symbol)
            # Existing events may overlap other modules. Retain and disclose, never use as pure signal stats.
            store_frame(folder/"opportunity_conversion.csv",events)
        for i,symbol in enumerate(UNIVERSE):
            self.stage(f"cache/{partition}/{symbol}",lambda folder,s=symbol:one(folder,s))
            if (i+1)%10==0:
                print(f"{partition}: {i+1}/50 symbols checkpointed",flush=True)
        def aggregate(folder):
            for filename in ("labels.csv","opportunity_conversion.csv"):
                store_frame(folder/filename,pd.concat([load_frame(self.base/f"cache/{partition}/{s}/{filename}")
                                                      for s in UNIVERSE],ignore_index=True))
        self.stage(f"datasets/{partition}",aggregate)
        features=load_frame(self.base/"datasets/features/decision_time_features.csv")
        labels=load_frame(self.base/f"datasets/{partition}/labels.csv")
        return joined(features,labels)

    def discovery(self,frame):
        for module in MODULES:
            def analyze(folder,m=module):
                tables,edges=analyze_module(frame,m)
                for name,table in tables.items():
                    store_frame(folder/f"{name}.csv",table)
                self.event_summary(folder,m,"discovery")
                save_json(folder/"bin_edges.json",edges)
                hypotheses=hypothesis_rows(frame,m,tables,edges)
                store_frame(folder/"hypotheses.csv",hypotheses)
                robust,groups=evaluate_hypotheses(frame,hypotheses,{m:edges})
                store_frame(folder/"hypothesis_robustness.csv",robust)
                store_frame(folder/"hypothesis_groups.csv",groups)
            status=self.stage(f"{module}/discovery",analyze)
            print(f"{module} discovery: {status}",flush=True)
        def freeze(folder):
            hs=pd.concat([load_frame(self.base/f"{m}/discovery/hypotheses.csv") for m in MODULES],ignore_index=True)
            path=self.base/"candidate_entry_hypotheses.csv"
            data=hs.to_csv(index=False).encode()
            if path.exists() and path.read_bytes()!=data:
                raise ValueError("Refusing to overwrite frozen hypotheses")
            if not path.exists():
                atomic_bytes(path,data)
            save_csv(folder/"candidate_entry_hypotheses.csv",hs)
            save_json(folder/"freeze.json",dict(frozen_at=now(),hypotheses_sha256=digest(path),
                discovery_markers={m:digest(self.base/f"{m}/discovery/completed.json") for m in MODULES},
                bin_edge_hashes={m:digest(self.base/f"{m}/discovery/bin_edges.json") for m in MODULES}))
        self.stage("hypothesis_freeze",freeze)
        print("All discovery hypotheses frozen; holdout may now open",flush=True)

    def holdout(self,frame,modules):
        for module in modules:
            def analyze(folder,m=module):
                edges=read_json(self.base/f"{m}/discovery/bin_edges.json")
                tables,_=analyze_module(frame,m,edges=edges)
                for name,table in tables.items():
                    store_frame(folder/f"{name}.csv",table)
                self.event_summary(folder,m,"holdout")
                hypotheses=load_frame(self.base/f"{m}/discovery/hypotheses.csv")
                result,groups=evaluate_hypotheses(frame,hypotheses,{m:edges})
                store_frame(folder/"holdout_results.csv",result)
                store_frame(folder/"hypothesis_groups.csv",groups)
            status=self.stage(f"{module}/holdout",analyze)
            self.stage(f"{module}/published",lambda f,m=module:self.module_report(f,m))
            if digest(self.base/module/"report.md") != digest(self.base/module/"published/report.md"):
                raise ValueError("Published module report checksum mismatch")
            print(f"{module} holdout: {status}",flush=True)

    def event_summary(self,folder,module,partition):
        events=load_frame(self.base/f"datasets/{partition}/opportunity_conversion.csv")
        events=events.loc[events.module==MODULES[module]]
        for by_blocker in (False,True):
            summary=opportunity_conversion_summary(events,by_blocker=by_blocker,min_events=1)
            summary=summary.loc[(summary.direction=="Long") & (summary.module==MODULES[module])].copy()
            summary["scope"]="existing module events including overlap; not pure signals"
            store_frame(folder/("event_conversion_by_blocker.csv" if by_blocker else "event_conversion_summary.csv"),summary)

    def module_report(self,folder,module):
        d=self.base/module/"discovery"
        h=self.base/module/"holdout"
        population=pd.concat([load_frame(p/"population.csv").assign(partition=label)
                              for p,label in ((d,"discovery"),(h,"holdout"))],ignore_index=True)
        results=load_frame(h/"holdout_results.csv")
        filters=load_frame(d/"filter_summary.csv")
        approved=pd.concat([load_frame(p/"baseline_summary.csv").query("cohort == 'approved_pure' and group == 'all'").assign(partition=label)
                            for p,label in ((d,"discovery"),(h,"holdout"))],ignore_index=True)
        text=f"# Pure {MODULES[module]} Entry Research V1\n\n"+COMMON_REPORT+"\n"
        text+=markdown(population,["partition","opportunities","pure_active","signals","final_gate_conversion","symbols","years"])
        events=pd.concat([load_frame(p/"event_conversion_summary.csv").assign(partition=label)
                          for p,label in ((d,"discovery"),(h,"holdout"))],ignore_index=True)
        text+="\nExisting module event conversion (includes overlap; conversion is to module activation, not necessarily a final signal; rate in percent):\n\n"
        text+=markdown(events,["partition","opportunity_events","eligible_events","converted_events","conversion_rate","censored_events"])
        text+="\nApproved pure future outcomes (fractions; sample counts exclude incomplete horizons):\n\n"
        text+=markdown(approved,["partition","horizon","complete","censored","mean","median","positive_rate","mean_mfe","mean_mae"])
        text+="\nDiscovery filters; B is the strictly isolated single blocker and A the approved pure cohort:\n\n"
        text+=markdown(filters,["filter","research_label","ablation_status","a_complete","b_complete","delta_mean","delta_trimmed","tail_dependent","year_agreement","symbol_agreement"])
        text+="\nFrozen hypotheses and Entry Holdout:\n\n"
        text+=markdown(results,["kind","feature","discovery_a_n","discovery_b_n","a_complete","b_complete","discovery_delta","delta_mean","direction_replicated","final_status"])
        text+="\nSee discovery/ and holdout/ CSVs for all five horizons, funnel, near misses, ablations, bins, feature distributions, false-positive enrichment, false-negative margins, and per-hypothesis year/symbol results.\n"
        atomic_bytes(folder/"report.md",text.encode())
        # Canonical convenience report is immutable after publication.
        atomic_bytes(self.base/module/"report.md",text.encode())

    def complete(self,discovery,holdout):
        if not all(verify_marker(self.base/f"{m}/holdout",self.identity) for m in MODULES):
            self.state["status"]="PARTIAL"
            save_json(self.state_path,self.state)
            return
        def outputs(folder):
            rows=[]
            for partition,frame in (("discovery",discovery),("holdout",holdout)):
                overlap=frame.loc[~frame.long_active_module_mask.isin([0,1,2,4,8]) & frame.long_signal]
                for mask,part in overlap.groupby("long_active_module_mask"):
                    for horizon in DEFAULT_HORIZONS:
                        met=metrics(part,horizon)
                        rows.append(dict(partition=partition,module_mask=mask,horizon=horizon,
                            modules=" + ".join(m for m,b in MODULE_BITS.items() if mask & b),
                            status="LOW SAMPLE" if met["complete"]<MIN_SAMPLE else "DESCRIPTIVE ONLY",**met))
            columns=["partition","module_mask","horizon","modules","status",*metrics(holdout.iloc[:0]).keys()]
            store_frame(folder/"overlap_summary.csv",pd.DataFrame(rows,columns=columns))
        self.stage("combined_modules",outputs)
        def publish(folder):
            results=pd.concat([load_frame(self.base/f"{m}/holdout/holdout_results.csv") for m in MODULES],ignore_index=True)
            store_frame(folder/"holdout_results.csv",results)
            labels=pd.concat([load_frame(self.base/f"datasets/{p}/labels.csv").assign(partition=p)
                              for p in ("discovery","holdout")],ignore_index=True)
            store_frame(folder/"future_outcome_labels.csv",labels)
            matrix=self.matrix(results)
            atomic_bytes(folder/"ENTRY_RESEARCH_MATRIX_V1.md",matrix.encode())
            atomic_bytes(self.base/"ENTRY_RESEARCH_MATRIX_V1.md",matrix.encode())
            save_csv(self.base/"holdout_results.csv",results)
            save_csv(self.base/"feature_manifest.csv",load_frame(self.base/"datasets/features/feature_manifest.csv"))
            save_json(folder/"public_hashes.json",{name:digest(self.base/name) for name in
                ["ENTRY_RESEARCH_MATRIX_V1.md","holdout_results.csv","feature_manifest.csv","candidate_entry_hypotheses.csv"]
                +[f"{m}/report.md" for m in MODULES]})
        self.stage("published",publish)
        public=read_json(self.base/"published/public_hashes.json")
        for name,sha in public.items():
            if digest(self.base/name)!=sha:
                raise ValueError(f"Public artifact checksum mismatch: {name}")
        self.register()
        if not (self.base/"failures.csv").exists():
            save_csv(self.base/"failures.csv",pd.DataFrame(columns=FAILURES))
        self.state["status"]="COMPLETED"
        save_json(self.state_path,self.state)

    def matrix(self,results):
        rows=[]
        details=[]
        for module in MODULES:
            population=pd.concat([load_frame(self.base/f"{module}/{p}/population.csv") for p in ("discovery","holdout")])
            r=results.loc[results.module==module]
            filters=load_frame(self.base/f"{module}/discovery/filter_summary.csv")
            def names(label):
                return ", ".join(filters.loc[filters.research_label==label,"filter"]) or "None"
            rep=r[r.final_status=="REPLICATED"]
            poor_discovery=load_frame(self.base/f"{module}/discovery/false_positives.csv")
            loose=poor_discovery[(poor_discovery.outcome_view=="negative_return_20")
                & (poor_discovery.eligible>=MIN_SAMPLE) & (poor_discovery.enrichment>1)]
            loose=loose.sort_values("enrichment",ascending=False).head(3)
            regions="; ".join(f"{x.feature} bin {x.bin}: {x.poor}/{x.eligible} negative20"
                              for x in loose.itertuples()) or "LOW SAMPLE / no enrichment"
            inconclusive=", ".join(filters.loc[~filters.research_label.isin(
                ["SUPPORTED","POTENTIALLY TOO STRICT"]),"filter"]) or "None"
            rows.append(dict(module=module,opportunity_bars=int(population.opportunities.sum()),
                pure_signals=int(population.signals.sum()),supported_discovery=names("SUPPORTED"),
                too_strict_discovery=names("POTENTIALLY TOO STRICT"),
                potentially_loose_exploratory=regions,inconclusive_or_mixed=inconclusive,
                replicated="; ".join(rep.feature) or "None",failed_holdout=int((r.final_status=="FAILED HOLDOUT").sum()),
                take_skip_candidates="; ".join(rep.loc[rep.kind=="feature","feature"]) or "None validated",
                low_sample=int((r.final_status=="LOW SAMPLE").sum()),
                holdout_approved=int(population.iloc[-1].signals)))
            poor=load_frame(self.base/f"{module}/holdout/false_positives.csv")
            for view in poor.outcome_view.unique():
                part=poor[(poor.outcome_view==view) & (poor.feature=="rsi")]
                details.append(dict(module=module,view=view,eligible=int(part.eligible.sum()),poor=int(part.poor.sum()),
                                    rate=float(part.poor.sum()/part.eligible.sum()) if part.eligible.sum() else np.nan))
        text="# Entry Research Matrix V1\n\n"+COMMON_REPORT+"\n"
        text+=f"Snapshot: `{SNAPSHOT_SESSION}`; hash `{self.plan['identity']['snapshot_hash']}`. "
        text+=f"Discovery < {self.split.date()}; Entry Holdout >= {self.split.date()}, through {self.plan['identity']['end'][:10]}. "
        text+="All 50 symbols; original warm-up retained. Rows are daily bar labels, not exact close-clock timestamps.\n\n"
        text+=markdown(pd.DataFrame(rows),list(rows[0]))
        text+="\nHoldout poor-approved views (multiple definitions; neither a trade loss nor profitability):\n\n"
        text+=markdown(pd.DataFrame(details),["module","view","eligible","poor","rate"])
        text+="\nAll replicated hypotheses with sample context:\n\n"
        rep=results[results.final_status=="REPLICATED"]
        text+=markdown(rep,["module","kind","feature","a_complete","b_complete","discovery_delta","delta_mean","delta_trimmed","symbol_agreement"])
        text+="\nInterpretation and cross-module comparison\n\n"
        for module in MODULES:
            rr=results[results.module==module]
            tails=rr[rr.tail_dependent | rr.one_year_dependent | rr.one_symbol_dependent]
            filters=load_frame(self.base/f"{module}/holdout/filter_summary.csv")
            meaningful=filters[filters.b_complete>=MIN_SAMPLE].sort_values("b_positive",ascending=False)
            leader=meaningful.iloc[0] if len(meaningful) else None
            detail=(f"Largest adequately sampled favorable blocked cohort: {leader['filter']}, "
                    f"{int(leader.b_positive)}/{int(leader.b_complete)} positive 10-bar observations, "
                    f"blocked-minus-approved mean {leader.delta_mean:.4%}." if leader is not None else
                    "No blocker cohort reaches the fixed minimum sample.")
            text+=f"- {module}: {detail} {len(tails)}/{len(rr)} holdout contrasts show tail, single-year or single-symbol sensitivity; "
            text+=f"{int((rr.final_status=='REPLICATED').sum())} fully replicated, {int((rr.final_status=='PARTIAL').sum())} partial.\n"
        cross=rep[rep.kind=="feature"].groupby("feature").module.agg(list)
        shared={k:v for k,v in cross.items() if len(v)>1}
        text+="\nFeatures with replicated contrasts in multiple modules: "+(str(shared) if shared else "None")+". "
        text+="Module-specific replicated effects are enumerated above; empty tables mean no finding passed the fixed screen. "
        text+="The highest poor-approved rate can differ by outcome view; the table supplies its exact denominator. "
        text+="No module is declared to have validated TAKE/SKIP separation. Positive false-negative counts alone do not justify relaxation. "
        text+="Potentially loose regions are the discovery-bin false-positive enrichments (enrichment >1); they remain exploratory unless the frozen feature contrast replicates. "
        text+="Inconclusive filters and individual tail/year/symbol flags remain in the module reports and CSVs.\n\n"
        text+="Exit context: MeanRev Trend OFF/Dynamic 2.0 PROVISIONAL; Pullback Trend ON/Dynamic 1.5 RESEARCH BASELINE; "
        text+="Breakout/Squeeze INCONCLUSIVE. No secondary trade replay is needed or used for entry conclusions.\n\n"
        text+="Storage: `datasets/features/decision_time_features.csv` and `published/future_outcome_labels.csv` are separate, with observation_id/symbol/timestamp/direction keys. "
        text+="Partition is research metadata in labels only. `datasets/{discovery,holdout}/opportunity_conversion.csv` contains existing retrospective events, "
        text+="including overlap and boundary censoring; it is not a decision feature or a pure signal denominator. "
        text+="A separate `results/entry_research_registry.csv` avoids overloading the exit registry's A/B execution-configuration schema.\n"
        return text

    def register(self):
        path=self.root/"results/entry_research_registry.csv"
        fields=["session","snapshot_session","snapshot_hash","hypotheses_hash","status","result_path"]
        row=dict(session=self.session,snapshot_session=SNAPSHOT_SESSION,snapshot_hash=self.plan["identity"]["snapshot_hash"],
                 hypotheses_hash=digest(self.base/"candidate_entry_hypotheses.csv"),status="COMPLETED",
                 result_path=str(self.base.relative_to(self.root)))
        old=pd.read_csv(path) if path.exists() else pd.DataFrame(columns=fields)
        match=old[old.session==self.session]
        if len(match):
            if match.iloc[0].to_dict()!=row:
                raise ValueError("Entry registry collision")
            return
        # Preserve historical bytes, including their quoting and ordering.
        import csv,io
        stream=io.StringIO(newline="")
        writer=csv.DictWriter(stream,fieldnames=fields,lineterminator="\n")
        if not path.exists():
            writer.writeheader()
        writer.writerow(row)
        prior=path.read_bytes() if path.exists() else b""
        atomic_bytes(path,prior+(b"\n" if prior and not prior.endswith(b"\n") else b"")+stream.getvalue().encode())

    def run(self,modules):
        self.prepare_features()
        discovery=self.labels("discovery")
        self.discovery(discovery)
        holdout=self.labels("holdout")
        self.holdout(holdout,modules)
        self.complete(discovery,holdout)


COMMON_REPORT="""Behavior change: NO. Existing strategy behavior changed: NO.
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
"""


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    selection=parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--all",action="store_true")
    selection.add_argument("--module",choices=MODULES)
    parser.add_argument("--session",default=DEFAULT_SESSION)
    args=parser.parse_args()
    # One process protects all entry sessions and their registry; OS releases on crash.
    lock=ROOT/"results/.entry-research.lock"
    with lock.open("a") as handle:
        fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        runner=EntryRunner(session=args.session)
        runner.run(list(MODULES) if args.all else [args.module])
        print(f"Entry Research: {runner.state['status']} — {runner.base}",flush=True)


if __name__ == "__main__":
    main()
