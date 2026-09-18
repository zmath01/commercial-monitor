from __future__ import annotations
import pandas as pd

OUTCOMES = {
    "research_emergence":"future research activity",
    "technology_adoption":"future engineering/developer ecosystem activity",
    "ip_translation":"future science-to-patent linkage",
    "funding":"future grant/financing activity",
    "labor":"future labor-demand activity",
    "company_formation":"future company/startup formation",
    "market_adoption":"future procurement/licensing/product/revenue proxy",
}

def future_relative_growth(panel, signal, horizon=2):
    wide = panel.pivot_table(index="year",columns="field",values=signal,aggfunc="sum").sort_index()
    delta = wide.shift(-horizon) - wide
    threshold = delta.stack().median()
    y = (delta > threshold).astype(int).stack().rename("target").reset_index()
    y.columns = ["year","field","target"]
    return y

def make_outcome_registry():
    return pd.DataFrame([{"outcome":k,"definition":v} for k,v in OUTCOMES.items()])
