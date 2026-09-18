from __future__ import annotations
from math import lgamma, log
import numpy as np
import pandas as pd

def yoy_growth(values):
    return pd.Series(values, dtype=float).pct_change()

def cagr(values, years=3):
    x = pd.Series(values).dropna().astype(float)
    if len(x) <= years:
        return float("nan")
    a, b = float(x.iloc[-years-1]), float(x.iloc[-1])
    if a <= 0 or b < 0:
        return float("nan")
    return (b / a) ** (1 / years) - 1

def zscore(values):
    s = pd.Series(values, dtype=float)
    sd = s.std(ddof=0)
    return (s - s.mean()) / sd if sd > 0 else pd.Series(0.0, index=s.index)

def minmax(values):
    s = pd.Series(values, dtype=float)
    lo, hi = s.min(), s.max()
    if not np.isfinite(lo) or hi <= lo:
        return pd.Series(0.0, index=s.index)
    return (s - lo) / (hi - lo)

def composite_index(frame, weights):
    parts, total = [], 0.0
    for name, weight in weights.items():
        if name not in frame:
            continue
        x = minmax(frame[name])
        parts.append(weight * x.fillna(0.0))
        total += weight
    if not parts or total == 0:
        return pd.Series(0.0, index=frame.index)
    return sum(parts) / total

def poisson_nll(k, rate):
    return rate - k * log(rate) + lgamma(k + 1)

def kleinberg_burst(values, s=2.0, gamma=1.0):
    x = pd.Series(values).fillna(0).astype(float).to_numpy()
    n = len(x)
    if n == 0:
        return pd.Series(dtype=int, index=values.index)
    rate0 = max(x.mean(), 1e-9)
    rates = np.array([rate0, s * rate0])
    dp = np.full((n, 2), np.inf)
    prev = np.zeros((n, 2), dtype=int)
    dp[0] = [poisson_nll(x[0], rates[0]), poisson_nll(x[0], rates[1])]
    transition = gamma * np.log(max(n, 2))
    for t in range(1, n):
        for state in range(2):
            emit = poisson_nll(x[t], rates[state])
            candidates = dp[t-1] + transition
            candidates[state] = dp[t-1, state]
            prev[t, state] = int(np.argmin(candidates))
            dp[t, state] = candidates[prev[t, state]] + emit
    state = np.zeros(n, dtype=int)
    state[-1] = int(np.argmin(dp[-1]))
    for t in range(n-1, 0, -1):
        state[t-1] = prev[t, state[t]]
    return pd.Series(state, index=values.index, name="burst")

def effective_conductance_2hop(graph, a, b):
    total = 0.0
    for v in set(graph.neighbors(a)).intersection(graph.neighbors(b)):
        wa = float(graph[a][v].get("weight", 1.0))
        wb = float(graph[v][b].get("weight", 1.0))
        if wa + wb > 0:
            total += wa * wb / (wa + wb)
    return total
