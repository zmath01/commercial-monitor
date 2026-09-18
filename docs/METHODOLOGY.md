# Methodology

## Layer separation

Commercial Monitor distinguishes research emergence, technology/adoption, science-to-invention/IP translation, funding, labor, company formation, and market outcomes.

The first runnable release has practical API adapters for OpenAlex, GitHub and Stack Overflow. Downstream outcome layers are explicit schemas/targets so they can be added without redefining the research layer.

## Taxonomy

32 arXiv categories map to 14 research-backed domains. FinTech is a separate multi-source monitoring domain because arXiv has no dedicated FinTech category. cs.ET is classified as Emerging Hardware/Devices and is documented as broad and overlapping.

## Signals

Growth, z-scores, burst states, signal level and slope are transparent features. The composite signal is normalized within each field, so it is a historical-position proxy rather than an absolute commercial-size measure.

## Graph baseline

The current graph is a field-level growth-correlation graph. It is not a paper-level concept co-occurrence graph. Effective conductance is retained as a transparent graph feature/baseline.

## Targets

The preferred target is:

P(Y_k(t+h)=1 | X_t)

No feature from t+h or later may enter X_t. The initial target is deliberately generic and should be replaced by outcome-specific targets once patent, funding, labor or market datasets are integrated.

## Evaluation

Expanding-window evaluation is mandatory. Random splits are inappropriate for temporal forecasting. Report ROC-AUC, average precision, Brier score, calibration, coverage, ablations, and null tests.

## Agent boundary

Human controls taxonomy, sources, outcome definitions, inclusion/exclusion rules, evaluation splits and publication decisions. LLMs may assist annotation, entity resolution and drafting. They may not change labels after observing outcomes or decide significance.
