# Graph-based approach to benchmark index tracking

**Concept page** · shared by **5** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #8,486) ·
researched 2026-10-30

| | |
|---|---|
| Task | Benchmark index tracking |
| Method | Graph / network models |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** The project buys the index as an ETF; replicating it from constituents adds cost and tracking error for nothing. |
| Implemented in volatility-ai | Nothing. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK60 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Graph Scholarly Index
Tracking Optimizer Alpha-28") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Choose weights to track a target index while controlling tracking error,
turnover and costs; an allocation objective, not a return edge. The
graph-based version represents assets as a network of correlation or
causality links and acts on its structure. I found no study of this
method on this task.

## The CSV's description

Proposed graph-based approach to benchmark index tracking: Choose
portfolio weights to track a target index while controlling tracking
error, turnover, liquidity constraints, and transaction costs; this is
an allocation objective, not inherently a return-prediction edge. This
is a concept-level interpretation of the title, not a complete trading
specification: the exact model inputs/target, calibration, entry/exit or
rebalance rules, and position sizing are not fully defined here.

## Evidence

* **Benidis, Feng & Palomar (2018), "Sparse Portfolios for
  High-Dimensional Financial Index Tracking," *IEEE Transactions on
  Signal Processing* 66(1):** track an index with a few constituents by
  penalised tracking-error minimisation. (Abstract.)

## Against, and failure modes

* Tracking with a subset of constituents adds tracking error and cost
  that buying the index ETF avoids.
* Networks estimated from correlations are noisy and change with the
  window.

## Fit with volatility-ai

The project holds the index as an ETF, so tracking it with a stock
subset adds cost for nothing.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Benidis, K., Feng, Y., Palomar, D. P. (2018). *IEEE Transactions on
  Signal Processing* 66(1), 155–170. Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 8486 | Graph Scholarly Index Tracking Optimizer Alpha-28 | Point processes / Hawkes kernels / Stock liquidity jumps | 1002 | 2904 | No |
| 8526 | Graph Scholarly Index Tracking Optimizer Alpha-128 | Point processes / Hawkes kernels / Stock liquidity jumps | 10731 | 11867 | No |
| 8566 | Graph Scholarly Index Tracking Optimizer Alpha-228 | Point processes / Hawkes kernels / Stock liquidity jumps | 1022 | 6511 | No |
| 8606 | Graph Scholarly Index Tracking Optimizer Alpha-328 | Point processes / Hawkes kernels / Stock liquidity jumps | 1031 | 2972 | No |
| 8646 | Graph Scholarly Index Tracking Optimizer Alpha-428 | Point processes / Hawkes kernels / Stock liquidity jumps | 10738 | 11872 | No |
