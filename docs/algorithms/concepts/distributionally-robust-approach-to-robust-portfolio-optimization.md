# Distributionally robust approach to robust portfolio optimization

**Concept page** · shared by **2** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #8,432) ·
researched 2026-10-30

| | |
|---|---|
| Task | Robust portfolio optimisation |
| Method | Distributionally robust optimisation |
| Fit with this project | 🧪 reference only · background, nothing to build now |
| Useful for volatility-ai | **Reference only.** A tractable, well-founded allocator (RK88), but the book has nothing to allocate across until a multi-ETF sleeve exists; background. |
| Implemented in volatility-ai | CVaR allocation is research code (`allocation.cvar_weights`, RK88). |
| Evidence | Evidence found (for the task; see the page for the method) |
| Related ledger entries | RK88, RK53, A5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Distributionally Robust
Scholarly Quantitative Stock Selector Ver-47") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Choose portfolio weights while allowing for uncertainty in the estimated
return distribution or tail losses. The distributionally robust version
optimises against the worst distribution in a ball around the empirical
one. I found no study of this method on this task.

## The CSV's description

Proposed distributionally robust approach to robust portfolio
optimization: Choose portfolio weights while allowing for uncertainty in
estimated return distributions or tail losses; the uncertainty set, risk
measure, and constraints require explicit definitions. This is a
concept-level interpretation of the title, not a complete trading
specification: the exact model inputs/target, calibration, entry/exit or
rebalance rules, and position sizing are not fully defined here.

## Evidence

* **Mohajerin Esfahani & Kuhn (2018), *Mathematical Programming* 171:**
  Wasserstein distributionally robust optimisation is tractable and has
  finite-sample guarantees (see RK88). (Abstract.)
* **DeMiguel, Garlappi & Uppal (2009), "Optimal Versus Naive
  Diversification," *Review of Financial Studies* 22(5), 1915–1953:**
  none of 14 optimised allocations consistently beat 1/N out of sample.
  (Standard reference.)

## Against, and failure modes

* The uncertainty set decides the answer; wide sets return cash or 1/N.
* The ball's radius sets the answer; too wide a ball returns cash or
  1/N.

## Fit with volatility-ai

An allocator for a multi-asset book. The distributionally robust CVaR
allocator (RK88) is the researched version; the engine trades one
symbol.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Mohajerin Esfahani, P., Kuhn, D. (2018). *Mathematical Programming*
  171, 115–166. Abstract.
* DeMiguel, V., Garlappi, L., Uppal, R. (2009). *Review of Financial
  Studies* 22(5), 1915–1953. Standard reference.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 8432 | Distributionally Robust Scholarly Quantitative Stock Selector Ver-47 | Reinforcement learning / Game theory / ETF arbitrage | 10855 | 10704 | No |
| 8461 | Distributionally Robust Scholarly Quantitative Stock Selector Ver-147 | Reinforcement learning / Game theory / ETF arbitrage | 4595 | 10708 | No |
