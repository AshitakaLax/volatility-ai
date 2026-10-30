# Evolutionary-optimization-based approach to trade-execution optimization

**Concept page** · shared by **11** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,725) ·
researched 2026-10-30

| | |
|---|---|
| Task | Trade-execution optimisation |
| Method | Evolutionary / genetic optimisation |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** The book's orders are too small for impact to matter; execution optimisation solves a problem it does not have. |
| Implemented in volatility-ai | Schedules and execution agents are research code (`execution`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK363, RK366, RK244 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Evolutionary Scholarly
Execution Trajectory Planner Ref-5") combine a method word, "Scholarly",
a task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Plan order timing and slicing over a horizon to balance slippage,
impact, completion risk and liquidity. The evolutionary version searches
parameters or weights with genetic algorithms. I found no study of this
method on this task.

## The CSV's description

Proposed evolutionary-optimization-based approach to trade-execution
optimization: Plan order timing and slicing over an execution horizon to
balance expected slippage, market impact, completion risk, and
liquidity. This is a concept-level interpretation of the title, not a
complete trading specification: the exact model inputs/target,
calibration, entry/exit or rebalance rules, and position sizing are not
fully defined here.

## Evidence

* **Almgren & Chriss (2001), "Optimal execution of portfolio
  transactions," *Journal of Risk* 3(2):** the mean-variance trade-off
  between impact and timing risk for a large order (see RK366).
  (Standard reference.)
* **Frazzini, Israel & Moskowitz (2018), "Trading Costs" (SSRN
  3229719):** on $1.7 trillion of live institutional trades, market
  impact averaged under 9 bp for orders completed within a day, an order
  of magnitude below earlier estimates. (Abstract and summaries.)

## Against, and failure modes

* Execution schedules address impact, which is a few basis points even
  for institutional orders (Frazzini, Israel & Moskowitz).
* A genetic search over a backtest is a large multiple-testing exercise
  that finds the noise that fits best.

## Fit with volatility-ai

The engine's orders are small against TQQQ's volume; slicing schedules
solve a problem this book does not have (RK363, RK366). A spread gate
(RK244) covers what matters.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Almgren, R., Chriss, N. (2001). *Journal of Risk* 3(2), 5–39. Standard
  reference.
* Frazzini, A., Israel, R., Moskowitz, T. J. (2018). "Trading Costs."
  SSRN 3229719. Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 1725 | Evolutionary Scholarly Execution Trajectory Planner Ref-5 | Rough path theory / Tensor signatures / Stock trend forecasting | 8235 | 7586 | No |
| 1780 | Evolutionary Scholarly Execution Trajectory Planner Ref-485 | Rough path theory / Tensor signatures / Stock trend forecasting | 8276 | 7610 | No |
| 1835 | Evolutionary Scholarly Execution Trajectory Planner Ref-965 | Rough path theory / Tensor signatures / Stock trend forecasting | 8317 | 7634 | No |
| 6207 | Evolutionary Scholarly Execution Trajectory Planner Ref-197 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6506 | 6539 | No |
| 6253 | Evolutionary Scholarly Execution Trajectory Planner Ref-677 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6549 | 6565 | No |
| 7479 | Evolutionary Scholarly Execution Trajectory Planner Ref-389 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6524 | 8440 | No |
| 7513 | Evolutionary Scholarly Execution Trajectory Planner Ref-869 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6567 | 8460 | No |
| 8715 | Evolutionary Scholarly Execution Trajectory Planner Ref-101 | Graph attention / Sector contagion / Stock baskets | 12251 | 13150 | No |
| 8906 | Evolutionary Scholarly Execution Trajectory Planner Ref-581 | Graph attention / Sector contagion / Stock baskets | 12264 | 13154 | No |
| 13883 | Evolutionary Scholarly Execution Trajectory Planner Ref-293 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13765 | 12796 | No |
| 13894 | Evolutionary Scholarly Execution Trajectory Planner Ref-773 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13773 | 12804 | No |
