# Model for trade-execution optimization

**Concept page** · shared by **8** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #7,414) ·
researched 2026-10-30

| | |
|---|---|
| Task | Trade-execution optimisation |
| Method | Unspecified model |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** The book's orders are too small for impact to matter; execution optimisation solves a problem it does not have. |
| Implemented in volatility-ai | Schedules and execution agents are research code (`execution`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK363, RK366, RK244 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Generative Scholarly
Execution Trajectory Optimizer Ver-49") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Plan order timing and slicing over a horizon to balance slippage,
impact, completion risk and liquidity. The title names no method beyond
"model", so this page judges the task itself. The task itself is out of
scope here; see the fit section.

## The CSV's description

Proposed model for trade-execution optimization: Plan order timing and
slicing over an execution horizon to balance expected slippage, market
impact, completion risk, and liquidity. This is a concept-level
interpretation of the title, not a complete trading specification: the
exact model inputs/target, calibration, entry/exit or rebalance rules,
and position sizing are not fully defined here.

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
| 7414 | Generative Scholarly Execution Trajectory Optimizer Ver-49 | Geometric deep learning / Riemannian optimization / Stock risk parity | 8173 | 2861 | No |
| 7417 | Transformer-Based Scholarly Execution Trajectory Optimizer Ver-69 | Geometric deep learning / Riemannian optimization / Stock risk parity | 6449 | 2864 | No |
| 7424 | Generative Scholarly Execution Trajectory Optimizer Ver-149 | Geometric deep learning / Riemannian optimization / Stock risk parity | 6457 | 8393 | No |
| 7427 | Transformer-Based Scholarly Execution Trajectory Optimizer Ver-169 | Geometric deep learning / Riemannian optimization / Stock risk parity | 8177 | 2888 | No |
| 8343 | Dynamic Scholarly Execution Trajectory Optimizer MK-23 | Topological data analysis / Clustering / Statistical arbitrage | 12769 | 13008 | No |
| 8344 | Dynamic Scholarly Execution Trajectory Optimizer MK-83 | Topological data analysis / Clustering / Statistical arbitrage | 12770 | 13009 | No |
| 13830 | Cross-Sectional Scholarly Execution Trajectory Optimizer MK-8 | Point processes / Recurrent neural networks / Volatility | 13564 | 11857 | No |
| 13835 | Cross-Sectional Scholarly Execution Trajectory Optimizer MK-68 | Point processes / Recurrent neural networks / Volatility | 13566 | 11859 | No |
