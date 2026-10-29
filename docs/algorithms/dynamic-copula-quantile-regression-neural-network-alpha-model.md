# Dynamic Copula-Quantile Regression Neural Network Alpha Model

**Ledger ID RK388** · rank 388 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Econometric copulas / Quantile regression / Deep learning |
| Potential effectiveness rank | 388 (1 = strongest) |
| AI implementability rank | 243 (1 = easiest) |
| Retail advantage rank | 167 (1 = strongest) |
| Fit with this project | ⛔ (stock-level alpha) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK296, RK94 |

## In one paragraph

Forecast each stock's full return distribution with quantile neural
networks and tie the margins together with a dynamic copula to rank
stocks. Quantile networks for return distributions have recent support:
across US and international markets, the means and variances they imply
beat standard models out of sample. I found no study adding the copula
layer for alpha, and the CSV's reference, arXiv 2001.05432, looks like a
placeholder ID (sequential digits, like arXiv 1908.01234 on RK97) and
could not be identified.

## Evidence

* **Baruník, Hronec & Tobek, "Forecasting stock return distributions
  around the globe with quantile neural networks" (arXiv 2408.07497):**
  two-stage quantile network with spline interpolation; significantly
  better out-of-sample mean and variance forecasts than standard models
  in US and international markets. No copula. (Abstract.)
* **No study found** combining quantile networks with a copula for
  alpha.

## Against, and failure modes

* The copula layer adds estimation error that a ranking does not need.

## Fit with volatility-ai

A cross-sectional stock-selection model; this project trades one
leveraged index ETF and has no stock universe, fundamentals or relation
data.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Baruník, J., Hronec, M., Tobek, O. "Forecasting stock return
  distributions around the globe with quantile neural networks."
  <https://arxiv.org/abs/2408.07497>. Abstract.
