# Riemannian Manifold Metric Persistent Homology Risk Parity

**Ledger ID RK188** · rank 188 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Geometric deep learning / Riemannian geometry / Topological risk parity |
| Potential effectiveness rank | 188 (1 = strongest) |
| AI implementability rank | 186 (1 = easiest) |
| Retail advantage rank | 151 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** A multi-asset allocator combining two methods without a study. |
| Implemented in volatility-ai | **Research code** `research.catalog.spd_covariance`: `metric_diffusion_risk_parity`. |
| Related ledger entries | RK185, RK187 |

## In one paragraph

Combine topological clustering with Riemannian covariance optimisation
to build risk-parity portfolios. Neither ingredient has a risk-parity
study; together they have none.

## Evidence

* **No portfolio study found** of Riemannian (SPD-manifold) risk parity;
  HRP itself (A5) is built here, and the covariance matrix, not the
  weights, is what lives on the manifold (see RK230).
* **Goel, Pasricha & Mehra (2020), *Expert Systems with Applications*;
  Goel, Sharma & Kanniainen (2026, arXiv 2601.03974):**
  persistence-landscape risk measures used for enhanced indexing and
  portfolio selection beat several benchmarks in the authors' tests; the
  2026 paper is a preprint. (Abstracts.)
* **No study found** that tests this combination as a trading strategy.

## Against, and failure modes

* Two layers of free choices on one covariance estimate.

## Fit with volatility-ai

A portfolio-construction rule for a multi-asset book. The engine trades
one symbol and the multi-asset allocator in ledger §11 is not built; it
becomes relevant only if a multi-ETF book is added (as X2/X3 explore).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Goel, A., Pasricha, P., Mehra, A. (2020). Topological data analysis in
  investment decisions. *Expert Systems with Applications*. Abstract;
  Goel, A., Sharma, Kanniainen, J. (2026).
  <https://arxiv.org/abs/2601.03974>. Abstract.
