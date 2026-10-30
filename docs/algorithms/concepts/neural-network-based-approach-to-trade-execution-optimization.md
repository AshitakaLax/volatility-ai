# Neural-network-based approach to trade-execution optimization

**Concept page** · shared by **10** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #3,814) ·
researched 2026-10-30

| | |
|---|---|
| Task | Trade-execution optimisation |
| Method | Neural networks |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** The book's orders are too small for impact to matter; execution optimisation solves a problem it does not have. |
| Implemented in volatility-ai | Schedules and execution agents are research code (`execution`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK363, RK366, RK244 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Neural Scholarly Execution
Trajectory Planner Ref-245") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Plan order timing and slicing over a horizon to balance slippage,
impact, completion risk and liquidity. The neural-network version fits a
neural network to the task. I found no study of this method on this
task.

## The CSV's description

Proposed neural-network-based approach to trade-execution optimization:
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
* Neural forecasts on one index have not reliably beaten simple rules;
  an LSTM's stock picks were largely short-term reversal (Fischer &
  Krauss 2018, RK292).

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
| 3814 | Neural Scholarly Execution Trajectory Planner Ref-245 | Rough path theory / Tensor signatures / Stock trend forecasting | 8255 | 7598 | No |
| 3900 | Neural Scholarly Execution Trajectory Planner Ref-725 | Rough path theory / Tensor signatures / Stock trend forecasting | 8296 | 7622 | No |
| 7462 | Neural Scholarly Execution Trajectory Planner Ref-149 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6503 | 8431 | No |
| 7496 | Neural Scholarly Execution Trajectory Planner Ref-629 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6546 | 8451 | No |
| 8345 | Neural Scholarly Execution Trajectory Planner Ref-437 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6528 | 6552 | No |
| 8347 | Neural Scholarly Execution Trajectory Planner Ref-917 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6571 | 6578 | No |
| 13877 | Neural Scholarly Execution Trajectory Planner Ref-53 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13761 | 12792 | No |
| 13884 | Neural Scholarly Execution Trajectory Planner Ref-341 | Graph attention / Sector contagion / Stock baskets | 12258 | 13152 | No |
| 13888 | Neural Scholarly Execution Trajectory Planner Ref-533 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13769 | 12800 | No |
| 13895 | Neural Scholarly Execution Trajectory Planner Ref-821 | Graph attention / Sector contagion / Stock baskets | 12271 | 13156 | No |
