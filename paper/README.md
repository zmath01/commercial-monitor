# arXiv submission package

main.tex is the manuscript source.

Build locally:

    latexmk -pdf -interaction=nonstopmode main.tex

The manuscript is a methodology/software paper at this stage. It deliberately does not invent empirical results. After the maintainer runs the live workflow, the results section should be extended with exact temporal splits, confidence intervals, ablations, null tests, and source-coverage diagnostics.

For arXiv submission, upload the TeX source package and verify that all referenced files are included. The generated PDF is produced by the repository workflow so that it is compiled from the same source reviewed in Git.
