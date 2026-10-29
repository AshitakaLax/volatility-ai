# Quantum Annealing Optimal Execution Trajectory Solver

**Ledger ID RK420** · rank 420 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-29

| | |
|---|---|
| Family | Quantum optimization / Execution |
| Potential effectiveness rank | 420 (1 = strongest) |
| AI implementability rank | 380 (1 = easiest) |
| Retail advantage rank | 8,379 (1 = strongest) |
| Fit with this project | ⛔ (large-order execution; hardware-limited) |
| Implemented in volatility-ai | **Research code** in `research.catalog.quantum`: `annealed_execution`, `execution_qubo`; tested on synthetic data, not wired into the engine. The classical Almgren-Chriss path is research code (RK366). |
| Related ledger entries | RK366, RK229, RK305 |

## In one paragraph

Encode the liquidation trajectory, with market impact and timing risk,
as a QUBO and solve it on a quantum annealer. It was done early: a
D-Wave formulation of multi-period portfolio trading with permanent and
temporary impact found the optimum with high success rates for small
instances, and the authors note the hardware caps the problem size.
Classical solvers handle the continuous problem in closed form. The
CSV's reference, arXiv 2103.01234, is a black-hole physics paper
("Hidden Symmetry of Vanishing Love"), unrelated to trading.

## Evidence

* **Rosenberg, Haghnegahdar, Goddard, Carr, Wu & López de Prado (2016),
  "Solving the Optimal Trading Trajectory Problem Using a Quantum
  Annealer," *IEEE J. Selected Topics in Signal Processing* 10(6),
  1053–1060 (arXiv 1508.06182):** D-Wave solves a discrete multi-period
  problem with impact costs at high success rates on small instances;
  hardware limits the size. (Abstract.)
* **Almgren & Chriss (2001):** the mean-variance optimal liquidation
  path; TWAP at zero risk aversion (see RK366).

## Against, and failure modes

* The continuous problem has a closed form (RK366); discretisation makes
  it harder, not better.

## Fit with volatility-ai

The grid's orders are small against TQQQ's daily volume, price-triggered
and single-venue; there is no parent order to schedule and no impact
worth modelling.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Rosenberg, G., Haghnegahdar, P., Goddard, P., Carr, P., Wu, K., López
  de Prado, M. (2016). *IEEE JSTSP* 10(6), 1053–1060.
  <https://arxiv.org/abs/1508.06182>. Abstract.
* Almgren, R., Chriss, N. (2001). *Journal of Risk* 3(2), 5–39. Standard
  reference.
