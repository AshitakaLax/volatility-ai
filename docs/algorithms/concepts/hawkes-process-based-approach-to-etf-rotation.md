# Hawkes-process-based approach to ETF rotation

**Concept page** · shared by **5** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #8,478) ·
researched 2026-10-30

| | |
|---|---|
| Task | ETF rotation |
| Method | Hawkes (self-exciting) point processes |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of Hawkes processes improving ETF rotation over relative strength with an absolute filter (X3, RK3). |
| Implemented in volatility-ai | `tools/rotation.py` runs relative strength (X3), defensive rotation (X2), dual momentum (RK3) and HRP weights (A5); Faber's moving-average filter is built (`tactical_allocation`, C-E2, RK17). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | X3, X2, RK3, RK17, C-E2, A5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Hawkes Scholarly ETF
Rotation Model Alpha-7") combine a method word, "Scholarly", a task and
a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Rank a defined ETF universe by momentum, trend or risk and rotate on a
fixed schedule, with a defensive asset and a cost model. The Hawkes
version models events (trades, jumps, crashes) as self-exciting, each
event raising the near-term chance of another. I found no study of this
method on this task.

## The CSV's description

Proposed Hawkes-process-based approach to ETF rotation: Rank a defined
ETF universe using a specified momentum, trend, or risk signal and
rotate exposure on a fixed schedule, with a defined defensive allocation
and trading-cost model. This is a concept-level interpretation of the
title, not a complete trading specification: the exact model
inputs/target, calibration, entry/exit or rebalance rules, and position
sizing are not fully defined here.

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
* Hawkes models describe intraday event clustering; daily bars hold too
  few events to fit them.

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
| 8478 | Hawkes Scholarly ETF Rotation Model Alpha-7 | Reinforcement learning / Policy gradient / ETF arbitrage | 12810 | 12507 | No |
| 8518 | Hawkes Scholarly ETF Rotation Model Alpha-107 | Reinforcement learning / Policy gradient / ETF arbitrage | 12018 | 10714 | No |
| 8558 | Hawkes Scholarly ETF Rotation Model Alpha-207 | Reinforcement learning / Policy gradient / ETF arbitrage | 6472 | 10718 | No |
| 8598 | Hawkes Scholarly ETF Rotation Model Alpha-307 | Reinforcement learning / Policy gradient / ETF arbitrage | 12817 | 12522 | No |
| 8638 | Hawkes Scholarly ETF Rotation Model Alpha-407 | Reinforcement learning / Policy gradient / ETF arbitrage | 12019 | 10728 | No |
