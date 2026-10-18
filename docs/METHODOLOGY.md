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

Each feature for year t is computed from the prefix ending at t. Z-scores use
population standard deviation of that prefix; constant prefixes map to zero.
Composite min/max bounds also come from prefixes. The two-state Poisson burst
dynamic program is evaluated on the prefix and only its endpoint is retained,
so later observations cannot revise past published burst features. Annual
growth uses an exact t−1 calendar join and is missing for zero origins or gaps.
The weights (repositories 0.5, questions 0.3, papers 0.2) are fixed conventions,
not empirically fitted commercial-value weights. CSI is diagnostic; the label
does not depend on future CSI values or a fitted full-sample threshold.

## Graph baseline

The current graph is a field-level growth-correlation graph. It is not a paper-level concept co-occurrence graph. Effective conductance is retained as a transparent graph feature/baseline.

A separate graph is built from each historical prefix. Positive Pearson edges
require correlation greater than 0.3 and at least three shared finite annual
changes. Gaps are not forward filled and infinite zero-origin growth is excluded.
Degree, maximum Adamic–Adar score over neighbors, and maximum two-hop effective
conductance describe this five-node graph. With so few nodes, graph features
provide a deliberately limited comparator, not proof of technology diffusion.

## Targets

The preferred target is:

P(Y_k(t+h) = 1 | X_t)

The implemented label is Y(t+2)=1 when (repos(t+2)/repos(t) − 1) ≥ 0.20.
The horizon and threshold are prespecified in `config.yaml`. Endpoints are
matched by exact calendar year, not the next available row. A missing future
endpoint or nonpositive starting count gives an unknown label. Unknown labels
are excluded from evaluation, including the final two years.

This is a GitHub engineering-activity proxy and should be replaced or complemented
with independently measured patent, funding, labor or market outcomes. GitHub
topic searches count surviving repositories with their current topic assignments;
they do not observe historical topic vintages, repository usage, or revenue.

## Evaluation

For each test year t, training rows have origin year < t and outcome year < t.
The strict inequality uses outcomes completed before the forecast year, with a
conservative gap for the two-year horizon. Require at least five distinct training
years, eight labeled training rows, and both classes in training. Unknown labels
are never imputed. Test folds can contain one class: ROC-AUC is then undefined;
average precision is undefined when no positives are observed; Brier score remains
available. All models use the same eligible folds.

Logistic regression has fixed C=1, no class reweighting, and training-only standard
scaling. Missing/infinite feature values are replaced with the fixed value zero,
never a statistic estimated from test data. No hyperparameter or target threshold
is selected on these folds. Comparators are the global training positive rate,
the last observable field-specific label (falling back to the global rate), and
logistic regression restricted to graph features. Research-only and adoption-only
logistic models are prespecified ablations. Brier differences compare each model
with the global rate on paired annual folds; negative differences favor the model.

Report ROC-AUC, average precision (the `pr_auc` column is average precision, not
trapezoidal PR area), Brier score, five fixed calibration bins, and prediction
counts. Means weight eligible annual folds equally. Confidence intervals are
descriptive 95% circular moving-block bootstrap intervals with 2,000 resamples,
seed 20260918, and block length ceil(sqrt(number of finite annual fold scores)).
With few folds these intervals are unstable and cannot establish significance.

Twenty seeded within-year label permutations preserve annual positive totals and
censored positions, then refit the entire model on the same rules. They test
alignment across fields conditional on annual class prevalence. They do not test
all temporal structure, commercialization validity, or the source-query taxonomy.
Null mean Brier scores and their empirical quantiles are descriptive diagnostics;
no automatic hypothesis-test conclusion is made.

## Coverage, provenance, and reproducibility

The configured window contains 90 field-year units: five domains over 2008–2025.
Each configured OpenAlex query, GitHub topic, and Stack Overflow tag is also stored
separately by year with source, metric, retrieval timestamp, and response SHA-256.
Coverage reports show query counts, nonzero-query counts, and match sums by field,
source and year. Overlapping queries can count an entity more than once, including
across domains. Aggregates are query-match sums, not deduplicated entity totals;
source rows are not independent forecasting observations. Broad OpenAlex full-text
searches have not been validated as precise domain-membership classifiers.

Adapters require expected response fields, check OpenAlex group totals, reject
incomplete GitHub searches, honor Stack Exchange backoff, and retry transient
network/server failures with bounded attempts. A failed query aborts the run;
missing responses never become zeros. Successful responses are cached for resume
and archived as compressed JSON lines. API credentials are excluded from stored
parameters. The output manifest records checksums and UTC generation time.
CSV observations support offline deterministic feature/evaluation rebuilding.

Current API snapshots contain retrospective changes. The prefix algorithm avoids
mechanical future leakage, but does not remove source-vintage leakage. These runs
are retrospective snapshot backtests. Archive future vintages before claiming a
historically executable forecast, validate queries and domain assignment, acquire
independent commercialization outcomes, and expand domain/time coverage before
making strong empirical claims.

API semantics: [GitHub repository search](https://docs.github.com/en/rest/search/search#search-repositories)
and [Stack Exchange filters](https://api.stackexchange.com/docs/filters).

## Agent boundary

Human controls taxonomy, sources, outcome definitions, inclusion/exclusion rules, evaluation splits and publication decisions. LLMs may assist annotation, entity resolution and drafting. They may not change labels after observing outcomes or decide significance.
