"""Independent integrity checks on the published, offline research snapshot."""
import gzip
import hashlib
import json
from pathlib import Path
import re

import pandas as pd
import pytest

from commercial_monitor.config import ROOT, load_config
from commercial_monitor.ingest import aggregate_observations, validate_observations


DATA = ROOT / "data"
pytestmark = pytest.mark.skipif(not (DATA / "manifest.json").exists(), reason="No published snapshot yet")


def test_published_checksums_coverage_and_censoring():
    manifest = json.loads((DATA / "manifest.json").read_text())
    for name, digest in manifest["files"].items():
        assert hashlib.sha256((DATA / name).read_bytes()).hexdigest() == digest, name
    observations = pd.read_csv(DATA / "source_observations.csv")
    validate_observations(observations, load_config())
    panel = pd.read_csv(DATA / "panel.csv")
    counts = ["field", "year", "papers", "repos", "questions"]
    expected = aggregate_observations(observations)[counts].sort_values(["field", "year"]).reset_index(drop=True)
    actual = panel[counts].sort_values(["field", "year"]).reset_index(drop=True)
    pd.testing.assert_frame_equal(actual, expected, check_dtype=False)
    assert panel.loc[panel.year > panel.year.max() - 2, "target"].isna().all()
    metrics = pd.read_csv(DATA / "model_comparison.csv")
    assert metrics.train_outcome_end.lt(metrics.year).all()
    assert metrics.groupby("model").year.apply(tuple).nunique() == 1


def test_every_observation_is_supported_by_archived_api_response():
    cfg = load_config()
    counts = {}
    with gzip.open(DATA / "raw_responses.jsonl.gz", "rt", encoding="utf-8") as handle:
        for line in handle:
            snapshot = json.loads(line)
            params, response = snapshot["params"], snapshot["response"]
            assert not {"api_key", "mailto", "access_token", "key"}.intersection(params)
            digest = hashlib.sha256(json.dumps(response, sort_keys=True).encode()).hexdigest()
            if "group_by" in params:
                groups = {int(row["key"]): int(row["count"]) for row in response["group_by"]}
                assert sum(groups.values()) == response["meta"]["count"]
                for year in range(cfg["project"]["start_year"], cfg["project"]["end_year"] + 1):
                    counts[("openalex", params["search"], year, digest)] = groups.get(year, 0)
            elif "q" in params:
                query, year = re.fullmatch(r"topic:(.+) created:(\d{4})-01-01\.\.(\d{4})-12-31", params["q"]).group(1, 2)
                assert response["incomplete_results"] is False
                counts[("github", query, int(year), digest)] = response["total_count"]
            else:
                year = pd.Timestamp(params["fromdate"], unit="s", tz="UTC").year
                counts[("stackoverflow", params["tagged"], year, digest)] = response["total"]
    for row in pd.read_csv(DATA / "source_observations.csv").itertuples():
        assert counts[(row.source, row.query, row.year, row.response_sha256)] == row.count
