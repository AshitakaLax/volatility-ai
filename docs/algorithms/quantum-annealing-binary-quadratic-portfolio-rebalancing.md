# Quantum Annealing Binary Quadratic Portfolio Rebalancing

**Ledger ID RK305** · rank 305 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Quantum computing / Quadratic programming / Portfolio optimization |
| Potential effectiveness rank | 305 (1 = strongest) |
| AI implementability rank | 260 (1 = easiest) |
| Retail advantage rank | 242 (1 = strongest) |
| Fit with this project | ⛔ (no portfolio problem to solve here) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK229, RK389, RK223 |

## In one paragraph

Pose rebalancing as a binary quadratic (QUBO) problem and solve it on a
quantum annealer. This duplicates RK229: it has been done on real data
with D-Wave hybrid solvers, without a claimed advantage over classical
methods. The CSV's reference, arXiv 2103.01234, looks like a placeholder
ID (sequential digits, like arXiv 1908.01234 on RK97) and could not be
identified.

## Evidence

* **Mugel et al. (2022), *Physical Review Research* 4(1), 013006:** 52
  assets over eight years; classical solvers, D-Wave hybrid annealing,
  VQE on IBM hardware and tensor networks compared; the hybrid annealer
  and tensor networks handled the largest instances, with no shown
  advantage over classical optimisation (see RK223, RK229). (Abstract.)
* **Herman et al. (2023), "Quantum computing for finance," *Nature
  Reviews Physics* 5, 450–465:** quantum Monte Carlo integration and
  gradient estimation offer up to a quadratic speed-up in principle, but
  the resources needed must fall a long way before any practical
  advantage; quantum machine learning carries its general strengths and
  difficulties over to finance. (Abstract and key points.)

## Against, and failure modes

* Penalty tuning and noise; classical heuristics solve the same QUBOs.

## Fit with volatility-ai

This book trades one instrument; it has no combinatorial portfolio
problem.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Mugel, S., et al. (2022). *Physical Review Research* 4(1), 013006.
  <https://arxiv.org/abs/2007.00017>. Abstract.
* Herman, D., et al. (2023). "Quantum computing for finance." *Nature
  Reviews Physics* 5, 450–465. doi:10.1038/s42254-023-00603-1.
  <https://arxiv.org/abs/2307.11230>. Abstract.
