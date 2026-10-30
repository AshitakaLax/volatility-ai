# Quantum Approximate Optimization Algorithm (QAOA) Allocation

**Ledger ID RK175** · rank 175 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Quantum computing / Portfolio optimization |
| Potential effectiveness rank | 175 (1 = strongest) |
| AI implementability rank | 219 (1 = easiest) |
| Retail advantage rank | 183 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** A quantum solver for an allocation problem this book does not have, with no shown advantage. |
| Implemented in volatility-ai | **Research code** `research.catalog.quantum`: `qaoa`, `portfolio_qubo`. |
| Related ledger entries | RK229, RK305 |

## In one paragraph

Map asset selection to a QUBO and solve it with the quantum approximate
optimisation algorithm. Benchmarks study circuit and optimiser choices
on toy portfolios under noise; none shows an advantage over classical
solvers.

## Evidence

* **No quantum advantage for portfolio problems** has been shown: QAOA
  benchmarks (Brandhofer et al. 2023, *Quantum Information Processing*)
  study circuit choices and noise on toy portfolios. (Abstract.)
* **This repository:** `quantum.qaoa`, `portfolio_qubo` (exact
  simulation).

## Against, and failure modes

* Toy sizes only; classical solvers find the same answers.

## Fit with volatility-ai

A portfolio-construction rule for a multi-asset book. The engine trades
one symbol and the multi-asset allocator in ledger §11 is not built; it
becomes relevant only if a multi-ETF book is added (as X2/X3 explore).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Brandhofer, S. et al. (2023). Benchmarking the performance of
  portfolio optimization with QAOA. *Quantum Information Processing* 22.
  <https://arxiv.org/abs/2207.10555>. Abstract.
