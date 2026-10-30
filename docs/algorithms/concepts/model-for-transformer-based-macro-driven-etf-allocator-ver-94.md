# Model for transformer-based macro-driven etf allocator ver-94

**Concept page** · shared by **1** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #3,172) ·
researched 2026-10-30

| | |
|---|---|
| Task | Macro-driven ETF allocation (one generated name) |
| Method | Transformer network |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of a transformer network extracting a usable signal from macro data, where even simple predictors fail out of sample. |
| Implemented in volatility-ai | Macro series are in the warehouse with publication lags (`engine/warehouse/queries.py`); no macro allocator. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK41, RK211, RK217, N5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Transformer-Based Scholarly
Macro-Driven ETF Allocator Ver-94") combine a method word, "Scholarly",
a task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Use macroeconomic and market indicators, lagged by their publication
dates, to shift allocations among index-linked assets. The transformer
version forecasts from macro and price histories with a transformer
network. I found no study of this method on this task.

## The CSV's description

Proposed model for transformer-based macro-driven etf allocator ver-94:
Interpret the named concept—Transformer-Based Macro-Driven ETF Allocator
Ver-94—as a proposed quantitative model, but the intended prediction
target, signal construction, trading objective, and position rules are
not fully specified in this record. This is a concept-level
interpretation of the title, not a complete trading specification: the
exact model inputs/target, calibration, entry/exit or rebalance rules,
and position sizing are not fully defined here.

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
* Transformers need far more independent observations than monthly macro
  data provide.

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
| 3172 | Transformer-Based Scholarly Macro-Driven ETF Allocator Ver-94 | Vine copulas / Regularization / Multi-factor equity allocation | 10376 | 2872 | No |
