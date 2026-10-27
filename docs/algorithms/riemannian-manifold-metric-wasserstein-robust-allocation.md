# Riemannian Manifold Metric Wasserstein Robust Allocation

**Ledger ID RK233** · rank 233 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Geometric deep learning / Riemannian geometry / Robust portfolio allocation |
| Potential effectiveness rank | 233 (1 = strongest) |
| AI implementability rank | 248 (1 = easiest) |
| Retail advantage rank | 203 (1 = strongest) |
| Fit with this project | ⛔ (no evidence; multi-asset allocator) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK225, RK230, RK88 |

## In one paragraph

Combine a Wasserstein ambiguity set with Riemannian descent on the
covariance manifold for distributionally robust allocation. Portfolio
weights do not live on the SPD manifold; the covariance matrix does. A
Riemannian method can estimate or smooth the covariance, after which the
allocation is an ordinary optimisation. I found no study applying this
to portfolios. The CSV's reference, arXiv 2106.09876, looks like a
placeholder ID (like arXiv 1908.01234 on RK97) and could not be
identified.

## Evidence

* **No study found** applying Riemannian (SPD-manifold) optimisation to
  portfolio construction; SPD-manifold descent methods exist in general
  (e.g. Darmwal & Rajawat, arXiv 2305.02041, with covariance estimation
  as an application).
* **Ledoit & Wolf:** linear (2004) and nonlinear (2017, *Review of
  Financial Studies*) shrinkage of the covariance matrix are the
  standard baselines any new estimator has to beat. (Standard
  references; not re-checked here.)
* **Blanchet, Chen & Zhou (2022), "Distributionally Robust Mean-Variance
  Portfolio Selection with Wasserstein Distances," *Management Science*
  68(9), 6382–6410:** the robust problem reduces to empirical variance
  minimisation plus a regularisation term, with the ambiguity radius and
  robust target return chosen from data; S&P 500 back-tests against
  Fama-French and Black-Litterman benchmarks. (Abstract.)

## Against, and failure modes

* Geometry-aware estimation must still beat shrinkage out of sample; no
  study shows it.

## Fit with volatility-ai

An allocator for a multi-asset book; the engine trades one symbol and
the allocator in ledger §11 is not built. Without published evidence, it
is not a candidate.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Darmwal, Y., Rajawat, K. "Low-complexity subspace-descent over
  symmetric positive definite manifold."
  <https://arxiv.org/abs/2305.02041>. Abstract.
* Ledoit, O., Wolf, M. (2017). "Nonlinear Shrinkage of the Covariance
  Matrix for Portfolio Selection: Markowitz Meets Goldilocks." *Review
  of Financial Studies* 30(12). Not re-checked.
* Blanchet, J., Chen, L., Zhou, X. Y. (2022). *Management Science*
  68(9), 6382–6410.
  <https://ideas.repec.org/a/inm/ormnsc/v68y2022i9p6382-6410.html>.
  Abstract.
