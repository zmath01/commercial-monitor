from __future__ import annotations
import numpy as np
import pandas as pd

def permute_labels(frame, label="target", block="year", seed=20260918):
    """Permutation null preserving the number of positives in each time block."""
    rng = np.random.default_rng(seed)

    def shuffle_observed(values):
        observed = values.dropna()
        # pandas can expose a read-only view, while NumPy needs a writable array.
        shuffled = rng.permutation(observed.to_numpy(copy=True))
        replacements = pd.Series(shuffled, index=observed.index).reindex(values.index)
        return values.where(values.isna(), replacements)

    out = frame.copy()
    out[label] = out.groupby(block, group_keys=False)[label].transform(shuffle_observed)
    return out
