# Riemannian Manifold Metric Diffusion Portfolio Allocation

**Ledger ID RK231** · rank 231 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Geometric deep learning / Riemannian geometry / Portfolio allocation |
| Potential effectiveness rank | 231 (1 = strongest) |
| AI implementability rank | 266 (1 = easiest) |
| Retail advantage rank | 197 (1 = strongest) |
| Fit with this project | ⛔ (no evidence; multi-asset allocator) |
| Implemented in volatility-ai | **Research code** in `research.catalog.spd_covariance`: `metric_diffusion_risk_parity`, `geodesic_smoothed_covariances`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK230, RK60 |

## In one paragraph

Diffuse covariance estimates along the SPD manifold's geometry so
risk-parity weights evolve smoothly through the cycle. Portfolio weights
do not live on the SPD manifold; the covariance matrix does. A
Riemannian method can estimate or smooth the covariance, after which the
allocation is an ordinary optimisation. I found no study applying this
to portfolios. The CSV's reference, arXiv 2106.09876, is a general graph
anomaly-detection paper ("Anomaly Detection in Dynamic Graphs via
Transformer"), not a finance one.

## Evidence

* **No study found** applying Riemannian (SPD-manifold) optimisation to
  portfolio construction; SPD-manifold descent methods exist in general
  (e.g. Darmwal & Rajawat, arXiv 2305.02041, with covariance estimation
  as an application).
* **Ledoit & Wolf:** linear (2004) and nonlinear (2017, *Review of
  Financial Studies*) shrinkage of the covariance matrix are the
  standard baselines any new estimator has to beat. (Standard
  references; not re-checked here.)
* Risk parity itself is documented on RK60.

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
