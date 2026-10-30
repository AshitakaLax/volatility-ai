# Attention-weighted approach to dependence-aware cointegration / relative-value analysis

**Concept page** · shared by **5** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #6,140) ·
researched 2026-10-30

| | |
|---|---|
| Task | Dependence-aware cointegration / relative-value analysis |
| Method | Attention networks |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Relative-value positions need a short leg, which the owner's rules exclude; modelling the dependence better does not change that. |
| Implemented in volatility-ai | Pairs rules are research code (`stat_arb`, RK72–RK74). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK74, RK94, RK37 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Attentional Scholarly
Copula Cointegration System Alpha-52") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Model joint and tail dependence among assets and test for a stable
long-run spread before taking relative-value positions. The attention
version weights its inputs with a learned attention network. I found no
study of this method on this task.

## The CSV's description

Proposed attention-weighted approach to dependence-aware cointegration /
relative-value analysis: Model joint and tail dependence among assets
and assess whether a stable long-run spread exists before considering
relative-value positions. This is a concept-level interpretation of the
title, not a complete trading specification: the exact model
inputs/target, calibration, entry/exit or rebalance rules, and position
sizing are not fully defined here.

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
| 6140 | Attentional Scholarly Copula Cointegration System Alpha-52 | Persistence landscapes / Topological contours / Equity index | 8185 | 12509 | No |
| 6150 | Attentional Scholarly Copula Cointegration System Alpha-152 | Persistence landscapes / Topological contours / Equity index | 4613 | 2933 | No |
| 6160 | Attentional Scholarly Copula Cointegration System Alpha-252 | Persistence landscapes / Topological contours / Equity index | 1024 | 2953 | No |
| 6170 | Attentional Scholarly Copula Cointegration System Alpha-352 | Persistence landscapes / Topological contours / Equity index | 8218 | 12524 | No |
| 6180 | Attentional Scholarly Copula Cointegration System Alpha-452 | Persistence landscapes / Topological contours / Equity index | 4641 | 3001 | No |
