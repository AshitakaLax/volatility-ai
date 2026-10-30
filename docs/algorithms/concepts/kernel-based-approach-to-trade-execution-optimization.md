# Kernel-based approach to trade-execution optimization

**Concept page** · shared by **10** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,766) ·
researched 2026-10-30

| | |
|---|---|
| Task | Trade-execution optimisation |
| Method | Kernel methods |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** The book's orders are too small for impact to matter; execution optimisation solves a problem it does not have. |
| Implemented in volatility-ai | Schedules and execution agents are research code (`execution`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK363, RK366, RK244 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Kernel Scholarly Execution
Trajectory Planner Ref-365") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Plan order timing and slicing over a horizon to balance slippage,
impact, completion risk and liquidity. The kernel-based version replaces
linear rules with kernel regressions or similarity-weighted estimates. I
found no study of this method on this task.

## The CSV's description

Proposed kernel-based approach to trade-execution optimization: Plan
order timing and slicing over an execution horizon to balance expected
slippage, market impact, completion risk, and liquidity. This is a
concept-level interpretation of the title, not a complete trading
specification: the exact model inputs/target, calibration, entry/exit or
rebalance rules, and position sizing are not fully defined here.

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
* Kernel bandwidths are tuning parameters, and with few independent
  episodes they overfit.

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
| 1766 | Kernel Scholarly Execution Trajectory Planner Ref-365 | Rough path theory / Tensor signatures / Stock trend forecasting | 8264 | 7604 | No |
| 1821 | Kernel Scholarly Execution Trajectory Planner Ref-845 | Rough path theory / Tensor signatures / Stock trend forecasting | 8305 | 7628 | No |
| 6194 | Kernel Scholarly Execution Trajectory Planner Ref-77 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6496 | 6533 | No |
| 6240 | Kernel Scholarly Execution Trajectory Planner Ref-557 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6539 | 6559 | No |
| 7471 | Kernel Scholarly Execution Trajectory Planner Ref-269 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6513 | 8435 | No |
| 7505 | Kernel Scholarly Execution Trajectory Planner Ref-749 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6556 | 8455 | No |
| 8857 | Kernel Scholarly Execution Trajectory Planner Ref-461 | Graph attention / Sector contagion / Stock baskets | 12261 | 13153 | No |
| 9048 | Kernel Scholarly Execution Trajectory Planner Ref-941 | Graph attention / Sector contagion / Stock baskets | 12274 | 13157 | No |
| 13880 | Kernel Scholarly Execution Trajectory Planner Ref-173 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13763 | 12794 | No |
| 13891 | Kernel Scholarly Execution Trajectory Planner Ref-653 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13771 | 12802 | No |
