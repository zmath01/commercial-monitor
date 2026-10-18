import numpy as np
import pandas as pd
import pytest
import os
import subprocess
import sys
from pandas.testing import assert_frame_equal

from commercial_monitor.ingest import make_sample_panel
from commercial_monitor.pipeline import build_features, build_target
from commercial_monitor.model import evaluation_folds, fit_logistic_walk_forward, persistence_baseline
from commercial_monitor.nulls import permute_labels
from commercial_monitor.evaluation import evaluate_models


def observed_frame():
    panel = make_sample_panel(["A", "B", "C"], range(2008, 2026))
    panel.loc[panel.field == "A", "repos"] = [10, 15, 20, 10, 30, 20, 10, 15, 20, 10, 30, 20, 10, 15, 20, 10, 30, 20]
    features, _ = build_features(panel)
    return build_target(features)


def test_appending_extreme_future_cannot_change_historical_features():
    panel = make_sample_panel(["A", "B", "C"], range(2008, 2018))
    before, _ = build_features(panel[panel.year <= 2015])
    panel.loc[panel.year > 2015, ["papers", "repos", "questions"]] = 1_000_000
    after, _ = build_features(panel)
    assert_frame_equal(before.reset_index(drop=True), after[after.year <= 2015].reset_index(drop=True))


def test_targets_use_exact_years_fixed_threshold_and_censoring():
    panel = pd.DataFrame({"field": ["A"] * 5, "year": [2010, 2011, 2013, 2014, 2015], "repos": [10, 10, 20, 0, 30]})
    out = build_target(panel).set_index("year")
    assert np.isnan(out.loc[2010, "target"])  # 2012 is absent
    assert out.loc[2011, "target"] == 1
    assert out.loc[2013, "target"] == 1
    assert out.loc[[2014, 2015], "target"].isna().all()
    earlier = build_target(panel[panel.year <= 2013]).set_index("year")
    assert earlier.loc[2011, "target"] == out.loc[2011, "target"]


def test_zero_origin_is_not_infinite_growth_or_negative_outcome():
    panel = make_sample_panel(["A"], [2010, 2011, 2012])
    panel["repos"] = [0, 10, 20]
    features, _ = build_features(panel)
    assert features["repos_growth"].iloc[:2].isna().all()
    assert build_target(features)["target"].isna().all()


def test_exact_growth_threshold_is_positive():
    panel = pd.DataFrame({"field": ["A", "A"], "year": [2010, 2012], "repos": [10, 12]})
    assert build_target(panel).target.iloc[0] == 1


def test_models_share_folds_and_wait_for_observable_labels():
    frame = observed_frame()
    for year, train, test in evaluation_folds(frame):
        assert train.outcome_year.max() < year
        assert train.year.nunique() >= 5
        assert train.target.notna().all() and test.target.notna().all()
    model = fit_logistic_walk_forward(frame)
    baseline = persistence_baseline(frame)
    assert not model.empty
    assert model.year.tolist() == baseline.year.tolist()
    assert model.n_test.tolist() == baseline.n_test.tolist()
    assert model.train_outcome_end.lt(model.year).all()


def test_test_outcomes_do_not_change_same_year_predictions():
    frame = observed_frame()
    _, before = fit_logistic_walk_forward(frame, return_predictions=True)
    year = before.year.min()
    frame.loc[frame.outcome_year >= year, "target"] = 1 - frame.loc[frame.outcome_year >= year, "target"]
    _, after = fit_logistic_walk_forward(frame, return_predictions=True)
    np.testing.assert_allclose(before.loc[before.year == year, "probability"], after.loc[after.year == year, "probability"])


def test_null_preserves_censored_rows_and_annual_positive_counts():
    frame = observed_frame()
    null = permute_labels(frame)
    assert null.target.isna().equals(frame.target.isna())
    pd.testing.assert_series_equal(null.groupby("year").target.sum(), frame.groupby("year").target.sum())
    assert_frame_equal(null, permute_labels(frame))


def test_ablations_calibration_and_null_outputs():
    outputs = evaluate_models(observed_frame(), null_repeats=2)
    assert set(outputs["model_comparison"].model) == {"full", "research_only", "adoption_only", "graph_only", "persistence", "global_rate"}
    assert outputs["calibration"].n.sum() == len(outputs["predictions"])
    assert set(outputs["null_metrics"].repeat) == {0, 1}


def test_short_panel_returns_readable_empty_evaluation():
    frame = build_target(build_features(make_sample_panel(["A", "B"], range(2010, 2013)))[0])
    metrics = fit_logistic_walk_forward(frame)
    assert metrics.empty and "brier" in metrics


def test_duplicate_panel_rejected():
    panel = make_sample_panel(["A"], range(2010, 2013))
    with pytest.raises(ValueError, match="Duplicate"):
        build_features(pd.concat([panel, panel.iloc[:1]]))


def test_graph_features_are_reproducible_across_python_hash_seeds():
    program = (
        "from commercial_monitor.ingest import make_sample_panel; "
        "from commercial_monitor.pipeline import build_features; "
        "p=make_sample_panel(['A','B','C','D','E'],range(2008,2026)); "
        "print(build_features(p)[0].to_csv(index=False))"
    )
    outputs = [subprocess.run([sys.executable, "-c", program], env={**os.environ, "PYTHONHASHSEED": seed}, text=True, capture_output=True, check=True).stdout for seed in ["1", "2"]]
    assert outputs[0] == outputs[1]
