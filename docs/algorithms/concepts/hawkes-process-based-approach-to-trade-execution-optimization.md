# Hawkes-process-based approach to trade-execution optimization

**Concept page** · shared by **5** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #6,141) ·
researched 2026-10-30

| | |
|---|---|
| Task | Trade-execution optimisation |
| Method | Hawkes (self-exciting) point processes |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** The book's orders are too small for impact to matter; execution optimisation solves a problem it does not have. |
| Implemented in volatility-ai | Schedules and execution agents are research code (`execution`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK363, RK366, RK244 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Hawkes Scholarly Execution
Trajectory Planner Alpha-57") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Plan order timing and slicing over a horizon to balance slippage,
impact, completion risk and liquidity. The Hawkes version models events
(trades, jumps, crashes) as self-exciting, each event raising the
near-term chance of another. I found no study of this method on this
task.

## The CSV's description

Proposed Hawkes-process-based approach to trade-execution optimization:
Plan order timing and slicing over an execution horizon to balance
expected slippage, market impact, completion risk, and liquidity. This
is a concept-level interpretation of the title, not a complete trading
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
* Hawkes models describe intraday event clustering; daily bars hold too
  few events to fit them.

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
| 6141 | Hawkes Scholarly Execution Trajectory Planner Alpha-57 | Wavelets / Multi-resolution / Statistical arbitrage stocks | 1006 | 6501 | No |
| 6151 | Hawkes Scholarly Execution Trajectory Planner Alpha-157 | Wavelets / Multi-resolution / Statistical arbitrage stocks | 10862 | 12515 | No |
| 6161 | Hawkes Scholarly Execution Trajectory Planner Alpha-257 | Wavelets / Multi-resolution / Statistical arbitrage stocks | 9280 | 6514 | No |
| 6171 | Hawkes Scholarly Execution Trajectory Planner Alpha-357 | Wavelets / Multi-resolution / Statistical arbitrage stocks | 1035 | 6520 | No |
| 6181 | Hawkes Scholarly Execution Trajectory Planner Alpha-457 | Wavelets / Multi-resolution / Statistical arbitrage stocks | 10867 | 12530 | No |
