from __future__ import annotations
import numpy as np
import pandas as pd

def permute_labels(frame, label="target", block="year", seed=20260918):
    """Permutation null preserving the number of positives in each time block."""
    rng = np.random.default_rng(seed)
    out = frame.copy()
    out[label] = out.groupby(block, group_keys=False)[label].transform(
        lambda s: pd.Series(rng.permutation(s.to_numpy()), index=s.index)
    )
    return out
