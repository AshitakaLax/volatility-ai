# Koopman-operator-based approach to quantum-circuit or quantum-inspired optimization

**Concept page** · shared by **10** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,769) ·
researched 2026-10-30

| | |
|---|---|
| Task | Quantum-circuit or quantum-inspired optimisation |
| Method | Koopman operators (DMD / EDMD) |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No quantum advantage has been shown in finance, and the book has no hard optimisation for one to solve. |
| Implemented in volatility-ai | QUBO, annealing and small-circuit simulations are research code (`quantum`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK397, RK420 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Koopman Scholarly Quantum
Circuit Optimizer Ref-425") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Optimise a circuit or encode a discrete optimisation subproblem; the
title names no financial objective and shows no quantum advantage. The
Koopman version linearises the dynamics in a lifted feature space and
forecasts with the linear operator. I found no study of this method on
this task.

## The CSV's description

Proposed Koopman-operator-based approach to quantum-circuit or
quantum-inspired optimization: Optimize a circuit or encode a discrete
optimization subproblem; the title does not specify a complete financial
objective or demonstrate a quantum advantage. This is a concept-level
interpretation of the title, not a complete trading specification: the
exact model inputs/target, calibration, entry/exit or rebalance rules,
and position sizing are not fully defined here.

## Evidence

* **Herman et al. (2023), "Quantum computing for finance," *Nature
  Reviews Physics* 5, 450–465:** surveys quantum optimisation, machine
  learning and simulation for finance; its case for finance as an early
  beneficiary is a forecast, and I found no demonstrated advantage on a
  financial problem. (Abstract.)

## Against, and failure modes

* No demonstrated quantum advantage on a financial problem; at this
  book's size a classical solver is exact.
* The Koopman entries in the list have no peer-reviewed trading evidence
  (RK206).

## Fit with volatility-ai

Nothing in this book needs a hard discrete optimisation: one symbol, lot
sizes from a strategy. Out of scope as anything but a curiosity.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Herman, D., et al. (2023). "Quantum computing for finance." *Nature
  Reviews Physics* 5, 450–465. doi:10.1038/s42254-023-00603-1. Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 1769 | Koopman Scholarly Quantum Circuit Optimizer Ref-425 | Rough path theory / Tensor signatures / Stock trend forecasting | 12648 | 10357 | No |
| 1824 | Koopman Scholarly Quantum Circuit Optimizer Ref-905 | Rough path theory / Tensor signatures / Stock trend forecasting | 12653 | 10368 | No |
| 3830 | Koopman Scholarly Quantum Circuit Optimizer Ref-329 | Geometric deep learning / Riemannian metrics / Stock risk parity | 12257 | 10452 | No |
| 3916 | Koopman Scholarly Quantum Circuit Optimizer Ref-809 | Geometric deep learning / Riemannian metrics / Stock risk parity | 12270 | 10456 | No |
| 6201 | Koopman Scholarly Quantum Circuit Optimizer Ref-137 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 12252 | 10240 | No |
| 6247 | Koopman Scholarly Quantum Circuit Optimizer Ref-617 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 12265 | 10244 | No |
| 8692 | Koopman Scholarly Quantum Circuit Optimizer Ref-41 | Graph attention / Sector contagion / Stock baskets | 13914 | 13982 | No |
| 8768 | Koopman Scholarly Quantum Circuit Optimizer Ref-233 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13764 | 12795 | No |
| 8883 | Koopman Scholarly Quantum Circuit Optimizer Ref-521 | Graph attention / Sector contagion / Stock baskets | 13922 | 13990 | No |
| 8959 | Koopman Scholarly Quantum Circuit Optimizer Ref-713 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13772 | 12803 | No |
