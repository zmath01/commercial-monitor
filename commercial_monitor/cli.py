from __future__ import annotations
import argparse
import json
import hashlib
import gzip
import platform
from importlib.metadata import version
from datetime import datetime, timezone
from pathlib import Path
from .config import load_config
from .ingest import make_sample_panel, fetch_live_observations, aggregate_observations, coverage_report, validate_observations
from .pipeline import build_features, build_target
from .evaluation import evaluate_models
from .provenance import write_manifest
from .storage import atomic_write

def main():
    ap = argparse.ArgumentParser(description="Commercial Monitor")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--sample",action="store_true", help="Synthetic software fixture; not empirical evidence")
    mode.add_argument("--live",action="store_true", help="Fetch and cache live source counts")
    mode.add_argument("--observations", help="Rebuild from a source_observations.csv snapshot without network access")
    ap.add_argument("--config",default="config.yaml")
    ap.add_argument("--out",default="data")
    ap.add_argument("--refresh-cache", action="store_true", help="Fetch a fresh snapshot instead of resuming cached responses")
    args = ap.parse_args()
    cfg = load_config(args.config)
    if args.refresh_cache:
        if not args.live:
            ap.error("--refresh-cache requires --live")
        cfg["outputs"]["cache_dir"] = str(Path(cfg["outputs"]["cache_dir"]) / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f"))
    observations = None
    if args.live:
        observations = fetch_live_observations(cfg)
        panel = aggregate_observations(observations)
    elif args.observations:
        import pandas as pd
        observations = pd.read_csv(args.observations)
        validate_observations(observations, cfg)
        panel = aggregate_observations(observations)
    else:
        fields = list(cfg["taxonomy"]["domains"])
        years = range(cfg["project"]["start_year"],cfg["project"]["end_year"]+1)
        panel = make_sample_panel(fields,years)
    frame,_ = build_features(panel,cfg["project"]["horizon_years"])
    frame = build_target(frame, "repos", cfg["project"]["horizon_years"], cfg["project"].get("target_growth_threshold", 0.20))
    outputs = {"panel": frame, **evaluate_models(frame, min_train_years=cfg["project"].get("min_train_years", 5), seed=cfg["project"]["random_seed"])}
    if observations is not None:
        outputs["source_observations"] = observations
        outputs["coverage"] = coverage_report(observations)
    out = Path(args.out); out.mkdir(parents=True,exist_ok=True)
    if args.sample and (out / "source_observations.csv").exists():
        ap.error("Sample mode cannot overwrite a directory containing live observations")
    for name, data in outputs.items():
        atomic_write(out / f"{name}.csv", data.to_csv(index=False))
    raw_archive = out / "raw_responses.jsonl.gz"
    if args.live:
        wanted = set(observations.response_sha256)
        snapshots = {}
        for path in Path(cfg["outputs"]["cache_dir"]).glob("*.json"):
            snapshot = json.loads(path.read_text())
            digest = hashlib.sha256(json.dumps(snapshot["response"], sort_keys=True).encode()).hexdigest()
            if digest in wanted:
                # Identical responses can still originate from different queries.
                snapshots[path.stem] = snapshot
        payload = "".join(json.dumps(snapshots[key], sort_keys=True) + "\n" for key in sorted(snapshots))
        atomic_write(raw_archive, gzip.compress(payload.encode(), mtime=0))
    metadata = {
        "dataset_kind": "synthetic" if args.sample else "live_snapshot",
        "config_sha256": hashlib.sha256(Path(args.config).read_bytes()).hexdigest(),
        "implementation_sha256": hashlib.sha256(b"".join(path.name.encode() + path.read_bytes() for path in sorted(Path(__file__).parent.glob("*.py")))).hexdigest(),
        "runtime": {"python": platform.python_version(), **{name: version(name) for name in ["numpy", "pandas", "scipy", "scikit-learn", "networkx", "requests", "PyYAML"]}},
        "random_seed": cfg["project"]["random_seed"],
        "n_panel_rows": len(frame), "n_source_observations": 0 if observations is None else len(observations),
        "n_labeled_rows": int(frame.target.notna().sum()),
        "start_year": int(frame.year.min()), "end_year": int(frame.year.max()),
        "target": {"signal": "repos", "horizon_years": cfg["project"]["horizon_years"], "growth_threshold": cfg["project"].get("target_growth_threshold", 0.20)},
        "evaluation": {"min_train_years": cfg["project"].get("min_train_years", 5), "label_availability": "outcome_year < test_year", "null_repeats": 20, "interval_method": "95% circular moving-block bootstrap of annual folds; block length ceil(sqrt(n_folds))"},
        "limitations": ["Query matches overlap and are not independent entity counts", "Historical counts are current API snapshots, not vintage data available in the historical year", "Only five domains; correlated years and no independent commercialization outcome dataset", "Block-bootstrap intervals are descriptive with few annual folds; no significance claim", "OpenAlex free-text query matches are broad activity proxies, not validated domain membership"],
    }
    atomic_write(out / "run.json", json.dumps(metadata, indent=2) + "\n")
    paths = [out / f"{name}.csv" for name in outputs] + [out / "run.json"]
    if observations is not None and raw_archive.exists():
        paths.append(raw_archive)
    write_manifest(paths, out / "manifest.json")
    print(f"wrote {len(frame)} rows to {out}")

if __name__ == "__main__":
    main()
