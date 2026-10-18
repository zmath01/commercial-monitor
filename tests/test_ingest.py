import copy
import json
from pathlib import Path
from unittest.mock import Mock
import requests

import pandas as pd
import pytest

from commercial_monitor import ingest
from commercial_monitor.config import load_config


def test_cache_replay_provenance_and_no_credentials(tmp_path):
    fetch = Mock(return_value={"total": 12})
    first = ingest._cached_json("https://example.org", {"tag": "ai", "api_key": "secret", "mailto": "private@example.org"}, fetch, tmp_path)
    second = ingest._cached_json("https://example.org", {"tag": "ai", "api_key": "changed"}, fetch, tmp_path)
    assert fetch.call_count == 1
    assert first == second
    cached = next(tmp_path.glob("*.json")).read_text()
    assert "secret" not in cached and "private@example.org" not in cached
    assert len(first["_provenance"]["response_sha256"]) == 64


@pytest.mark.parametrize("response", [{"incomplete_results": True}, {"error_id": 502}, {"error": "quota exhausted"}])
def test_failed_or_incomplete_responses_are_not_cached(tmp_path, response):
    with pytest.raises(ValueError):
        ingest._cached_json("https://example.org", {}, lambda: response, tmp_path)
    assert not list(tmp_path.iterdir())


def test_query_observations_aggregate_and_missing_query_is_rejected(monkeypatch, tmp_path):
    cfg = copy.deepcopy(load_config())
    cfg["project"].update(start_year=2010, end_year=2012)
    cfg["taxonomy"]["domains"] = {"A": {"openalex": ["a", "b"], "github": ["c"], "stackoverflow": ["d"]}}
    def adapter(metric):
        def fetch(query, start, end, config):
            return pd.DataFrame({"year": list(range(start, end+1)), metric: [2, 0, 3], "retrieved_at": "2026-01-01T00:00:00Z", "response_sha256": "a" * 64})
        return fetch
    for source, metric in [("openalex", "papers"), ("github", "repos"), ("stackoverflow", "questions")]:
        monkeypatch.setattr(ingest, f"fetch_{source}", adapter(metric))
    observations = ingest.fetch_live_observations(cfg)
    assert len(observations) == 12
    panel = ingest.aggregate_observations(observations)
    assert panel.papers.tolist() == [4, 0, 6]
    coverage = ingest.coverage_report(observations)
    assert coverage[coverage.source == "openalex"].n_queries.tolist() == [2, 2, 2]
    with pytest.raises(ValueError, match="cover"):
        ingest.validate_observations(observations.iloc[:-1], cfg)
    with pytest.raises(ValueError, match="unique"):
        ingest.validate_observations(pd.concat([observations, observations.iloc[:1]]), cfg)


def test_openalex_empty_valid_counts_and_schema_failure(monkeypatch, tmp_path):
    cfg = load_config()
    cfg["outputs"]["cache_dir"] = str(tmp_path)
    provenance = {"retrieved_at": "today", "response_sha256": "a"*64}
    monkeypatch.setattr(ingest, "_get", lambda *args, **kwargs: {"meta": {"count": 0}, "group_by": [], "_provenance": provenance})
    assert ingest.fetch_openalex("empty", 2010, 2012, cfg).papers.tolist() == [0, 0, 0]
    monkeypatch.setattr(ingest, "_get", lambda *args, **kwargs: {})
    with pytest.raises(ValueError, match="lacks"):
        ingest.fetch_openalex("bad", 2010, 2012, cfg)


def test_transient_github_connection_failure_is_retried(monkeypatch):
    response = Mock(status_code=200)
    response.json.return_value = {"total_count": 3, "incomplete_results": False}
    get = Mock(side_effect=[requests.ConnectionError("temporary"), response])
    monkeypatch.setattr(ingest.requests, "get", get)
    monkeypatch.setattr(ingest.time, "sleep", lambda seconds: None)
    assert ingest._github_search_request("https://example.org", {}, {})["total_count"] == 3
    assert get.call_count == 2


def test_nonretryable_http_error_is_not_retried(monkeypatch):
    response = Mock(status_code=401)
    response.raise_for_status.side_effect = requests.HTTPError("unauthorized", response=response)
    get = Mock(return_value=response)
    monkeypatch.setattr(ingest.requests, "get", get)
    with pytest.raises(requests.HTTPError):
        ingest._get("https://example.org")
    assert get.call_count == 1
