# Scientific status

This repository is currently a **methodology + software release**, not a completed empirical study.

The committed data are live API count snapshots, not synthetic observations.
The configured historical panel is five domains over 2008–2025. Source-query-year
records preserve coverage and provenance but overlap and do not increase the
number of independent forecasting units.

The implemented research target is a prespecified two-year GitHub activity-growth
proxy, not an independent commercialization outcome. Features are causal with
respect to observation years; training excludes labels not yet available at the
forecast origin. Retrospective source revisions and topic assignments still
prevent a claim of a historically executable forecasting simulation.

The software now produces matched baselines, ablations, calibration, seeded
permutation diagnostics, and descriptive moving-block bootstrap intervals. No
significance or commercial predictive-validity claim follows automatically from
these outputs. Published metrics from the original median-threshold, full-window
feature implementation are superseded.

The published snapshot contains 1,512 source-query-year observations, 90
field-year units, and 73 labels with positive starting counts and observed
two-year endpoints. Only four test years (2020–2023), totaling 20 predictions,
meet the training-history and class-availability requirements. The larger
input audit trail therefore does not resolve the small evaluation sample.

Before treating any forecast as evidence, the maintainer should:

1. freeze the taxonomy and source queries;
2. run the deterministic test workflow;
3. run the live data workflow manually;
4. inspect coverage and API provenance;
5. execute temporal backtests and null/permutation tests;
6. add outcome-specific datasets, especially paper-patent linkage;
7. report exact train/test periods, missingness, ablations and confidence intervals;
8. only then update the arXiv manuscript with empirical results.

No investment recommendation or financial-return forecast is produced by the system.
