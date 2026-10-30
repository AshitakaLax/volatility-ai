# Multi-scale approach to multi-scale quantitative stock selector ver-87

**Concept page** · shared by **1** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #8,442) ·
researched 2026-10-30

| | |
|---|---|
| Task | Quantitative stock selection (one generated name) |
| Method | Multi-scale (several horizons combined) |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Stock ranking needs a stock universe and a multi-name book; the project trades one ETF and holds no stock data. |
| Implemented in volatility-ai | Cross-sectional rankers are research code (`cross_section`, RK214). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK7, RK214, RK291, RK89 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Multi-Scale Scholarly
Quantitative Stock Selector Ver-87") combine a method word, "Scholarly",
a task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Score stocks against one another and form a portfolio from the ranks.
The multi-scale version combines signals or estimates measured over
several horizons. I found no study of this method on this task.

## The CSV's description

Proposed multi-scale approach to multi-scale quantitative stock selector
ver-87: Interpret the named concept—Multi-Scale Quantitative Stock
Selector Ver-87—as a proposed quantitative model, but the intended
prediction target, signal construction, trading objective, and position
rules are not fully specified in this record. This is a concept-level
interpretation of the title, not a complete trading specification: the
exact model inputs/target, calibration, entry/exit or rebalance rules,
and position sizing are not fully defined here.

## Evidence

* **Gu, Kelly & Xiu (2020), "Empirical Asset Pricing via Machine
  Learning," *Review of Financial Studies* 33(5), 2223–2274:** trees and
  neural networks forecast stock returns best, mostly from momentum,
  liquidity and volatility signals; a neural long-short decile spread
  had an out-of-sample Sharpe of 1.35. (Abstract.)
* **McLean & Pontiff (2016), "Does Academic Research Destroy Stock
  Return Predictability?" *Journal of Finance* 71(1):** anomaly
  portfolio returns are 26% lower out of sample and 58% lower after
  publication. (Abstract.)

## Against, and failure modes

* Anomaly returns shrink after publication (McLean & Pontiff); the
  long-only top-k form keeps only part of the long-short spread.
* More horizons mean more weights to choose, and the blend can be
  overfitted.

## Fit with volatility-ai

Needs a stock universe, point-in-time data and a multi-name book; the
engine trades one ETF and the warehouse holds no stock universe. The
researched form is RK214 (long-only top-k), which stays a reference.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Gu, S., Kelly, B., Xiu, D. (2020). *Review of Financial Studies*
  33(5), 2223–2274. Abstract.
* McLean, R. D., Pontiff, J. (2016). *Journal of Finance* 71(1).
  Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 8442 | Multi-Scale Scholarly Quantitative Stock Selector Ver-87 | Reinforcement learning / Game theory / ETF arbitrage | 4592 | 10705 | No |
