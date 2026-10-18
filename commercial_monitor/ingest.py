from __future__ import annotations
import os
import time
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import requests
from .storage import atomic_write

UA = "commercial-monitor/0.3 research reproducibility"

# GitHub's REST search API has a much tighter limit than the general REST API.
# Keep search requests serial and below 30 requests/minute, and honor rate-limit
# responses instead of hammering the endpoint.
_GITHUB_SEARCH_MIN_INTERVAL = 2.1
_last_github_search = 0.0


def _cached_json(url, params, fetch, cache_dir=None):
    # Credentials and contact information are never persisted in the cache.
    safe = {k: v for k, v in (params or {}).items() if k not in {"api_key", "mailto", "key", "access_token"}}
    identity = json.dumps({"url": url, "params": safe}, sort_keys=True)
    key = hashlib.sha256(identity.encode()).hexdigest()
    path = Path(cache_dir) / f"{key}.json" if cache_dir else None
    if path and path.exists():
        snapshot = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = fetch()
        if not isinstance(data, dict) or "error_id" in data or "error" in data:
            raise ValueError(f"Invalid API response from {url}")
        if data.get("incomplete_results"):
            raise ValueError("GitHub search returned incomplete results; retry this query")
        snapshot = {"url": url, "params": safe, "retrieved_at": datetime.now(timezone.utc).isoformat(), "response": data}
        if path:
            atomic_write(path, json.dumps(snapshot, sort_keys=True))
    data = snapshot["response"].copy()
    data["_provenance"] = {
        "retrieved_at": snapshot["retrieved_at"],
        "response_sha256": hashlib.sha256(json.dumps(snapshot["response"], sort_keys=True).encode()).hexdigest(),
    }
    return data


def _get(url, params=None, headers=None, cache_dir=None):
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    def fetch():
        for attempt in range(4):
            try:
                r = requests.get(url, params=params, headers=h, timeout=60)
                if r.status_code == 429 or r.status_code >= 500:
                    r.raise_for_status()
                r.raise_for_status()
                data = r.json()
                if data.get("backoff"):
                    time.sleep(float(data["backoff"]))
                return data
            except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as error:
                response = getattr(error, "response", None)
                retryable = response is None or response.status_code == 429 or response.status_code >= 500
                if not retryable or attempt == 3:
                    raise
                retry_after = response.headers.get("Retry-After") if response is not None else None
                time.sleep(min(float(retry_after) if retry_after else 2 ** attempt, 60.0))
    return _cached_json(url, params, fetch, cache_dir)


def _get_github_search(url, params, headers, cache_dir=None):
    return _cached_json(url, params, lambda: _github_search_request(url, params, headers), cache_dir)


def _github_search_request(url, params, headers):
    global _last_github_search

    for attempt in range(5):
        interval = _GITHUB_SEARCH_MIN_INTERVAL if "Authorization" in headers else 6.1
        wait = interval - (time.monotonic() - _last_github_search)
        if wait > 0:
            time.sleep(wait)

        try:
            r = requests.get(url, params=params, headers=headers, timeout=30)
        except (requests.ConnectionError, requests.Timeout):
            if attempt == 4:
                raise
            time.sleep(2 ** attempt)
            continue
        _last_github_search = time.monotonic()

        if r.status_code >= 500 and attempt < 4:
            time.sleep(2 ** attempt)
            continue
        if r.status_code not in (403, 429):
            r.raise_for_status()
            return r.json()

        body = r.text.lower()
        remaining = r.headers.get("X-RateLimit-Remaining")
        retry_after = r.headers.get("Retry-After")
        reset = r.headers.get("X-RateLimit-Reset")

        # GitHub can return 403 for either primary/secondary rate limiting.
        # Retry only when the response looks like a rate-limit response.
        rate_limited = (
            r.status_code == 429
            or remaining == "0"
            or "rate limit" in body
            or "secondary rate limit" in body
        )
        if not rate_limited:
            r.raise_for_status()

        if retry_after:
            delay = float(retry_after)
        elif remaining == "0" and reset:
            delay = max(1.0, float(reset) - time.time())
        else:
            # GitHub recommends backing off for secondary limits.
            delay = min(60.0 * (2 ** attempt), 300.0)

        time.sleep(delay)

    r.raise_for_status()
    return r.json()


def fetch_openalex(query, start_year, end_year, cfg):
    params = {
        "search": query,
        "filter": f"from_publication_date:{start_year}-01-01,to_publication_date:{end_year}-12-31",
        "group_by": "publication_year",
        "per-page": 200,
    }
    mailto = os.getenv(cfg["sources"]["openalex"].get("mailto_env", "OPENALEX_MAILTO"))
    if mailto:
        params["mailto"] = mailto
    api_key = os.getenv(cfg["sources"]["openalex"].get("api_key_env", "OPENALEX_API_KEY"))
    if api_key:
        params["api_key"] = api_key
    data = _get(cfg["sources"]["openalex"]["base_url"], params, cache_dir=cfg["outputs"]["cache_dir"])
    if "group_by" not in data or "meta" not in data or "count" not in data["meta"]:
        raise ValueError("OpenAlex response lacks annual counts")
    counts = {int(x["key"]): int(x["count"]) for x in data["group_by"]}
    if sum(counts.values()) != int(data["meta"]["count"]):
        raise ValueError("OpenAlex annual groups do not cover the full result count")
    return pd.DataFrame([
        {"year": year, "papers": counts.get(year, 0), **data["_provenance"]}
        for year in range(start_year, end_year + 1)
    ])


def fetch_github(keyword, start_year, end_year, cfg):
    token = os.getenv(cfg["sources"]["github"].get("token_env", "GITHUB_TOKEN"))
    headers = {
        "User-Agent": UA,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    rows = []
    for year in range(start_year, end_year + 1):
        q = f"topic:{keyword} created:{year}-01-01..{year}-12-31"
        data = _get_github_search(
            cfg["sources"]["github"]["base_url"],
            {"q": q, "per_page": 1},
            headers,
            cache_dir=cfg["outputs"]["cache_dir"],
        )
        if "total_count" not in data:
            raise ValueError("GitHub response lacks total_count")
        rows.append({"year": year, "repos": int(data["total_count"]), **data["_provenance"]})
    return pd.DataFrame(rows)


def fetch_stackoverflow(tag, start_year, end_year, cfg):
    rows = []
    for year in range(start_year, end_year + 1):
        params = {
            "site": "stackoverflow",
            "tagged": tag,
            "fromdate": int(pd.Timestamp(f"{year}-01-01", tz="UTC").timestamp()),
            "todate": int(pd.Timestamp(f"{year+1}-01-01", tz="UTC").timestamp()) - 1,
            "filter": "total",
        }
        data = _get(cfg["sources"]["stackoverflow"]["base_url"], params, cache_dir=cfg["outputs"]["cache_dir"])
        if "total" not in data:
            raise ValueError("Stack Overflow response lacks total")
        rows.append({"year": year, "questions": int(data["total"]), **data["_provenance"]})
        time.sleep(0.2)
    return pd.DataFrame(rows)


def make_sample_panel(fields, years):
    rows = []
    for fi, field in enumerate(fields):
        for yi, year in enumerate(years):
            rows.append({
                "field": field,
                "year": year,
                "papers": 50 + 5*fi + yi*(2 + fi % 4),
                "repos": 10 + yi*(1 + fi % 3),
                "questions": 20 + yi*(1 + fi % 2),
            })
    return pd.DataFrame(rows)


def fetch_live_observations(cfg):
    """Keep source-query-year measurements instead of discarding them in sums."""
    start, end = cfg["project"]["start_year"], cfg["project"]["end_year"]
    rows = []
    for field, spec in cfg["taxonomy"]["domains"].items():
        for source, metric, adapter in [("openalex", "papers", fetch_openalex), ("github", "repos", fetch_github), ("stackoverflow", "questions", fetch_stackoverflow)]:
            for query in dict.fromkeys(spec.get(source, [])):
                print(f"Fetching {field}/{source}/{query}: {start}–{end}", flush=True)
                measurements = adapter(query, start, end, cfg)
                for row in measurements.to_dict("records"):
                    rows.append({"field": field, "source": source, "query": query, "metric": metric, "year": row["year"], "count": row[metric], "retrieved_at": row["retrieved_at"], "response_sha256": row["response_sha256"]})
    observations = pd.DataFrame(rows)
    validate_observations(observations, cfg)
    return observations


def validate_observations(observations, cfg):
    years = range(cfg["project"]["start_year"], cfg["project"]["end_year"] + 1)
    expected = {(field, source, query, year) for field, spec in cfg["taxonomy"]["domains"].items() for source in ["openalex", "github", "stackoverflow"] for query in set(spec.get(source, [])) for year in years}
    keys = ["field", "source", "query", "year"]
    if observations.empty or observations.duplicated(keys).any():
        raise ValueError("Observations must be nonempty with unique field/source/query/year keys")
    if set(observations[keys].itertuples(index=False, name=None)) != expected:
        raise ValueError("Observations do not cover the configured queries and years")
    counts = observations["count"]
    if counts.isna().any() or (counts < 0).any() or (counts % 1 != 0).any():
        raise ValueError("Source counts must be nonnegative integers")
    mapping = {"openalex": "papers", "github": "repos", "stackoverflow": "questions"}
    if not observations["source"].map(mapping).eq(observations["metric"]).all():
        raise ValueError("Source and metric do not match")
    if pd.to_datetime(observations["retrieved_at"], errors="coerce", utc=True).isna().any():
        raise ValueError("Every observation needs a valid retrieval timestamp")
    if not observations["response_sha256"].astype(str).str.fullmatch(r"[0-9a-f]{64}").all():
        raise ValueError("Every observation needs a response SHA-256")


def aggregate_observations(observations):
    # Query matches overlap. These are activity sums, not unique entity counts.
    panel = observations.groupby(["field", "year", "metric"])["count"].sum().unstack("metric").reset_index()
    panel.columns.name = None
    return panel


def coverage_report(observations):
    return observations.groupby(["field", "source", "year"]).agg(
        n_queries=("query", "nunique"),
        n_nonzero_queries=("count", lambda s: int(s.gt(0).sum())),
        query_match_count=("count", "sum"),
    ).reset_index()


def fetch_live_panel(cfg):
    return aggregate_observations(fetch_live_observations(cfg))
