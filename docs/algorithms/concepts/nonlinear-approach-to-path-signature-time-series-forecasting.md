# Nonlinear approach to path-signature time-series forecasting

**Concept page** · shared by **5** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #8,484) ·
researched 2026-10-30

| | |
|---|---|
| Task | Path-signature time-series forecasting |
| Method | Nonlinear models |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Signature forecasting has no out-of-sample trading evidence; a better method word does not fix that. |
| Implemented in volatility-ai | Signatures are research code (`point_processes`, `cross_section`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK328 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Non-Linear Scholarly Tensor
Signature Predictor Alpha-26") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Encode the ordered evolution of market data with path-signature features
and forecast a target from them. The nonlinear version replaces linear
rules with nonlinear regressions or filters. I found no study of this
method on this task.

## The CSV's description

Proposed nonlinear approach to path-signature time-series forecasting:
Encode the ordered evolution of multivariate market data with
path-signature features and use them to forecast a defined target; the
asset, horizon, and conversion of forecasts into trades remain
unspecified. This is a concept-level interpretation of the title, not a
complete trading specification: the exact model inputs/target,
calibration, entry/exit or rebalance rules, and position sizing are not
fully defined here.

## Evidence

* **Futter, Horvath & Wiese (2023):** positions linear in the signature
  have an explicit mean-variance solution (see RK328); a construction,
  not an out-of-sample trading result.

## Against, and failure modes

* Signature features grow fast with depth and dimension; no
  out-of-sample trading result found.
* Nonlinear fits on a few thousand daily bars overfit easily; gains over
  linear rules are usually small out of sample.

## Fit with volatility-ai

No trading evidence; the signature code exists only as a reference
(RK328).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Futter, O., Horvath, B., Wiese, M. (2023). "Signature Trading." See
  RK328.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 8484 | Non-Linear Scholarly Tensor Signature Predictor Alpha-26 | Quantum machine learning / Parametrized circuits / Index forecasting | 13976 | 13974 | No |
| 8524 | Non-Linear Scholarly Tensor Signature Predictor Alpha-126 | Quantum machine learning / Parametrized circuits / Index forecasting | 11268 | 5944 | No |
| 8564 | Non-Linear Scholarly Tensor Signature Predictor Alpha-226 | Quantum machine learning / Parametrized circuits / Index forecasting | 11272 | 5948 | No |
| 8604 | Non-Linear Scholarly Tensor Signature Predictor Alpha-326 | Quantum machine learning / Parametrized circuits / Index forecasting | 13980 | 13978 | No |
| 8644 | Non-Linear Scholarly Tensor Signature Predictor Alpha-426 | Quantum machine learning / Parametrized circuits / Index forecasting | 11281 | 5957 | No |
