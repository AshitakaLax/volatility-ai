# Path-signature-based approach to path-signature time-series forecasting

**Concept page** · shared by **10** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #8,501) ·
researched 2026-10-30

| | |
|---|---|
| Task | Path-signature time-series forecasting |
| Method | Path signatures |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Signature forecasting has no out-of-sample trading evidence; a better method word does not fix that. |
| Implemented in volatility-ai | Signatures are research code (`point_processes`, `cross_section`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK328 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Wasserstein Scholarly
Tensor Signature Predictor Alpha-66") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Encode the ordered evolution of market data with path-signature features
and forecast a target from them. The path-signature version describes
price paths by their iterated-integral signatures and fits on those
features. I found no study of this method on this task.

## The CSV's description

Proposed path-signature-based approach to path-signature time-series
forecasting: Encode the ordered evolution of multivariate market data
with path-signature features and use them to forecast a defined target;
the asset, horizon, and conversion of forecasts into trades remain
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
* Signature features multiply with depth and dimension; no out-of-sample
  trading evidence found (RK328).

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
| 8501 | Wasserstein Scholarly Tensor Signature Predictor Alpha-66 | Quantum machine learning / Parametrized circuits / Index forecasting | 12638 | 9813 | No |
| 8509 | Signature Scholarly Tensor Signature Predictor Alpha-86 | Quantum machine learning / Parametrized circuits / Index forecasting | 13977 | 13975 | No |
| 8541 | Wasserstein Scholarly Tensor Signature Predictor Alpha-166 | Quantum machine learning / Parametrized circuits / Index forecasting | 12640 | 9814 | No |
| 8549 | Signature Scholarly Tensor Signature Predictor Alpha-186 | Quantum machine learning / Parametrized circuits / Index forecasting | 11270 | 5946 | No |
| 8581 | Wasserstein Scholarly Tensor Signature Predictor Alpha-266 | Quantum machine learning / Parametrized circuits / Index forecasting | 14225 | 14199 | No |
| 8589 | Signature Scholarly Tensor Signature Predictor Alpha-286 | Quantum machine learning / Parametrized circuits / Index forecasting | 11275 | 5951 | No |
| 8621 | Wasserstein Scholarly Tensor Signature Predictor Alpha-366 | Quantum machine learning / Parametrized circuits / Index forecasting | 12641 | 9816 | No |
| 8629 | Signature Scholarly Tensor Signature Predictor Alpha-386 | Quantum machine learning / Parametrized circuits / Index forecasting | 13981 | 13979 | No |
| 8661 | Wasserstein Scholarly Tensor Signature Predictor Alpha-466 | Quantum machine learning / Parametrized circuits / Index forecasting | 12643 | 9817 | No |
| 8669 | Signature Scholarly Tensor Signature Predictor Alpha-486 | Quantum machine learning / Parametrized circuits / Index forecasting | 11283 | 5959 | No |
