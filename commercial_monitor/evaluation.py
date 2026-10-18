from __future__ import annotations
import numpy as np
import pandas as pd

def temporal_folds(frame, year_col="year", min_train_years=5):
    """Expanding windows, excluding outcomes unavailable at the test origin."""
    years = sorted(frame[year_col].dropna().unique())
    for year in years:
        train = frame[frame[year_col] < year]
        if "outcome_year" in frame:
            train = train[train.outcome_year < year]
        if train[year_col].nunique() >= min_train_years:
            yield year, train.copy(), frame[frame[year_col] == year].copy()

def aggregate_metrics(metrics):
    if metrics is None or len(metrics) == 0:
        return pd.DataFrame()
    return metrics.agg({"roc_auc":"mean","pr_auc":"mean","brier":"mean"}).to_frame("mean")

def bootstrap_mean(values, n=2000, seed=20260918, block_length=None):
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return {"mean": np.nan, "lo": np.nan, "hi": np.nan}
    if n < 1:
        raise ValueError("n must be positive")
    # Circular blocks retain local dependence between adjacent annual folds.
    length = min(len(x), max(1, int(block_length or np.ceil(np.sqrt(len(x))))))
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, len(x), size=(n, int(np.ceil(len(x) / length))))
    indices = (starts[:, :, None] + np.arange(length)) % len(x)
    samples = x[indices.reshape(n, -1)[:, :len(x)]].mean(axis=1)
    return {"mean": float(x.mean()), "lo": float(np.quantile(samples,0.025)), "hi": float(np.quantile(samples,0.975))}


def evaluate_models(frame, min_train_years=5, null_repeats=20, seed=20260918):
    """Prespecified ablations, matched baselines and within-year nulls.

    Nulls are descriptive diagnostics; correlated folds and five domains do
    not justify treating these rows as independent significance experiments.
    """
    from .model import FEATURES, fit_logistic_walk_forward, persistence_baseline
    from .nulls import permute_labels
    full, predictions = fit_logistic_walk_forward(frame, min_train_years=min_train_years, return_predictions=True)
    comparisons = [full.assign(model="full")]
    groups = {
        "research_only": [c for c in FEATURES if c.startswith("papers_")],
        "adoption_only": [c for c in FEATURES if c.startswith(("repos_", "questions_"))],
        "graph_only": [c for c in FEATURES if c.startswith("graph_")],
    }
    for name, columns in groups.items():
        metrics = fit_logistic_walk_forward(frame, min_train_years=min_train_years, features=columns)
        comparisons.append(metrics.assign(model=name))
    baseline = persistence_baseline(frame, min_train_years=min_train_years)
    comparisons.append(baseline.assign(model="persistence"))
    comparisons.append(persistence_baseline(frame, min_train_years=min_train_years, global_rate=True).assign(model="global_rate"))
    nulls = []
    for repeat in range(null_repeats):
        permuted = permute_labels(frame, seed=seed + repeat)
        nulls.append(fit_logistic_walk_forward(permuted, min_train_years=min_train_years).assign(repeat=repeat, seed=seed+repeat))
    comparison = pd.concat(comparisons, ignore_index=True)
    summary = []
    for model, group in comparison.groupby("model"):
        for metric in ["roc_auc", "pr_auc", "brier"]:
            estimate = bootstrap_mean(group[metric], seed=seed)
            n_folds = int(group[metric].notna().sum())
            summary.append({"model": model, "metric": metric, "n_folds": n_folds, "block_length": int(np.ceil(np.sqrt(n_folds))), **estimate})
    calibration = []
    if not predictions.empty:
        predictions["bin"] = pd.cut(predictions.probability, bins=np.linspace(0, 1, 6), include_lowest=True)
        for interval, group in predictions.groupby("bin", observed=True):
            calibration.append({"bin": str(interval), "n": len(group), "mean_probability": float(group.probability.mean()), "observed_rate": float(group.target.mean())})
        predictions = predictions.drop(columns="bin")
    from .model import METRIC_COLUMNS
    null_frame = pd.concat(nulls, ignore_index=True) if nulls else pd.DataFrame(columns=METRIC_COLUMNS + ["repeat", "seed"])
    paired = []
    global_scores = comparison[comparison.model == "global_rate"][["year", "brier"]]
    for model, group in comparison.groupby("model"):
        joined = group[["year", "brier"]].merge(global_scores, on="year", suffixes=("", "_global"))
        paired.append({"model": model, "n_folds": len(joined), **bootstrap_mean(joined.brier - joined.brier_global, seed=seed)})
    null_means = null_frame.groupby("repeat").brier.mean()
    null_summary = pd.DataFrame([{
        "n_repeats": len(null_means), "observed_mean_brier": full.brier.mean(),
        "null_mean_brier": null_means.mean(), "null_brier_q025": null_means.quantile(0.025), "null_brier_q975": null_means.quantile(0.975),
    }])
    return {
        "walk_forward": full, "baseline": baseline, "model_comparison": comparison,
        "predictions": predictions, "metric_summary": pd.DataFrame(summary, columns=["model", "metric", "n_folds", "block_length", "mean", "lo", "hi"]),
        "calibration": pd.DataFrame(calibration, columns=["bin", "n", "mean_probability", "observed_rate"]),
        "null_metrics": null_frame,
        "null_summary": null_summary,
        "paired_brier": pd.DataFrame(paired, columns=["model", "n_folds", "mean", "lo", "hi"]),
    }
