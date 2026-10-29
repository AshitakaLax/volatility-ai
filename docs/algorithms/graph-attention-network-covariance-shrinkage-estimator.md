# Graph Attention Network Covariance Shrinkage Estimator

**Ledger ID RK232** · rank 232 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Graph neural networks / Covariance estimation / Portfolio construction |
| Potential effectiveness rank | 232 (1 = strongest) |
| AI implementability rank | 181 (1 = easiest) |
| Retail advantage rank | 170 (1 = strongest) |
| Fit with this project | ⛔ (multi-asset allocator; thin evidence) |
| Implemented in volatility-ai | **Research code** in `research.catalog.spd_covariance`: `GATShrinkage`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK235, RK267, RK237 |

## In one paragraph

Run a graph attention network over the asset correlation graph to
produce a nonlinearly shrunk covariance matrix for Markowitz
optimisation. Shrinkage (Ledoit–Wolf) and eigenvalue clipping from
random matrix theory are the classical answers to noisy covariance
matrices. GNN versions exist only as a thesis and an arXiv comparison
that I could not read. The CSV's reference, arXiv 2103.01234, is a
black-hole physics paper ("Hidden Symmetry of Vanishing Love"),
unrelated to trading.

## Evidence

* **Korangi, Mues & Bravo (2024), "Large-scale Time-Varying Portfolio
  Optimisation using Graph Attention Networks" (arXiv 2407.15532):** a
  GAT over a distance-correlation graph outputs weights directly,
  trained on a Sharpe-ratio loss; it does not estimate a covariance.
  (Abstract.)
* A comparative evaluation of deep portfolio methods (arXiv 2604.24486)
  includes a GNN covariance estimator inside Markowitz, and a 2026
  Politecnico di Torino thesis uses GNNs to clean empirical covariance
  matrices. (Summaries; not read.)
* **Ledoit & Wolf:** linear (2004) and nonlinear (2017, *Review of
  Financial Studies*) shrinkage of the covariance matrix are the
  standard baselines any new estimator has to beat. (Standard
  references; not re-checked here.)

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

* Korangi, K., Mues, C., Bravo, C. (2024).
  <https://arxiv.org/abs/2407.15532>. Abstract.
* Ledoit, O., Wolf, M. (2017). "Nonlinear Shrinkage of the Covariance
  Matrix for Portfolio Selection: Markowitz Meets Goldilocks." *Review
  of Financial Studies* 30(12). Not re-checked.
