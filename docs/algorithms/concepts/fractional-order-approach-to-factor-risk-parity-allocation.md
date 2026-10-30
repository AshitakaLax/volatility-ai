# Fractional-order approach to factor risk-parity allocation

**Concept page** · shared by **5** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #3,694) ·
researched 2026-10-30

| | |
|---|---|
| Task | Factor risk-parity allocation |
| Method | Fractional-order models (long memory, fractional calculus) |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of fractional-order models improving factor risk parity, and the book has no factors to budget. |
| Implemented in volatility-ai | Factor risk parity is research code (`concepts.factor_risk_parity`); HRP is built (A5). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK61, A5, RK60 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Fractional Scholarly Factor
Risk Parity Framework Alpha-49") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Estimate factor volatility and dependence, then choose weights so the
factors' risk contributions match a target budget. The fractional-order
version models long memory with fractional differencing or
fractional-order dynamics. I found no study of this method on this task.

## The CSV's description

Proposed fractional-order approach to factor risk-parity allocation:
Estimate factor volatility and dependence, then choose portfolio weights
so risk contributions align with a target risk budget. This is a
concept-level interpretation of the title, not a complete trading
specification: the exact model inputs/target, calibration, entry/exit or
rebalance rules, and position sizing are not fully defined here.

## Evidence

* **Roncalli & Weisang (2016), "Risk parity portfolios with risk
  factors," *Quantitative Finance* 16(3), 377–388:** equalise factor
  risk contributions instead of asset contributions; the solution can be
  non-unique. (Abstract.)
* **Asness, Frazzini & Pedersen (2012), *Financial Analysts Journal*:**
  risk parity's historical edge relies on leverage (see RK61). (Standard
  reference.)

## Against, and failure modes

* Factor risk parity needs a factor model whose loadings drift;
  solutions can be non-unique.
* Unlevered risk parity is a low-volatility, bond-heavy portfolio; its
  historical edge came with leverage (RK61).
* Long memory in returns is weak once short-range dependence is allowed
  for (Lo 1991); in volatility, the simpler HAR model reproduces it
  (Corsi 2009).

## Fit with volatility-ai

An allocator for a multi-asset book; the engine trades one symbol. HRP
(A5) is the built allocator, and factor risk parity adds a factor model
a book of a few ETFs does not need.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Roncalli, T., Weisang, G. (2016). *Quantitative Finance* 16(3),
  377–388. Abstract.
* Asness, C., Frazzini, A., Pedersen, L. H. (2012). "Leverage aversion
  and risk parity." *Financial Analysts Journal* 68(1). Standard
  reference.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 3694 | Fractional Scholarly Factor Risk Parity Framework Alpha-49 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8183 | 2908 | No |
| 3711 | Fractional Scholarly Factor Risk Parity Framework Alpha-149 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6468 | 8403 | No |
| 3728 | Fractional Scholarly Factor Risk Parity Framework Alpha-249 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6475 | 2952 | No |
| 3745 | Fractional Scholarly Factor Risk Parity Framework Alpha-349 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8216 | 2976 | No |
| 3762 | Fractional Scholarly Factor Risk Parity Framework Alpha-449 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6486 | 8421 | No |
