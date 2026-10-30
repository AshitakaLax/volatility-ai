# Spectral approach to ETF rotation

**Concept page** · shared by **5** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #8,493) ·
researched 2026-10-30

| | |
|---|---|
| Task | ETF rotation |
| Method | Spectral (frequency-domain) decomposition |
| Fit with this project | ⏳ reference only · background, nothing to build now |
| Useful for volatility-ai | **Reference only.** A spectral method could rank or weight the rotation, but no study shows it beating plain relative strength with an absolute-momentum filter; background until X3 is measured. |
| Implemented in volatility-ai | `tools/rotation.py` runs relative strength (X3), defensive rotation (X2), dual momentum (RK3) and HRP weights (A5); Faber's moving-average filter is built (`tactical_allocation`, C-E2, RK17). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | X3, X2, RK3, RK17, C-E2, A5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Spectral Scholarly ETF
Rotation Model Alpha-47") combine a method word, "Scholarly", a task and
a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Rank a defined ETF universe by momentum, trend or risk and rotate on a
fixed schedule, with a defensive asset and a cost model. The spectral
version works in the frequency domain, filtering or weighting components
by cycle length. I found no study of this method on this task.

## The CSV's description

Proposed spectral approach to ETF rotation: Rank a defined ETF universe
using a specified momentum, trend, or risk signal and rotate exposure on
a fixed schedule, with a defined defensive allocation and trading-cost
model. This is a concept-level interpretation of the title, not a
complete trading specification: the exact model inputs/target,
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

## Against, and failure modes

* Rotation results depend heavily on the universe and the rebalance day;
  many published variants are fitted on the same few decades.
* Momentum-based rotation lags turning points and whipsaws in sideways
  markets.
* Spectral estimates need long stationary windows; market cycles are
  neither.

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

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 8493 | Spectral Scholarly ETF Rotation Model Alpha-47 | Reinforcement learning / Policy gradient / ETF arbitrage | 10861 | 10712 | No |
| 8533 | Spectral Scholarly ETF Rotation Model Alpha-147 | Reinforcement learning / Policy gradient / ETF arbitrage | 4612 | 10715 | No |
| 8573 | Spectral Scholarly ETF Rotation Model Alpha-247 | Reinforcement learning / Policy gradient / ETF arbitrage | 12516 | 12519 | No |
| 8613 | Spectral Scholarly ETF Rotation Model Alpha-347 | Reinforcement learning / Policy gradient / ETF arbitrage | 10866 | 10726 | No |
| 8653 | Spectral Scholarly ETF Rotation Model Alpha-447 | Reinforcement learning / Policy gradient / ETF arbitrage | 4640 | 10729 | No |
