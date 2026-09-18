from __future__ import annotations
import argparse
from pathlib import Path
from .config import load_config
from .ingest import make_sample_panel, fetch_live_panel
from .pipeline import build_features, build_target
from .model import fit_logistic_walk_forward, persistence_baseline

def main():
    ap = argparse.ArgumentParser(description="Commercial Monitor")
    ap.add_argument("--sample",action="store_true")
    ap.add_argument("--live",action="store_true")
    ap.add_argument("--config",default="config.yaml")
    ap.add_argument("--out",default="data")
    args = ap.parse_args()
    cfg = load_config(args.config)
    if args.live:
        panel = fetch_live_panel(cfg)
    else:
        fields = list(cfg["taxonomy"]["domains"])
        years = range(cfg["project"]["start_year"],cfg["project"]["end_year"]+1)
        panel = make_sample_panel(fields,years)
    frame,_ = build_features(panel,cfg["project"]["horizon_years"])
    frame = build_target(frame,"csi",cfg["project"]["horizon_years"])
    out = Path(args.out); out.mkdir(parents=True,exist_ok=True)
    frame.to_csv(out/"panel.csv",index=False)
    fit_logistic_walk_forward(frame).to_csv(out/"walk_forward.csv",index=False)
    persistence_baseline(frame).to_csv(out/"baseline.csv",index=False)
    print(f"wrote {len(frame)} rows to {out}")

if __name__ == "__main__":
    main()
