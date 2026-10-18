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

def future_relative_growth(panel, signal, horizon=2, threshold=0.20):
    from .pipeline import build_target
    return build_target(panel, signal, horizon, threshold)[["year", "field", "target", "outcome_year"]]

def make_outcome_registry():
    return pd.DataFrame([{"outcome":k,"definition":v} for k,v in OUTCOMES.items()])
