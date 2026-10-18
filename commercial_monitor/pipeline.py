from __future__ import annotations
import pandas as pd
import numpy as np
from .graphs import build_growth_correlation_graph, graph_features
from .signals import kleinberg_burst, zscore, minmax

def build_features(panel, horizon=2):
    required = ["field", "year", "papers", "repos", "questions"]
    if panel.empty or panel[required].isna().any().any():
        raise ValueError("A nonempty, fully observed panel is required")
    if panel.duplicated(["field", "year"]).any():
        raise ValueError("Duplicate field-year observations")
    if (panel[["papers", "repos", "questions"]] < 0).any().any():
        raise ValueError("Activity counts must be nonnegative")
    if not np.isfinite(panel[["year", "papers", "repos", "questions"]].to_numpy()).all():
        raise ValueError("Years and counts must be finite")
    if (panel.year % 1 != 0).any():
        raise ValueError("Calendar years must be integers")
    panel = panel.sort_values(["field", "year"]).copy()
    def causal_transform(values, transform):
        # Recompute only the current endpoint. Appending future years cannot
        # revise any previously published feature, including burst states.
        return pd.Series([transform(values.iloc[:i+1]).iloc[-1] for i in range(len(values))], index=values.index)
    for col in ["papers", "repos", "questions"]:
        previous = panel[["field", "year", col]].copy()
        previous["year"] += 1
        previous = previous.rename(columns={col: "previous"})
        lag = panel[["field", "year"]].merge(previous, on=["field", "year"], how="left")["previous"].to_numpy()
        panel[f"{col}_growth"] = panel[col].to_numpy() / np.where(lag > 0, lag, np.nan) - 1
        panel[f"{col}_z"] = panel.groupby("field")[col].transform(lambda s: causal_transform(s, zscore))
        panel[f"{col}_burst"] = panel.groupby("field")[col].transform(lambda s: causal_transform(s, kleinberg_burst).astype(float))
    raw = (0.5*panel["repos_z"].fillna(0) + 0.3*panel["questions_z"].fillna(0) + 0.2*panel["papers_z"].fillna(0))
    panel["csi"] = raw.groupby(panel["field"]).transform(lambda s: causal_transform(s, minmax))
    panel["csi_slope"] = panel.groupby("field")["csi"].diff()
    panel.loc[panel.groupby("field")["year"].diff().ne(1), "csi_slope"] = np.nan
    rows = []
    for year in sorted(panel["year"].unique()):
        graph = build_growth_correlation_graph(panel[panel.year <= year])
        for field in panel.loc[panel.year == year, "field"]:
            rows.append({"field": field, "year": year, **graph_features(graph, field)})
    return panel.merge(pd.DataFrame(rows), on=["field", "year"], how="left"), graph

def build_target(frame, signal="repos", horizon=2, threshold=0.20):
    """Fixed, prespecified relative adoption growth; unknown outcomes stay NA.

    Match exact calendar years rather than shifting observation positions.
    The threshold is never estimated from held-out outcomes.
    """
    if not isinstance(horizon, int) or horizon < 1:
        raise ValueError("horizon must be a positive integer")
    if not np.isfinite(threshold) or threshold < 0:
        raise ValueError("threshold must be finite and nonnegative")
    if frame.duplicated(["field", "year"]).any():
        raise ValueError("Duplicate field-year observations")
    future = frame[["field", "year", signal]].rename(columns={signal: "future_count"}).copy()
    future["year"] -= horizon
    out = frame.drop(columns=["target", "outcome_year", "target_growth"], errors="ignore").merge(future, on=["field", "year"], how="left")
    valid = out[signal].gt(0) & out["future_count"].notna()
    out["target_growth"] = (out["future_count"] / out[signal] - 1).where(valid)
    # Compare counts directly so a 10 -> 12 change is not misclassified by
    # floating-point rounding in (12 / 10 - 1) at the 20% boundary.
    out["target"] = out["future_count"].ge(out[signal] * (1 + threshold)).astype(float).where(valid)
    out["outcome_year"] = out["year"] + horizon
    return out.drop(columns="future_count")
