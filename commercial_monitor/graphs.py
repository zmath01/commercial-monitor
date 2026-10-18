from __future__ import annotations
import itertools
from math import fsum, log
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
    wide = wide.reindex(range(int(wide.index.min()), int(wide.index.max()) + 1))
    growth = wide.pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan)
    # Require at least three shared annual changes; a single pair cannot
    # establish a correlation edge.
    corr = growth.corr(min_periods=3)
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
    for neighbor in sorted(g.neighbors(field)):
        # Stable summation avoids hash-seed-dependent rounding from set order.
        common = sorted(nx.common_neighbors(g, field, neighbor))
        score = fsum(1 / log(g.degree(v)) for v in common)
        aa_max = max(aa_max, float(score))
    conduct = max((effective_conductance_2hop(g, field, v) for v in g.neighbors(field)), default=0.0)
    return {"graph_degree": degree, "graph_aa_max": aa_max, "graph_conductance_max": float(conduct)}
