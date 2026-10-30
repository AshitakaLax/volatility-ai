# Hierarchical approach to ETF rotation

**Concept page** · shared by **1** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #8,399) ·
researched 2026-10-30

| | |
|---|---|
| Task | ETF rotation |
| Method | Hierarchical (tree or multi-level) model |
| Fit with this project | 🧪 reference only · background, nothing to build now |
| Useful for volatility-ai | **Reference only.** HRP weighting is built into the rotation tool (A5, RK56), but 1/N is hard to beat out of sample (DeMiguel et al. 2009); measure it only alongside the rotation itself. |
| Implemented in volatility-ai | `tools/rotation.py` runs relative strength (X3), defensive rotation (X2), dual momentum (RK3) and HRP weights (A5); Faber's moving-average filter is built (`tactical_allocation`, C-E2, RK17). |
| Evidence | Evidence found (for the task; see the page for the method) |
| Related ledger entries | X3, X2, RK3, RK17, C-E2, A5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Hierarchical Scholarly ETF
Rotation Engine MK-41") combine a method word, "Scholarly", a task and a
serial number, and the rows' references are software libraries or papers
the CSV's own review calls unrelated. There is no specific algorithm
behind each name to research, so this page researches what the members
share: the task, done with the method.

## In one paragraph

Rank a defined ETF universe by momentum, trend or risk and rotate on a
fixed schedule, with a defensive asset and a cost model. The
hierarchical version organises assets or states in a tree and allocates
or pools estimates down it. Hierarchical weighting is HRP, which the
rotation tool already offers; the open question is whether any optimised
weighting beats equal weight out of sample.

## The CSV's description

Proposed hierarchical approach to ETF rotation: Rank a defined ETF
universe using a specified momentum, trend, or risk signal and rotate
exposure on a fixed schedule, with a defined defensive allocation and
trading-cost model. This is a concept-level interpretation of the title,
not a complete trading specification: the exact model inputs/target,
calibration, entry/exit or rebalance rules, and position sizing are not
fully defined here.

## Evidence

* **Faber (2007), "A Quantitative Approach to Tactical Asset
  Allocation":** a 10-month moving-average filter across asset classes
  gave comparable returns with much lower volatility and drawdown (see
  RK17). (Summaries.)
* **Antonacci (2012, published 2017), "Risk Premia Harvesting Through
  Dual Momentum":** relative strength picks the asset, absolute momentum
  against T-bills decides whether to hold it (see RK3). (Paper summary.)
* **DeMiguel, Garlappi & Uppal (2009), "Optimal Versus Naive
  Diversification," *Review of Financial Studies* 22(5), 1915–1953:**
  none of 14 optimised allocations consistently beat 1/N out of sample.
  (Standard reference.)

## Against, and failure modes

* Rotation results depend heavily on the universe and the rebalance day;
  many published variants are fitted on the same few decades.
* Momentum-based rotation lags turning points and whipsaws in sideways
  markets.
* The hierarchy is itself estimated; a different clustering gives
  different weights.

## Fit with volatility-ai

Built as X3 (relative-strength rotation), X2 (defensive rotation), RK3
(dual momentum) and C-E2 (Faber TAA), none yet measured. A rotation
sleeve sits beside the TQQQ grid.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Faber, M. T. (2007). "A Quantitative Approach to Tactical Asset
  Allocation." *Journal of Wealth Management*. Summaries; see RK17.
* Antonacci, G. (2017). "Risk Premia Harvesting Through Dual Momentum."
  See RK3.
* DeMiguel, V., Garlappi, L., Uppal, R. (2009). *Review of Financial
  Studies* 22(5), 1915–1953. Standard reference.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 8399 | Hierarchical Scholarly ETF Rotation Engine MK-41 | Graph neural networks / Sector rotation / ETFs | 13465 | 13685 | No |
