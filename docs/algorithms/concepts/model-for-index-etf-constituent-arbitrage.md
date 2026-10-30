# Model for index/ETF constituent arbitrage

**Concept page** · shared by **6** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,630) ·
researched 2026-10-30

| | |
|---|---|
| Task | Index / ETF constituent arbitrage |
| Method | Unspecified model |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Constituent arbitrage needs creation/redemption access or a short leg against the basket; both are outside this book. |
| Implemented in volatility-ai | Creation/redemption arbitrage is research code in `excluded` (C-RJ6). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK24, C-RJ6 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Manifold-Valued Scholarly
Index Arbitrage Model Ver-86") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Estimate fair-value gaps between an index-linked instrument and its
constituent basket and trade the convergence after fees and slippage.
The title names no method beyond "model", so this page judges the task
itself. The task itself is out of scope here; see the fit section.

## The CSV's description

Proposed model for index/ETF constituent arbitrage: Estimate fair-value
differences between an index-linked instrument and its constituent
basket, then evaluate convergence trades only after accounting for
synchronized prices, basket execution, fees, and slippage. This is a
concept-level interpretation of the title, not a complete trading
specification: the exact model inputs/target, calibration, entry/exit or
rebalance rules, and position sizing are not fully defined here.

## Evidence

* **Petajisto (2017), "Inefficiencies in the Pricing of Exchange-Traded
  Funds," *Financial Analysts Journal*:** ETF prices deviate from NAV in
  a band about 100 bp wide after correcting for stale NAVs (see RK24).
  (Abstract.)
* **Ben-David, Franzoni & Moussawi (2018), "Do ETFs Increase
  Volatility?" *Journal of Finance* 73(6), 2471–2535:** arbitrage
  between ETFs and their constituents passes ETF demand shocks into the
  stocks, raising their volatility. (Abstract.)

## Against, and failure modes

* The gaps are a few basis points for liquid ETFs and are closed by
  authorised participants with creation/redemption access.

## Fit with volatility-ai

Requires authorised-participant access or a hedged basket with a short
leg (C-RJ6, RK24). Out of scope.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Petajisto, A. (2017). *Financial Analysts Journal* 73(1). See RK24.
* Ben-David, I., Franzoni, F., Moussawi, R. (2018). *Journal of Finance*
  73(6), 2471–2535. Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 1630 | Manifold-Valued Scholarly Index Arbitrage Model Ver-86 | Quantum machine learning / Support vector machines / Stock forecasting | 14224 | 14198 | No |
| 1654 | Manifold-Valued Scholarly Index Arbitrage Model Ver-186 | Quantum machine learning / Support vector machines / Stock forecasting | 12637 | 11864 | No |
| 7405 | Optimal Scholarly Index Arbitrage Model MK-22 | Robust statistics / Mean-variance / Index allocation | 10025 | 11271 | No |
| 7409 | Optimal Scholarly Index Arbitrage Model MK-82 | Robust statistics / Mean-variance / Index allocation | 10027 | 11273 | No |
| 8431 | Recurrent Scholarly Index Arbitrage Model Ver-46 | Quantum machine learning / Support vector machines / Stock forecasting | 11258 | 11278 | No |
| 8460 | Recurrent Scholarly Index Arbitrage Model Ver-146 | Quantum machine learning / Support vector machines / Stock forecasting | 13975 | 13973 | No |
