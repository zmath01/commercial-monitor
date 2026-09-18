# Methodology

## Objective

Commercial Monitor studies whether scientific activity is followed by measurable technology adoption and commercialization-related outcomes. It is a forecasting/evidence-aggregation framework, not an investment-return model.

## Taxonomy

The primary taxonomy contains five stable commercial-technology domains:

1. Computer Systems & Engineering
2. AI & Applied Mathematics
3. Quantitative Finance
4. FinTech & Digital Finance
5. Computational Quantum & Matter

The taxonomy intentionally does **not** attempt to reproduce every academic discipline as a top-level class. In particular, ML, DL, foundation models, LLMs, inference, scaling, and AI agents overlap in abstraction level and therefore live under AI & Applied Mathematics as subdomains/tags. Scaling is treated as a cross-cutting training/inference property rather than a domain.

ArXiv categories, OpenAlex concepts, GitHub topics, and Stack Overflow tags are source-specific mappings beneath these stable domains. Domain membership is not required to be mutually exclusive for future multi-label observations.

## Commercialization dimensions

Domain and academic topic are separate from economic artifact and pathway:

- artifact: software, model, algorithm, data, hardware, material, manufacturing, service;
- pathway: open source, developer tool, API, cloud, enterprise software, financial strategy/infrastructure, patent, hardware, manufacturing, licensing.

This makes software/hardware an observable economic dimension rather than an arbitrary taxonomy boundary. Patent data are not assumed to represent hardware only; software and ICT generate substantial patent activity as well.

## Layer separation

Commercial Monitor distinguishes research emergence, technology/adoption, science-to-invention/IP translation, funding, labor, company formation, and market outcomes.

The first runnable release has practical API adapters for OpenAlex, GitHub and Stack Overflow. Downstream outcome layers are explicit schemas/targets so they can be added without redefining the research layer.

## Signals

Growth, z-scores, burst states, signal level and slope are transparent features. The composite signal is normalized within each field, so it is a historical-position proxy rather than an absolute commercial-size measure.

## Graph baseline

The current graph is a field-level growth-correlation graph. It is not a paper-level concept co-occurrence graph. Effective conductance is retained as a transparent graph feature/baseline.

## Targets

The preferred target is:

P(Y_k(t+h) = 1 | X_t)

No feature from t+h or later may enter X_t. The initial target is deliberately generic and should be replaced by outcome-specific targets once patent, funding, labor or market datasets are integrated.

## Evaluation

Expanding-window evaluation is mandatory. Random splits are inappropriate for temporal forecasting. Report ROC-AUC, average precision, Brier score, calibration, coverage, ablations, and null tests.

## Agent boundary

Human controls taxonomy, sources, outcome definitions, inclusion/exclusion rules, evaluation splits and publication decisions. LLMs may assist annotation, entity resolution and drafting. They may not change labels after observing outcomes or decide significance.
