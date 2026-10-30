# Attention-weighted approach to cointegration/pairs trading

**Concept page** · shared by **2** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #6,114) ·
researched 2026-10-30

| | |
|---|---|
| Task | Cointegration / pairs trading |
| Method | Attention networks |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** A pairs trade is long one leg and short the other; the owner's rules are long-only. |
| Implemented in volatility-ai | Pairs rules are research code (`stat_arb`, RK72–RK74). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK37, RK72, RK73, RK74, RK94 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Attention-Weighted
Scholarly Cointegrated Stock Pair Ver-63") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Test related securities for a stable long-run relationship and trade the
spread when it deviates, with safeguards for breakdown. The attention
version weights its inputs with a learned attention network. I found no
study of this method on this task.

## The CSV's description

Proposed attention-weighted approach to cointegration/pairs trading:
Test related securities for a stable long-run relationship and consider
trades when the estimated spread deviates from its equilibrium, with
safeguards for relationship breakdown. This is a concept-level
interpretation of the title, not a complete trading specification: the
exact model inputs/target, calibration, entry/exit or rebalance rules,
and position sizing are not fully defined here.

## Evidence

* **Gatev, Goetzmann & Rouwenhorst (2006), "Pairs Trading," *Review of
  Financial Studies* 19(3), 797–827:** matched pairs earned up to 11% a
  year in excess returns over 1962–2002, with lower raw profits in the
  later years (see RK72). (Abstract and summaries.)

## Against, and failure modes

* Pairs profits have fallen since the 1980s and relationships break down
  without warning.
* Attention networks need far more data than daily bars of a few ETFs
  provide.

## Fit with volatility-ai

A relative-value trade needs a short leg and a universe of related
instruments; the engine trades one leveraged ETF long-only. Out of scope
as a strategy.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Gatev, E., Goetzmann, W. N., Rouwenhorst, K. G. (2006). *Review of
  Financial Studies* 19(3), 797–827. Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 6114 | Attention-Weighted Scholarly Cointegrated Stock Pair Ver-63 | Topological data analysis / Clustering / Statistical arbitrage stocks | 2061 | 6490 | No |
| 6129 | Attention-Weighted Scholarly Cointegrated Stock Pair Ver-163 | Topological data analysis / Clustering / Statistical arbitrage stocks | 2073 | 6495 | No |
