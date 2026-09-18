from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss

FEATURES = [
    "papers_growth","repos_growth","questions_growth",
    "papers_z","repos_z","questions_z","repos_burst","questions_burst",
    "csi","csi_slope","graph_degree","graph_aa_max","graph_conductance_max",
]

def _metrics(y, p):
    return {
        "roc_auc": roc_auc_score(y, p) if y.nunique() > 1 else np.nan,
        "pr_auc": average_precision_score(y, p),
        "brier": brier_score_loss(y, p),
    }

def fit_logistic_walk_forward(frame, label="target"):
    rows = []
    frame = frame.sort_values("year").dropna(subset=[label]).copy()
    cols = [c for c in FEATURES if c in frame.columns]
    for year in sorted(frame["year"].unique()):
        train, test = frame[frame.year < year], frame[frame.year == year]
        if len(train) < 8 or train[label].nunique() < 2 or test.empty:
            continue
        Xtr = train[cols].replace([np.inf,-np.inf],np.nan).fillna(0)
        Xte = test[cols].replace([np.inf,-np.inf],np.nan).fillna(0)
        ytr, yte = train[label].astype(int), test[label].astype(int)
        model = LogisticRegression(C=1.0,max_iter=2000,class_weight="balanced")
        model.fit(Xtr,ytr)
        p = model.predict_proba(Xte)[:,1]
        rows.append({"year":int(year),"n_test":len(test),"positive_rate":float(yte.mean()),**_metrics(yte,p)})
    return pd.DataFrame(rows)

def persistence_baseline(frame, label="target"):
    rows = []
    for year in sorted(frame.year.unique()):
        train, test = frame[frame.year < year], frame[frame.year == year]
        if train.empty or test.empty:
            continue
        p = float(train[label].mean())
        y = test[label].astype(int)
        rows.append({"year":int(year),"n_test":len(test),"positive_rate":float(y.mean()),**_metrics(y,np.repeat(p,len(y)))})
    return pd.DataFrame(rows)
