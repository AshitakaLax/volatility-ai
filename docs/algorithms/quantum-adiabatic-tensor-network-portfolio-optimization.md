# Quantum Adiabatic Tensor Network Portfolio Optimization

**Ledger ID RK238** · rank 238 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Quantum computing / Tensor networks / Portfolio optimization |
| Potential effectiveness rank | 238 (1 = strongest) |
| AI implementability rank | 221 (1 = easiest) |
| Retail advantage rank | 210 (1 = strongest) |
| Fit with this project | ⛔ (no evidence; no portfolio problem here) |
| Implemented in volatility-ai | **Research code** in `research.catalog.quantum`: `mps_portfolio`, `adiabatic_evolution`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK223, RK229 |

## In one paragraph

Combine matrix-product-state tensor networks with adiabatic quantum
evolution to solve large allocation problems. Mugel et al. tested tensor
networks and annealing side by side, not together; I found no study of
the combination. The CSV's reference, arXiv 2103.02345, could not be
identified.

## Evidence

* **Mugel et al. (2022), "Dynamic portfolio optimization with real
  datasets using quantum processors and quantum-inspired tensor
  networks," *Physical Review Research* 4(1), 013006:** 52 assets, eight
  years of daily prices; classical solvers, D-Wave hybrid annealing, two
  VQE variants on IBM hardware and a tensor-network optimiser compared
  on Sharpe ratio, profit and time; the hybrid annealer and tensor
  networks handled the largest instances (up to 1,272 fully connected
  qubits as a demonstration). (Abstract.)
* **No study found** of the combined method.

## Against, and failure modes

* No benchmark for the combination.

## Fit with volatility-ai

This book trades one instrument; it has no combinatorial portfolio
problem for a quantum solver, and none of these studies shows an
advantage over classical optimisation at a useful scale.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Mugel, S., et al. (2022). *Physical Review Research* 4(1), 013006.
  <https://arxiv.org/abs/2007.00017>. Abstract.
