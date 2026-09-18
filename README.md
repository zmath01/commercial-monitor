# Commercial Monitor

Reproducible research → technology → commercialization monitoring and forecasting.

The project separates research emergence, technology/adoption, IP translation, funding/labor/company outcomes, and market outcomes. It does not treat a composite signal as revenue or investment return.

## Taxonomy

32 arXiv categories map to 14 research-backed domains:

- AI/ML: cs.AI, cs.LG, cs.CL, cs.CV, stat.ML, cs.NE
- Applied mathematics: math.OC, math.NA
- Computer science: cs.DS, cs.DC
- Software engineering: cs.SE, cs.PL
- Security/cryptography: cs.CR
- Quantitative finance: q-fin.CP, q-fin.MF, q-fin.RM, q-fin.ST, q-fin.TR
- Quantum computing: quant-ph
- Quantum materials/electronics: cond-mat.mtrl-sci, cond-mat.mes-hall, cond-mat.str-el, cond-mat.supr-con
- Statistical/complex systems: cond-mat.stat-mech, cond-mat.dis-nn
- Quantum simulation/ultracold matter: cond-mat.quant-gas
- Photonics/optics: physics.optics
- Computational science/engineering: physics.comp-ph, cs.CE
- Emerging hardware/devices: cs.ET
- Digital markets/mechanism design: cs.GT

FinTech is a separate monitoring domain with no dedicated arXiv category. It uses multi-source OpenAlex/GitHub/Stack Overflow signals.

cs.ET is deliberately called Emerging Hardware/Devices rather than chips: the arXiv category is broad and overlaps several hardware technologies.

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

The monthly workflow is manual/scheduled and does not need to be run while taxonomy/code is being reviewed.

## Project roles

- commercial-trend-fusion: concept emergence/co-occurrence and network-science baseline.
- commercial-trend: field-level multi-source research/technology/adoption signals.
- commercial-monitor: canonical research → technology → commercialization framework.

Effective conductance is retained as a graph baseline, not assumed to be a commercialization metric.
