# Conformal-prediction-based approach to path-signature time-series forecasting

**Concept page** · shared by **62** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,880) ·
researched 2026-10-30

| | |
|---|---|
| Task | Path-signature time-series forecasting |
| Method | Conformal prediction intervals |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Signature forecasting has no out-of-sample trading evidence; a better method word does not fix that. |
| Implemented in volatility-ai | Signatures are research code (`point_processes`, `cross_section`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK328 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Conformal Scholarly Tensor
Signature Predictor Sys-402") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Encode the ordered evolution of market data with path-signature features
and forecast a target from them. The conformal version wraps a forecast
in distribution-free prediction intervals and acts only when the
interval is decisive. I found no study of this method on this task.

## The CSV's description

Proposed conformal-prediction-based approach to path-signature
time-series forecasting: Encode the ordered evolution of multivariate
market data with path-signature features and use them to forecast a
defined target; the asset, horizon, and conversion of forecasts into
trades remain unspecified. This is a concept-level interpretation of the
title, not a complete trading specification: the exact model
inputs/target, calibration, entry/exit or rebalance rules, and position
sizing are not fully defined here.

## Evidence

* **Futter, Horvath & Wiese (2023):** positions linear in the signature
  have an explicit mean-variance solution (see RK328); a construction,
  not an out-of-sample trading result.

## Against, and failure modes

* Signature features grow fast with depth and dimension; no
  out-of-sample trading result found.
* Conformal intervals measure a forecast's uncertainty; they do not
  create a forecast where none exists.

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
| 1880 | Conformal Scholarly Tensor Signature Predictor Sys-402 | Robust optimization / Distributionally robust CVaR / Index tracking | 1143 | 1099 | No |
| 1929 | Conformal Scholarly Tensor Signature Predictor Sys-882 | Robust optimization / Distributionally robust CVaR / Index tracking | 1173 | 1123 | No |
| 1978 | Conformal Scholarly Tensor Signature Predictor Sys-1362 | Robust optimization / Distributionally robust CVaR / Index tracking | 1203 | 1147 | No |
| 2027 | Conformal Scholarly Tensor Signature Predictor Sys-1842 | Robust optimization / Distributionally robust CVaR / Index tracking | 1233 | 1171 | No |
| 2091 | Conformal Scholarly Tensor Signature Predictor Mod-462 | Robust optimization / Distributionally robust CVaR / Index tracking | 1272 | 1203 | No |
| 2144 | Conformal Scholarly Tensor Signature Predictor Mod-942 | Robust optimization / Distributionally robust CVaR / Index tracking | 1303 | 1227 | No |
| 2197 | Conformal Scholarly Tensor Signature Predictor Mod-1422 | Robust optimization / Distributionally robust CVaR / Index tracking | 1334 | 1251 | No |
| 2250 | Conformal Scholarly Tensor Signature Predictor Mod-1902 | Robust optimization / Distributionally robust CVaR / Index tracking | 1365 | 1275 | No |
| 2303 | Conformal Scholarly Tensor Signature Predictor Mod-2382 | Robust optimization / Distributionally robust CVaR / Index tracking | 1396 | 1299 | No |
| 2356 | Conformal Scholarly Tensor Signature Predictor Mod-2862 | Robust optimization / Distributionally robust CVaR / Index tracking | 1427 | 1323 | No |
| 2409 | Conformal Scholarly Tensor Signature Predictor Mod-3342 | Robust optimization / Distributionally robust CVaR / Index tracking | 1458 | 1347 | No |
| 2462 | Conformal Scholarly Tensor Signature Predictor Mod-3822 | Robust optimization / Distributionally robust CVaR / Index tracking | 1489 | 1371 | No |
| 3215 | Conformal Scholarly Tensor Signature Predictor Sys-114 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1127 | 3277 | No |
| 3237 | Conformal Scholarly Tensor Signature Predictor Sys-594 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1157 | 3372 | No |
| 3259 | Conformal Scholarly Tensor Signature Predictor Sys-1074 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1187 | 3467 | No |
| 3281 | Conformal Scholarly Tensor Signature Predictor Sys-1554 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1217 | 3562 | No |
| 3309 | Conformal Scholarly Tensor Signature Predictor Mod-174 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1254 | 3684 | No |
| 3327 | Conformal Scholarly Tensor Signature Predictor Mod-654 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1285 | 3779 | No |
| 3345 | Conformal Scholarly Tensor Signature Predictor Mod-1134 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1316 | 3874 | No |
| 3363 | Conformal Scholarly Tensor Signature Predictor Mod-1614 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1347 | 3969 | No |
| 3381 | Conformal Scholarly Tensor Signature Predictor Mod-2094 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1378 | 4064 | No |
| 3399 | Conformal Scholarly Tensor Signature Predictor Mod-2574 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1409 | 4159 | No |
| 3417 | Conformal Scholarly Tensor Signature Predictor Mod-3054 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1440 | 4254 | No |
| 3435 | Conformal Scholarly Tensor Signature Predictor Mod-3534 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1471 | 4349 | No |
| 7522 | Conformal Scholarly Tensor Signature Predictor Sys-18 | Attention networks / Transformer encoders / Stock alpha generation | 3244 | 6587 | No |
| 7553 | Conformal Scholarly Tensor Signature Predictor Sys-498 | Attention networks / Transformer encoders / Stock alpha generation | 3268 | 6623 | No |
| 7584 | Conformal Scholarly Tensor Signature Predictor Sys-978 | Attention networks / Transformer encoders / Stock alpha generation | 3292 | 6659 | No |
| 7615 | Conformal Scholarly Tensor Signature Predictor Sys-1458 | Attention networks / Transformer encoders / Stock alpha generation | 3316 | 6695 | No |
| 7646 | Conformal Scholarly Tensor Signature Predictor Sys-1938 | Attention networks / Transformer encoders / Stock alpha generation | 3340 | 6731 | No |
| 7655 | Conformal Scholarly Tensor Signature Predictor Mod-78 | Attention networks / Transformer encoders / Stock alpha generation | 3346 | 6741 | No |
| 7687 | Conformal Scholarly Tensor Signature Predictor Mod-558 | Attention networks / Transformer encoders / Stock alpha generation | 3366 | 6775 | No |
| 7719 | Conformal Scholarly Tensor Signature Predictor Mod-1038 | Attention networks / Transformer encoders / Stock alpha generation | 3386 | 6809 | No |
| 7751 | Conformal Scholarly Tensor Signature Predictor Mod-1518 | Attention networks / Transformer encoders / Stock alpha generation | 3406 | 6843 | No |
| 7783 | Conformal Scholarly Tensor Signature Predictor Mod-1998 | Attention networks / Transformer encoders / Stock alpha generation | 3426 | 6877 | No |
| 7815 | Conformal Scholarly Tensor Signature Predictor Mod-2478 | Attention networks / Transformer encoders / Stock alpha generation | 3446 | 6911 | No |
| 7847 | Conformal Scholarly Tensor Signature Predictor Mod-2958 | Attention networks / Transformer encoders / Stock alpha generation | 3466 | 6945 | No |
| 7879 | Conformal Scholarly Tensor Signature Predictor Mod-3438 | Attention networks / Transformer encoders / Stock alpha generation | 3486 | 6979 | No |
| 7911 | Conformal Scholarly Tensor Signature Predictor Mod-3918 | Attention networks / Transformer encoders / Stock alpha generation | 3506 | 7013 | No |
| 9155 | Conformal Scholarly Tensor Signature Predictor Sys-210 | Neural operators / Deep operator networks / ETF rotation | 5886 | 2209 | No |
| 9193 | Conformal Scholarly Tensor Signature Predictor Sys-306 | Quantum machine learning / Variational circuits / Index prediction | 11353 | 6013 | No |
| 9342 | Conformal Scholarly Tensor Signature Predictor Sys-690 | Neural operators / Deep operator networks / ETF rotation | 5906 | 2228 | No |
| 9380 | Conformal Scholarly Tensor Signature Predictor Sys-786 | Quantum machine learning / Variational circuits / Index prediction | 11379 | 6028 | No |
| 9529 | Conformal Scholarly Tensor Signature Predictor Sys-1170 | Neural operators / Deep operator networks / ETF rotation | 5926 | 2247 | No |
| 9567 | Conformal Scholarly Tensor Signature Predictor Sys-1266 | Quantum machine learning / Variational circuits / Index prediction | 11405 | 6043 | No |
| 9716 | Conformal Scholarly Tensor Signature Predictor Sys-1650 | Neural operators / Deep operator networks / ETF rotation | 5946 | 2266 | No |
| 9754 | Conformal Scholarly Tensor Signature Predictor Sys-1746 | Quantum machine learning / Variational circuits / Index prediction | 11431 | 6058 | No |
| 9962 | Conformal Scholarly Tensor Signature Predictor Mod-270 | Neural operators / Deep operator networks / ETF rotation | 5973 | 2292 | No |
| 10000 | Conformal Scholarly Tensor Signature Predictor Mod-366 | Quantum machine learning / Variational circuits / Index prediction | 11467 | 6080 | No |
| 10153 | Conformal Scholarly Tensor Signature Predictor Mod-750 | Neural operators / Deep operator networks / ETF rotation | 5997 | 2315 | No |
| 10191 | Conformal Scholarly Tensor Signature Predictor Mod-846 | Quantum machine learning / Variational circuits / Index prediction | 11494 | 6097 | No |
| 10344 | Conformal Scholarly Tensor Signature Predictor Mod-1230 | Neural operators / Deep operator networks / ETF rotation | 6021 | 2338 | No |
| 10382 | Conformal Scholarly Tensor Signature Predictor Mod-1326 | Quantum machine learning / Variational circuits / Index prediction | 11521 | 6114 | No |
| 10535 | Conformal Scholarly Tensor Signature Predictor Mod-1710 | Neural operators / Deep operator networks / ETF rotation | 6045 | 2361 | No |
| 10573 | Conformal Scholarly Tensor Signature Predictor Mod-1806 | Quantum machine learning / Variational circuits / Index prediction | 11548 | 6131 | No |
| 10726 | Conformal Scholarly Tensor Signature Predictor Mod-2190 | Neural operators / Deep operator networks / ETF rotation | 6069 | 2384 | No |
| 10764 | Conformal Scholarly Tensor Signature Predictor Mod-2286 | Quantum machine learning / Variational circuits / Index prediction | 11575 | 6148 | No |
| 10917 | Conformal Scholarly Tensor Signature Predictor Mod-2670 | Neural operators / Deep operator networks / ETF rotation | 6093 | 2407 | No |
| 10955 | Conformal Scholarly Tensor Signature Predictor Mod-2766 | Quantum machine learning / Variational circuits / Index prediction | 11602 | 6165 | No |
| 11108 | Conformal Scholarly Tensor Signature Predictor Mod-3150 | Neural operators / Deep operator networks / ETF rotation | 6117 | 2430 | No |
| 11146 | Conformal Scholarly Tensor Signature Predictor Mod-3246 | Quantum machine learning / Variational circuits / Index prediction | 11629 | 6182 | No |
| 11299 | Conformal Scholarly Tensor Signature Predictor Mod-3630 | Neural operators / Deep operator networks / ETF rotation | 6141 | 2453 | No |
| 11337 | Conformal Scholarly Tensor Signature Predictor Mod-3726 | Quantum machine learning / Variational circuits / Index prediction | 11656 | 6199 | No |
