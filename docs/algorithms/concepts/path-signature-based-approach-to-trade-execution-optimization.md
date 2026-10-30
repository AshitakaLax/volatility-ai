# Path-signature-based approach to trade-execution optimization

**Concept page** · shared by **11** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,741) ·
researched 2026-10-30

| | |
|---|---|
| Task | Trade-execution optimisation |
| Method | Path signatures |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** The book's orders are too small for impact to matter; execution optimisation solves a problem it does not have. |
| Implemented in volatility-ai | Schedules and execution agents are research code (`execution`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK363, RK366, RK244 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Signature Scholarly
Execution Trajectory Planner Ref-125") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Plan order timing and slicing over a horizon to balance slippage,
impact, completion risk and liquidity. The path-signature version
describes price paths by their iterated-integral signatures and fits on
those features. I found no study of this method on this task.

## The CSV's description

Proposed path-signature-based approach to trade-execution optimization:
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
* Signature features multiply with depth and dimension; no out-of-sample
  trading evidence found (RK328).

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
| 1741 | Signature Scholarly Execution Trajectory Planner Ref-125 | Rough path theory / Tensor signatures / Stock trend forecasting | 8246 | 7592 | No |
| 1796 | Signature Scholarly Execution Trajectory Planner Ref-605 | Rough path theory / Tensor signatures / Stock trend forecasting | 8287 | 7616 | No |
| 6218 | Signature Scholarly Execution Trajectory Planner Ref-317 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6517 | 6545 | No |
| 6264 | Signature Scholarly Execution Trajectory Planner Ref-797 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6560 | 6571 | No |
| 7452 | Signature Scholarly Execution Trajectory Planner Ref-29 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6492 | 8426 | No |
| 7486 | Signature Scholarly Execution Trajectory Planner Ref-509 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6535 | 8446 | No |
| 7520 | Signature Scholarly Execution Trajectory Planner Ref-989 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6578 | 8466 | No |
| 8762 | Signature Scholarly Execution Trajectory Planner Ref-221 | Graph attention / Sector contagion / Stock baskets | 12254 | 13151 | No |
| 8953 | Signature Scholarly Execution Trajectory Planner Ref-701 | Graph attention / Sector contagion / Stock baskets | 12267 | 13155 | No |
| 13886 | Signature Scholarly Execution Trajectory Planner Ref-413 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13767 | 12798 | No |
| 13897 | Signature Scholarly Execution Trajectory Planner Ref-893 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13775 | 12806 | No |
