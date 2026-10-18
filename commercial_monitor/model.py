from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from .evaluation import temporal_folds
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss

FEATURES = [
    "papers_growth","repos_growth","questions_growth",
    "papers_z","repos_z","questions_z","repos_burst","questions_burst",
    "csi","csi_slope","graph_degree","graph_aa_max","graph_conductance_max",
]

def _metrics(y, p):
    return {
        "roc_auc": roc_auc_score(y, p) if y.nunique() > 1 else np.nan,
        "pr_auc": average_precision_score(y, p) if y.sum() else np.nan,
        "brier": brier_score_loss(y, p),
    }

METRIC_COLUMNS = ["year", "n_train", "n_train_years", "train_outcome_end", "n_test", "positive_rate", "roc_auc", "pr_auc", "brier"]


def evaluation_folds(frame, label="target", min_train_years=5):
    if "outcome_year" not in frame:
        raise ValueError("outcome_year is required to enforce label availability")
    observed = frame.dropna(subset=[label]).sort_values(["year", "field"])
    for year, train, test in temporal_folds(observed, min_train_years=min_train_years):
        if len(train) >= 8 and train[label].nunique() == 2 and not test.empty:
            yield year, train, test


def _fold_metrics(year, train, test, label, p):
    y = test[label].astype(int)
    return {"year": int(year), "n_train": len(train), "n_train_years": train.year.nunique(), "train_outcome_end": int(train.outcome_year.max()), "n_test": len(test), "positive_rate": float(y.mean()), **_metrics(y, p)}


def fit_logistic_walk_forward(frame, label="target", min_train_years=5, features=None, return_predictions=False):
    rows, predictions = [], []
    cols = FEATURES if features is None else features
    if not cols or not set(cols).issubset(frame.columns):
        raise ValueError("All requested model features must be present")
    for year, train, test in evaluation_folds(frame, label, min_train_years):
        Xtr = train[cols].replace([np.inf,-np.inf],np.nan).fillna(0)
        Xte = test[cols].replace([np.inf,-np.inf],np.nan).fillna(0)
        model = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=2000))
        model.fit(Xtr, train[label].astype(int))
        p = model.predict_proba(Xte)[:,1]
        rows.append(_fold_metrics(year, train, test, label, p))
        for field, target, probability in zip(test.field, test[label], p):
            predictions.append({"year": int(year), "field": field, "target": int(target), "probability": float(probability)})
    metrics = pd.DataFrame(rows, columns=METRIC_COLUMNS)
    if return_predictions:
        return metrics, pd.DataFrame(predictions, columns=["year", "field", "target", "probability"])
    return metrics

def persistence_baseline(frame, label="target", min_train_years=5, global_rate=False):
    rows = []
    for year, train, test in evaluation_folds(frame, label, min_train_years):
        rate = float(train[label].mean())
        if global_rate:
            p = np.repeat(rate, len(test))
        else:
            last = train.sort_values("year").groupby("field")[label].last()
            p = test.field.map(last).fillna(rate).to_numpy()
        rows.append(_fold_metrics(year, train, test, label, p))
    return pd.DataFrame(rows, columns=METRIC_COLUMNS)
