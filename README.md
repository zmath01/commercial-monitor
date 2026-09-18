# Commercial Monitor

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

## Technology and commercialization dimensions

Domain is only one axis. Observations can additionally describe:

- **artifact type:** software, model, algorithm, data, hardware, material, manufacturing, service
- **commercial pathway:** open source, developer tool, API, cloud, enterprise software, financial strategy/infrastructure, patent, hardware, manufacturing, licensing

This avoids forcing "software vs hardware" into the domain taxonomy. Hardware is not assumed to have lower commercial value; it simply has a different and often less GitHub-observable commercialization pathway.

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

LLMs may assist semantic annotation/entity resolution/report drafting, but may not choose scientific conclusions, delete data, select the winning model, or establish significance.

## Software

Python + pandas/numpy/scipy/scikit-learn + NetworkX + YAML + pytest + GitHub Actions. CSV is the initial portable artifact; Parquet/DuckDB are planned when volume warrants them.

Run the deterministic smoke test:

    pip install -r requirements.txt
    pytest -q
    python -m commercial_monitor.cli --sample

The monthly workflow is manual/scheduled. Run it only after reviewing taxonomy and code changes.

## Project roles

- **commercial-trend-fusion:** concept emergence/co-occurrence and network-science baseline.
- **commercial-trend:** field-level multi-source research/technology/adoption signals.
- **commercial-monitor:** canonical research → technology → commercialization framework.

Effective conductance is retained as a graph baseline, not assumed to be a commercialization metric.
