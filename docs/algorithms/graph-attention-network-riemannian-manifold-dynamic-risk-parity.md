# Graph Attention Network Riemannian Manifold Dynamic Risk Parity

**Ledger ID RK191** · rank 191 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Graph neural networks / Riemannian geometry / Risk parity |
| Potential effectiveness rank | 191 (1 = strongest) |
| AI implementability rank | 271 (1 = easiest) |
| Retail advantage rank | 115 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** A multi-asset allocator with no study. |
| Implemented in volatility-ai | **Research code** `research.catalog.spd_covariance`: `riemannian_gat_weights`. |
| Related ledger entries | RK232, RK237 |

## In one paragraph

Compute risk-parity weights with graph attention over asset relations on
the SPD manifold. GNN covariance estimators appear only in unread theses
and preprints (RK232); I found no risk-parity study.

## Evidence

* **No portfolio study found** of Riemannian (SPD-manifold) risk parity;
  HRP itself (A5) is built here, and the covariance matrix, not the
  weights, is what lives on the manifold (see RK230).
* **No study found** that tests this combination as a trading strategy.

## Against, and failure modes

* Attention weights trained on a few years of a handful of assets
  over-fit.

## Fit with volatility-ai

A portfolio-construction rule for a multi-asset book. The engine trades
one symbol and the multi-asset allocator in ledger §11 is not built; it
becomes relevant only if a multi-ETF book is added (as X2/X3 explore).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* See RK232 and RK230's references.
