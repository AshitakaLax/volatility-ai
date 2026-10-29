# Quantum Annealing Graph Neural Network Covariance Shrinkage

**Ledger ID RK397** · rank 397 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Quantum computing / Graph neural networks / Covariance estimation |
| Potential effectiveness rank | 397 (1 = strongest) |
| AI implementability rank | 343 (1 = easiest) |
| Retail advantage rank | 294 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **Research code** in `research.catalog.quantum`: `covariance_mask_qubo`, `masked_covariance`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK232, RK236 |

## In one paragraph

Choose covariance shrinkage targets with a graph neural network and
optimise them on a quantum annealer. Shrinkage (Ledoit-Wolf) is the
baseline. GNN covariance estimators appear only in work I could not read
(RK232), and I found nothing for this combination.

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
