from __future__ import annotations
import itertools
import networkx as nx
import numpy as np
import pandas as pd
from .signals import effective_conductance_2hop

def build_growth_correlation_graph(panel, threshold=0.3):
    """Field graph from correlations of growth profiles.

    It is deliberately not called a topic-cooccurrence graph: the inputs are
    field-level annual paper counts, not document-level concept pairs.
    """
    g = nx.Graph()
    fields = sorted(panel["field"].unique())
    g.add_nodes_from(fields)
    wide = panel.pivot_table(index="year", columns="field", values="papers", aggfunc="sum")
    corr = wide.pct_change().corr()
    for a, b in itertools.combinations(fields, 2):
        w = corr.loc[a, b]
        if pd.notna(w) and w > threshold:
            g.add_edge(a, b, weight=float(w))
    return g

def graph_features(g, field):
    if field not in g:
        return {"graph_degree": 0.0, "graph_aa_max": 0.0, "graph_conductance_max": 0.0}
    degree = float(g.degree(field))
    aa_max = 0.0
    for _, _, score in nx.adamic_adar_index(g, [(field, v) for v in g.neighbors(field)]):
        aa_max = max(aa_max, float(score))
    conduct = max((effective_conductance_2hop(g, field, v) for v in g.neighbors(field)), default=0.0)
    return {"graph_degree": degree, "graph_aa_max": aa_max, "graph_conductance_max": float(conduct)}
