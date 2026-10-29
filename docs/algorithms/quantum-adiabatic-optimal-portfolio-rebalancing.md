# Quantum Adiabatic Optimal Portfolio Rebalancing

**Ledger ID RK229** · rank 229 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Quantum computing / Adiabatic evolution / Portfolio optimization |
| Potential effectiveness rank | 229 (1 = strongest) |
| AI implementability rank | 259 (1 = easiest) |
| Retail advantage rank | 241 (1 = strongest) |
| Fit with this project | ⛔ (no portfolio problem to solve here) |
| Implemented in volatility-ai | **Research code** in `research.catalog.quantum`: `rebalance_qubo`, `adiabatic_evolution`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK223, RK236, RK238 |

## In one paragraph

Write portfolio rebalancing with transaction costs as a quadratic
unconstrained binary optimisation (QUBO) and solve it on a quantum
annealer. It has been tried: a D-Wave hybrid annealer solved dynamic
portfolio problems on real data, and optimal trading trajectories were
posed on early annealers. None of the abstracts claims an advantage over
classical optimisation. The CSV's reference, arXiv 2103.01234, is a
black-hole physics paper ("Hidden Symmetry of Vanishing Love"),
unrelated to trading.

## The rule

```text
binary x_(i,t,k) = holding level k of asset i at time t
H = - returns' x + gamma x' Sigma x + costs(turnover) + penalty (sum x - budget)^2  -> anneal to the ground state
```

## Evidence

* **Mugel et al. (2022), "Dynamic portfolio optimization with real
  datasets using quantum processors and quantum-inspired tensor
  networks," *Physical Review Research* 4(1), 013006:** 52 assets, eight
  years of daily prices; classical solvers, D-Wave hybrid annealing, two
  VQE variants on IBM hardware and a tensor-network optimiser compared
  on Sharpe ratio, profit and time; the hybrid annealer and tensor
  networks handled the largest instances (up to 1,272 fully connected
  qubits as a demonstration). (Abstract.)
* **Rosenberg et al. (2016), "Solving the optimal trading trajectory
  problem using a quantum annealer" (IEEE J. Selected Topics in Signal
  Processing):** an early annealer formulation. (Standard reference; not
  re-checked here.)

## Against, and failure modes

* Penalty weights, discretisation and noise; classical heuristics solve
  the same QUBOs.

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
* Rosenberg, G., et al. (2016). IEEE J-STSP. Not re-checked.
