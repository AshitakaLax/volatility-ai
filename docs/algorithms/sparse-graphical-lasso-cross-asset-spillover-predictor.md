# Sparse Graphical Lasso Cross-Asset Spillover Predictor

**Ledger ID RK109** · rank 109 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Graphical models / Econometrics / Risk management |
| Potential effectiveness rank | 109 (1 = strongest) |
| AI implementability rank | 64 (1 = easiest) |
| Retail advantage rank | 145 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** A multi-asset risk-network estimator with no forecasting evidence for trading. |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK262, RK264 |

## In one paragraph

Estimate a sparse precision matrix of asset returns with the graphical
lasso and read the resulting conditional-dependence network as a map of
spillovers. Sparse network methods are used to rank systemic firms
(Barigozzi and Hallin); I found no study showing glasso networks
forecast returns or volatility well enough to trade, and the CSV's
reference, arXiv 1910.01234, could not be identified.

## Evidence

* **Barigozzi & Hallin (2017), *JRSS-C* 66(3):** sparse VAR networks of
  volatility, after removing common shocks, identify financial firms as
  contagion sources in 2007–2008; they warn penalised estimates are
  unstable under collinearity. (Abstract.)
* **Graph-based volatility forecasting** finds mixed gains: multi-hop
  spillovers add little; nonlinear spillovers help at horizons up to a
  week (arXiv 2410.22706). (Abstract.)

## Against, and failure modes

* The network changes with the penalty and the window; with one traded
  instrument there is nothing to allocate across.

## Fit with volatility-ai

A portfolio-construction rule for a multi-asset book. The engine trades
one symbol and the multi-asset allocator in ledger §11 is not built; it
becomes relevant only if a multi-ETF book is added (as X2/X3 explore).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Barigozzi, M., Hallin, M. (2017). A network analysis of the volatility
  of high dimensional financial series. *JRSS Series C* 66(3), 581–605.
  Abstract.
* Graph Signal Processing for Global Stock Market Realized Volatility
  Forecasting. <https://arxiv.org/abs/2410.22706>. Abstract.
* The CSV's reference, arXiv 1910.01234 (not identified).
