# Neural Operator Functional Gradient Boosting Cross-Sectional Alpha

**Ledger ID RK326** · rank 326 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Neural operators / Functional data analysis / Quantitative equity |
| Potential effectiveness rank | 326 (1 = strongest) |
| AI implementability rank | 319 (1 = easiest) |
| Retail advantage rank | 172 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **Research code** in `research.catalog.cross_section`: `operator_boosting`, `spectral_features`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK390, RK287 |

## In one paragraph

Treat each stock's return history as a function, map it to forecasts
with a neural operator, and combine operators by gradient boosting.
Fourier neural operators (the CSV's reference, arXiv 2010.08895, is the
real FNO paper) learn maps between function spaces for partial
differential equations. I found no cross-sectional alpha study.

## Evidence

* **Li et al. (2021), "Fourier Neural Operator for Parametric Partial
  Differential Equations," ICLR (arXiv 2010.08895):** the operator
  class, for PDEs. (Standard reference.)
* **No alpha study found.**

## Against, and failure modes

* A PDE tool applied to noisy return series with no physics to learn.

## Fit with volatility-ai

A cross-sectional stock-selection model; this project trades one
leveraged index ETF and has no stock universe, fundamentals or relation
data.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Li, Z., et al. (2021). "Fourier Neural Operator for Parametric Partial
  Differential Equations." ICLR. <https://arxiv.org/abs/2010.08895>.
