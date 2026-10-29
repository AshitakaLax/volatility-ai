# Generative Moment Matching Network (GMMN) Portfolio Simulator

**Ledger ID RK373** · rank 373 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Generative Machine Learning / Portfolio Stress Testing |
| Potential effectiveness rank | 373 (1 = strongest) |
| AI implementability rank | 215 (1 = easiest) |
| Retail advantage rank | 166 (1 = strongest) |
| Fit with this project | ⏳ as a stress-test sampler · not a strategy |
| Implemented in volatility-ai | **Research code** in `research.catalog.generative`: `GMMN`, `mmd2`, `expected_shortfall`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK349, RK200, RK53 |

## In one paragraph

A generative moment matching network maps uniform noise to samples by
minimising the maximum mean discrepancy to the data, a simpler objective
than a GAN's. In risk management it can turn a quasi-random point set
into samples from a fitted multivariate (copula) model, giving
lower-variance estimates of tail measures such as expected shortfall
than plain Monte Carlo.

## Evidence

* **Li, Swersky & Zemel (2015), "Generative Moment Matching Networks,"
  ICML (arXiv 1502.02761, the CSV's reference):** the method. (Standard
  reference.)
* **Hofert, Prasad & Zhu (2021), "Quasi-random sampling for multivariate
  distributions via generative neural networks," *Journal of
  Computational and Graphical Statistics*:** GMMNs fed with randomized
  quasi-Monte Carlo points sample from models with any copula, with
  variance reduction; examples include expected shortfall of sums of
  dependent risks. (Abstract.)

## Against, and failure modes

* A generator fitted to the sample cannot produce a dependence structure
  the sample lacks.

## Fit with volatility-ai

As a stress-testing tool (RK200): synthetic crash paths would show how
lots accumulate and how the regime exit behaves beyond the few real
drawdowns. A block bootstrap of real TQQQ returns is the cheaper first
step, and any generator must be validated on statistics it was not
trained to match.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Li, Y., Swersky, K., Zemel, R. (2015). ICML.
  <https://arxiv.org/abs/1502.02761>.
* Hofert, M., Prasad, A., Zhu, M. (2021). *JCGS*.
  <https://arxiv.org/abs/1811.00683>. Abstract.
