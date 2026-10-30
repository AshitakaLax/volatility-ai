# Fractional-order approach to covariance estimation for portfolio risk

**Concept page** · shared by **5** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #3,703) ·
researched 2026-10-30

| | |
|---|---|
| Task | Covariance estimation for portfolio risk |
| Method | Fractional-order models (long memory, fractional calculus) |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of fractional-order models beating shrinkage covariance, and the book has no covariance to estimate. |
| Implemented in volatility-ai | Covariance estimators are research code (`concepts.dcc_garch_covariance`, `concepts.robust_covariance`, `spd_covariance`); HRP is built (A5). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK60, A5, RK232 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Fractional Scholarly
Manifold Covariance Estimator Alpha-99") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Estimate a more stable covariance matrix of asset returns for portfolio
construction, risk budgeting or hedging. The fractional-order version
models long memory with fractional differencing or fractional-order
dynamics. I found no study of this method on this task.

## The CSV's description

Proposed fractional-order approach to covariance estimation for
portfolio risk: Estimate a more stable asset-return covariance matrix
using regularization or geometric constraints, then use it for portfolio
construction, risk budgeting, or hedging. This is a concept-level
interpretation of the title, not a complete trading specification: the
exact model inputs/target, calibration, entry/exit or rebalance rules,
and position sizing are not fully defined here.

## Evidence

* **Ledoit & Wolf (2004, 2017):** linear and nonlinear shrinkage of the
  sample covariance, the baselines any new estimator must beat.
  (Standard references.)
* **Engle (2002), "Dynamic conditional correlation," *Journal of
  Business & Economic Statistics* 20(3):** DCC-GARCH for time-varying
  correlations. (Standard reference.)

## Against, and failure modes

* A new estimator must beat nonlinear shrinkage out of sample; few
  studies show it.
* Long memory in returns is weak once short-range dependence is allowed
  for (Lo 1991); in volatility, the simpler HAR model reproduces it
  (Corsi 2009).

## Fit with volatility-ai

A covariance matrix is an input to a multi-asset allocator; the engine
trades one symbol, and HRP (A5) estimates its own correlation
clustering. Not a candidate until a multi-ETF book exists.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Ledoit, O., Wolf, M. (2017). "Nonlinear Shrinkage of the Covariance
  Matrix for Portfolio Selection." *Review of Financial Studies* 30(12).
  Not re-checked.
* Engle, R. (2002). *Journal of Business & Economic Statistics* 20(3).
  Not re-checked.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 3703 | Fractional Scholarly Manifold Covariance Estimator Alpha-99 | Riemannian manifold / Geodesic descent / Stock portfolio optimization | 2088 | 2921 | No |
| 3720 | Fractional Scholarly Manifold Covariance Estimator Alpha-199 | Riemannian manifold / Geodesic descent / Stock portfolio optimization | 8201 | 2942 | No |
| 3737 | Fractional Scholarly Manifold Covariance Estimator Alpha-299 | Riemannian manifold / Geodesic descent / Stock portfolio optimization | 6477 | 8412 | No |
| 3754 | Fractional Scholarly Manifold Covariance Estimator Alpha-399 | Riemannian manifold / Geodesic descent / Stock portfolio optimization | 2118 | 2989 | No |
| 3771 | Fractional Scholarly Manifold Covariance Estimator Alpha-499 | Riemannian manifold / Geodesic descent / Stock portfolio optimization | 8234 | 3010 | No |
