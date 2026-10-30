# Riemannian Manifold Metric Hierarchical Risk Parity

**Ledger ID RK185** · rank 185 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Geometric deep learning / Riemannian geometry / Portfolio construction |
| Potential effectiveness rank | 185 (1 = strongest) |
| AI implementability rank | 249 (1 = easiest) |
| Retail advantage rank | 205 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** A multi-asset allocator; HRP is built and the Riemannian variant has no study. |
| Implemented in volatility-ai | **Research code** `research.strategies.hrp`: `hrp_weights`; `research.catalog.spd_covariance`: `karcher_mean`. |
| Related ledger entries | A5, RK230, RK21 |

## In one paragraph

Cluster and allocate hierarchical risk parity on the SPD manifold of
covariance matrices. No portfolio study was found of Riemannian
(SPD-manifold) risk parity; HRP itself (A5) is built here, and the
covariance matrix, not the weights, is what lives on the manifold (see
RK230).

## Evidence

* **No portfolio study found** of Riemannian (SPD-manifold) risk parity;
  HRP itself (A5) is built here, and the covariance matrix, not the
  weights, is what lives on the manifold (see RK230).

## Against, and failure modes

* Manifold distances change the dendrogram, not the estimation error
  that HRP is meant to control.

## Fit with volatility-ai

A portfolio-construction rule for a multi-asset book. The engine trades
one symbol and the multi-asset allocator in ledger §11 is not built; it
becomes relevant only if a multi-ETF book is added (as X2/X3 explore).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* See RK230's references.
* The CSV's reference, arXiv 2106.09876 (graph anomaly detection; not
  finance).
