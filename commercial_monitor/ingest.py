from __future__ import annotations
import os
import time
import pandas as pd
import requests

UA = "commercial-monitor/0.1 research reproducibility"

def _get(url, params=None, headers=None):
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    r = requests.get(url, params=params, headers=h, timeout=30)
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
    data = _get(cfg["sources"]["openalex"]["base_url"], params)
    return pd.DataFrame([
        {"year": int(x["key"]), "papers": int(x["count"])}
        for x in data.get("group_by", [])
    ])

def fetch_github(keyword, start_year, end_year, cfg):
    token = os.getenv(cfg["sources"]["github"].get("token_env", "GITHUB_TOKEN"))
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    rows = []
    for year in range(start_year, end_year + 1):
        q = f"topic:{keyword} created:{year}-01-01..{year}-12-31"
        data = _get(cfg["sources"]["github"]["base_url"], {"q": q, "per_page": 1}, headers)
        rows.append({"year": year, "repos": int(data.get("total_count", 0))})
        time.sleep(0.2)
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
        data = _get(cfg["sources"]["stackoverflow"]["base_url"], params)
        rows.append({"year": year, "questions": int(data.get("total", 0))})
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

def fetch_live_panel(cfg):
    start, end = cfg["project"]["start_year"], cfg["project"]["end_year"]
    years = list(range(start, end + 1))
    rows = []
    for field, spec in cfg["taxonomy"]["domains"].items():
        p = pd.DataFrame({"year": years, "papers": 0})
        for query in spec.get("openalex", []):
            x = fetch_openalex(query, start, end, cfg).set_index("year")["papers"]
            p["papers"] += x.reindex(years, fill_value=0).to_numpy()
        g = pd.DataFrame({"year": years, "repos": 0})
        for keyword in spec.get("github", []):
            x = fetch_github(keyword, start, end, cfg).set_index("year")["repos"]
            g["repos"] += x.reindex(years, fill_value=0).to_numpy()
        s = pd.DataFrame({"year": years, "questions": 0})
        for tag in spec.get("stackoverflow", []):
            x = fetch_stackoverflow(tag, start, end, cfg).set_index("year")["questions"]
            s["questions"] += x.reindex(years, fill_value=0).to_numpy()
        p = p.merge(g, on="year").merge(s, on="year")
        p.insert(0, "field", field)
        rows.append(p)
    return pd.concat(rows, ignore_index=True)
