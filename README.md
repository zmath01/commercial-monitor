# Commercial Monitor

**Dashboard:** https://zmath01.github.io/commercial-monitor/

The dashboard shows annual activity by source, query concentration, paired model
comparisons, and calibration. Export a self-contained copy using the committed data:

    python docs/export_dashboard.py /tmp/commercial-monitor.html

Reproducible **research → technology → commercialization** monitoring and forecasting.

The project is designed for commercially relevant technology signals rather than an exhaustive academic taxonomy. It separates research emergence, technology/adoption, IP translation, funding/labor/company outcomes, and market outcomes. It does not treat a composite signal as revenue, investment return, or a recommendation.

## Taxonomy

The primary taxonomy has **5 stable commercial-technology domains**:

1. **Computer Systems & Engineering**
   - software engineering, applied programming languages, algorithms/data structures
   - parallel/distributed systems, databases/storage, compilers/runtimes
   - cloud/infrastructure, embedded software, security/cryptography

2. **AI & Applied Mathematics**
   - optimization, numerical methods, statistical learning
   - ML, DL, foundation models, LLMs, multimodal models
   - inference, training, scaling, AI agents, scientific ML

   ML/DL/Foundation Models/LLM/Inference/Scaling/AI Agents are intentionally **not separate top-level domains**. They overlap in level and are represented as subdomains/tags. Scaling is a cross-cutting property, not a standalone field.

3. **Quantitative Finance**
   - mathematical/stochastic/numerical finance
   - Monte Carlo, econometrics, quant trading, risk
   - ML/DL/LLM for finance

4. **FinTech & Digital Finance**
   - digital banking, payments, open banking, financial infrastructure
   - lending/wealthtech
   - blockchain, stablecoins, crypto infrastructure, DeFi
   - digital markets/mechanism design

5. **Computational Quantum & Matter**
   - quantum algorithms/software/compilation/simulation
   - quantum ML, quantum chemistry, tensor networks
   - computational materials and scientific simulation
   - computational optics

Academic source categories (including arXiv categories) are **secondary mappings**, not the primary taxonomy. The taxonomy is deliberately not mutually exclusive at the observation level: a technology may carry multiple subdomain tags.

The five domains are monitoring views across methods, technology families and
applications. The [taxonomy audit](docs/METHODOLOGY.md#taxonomy-audit) defines
entity-level assignment rules and identifies broad queries. The current count
series use the version 1 query sets in `config.yaml`.

## Technology and commercialization dimensions

Entity-level work can record the artifact, such as software or hardware, the
commercial pathway, such as licensing or manufacturing, and a dated evidence
event, such as a patent filing or a procurement award. These axes complement
the monitoring domain. The current API snapshot stores aggregate query counts.

## Forecasting target

The primary estimand is

    P(Y_k(t+h)=1 | X_t),

where X_t contains only information available by t and Y_k is an explicitly defined future outcome. Candidate outcomes include technology adoption, science-to-patent linkage, funding, labor demand, company formation, and market adoption.

Investment relevance is a downstream interpretation layer, not a prediction target.

## Design principles

- expanding-window temporal evaluation;
- persistence/global-rate and graph-only baselines;
- calibration via Brier score;
- null/permutation experiments;
- source-coverage diagnostics;
- deterministic transforms and tests;
- cached raw data and provenance;
- human-defined taxonomy, targets and evaluation boundaries.

## Data coverage and research status

The original release contained **55 field-year rows** (five domains, 2015–2025).
The configured window now covers **2008–2025**, giving **90 field-year rows**.
Live runs also retain every configured **source-query-year observation**, rather
than discarding the inputs after aggregation. These overlapping measurements are
an audit trail, **not additional independent forecasting samples**. API totals
are counts of query matches, not a sample of downloaded papers or repositories.

The runnable target is **at least 20% growth in GitHub topic-query repository
counts over two calendar years**, with a positive starting count. It measures an
engineering activity proxy. It does not establish commercialization, revenue,
patent translation, or investment returns. Final-horizon outcomes and zero-origin
growth remain unknown; they are never silently labeled as negatives.

Historical features use only prefixes through their observation year. Training
uses only labels whose outcome year precedes the test year, with at least five
training years. Scaling is fitted inside each training fold. All models share
the same eligible test folds. Published diagnostics include field persistence,
global-rate, GitHub-only and graph-only baselines, research/adoption ablations,
Brier score, ROC-AUC, average precision, calibration, paired Brier differences,
and 20 seeded within-year permutation runs. `research_increment.csv` reports
the paired Brier change from adding direct OpenAlex features to the same GitHub
and Stack Overflow features. Descriptive intervals use circular moving blocks
of annual folds. These changes supersede the original full-window normalization
and future-dependent target threshold.

Current API snapshots can revise past counts and topic assignments. Consequently,
these are **retrospective snapshot backtests**, not a reconstruction of the data
actually available to historical forecasters. Five domains and correlated annual
observations remain too little evidence for strong empirical claims. See
[methodology](docs/METHODOLOGY.md) and [scientific status](SCIENTIFIC_STATUS.md).

LLMs may assist semantic annotation/entity resolution/report drafting, but may not choose scientific conclusions, delete data, select the winning model, or establish significance.

## Software

Python + pandas/numpy/scipy/scikit-learn + NetworkX + YAML + pytest + GitHub Actions. CSV is the initial portable artifact; Parquet/DuckDB are planned when volume warrants them.

Run the deterministic smoke test:

    pip install -r requirements.txt
    pytest -q
    python -m commercial_monitor.cli --sample

Fetch a live snapshot (the initial run takes time because GitHub search is serial
and rate limited):

    export GITHUB_TOKEN=...  # Set privately in your shell; never commit it.
    python -m commercial_monitor.cli --live --out data

Successful responses are cached in `cache/`, so rerunning after an interruption
resumes the snapshot. Use `--refresh-cache` to start a new snapshot. Optional
`OPENALEX_API_KEY` and `OPENALEX_MAILTO` environment variables support OpenAlex
access; credentials and contact addresses are excluded from cached parameters.
Failed, malformed, or incomplete responses fail the run rather than supplying
zero observations. Real zero counts are preserved.

Rebuild features and research diagnostics without network access:

    python -m commercial_monitor.cli --observations data/source_observations.csv --out data

Published outputs include `panel.csv`, `source_observations.csv`, `coverage.csv`,
model metrics, out-of-time predictions, calibration, null diagnostics, `run.json`,
and a checksum manifest. Live runs retain compressed raw API responses in
`raw_responses.jsonl.gz`. Synthetic smoke runs are labeled explicitly and cannot
overwrite an output directory containing live observations.

Tests run on pushes and pull requests. The monthly workflow refreshes data on the
first day of each month and supports manual `refresh` and offline `rebuild` modes.
It runs tests before publishing outputs and rebuilds the manuscript PDF. Review
taxonomy and target changes before interpreting a new run.

## Project roles

- **commercial-trend-fusion:** concept emergence/co-occurrence and network-science baseline.
- **commercial-trend:** field-level multi-source research/technology/adoption signals.
- **commercial-monitor:** canonical research → technology → commercialization framework.

Effective conductance is retained as a graph baseline, not assumed to be a commercialization metric.
