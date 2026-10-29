# Quantum Annealing Entropic Value-at-Risk Portfolio Optimization

**Ledger ID RK389** · rank 389 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Quantum computing / Tail risk optimization |
| Potential effectiveness rank | 389 (1 = strongest) |
| AI implementability rank | 346 (1 = easiest) |
| Retail advantage rank | 231 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK305, RK53 |

## In one paragraph

Minimise entropic value-at-risk, a coherent tail-risk measure tighter
than CVaR, with a quantum annealer. EVaR is a sound risk measure; I
found no quantum EVaR study, and the CSV's reference, arXiv 2103.01234,
is a black-hole physics paper ("Hidden Symmetry of Vanishing Love"),
unrelated to trading.

## Evidence

* **Ahmadi-Javid (2012), "Entropic value-at-risk," *Journal of
  Optimization Theory and Applications* 155:** the measure. (Standard
  reference; not re-checked here.)
* **Mugel et al. (2022), *Physical Review Research* 4(1), 013006:** 52
  assets over eight years; classical solvers, D-Wave hybrid annealing,
  VQE on IBM hardware and tensor networks compared; the hybrid annealer
  and tensor networks handled the largest instances, with no shown
  advantage over classical optimisation (see RK223, RK229). (Abstract.)

## Against, and failure modes

* EVaR is convex and solves classically; nothing calls for an annealer.

## Fit with volatility-ai

This book trades one instrument; it has no combinatorial portfolio
problem.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Ahmadi-Javid, A. (2012). *JOTA* 155. Not re-checked.
* Mugel, S., et al. (2022). *Physical Review Research* 4(1), 013006.
  <https://arxiv.org/abs/2007.00017>. Abstract.
