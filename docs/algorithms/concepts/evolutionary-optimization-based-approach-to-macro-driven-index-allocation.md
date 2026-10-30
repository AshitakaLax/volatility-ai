# Evolutionary-optimization-based approach to macro-driven index allocation

**Concept page** · shared by **5** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #7,431) ·
researched 2026-10-30

| | |
|---|---|
| Task | Macro-driven index allocation |
| Method | Evolutionary / genetic optimisation |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of a genetic search extracting a usable signal from macro data, where even simple predictors fail out of sample. |
| Implemented in volatility-ai | Macro series are in the warehouse with publication lags (`engine/warehouse/queries.py`); no macro allocator. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK41, RK211, RK217, N5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Evolutionary Scholarly
Macro-Driven Index Allocator Alpha-18") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Use macroeconomic and market indicators, lagged by their publication
dates, to shift allocations among index-linked assets. The evolutionary
version searches parameters or weights with genetic algorithms. I found
no study of this method on this task.

## The CSV's description

Proposed evolutionary-optimization-based approach to macro-driven index
allocation: Use macroeconomic and market indicators to adjust
allocations among index-linked assets, with explicit publication lags
and rebalance rules needed to prevent look-ahead bias. This is a
concept-level interpretation of the title, not a complete trading
specification: the exact model inputs/target, calibration, entry/exit or
rebalance rules, and position sizing are not fully defined here.

## Evidence

* **Welch & Goyal (2008), "A Comprehensive Look at the Empirical
  Performance of Equity Premium Prediction," *Review of Financial
  Studies* 21(4), 1455–1508:** the standard macro and valuation
  predictors of the equity premium performed poorly out of sample.
  (Standard reference.)
* **Rapach, Strauss & Zhou (2010), *Review of Financial Studies* 23(2),
  821–862:** combining the individual predictors' forecasts gives small
  but consistent out-of-sample gains, linked to the business cycle.
  (Abstract.)

## Against, and failure modes

* Macro data are monthly or quarterly, revised and published with lags;
  a few decades give few independent observations.
* Each predictor alone has failed out of sample (Welch & Goyal); gains
  come only from combining many, and they are small.
* A genetic search over a backtest is a large multiple-testing exercise
  that finds the noise that fits best.

## Fit with volatility-ai

The warehouse already holds macro series, shifted by their publication
lag before the as-of join (`engine/warehouse/queries.py`), so a macro
input is possible. The evidence says expect little; a macro signal would
be one more regime input, tested against the NATR exit like any other.
The inflation-regime rotation (RK41) is the researched candidate.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Welch, I., Goyal, A. (2008). *Review of Financial Studies* 21(4),
  1455–1508. Standard reference.
* Rapach, D. E., Strauss, J. K., Zhou, G. (2010). *Review of Financial
  Studies* 23(2), 821–862. Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 7431 | Evolutionary Scholarly Macro-Driven Index Allocator Alpha-18 | Attention networks / Self-attention / Stock alpha generation | 3191 | 1825 | No |
| 7435 | Evolutionary Scholarly Macro-Driven Index Allocator Alpha-118 | Attention networks / Self-attention / Stock alpha generation | 3194 | 981 | No |
| 7439 | Evolutionary Scholarly Macro-Driven Index Allocator Alpha-218 | Attention networks / Self-attention / Stock alpha generation | 12815 | 11266 | No |
| 7443 | Evolutionary Scholarly Macro-Driven Index Allocator Alpha-318 | Attention networks / Self-attention / Stock alpha generation | 3202 | 1836 | No |
| 7447 | Evolutionary Scholarly Macro-Driven Index Allocator Alpha-418 | Attention networks / Self-attention / Stock alpha generation | 3205 | 1000 | No |
