# Graph Attention Network Riemannian Manifold Covariance Shrinkage

**Ledger ID RK400** · rank 400 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Graph neural networks / Riemannian geometry / Covariance estimation |
| Potential effectiveness rank | 400 (1 = strongest) |
| AI implementability rank | 270 (1 = easiest) |
| Retail advantage rank | 175 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK232, RK237, RK396 |

## In one paragraph

Shrink covariance matrices with graph attention while keeping them on
the positive-definite manifold. Shrinkage (Ledoit-Wolf) is the baseline.
GNN covariance estimators appear only in work I could not read (RK232),
and I found nothing for this combination.

## Evidence

* **Ledoit & Wolf:** linear (2004) and nonlinear (2017) shrinkage are
  the baselines a new covariance estimator must beat (see RK232).
* **GNN covariance estimators** appear only in an arXiv comparison
  (2604.24486) and a 2026 Politecnico di Torino thesis, neither read
  (see RK232).

## Against, and failure modes

* A learned estimator must beat nonlinear shrinkage out of sample;
  nothing verified shows it does.

## Fit with volatility-ai

An allocator for a multi-asset book; the engine trades one symbol and
the allocator in ledger §11 is not built. Without published evidence, it
is not a candidate.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Ledoit, O., Wolf, M. (2017). "Nonlinear Shrinkage of the Covariance
  Matrix for Portfolio Selection." *Review of Financial Studies* 30(12).
  Not re-checked.
