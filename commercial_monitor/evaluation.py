from __future__ import annotations
import numpy as np
import pandas as pd

def temporal_folds(frame, year_col="year", min_train_years=5):
    years = sorted(frame[year_col].dropna().unique())
    for year in years:
        train_years = [y for y in years if y < year]
        if len(train_years) >= min_train_years:
            yield year, frame[frame[year_col] < year].copy(), frame[frame[year_col] == year].copy()

def aggregate_metrics(metrics):
    if metrics is None or len(metrics) == 0:
        return pd.DataFrame()
    return metrics.agg({"roc_auc":"mean","pr_auc":"mean","brier":"mean"}).to_frame("mean")

def bootstrap_mean(values, n=2000, seed=20260918):
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return {"mean": np.nan, "lo": np.nan, "hi": np.nan}
    rng = np.random.default_rng(seed)
    samples = rng.choice(x, size=(n, len(x)), replace=True).mean(axis=1)
    return {"mean": float(x.mean()), "lo": float(np.quantile(samples,0.025)), "hi": float(np.quantile(samples,0.975))}
