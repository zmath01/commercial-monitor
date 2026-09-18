import networkx as nx
import pandas as pd
from commercial_monitor.signals import minmax,cagr,effective_conductance_2hop

def test_minmax():
    assert minmax(pd.Series([1,2,3])).tolist() == [0.0,0.5,1.0]

def test_cagr():
    assert round(cagr(pd.Series([10,20,40,80]),2),8) == round((80/20)**0.5-1,8)

def test_conductance():
    g=nx.Graph(); g.add_edge("a","v",weight=2); g.add_edge("v","b",weight=4)
    assert effective_conductance_2hop(g,"a","b") == 4/3
