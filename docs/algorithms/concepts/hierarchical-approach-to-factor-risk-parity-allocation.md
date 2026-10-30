# Hierarchical approach to factor risk-parity allocation

**Concept page** · shared by **2** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,624) ·
researched 2026-10-30

| | |
|---|---|
| Task | Factor risk-parity allocation |
| Method | Hierarchical (tree or multi-level) model |
| Fit with this project | 🧪 reference only · background, nothing to build now |
| Useful for volatility-ai | **Reference only.** Hierarchical risk budgeting is HRP's idea and is built (A5); factor budgets add a factor model a few-ETF book does not need. Background. |
| Implemented in volatility-ai | Factor risk parity is research code (`concepts.factor_risk_parity`); HRP is built (A5). |
| Evidence | Evidence found (for the task; see the page for the method) |
| Related ledger entries | RK61, A5, RK60 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Hierarchical Scholarly
Factor Risk Parity Strategy Ver-64") combine a method word, "Scholarly",
a task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Estimate factor volatility and dependence, then choose weights so the
factors' risk contributions match a target budget. The hierarchical
version organises assets or states in a tree and allocates or pools
estimates down it. Hierarchical risk allocation already exists here as
HRP, which budgets risk down a correlation tree instead of across
factors.

## The CSV's description

Proposed hierarchical approach to factor risk-parity allocation:
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
* The hierarchy is itself estimated; a different clustering gives
  different weights.

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
| 1624 | Hierarchical Scholarly Factor Risk Parity Strategy Ver-64 | Operator theory / Fixed income / ETF allocation | 3826 | 970 | No |
| 1648 | Hierarchical Scholarly Factor Risk Parity Strategy Ver-164 | Operator theory / Fixed income / ETF allocation | 2074 | 2887 | No |
