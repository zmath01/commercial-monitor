from __future__ import annotations
import pandas as pd
from .graphs import build_growth_correlation_graph, graph_features
from .signals import kleinberg_burst, zscore, minmax

def build_features(panel, horizon=2):
    panel = panel.sort_values(["field", "year"]).copy()
    for col in ["papers", "repos", "questions"]:
        panel[f"{col}_growth"] = panel.groupby("field")[col].pct_change()
        panel[f"{col}_z"] = panel.groupby("field")[col].transform(zscore)
        panel[f"{col}_burst"] = panel.groupby("field")[col].transform(lambda s: kleinberg_burst(s).astype(float))
    raw = (0.5*panel["repos_z"].fillna(0) + 0.3*panel["questions_z"].fillna(0) + 0.2*panel["papers_z"].fillna(0))
    panel["csi"] = raw.groupby(panel["field"]).transform(minmax)
    panel["csi_slope"] = panel.groupby("field")["csi"].diff()
    graph = build_growth_correlation_graph(panel)
    rows = []
    for field in panel["field"].unique():
        row = graph_features(graph, field)
        row["field"] = field
        rows.append(row)
    return panel.merge(pd.DataFrame(rows), on="field", how="left"), graph

def build_target(frame, signal="csi", horizon=2):
    wide = frame.pivot(index="year", columns="field", values=signal).sort_index()
    delta = wide.shift(-horizon) - wide
    threshold = delta.stack().median()
    y = (delta > threshold).astype(int).stack().rename("target").reset_index()
    return frame.merge(y, on=["year", "field"], how="left")
