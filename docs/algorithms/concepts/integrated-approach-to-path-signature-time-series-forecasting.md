# Integrated approach to path-signature time-series forecasting

**Concept page** · shared by **5** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #8,492) ·
researched 2026-10-30

| | |
|---|---|
| Task | Path-signature time-series forecasting |
| Method | Integrated (combined) models |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Signature forecasting has no out-of-sample trading evidence; a better method word does not fix that. |
| Implemented in volatility-ai | Signatures are research code (`point_processes`, `cross_section`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK328 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Holistic Scholarly Tensor
Signature Predictor Alpha-46") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Encode the ordered evolution of market data with path-signature features
and forecast a target from them. The integrated version chains several
models or data sources into one pipeline; the title does not say which.
I found no study of this method on this task.

## The CSV's description

Proposed integrated approach to path-signature time-series forecasting:
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
* An unspecified combination cannot be tested as stated; each part would
  need its own evidence.

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
| 8492 | Holistic Scholarly Tensor Signature Predictor Alpha-46 | Quantum machine learning / Parametrized circuits / Index forecasting | 11265 | 5941 | No |
| 8532 | Holistic Scholarly Tensor Signature Predictor Alpha-146 | Quantum machine learning / Parametrized circuits / Index forecasting | 13978 | 13976 | No |
| 8572 | Holistic Scholarly Tensor Signature Predictor Alpha-246 | Quantum machine learning / Parametrized circuits / Index forecasting | 11273 | 5949 | No |
| 8612 | Holistic Scholarly Tensor Signature Predictor Alpha-346 | Quantum machine learning / Parametrized circuits / Index forecasting | 11278 | 5954 | No |
| 8652 | Holistic Scholarly Tensor Signature Predictor Alpha-446 | Quantum machine learning / Parametrized circuits / Index forecasting | 13982 | 13980 | No |
