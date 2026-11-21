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

arXiv categories, OpenAlex text queries, GitHub topics, and Stack Overflow tags
are source-specific mappings. The current data use the latter three sources.
Future entity-level observations can have multiple domain labels.

### Taxonomy audit

The five domains serve as a monitoring portfolio for computing, finance and
computational physical science. They mix methods, technology families and
application areas. Research fields for official R&D statistics can be represented
on a separate axis using OECD FORD.
[Frascati Manual, §2.42–2.45](https://www.oecd.org/content/dam/oecd/en/publications/reports/2015/10/frascati-manual-2015_g1g57dcb/9789264239012-en.pdf)

| Monitoring domain | Entity-level assignment rule | Main measurement risk |
| --- | --- | --- |
| Computer Systems & Engineering | The contribution concerns software systems, infrastructure, algorithms for systems, or computer engineering. | OpenAlex `computer science` covers work outside systems. AI infrastructure crosses both views. |
| AI & Applied Mathematics | Record separate AI/ML and computational mathematics tags. An application qualifies when it also contributes an AI or numerical method. | General `optimization` covers unrelated applications. The AI and numerical-methods trends can move differently. |
| Quantitative Finance | The objective includes financial modeling, pricing, portfolio or trading decisions, or financial risk. | `risk management` reaches beyond finance. A production financial-risk system may also qualify for FinTech. |
| FinTech & Digital Finance | The contribution concerns delivery or infrastructure for a digital financial service. | `mechanism design`, `electronic commerce`, `blockchain`, and broad arXiv `cs.GT` need financial context. |
| Computational Quantum & Matter | Record separate quantum computing, computational materials, and computational optics tags based on the technical contribution. | Broad physics and optics mappings include experimental and theoretical work outside the computational scope. Repository matches mainly show software-visible activity. |

For entity annotation, record the technical method and application context
independently. A quantum derivative-pricing library can have quantum algorithms
as the method, Quantitative Finance as the application and software as the
artifact. Cross-tags preserve this information. Compare series within a source
and query version, and use stable entity IDs for deduplication when aggregate
population estimates are needed.

The archived measurements use query version `1`. A future query revision should
publish both old and new definitions for a common window. Audit a stratified
sample of matches by source, domain and period with two independent reviewers,
report precision and agreement before adjudication, and use a separate reference
set containing nonmatches to estimate recall. Use entity IDs to estimate
cross-query and cross-domain overlap. The count-only archive supports measuring
query concentration. Precision, recall and overlap require entity-level data.
[Stanford IR, precision and recall](https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-unranked-retrieval-sets-1.html)

## Commercialization dimensions

For entity-level data, the artifact is the product of the work, such as software,
a model, hardware, a material, or a service. The pathway describes how it is made
available or used, such as an API, enterprise deployment, licensing, or manufacturing.
An evidence event records what was observed and when, such as a patent filing,
procurement award, or license agreement. A patent event can concern many artifact
types. The current count snapshot has no entity records to which these attributes
can be applied.

## Layer separation

Commercial Monitor distinguishes research emergence, technology/adoption, science-to-invention/IP translation, funding, labor, company formation, and market outcomes.

The first runnable release has practical API adapters for OpenAlex, GitHub and Stack Overflow. Downstream outcome layers are explicit schemas/targets so they can be added without redefining the research layer. Operationalize actual adoption with dated evidence of use, such as organization deployments. Commercial outcomes need an independent measure such as dated procurement or licensing. [OECD/Eurostat Oslo Manual, chapter 3](https://www.oecd.org/en/publications/2018/10/oslo-manual-2018_g1g9373b/full-report/component-9.html)

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
logistic regression restricted to graph features or GitHub features. Research-only
and adoption-only logistic models are ablations. `paired_brier.csv` compares
each model with the global rate on paired annual folds. `research_increment.csv`
compares GitHub plus Stack Overflow features with the same features plus direct
OpenAlex growth and standardized counts. The nested comparison excludes the
composite and graph features because they mix data sources. Negative Brier
differences favor the expanded model. Treat this comparison as exploratory on
the existing snapshot and freeze it before testing on new vintages.
[Rolling-origin evaluation](https://otexts.com/fpp3/tscv.html)

Report ROC-AUC, average precision (the `pr_auc` column is average precision, not
trapezoidal PR area), Brier score, five fixed calibration bins, and prediction
counts. Means weight eligible annual folds equally. Average precision equals
one in an all-positive fold by definition, which gives no evidence about
discrimination in that fold. Brier score assesses the probability forecasts
and calibration bins diagnose their agreement with observed rates. Intervals are
descriptive 95% circular moving-block bootstrap intervals with 2,000 resamples,
seed 20260918, and block length ceil(sqrt(number of finite annual fold scores)).
With few folds these intervals are unstable and cannot establish significance.

Twenty seeded within-year label permutations preserve annual positive totals and
censored positions, then refit the entire model on the same rules. They test
alignment across fields conditional on annual class prevalence. They do not test
all temporal structure, commercialization validity, or the source-query taxonomy.
Null mean Brier scores and their empirical quantiles are descriptive diagnostics;
no automatic hypothesis-test conclusion is made.

### What the current snapshot supports

The 2008–2025 panel has 90 domain-years and 73 labels. Evaluation uses 20
predictions in four annual folds (2020–2023). In 2021 all five test outcomes
are negative. In 2023 all five are positive. The full model assigned 19 of 20
predictions to the 0.8–1 probability bin. Their mean probability is 93.2%
and their observed rate is 42.1%.

Adding OpenAlex reduces mean Brier from 0.500 to 0.486 on the same four
folds. The paired change is −0.014 with a descriptive 95% interval of
[−0.040, +0.012]. The direction varies by year, and the sample leaves
predictive improvement unresolved. These data provide no independent evidence
about commercialization outcomes.

## Coverage, provenance, and reproducibility

The configured window contains 90 field-year units: five domains over 2008–2025.
Each configured OpenAlex query, GitHub topic, and Stack Overflow tag is also stored
separately by year with source, metric, retrieval timestamp, and response SHA-256.
Coverage reports show query counts, nonzero-query counts, and match sums by field,
source and year. The dashboard shows each query's contribution and the share
of the largest query within each domain-source-year. For example, `risk management`
accounts for 78.5% of the 2025 Quantitative Finance OpenAlex query-match sum.
Overlapping queries can count an entity more than once, including
across domains. Aggregates are query-match sums, not deduplicated entity totals;
source rows are not independent forecasting observations. The OpenAlex adapter
filters by publication date and can return multiple work types. Its broad text
search provides an unvalidated activity proxy. [OpenAlex search semantics](https://help.openalex.org/api/searching/)

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

The sources document [GitHub repository search](https://docs.github.com/en/rest/search/search#search-repositories)
and [Stack Exchange filters](https://api.stackexchange.com/docs/filters).

## Agent boundary

Human controls taxonomy, sources, outcome definitions, inclusion/exclusion rules, evaluation splits and publication decisions. LLMs may assist annotation, entity resolution and drafting. They may not change labels after observing outcomes or decide significance.
