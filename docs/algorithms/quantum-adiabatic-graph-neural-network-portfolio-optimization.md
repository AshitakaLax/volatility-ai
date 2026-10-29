# Quantum Adiabatic Graph Neural Network Portfolio Optimization

**Ledger ID RK236** · rank 236 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Quantum computing / Graph neural networks / Portfolio optimization |
| Potential effectiveness rank | 236 (1 = strongest) |
| AI implementability rank | 342 (1 = easiest) |
| Retail advantage rank | 292 (1 = strongest) |
| Fit with this project | ⛔ (no evidence; no portfolio problem here) |
| Implemented in volatility-ai | **Research code** in `research.catalog.quantum`: `gnn_adiabatic_portfolio`, `sgc_scores`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK229, RK232 |

## In one paragraph

Encode graph-neural-network embeddings of asset relationships into the
Hamiltonian of a quantum annealing problem for constrained portfolio
selection. Each half exists (GNN portfolio models; annealer QUBOs); I
found no study combining them.

## Evidence

* **Mugel et al. (2022), "Dynamic portfolio optimization with real
  datasets using quantum processors and quantum-inspired tensor
  networks," *Physical Review Research* 4(1), 013006:** 52 assets, eight
  years of daily prices; classical solvers, D-Wave hybrid annealing, two
  VQE variants on IBM hardware and a tensor-network optimiser compared
  on Sharpe ratio, profit and time; the hybrid annealer and tensor
  networks handled the largest instances (up to 1,272 fully connected
  qubits as a demonstration). (Abstract.)
* **Korangi, Mues & Bravo (2024), "Large-scale Time-Varying Portfolio
  Optimisation using Graph Attention Networks" (arXiv 2407.15532):** a
  GAT over a distance-correlation graph outputs weights directly,
  trained on a Sharpe-ratio loss; it does not estimate a covariance.
  (Abstract.)
* **No study found** combining GNN embeddings with annealing
  Hamiltonians.

## Against, and failure modes

* Two immature components stacked; no benchmark.

## Fit with volatility-ai

This book trades one instrument; it has no combinatorial portfolio
problem for a quantum solver, and none of these studies shows an
advantage over classical optimisation at a useful scale.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Mugel, S., et al. (2022). *Physical Review Research* 4(1), 013006.
  <https://arxiv.org/abs/2007.00017>. Abstract.
* Korangi, K., Mues, C., Bravo, C. (2024).
  <https://arxiv.org/abs/2407.15532>. Abstract.
