# Quantum Tensor Network Portfolio Optimization

**Ledger ID RK223** · rank 223 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Quantum computing / Tensor networks / Portfolio optimization |
| Potential effectiveness rank | 223 (1 = strongest) |
| AI implementability rank | 257 (1 = easiest) |
| Retail advantage rank | 239 (1 = strongest) |
| Fit with this project | ⛔ (no portfolio problem to solve here) |
| Implemented in volatility-ai | **Research code** in `research.catalog.quantum`: `mps_portfolio`, `mps_minimize`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK238, RK229, RK236 |

## In one paragraph

Represent a high-dimensional portfolio optimisation as a matrix product
state and solve it with tensor-network contractions, a quantum-inspired
method that runs on classical hardware. One study tested it alongside
quantum annealers and VQE on 52 assets; the tensor networks and the
hybrid annealer handled the largest instances. The CSV's reference,
arXiv 2103.02345, could not be identified.

## Evidence

* **Mugel et al. (2022), "Dynamic portfolio optimization with real
  datasets using quantum processors and quantum-inspired tensor
  networks," *Physical Review Research* 4(1), 013006:** 52 assets, eight
  years of daily prices; classical solvers, D-Wave hybrid annealing, two
  VQE variants on IBM hardware and a tensor-network optimiser compared
  on Sharpe ratio, profit and time; the hybrid annealer and tensor
  networks handled the largest instances (up to 1,272 fully connected
  qubits as a demonstration). (Abstract.)
* **Brandhofer et al. (2022), "Benchmarking the performance of portfolio
  optimization with QAOA," *Quantum Information Processing* (arXiv
  2207.10555):** cardinality-constrained portfolio selection as a QUBO;
  studies variational forms, optimisers, shot noise and hardware errors.
  The abstract claims no advantage over classical solvers. (Abstract.)

## Against, and failure modes

* Problem sizes that need these methods are far beyond a
  single-instrument book; classical solvers remain the benchmark.

## Fit with volatility-ai

This book trades one instrument; it has no combinatorial portfolio
problem for a quantum solver, and none of these studies shows an
advantage over classical optimisation at a useful scale.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Brandhofer, S., et al. (2022). *Quantum Information Processing*.
  <https://arxiv.org/abs/2207.10555>. Abstract.
* Mugel, S., et al. (2022). *Physical Review Research* 4(1), 013006.
  <https://arxiv.org/abs/2007.00017>. Abstract.
* The CSV's references: TeNPy; arXiv 2103.02345 (not identified).
