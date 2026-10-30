# Spectral approach to path-signature time-series forecasting

**Concept page** · shared by **63** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,842) ·
researched 2026-10-30

| | |
|---|---|
| Task | Path-signature time-series forecasting |
| Method | Spectral (frequency-domain) decomposition |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Signature forecasting has no out-of-sample trading evidence; a better method word does not fix that. |
| Implemented in volatility-ai | Signatures are research code (`point_processes`, `cross_section`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK328 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Spectral Scholarly Tensor
Signature Predictor Sys-42") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Encode the ordered evolution of market data with path-signature features
and forecast a target from them. The spectral version works in the
frequency domain, filtering or weighting components by cycle length. I
found no study of this method on this task.

## The CSV's description

Proposed spectral approach to path-signature time-series forecasting:
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
* Spectral estimates need long stationary windows; market cycles are
  neither.

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
| 1842 | Spectral Scholarly Tensor Signature Predictor Sys-42 | Robust optimization / Distributionally robust CVaR / Index tracking | 1120 | 1082 | No |
| 1891 | Spectral Scholarly Tensor Signature Predictor Sys-522 | Robust optimization / Distributionally robust CVaR / Index tracking | 1150 | 1106 | No |
| 1940 | Spectral Scholarly Tensor Signature Predictor Sys-1002 | Robust optimization / Distributionally robust CVaR / Index tracking | 1180 | 1130 | No |
| 1989 | Spectral Scholarly Tensor Signature Predictor Sys-1482 | Robust optimization / Distributionally robust CVaR / Index tracking | 1210 | 1154 | No |
| 2038 | Spectral Scholarly Tensor Signature Predictor Sys-1962 | Robust optimization / Distributionally robust CVaR / Index tracking | 1240 | 1178 | No |
| 2077 | Spectral Scholarly Tensor Signature Predictor Mod-342 | Robust optimization / Distributionally robust CVaR / Index tracking | 1263 | 1196 | No |
| 2130 | Spectral Scholarly Tensor Signature Predictor Mod-822 | Robust optimization / Distributionally robust CVaR / Index tracking | 1294 | 1220 | No |
| 2183 | Spectral Scholarly Tensor Signature Predictor Mod-1302 | Robust optimization / Distributionally robust CVaR / Index tracking | 1325 | 1244 | No |
| 2236 | Spectral Scholarly Tensor Signature Predictor Mod-1782 | Robust optimization / Distributionally robust CVaR / Index tracking | 1356 | 1268 | No |
| 2289 | Spectral Scholarly Tensor Signature Predictor Mod-2262 | Robust optimization / Distributionally robust CVaR / Index tracking | 1387 | 1292 | No |
| 2342 | Spectral Scholarly Tensor Signature Predictor Mod-2742 | Robust optimization / Distributionally robust CVaR / Index tracking | 1418 | 1316 | No |
| 2395 | Spectral Scholarly Tensor Signature Predictor Mod-3222 | Robust optimization / Distributionally robust CVaR / Index tracking | 1449 | 1340 | No |
| 2448 | Spectral Scholarly Tensor Signature Predictor Mod-3702 | Robust optimization / Distributionally robust CVaR / Index tracking | 1480 | 1364 | No |
| 3222 | Spectral Scholarly Tensor Signature Predictor Sys-234 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1134 | 3301 | No |
| 3244 | Spectral Scholarly Tensor Signature Predictor Sys-714 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1164 | 3396 | No |
| 3266 | Spectral Scholarly Tensor Signature Predictor Sys-1194 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1194 | 3491 | No |
| 3288 | Spectral Scholarly Tensor Signature Predictor Sys-1674 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1224 | 3586 | No |
| 3304 | Spectral Scholarly Tensor Signature Predictor Mod-54 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1247 | 3661 | No |
| 3322 | Spectral Scholarly Tensor Signature Predictor Mod-534 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1278 | 3756 | No |
| 3340 | Spectral Scholarly Tensor Signature Predictor Mod-1014 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1309 | 3851 | No |
| 3358 | Spectral Scholarly Tensor Signature Predictor Mod-1494 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1340 | 3946 | No |
| 3376 | Spectral Scholarly Tensor Signature Predictor Mod-1974 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1371 | 4041 | No |
| 3394 | Spectral Scholarly Tensor Signature Predictor Mod-2454 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1402 | 4136 | No |
| 3412 | Spectral Scholarly Tensor Signature Predictor Mod-2934 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1433 | 4231 | No |
| 3430 | Spectral Scholarly Tensor Signature Predictor Mod-3414 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1464 | 4326 | No |
| 3448 | Spectral Scholarly Tensor Signature Predictor Mod-3894 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1495 | 4421 | No |
| 7531 | Spectral Scholarly Tensor Signature Predictor Sys-138 | Attention networks / Transformer encoders / Stock alpha generation | 3250 | 6596 | No |
| 7562 | Spectral Scholarly Tensor Signature Predictor Sys-618 | Attention networks / Transformer encoders / Stock alpha generation | 3274 | 6632 | No |
| 7593 | Spectral Scholarly Tensor Signature Predictor Sys-1098 | Attention networks / Transformer encoders / Stock alpha generation | 3298 | 6668 | No |
| 7624 | Spectral Scholarly Tensor Signature Predictor Sys-1578 | Attention networks / Transformer encoders / Stock alpha generation | 3322 | 6704 | No |
| 7678 | Spectral Scholarly Tensor Signature Predictor Mod-438 | Attention networks / Transformer encoders / Stock alpha generation | 3361 | 6767 | No |
| 7710 | Spectral Scholarly Tensor Signature Predictor Mod-918 | Attention networks / Transformer encoders / Stock alpha generation | 3381 | 6801 | No |
| 7742 | Spectral Scholarly Tensor Signature Predictor Mod-1398 | Attention networks / Transformer encoders / Stock alpha generation | 3401 | 6835 | No |
| 7774 | Spectral Scholarly Tensor Signature Predictor Mod-1878 | Attention networks / Transformer encoders / Stock alpha generation | 3421 | 6869 | No |
| 7806 | Spectral Scholarly Tensor Signature Predictor Mod-2358 | Attention networks / Transformer encoders / Stock alpha generation | 3441 | 6903 | No |
| 7838 | Spectral Scholarly Tensor Signature Predictor Mod-2838 | Attention networks / Transformer encoders / Stock alpha generation | 3461 | 6937 | No |
| 7870 | Spectral Scholarly Tensor Signature Predictor Mod-3318 | Attention networks / Transformer encoders / Stock alpha generation | 3481 | 6971 | No |
| 7902 | Spectral Scholarly Tensor Signature Predictor Mod-3798 | Attention networks / Transformer encoders / Stock alpha generation | 3501 | 7005 | No |
| 9204 | Spectral Scholarly Tensor Signature Predictor Sys-330 | Neural operators / Deep operator networks / ETF rotation | 5889 | 2213 | No |
| 9240 | Spectral Scholarly Tensor Signature Predictor Sys-426 | Quantum machine learning / Variational circuits / Index prediction | 11359 | 6016 | No |
| 9391 | Spectral Scholarly Tensor Signature Predictor Sys-810 | Neural operators / Deep operator networks / ETF rotation | 5909 | 2232 | No |
| 9427 | Spectral Scholarly Tensor Signature Predictor Sys-906 | Quantum machine learning / Variational circuits / Index prediction | 11385 | 6031 | No |
| 9578 | Spectral Scholarly Tensor Signature Predictor Sys-1290 | Neural operators / Deep operator networks / ETF rotation | 5929 | 2251 | No |
| 9614 | Spectral Scholarly Tensor Signature Predictor Sys-1386 | Quantum machine learning / Variational circuits / Index prediction | 11411 | 6046 | No |
| 9765 | Spectral Scholarly Tensor Signature Predictor Sys-1770 | Neural operators / Deep operator networks / ETF rotation | 5949 | 2270 | No |
| 9801 | Spectral Scholarly Tensor Signature Predictor Sys-1866 | Quantum machine learning / Variational circuits / Index prediction | 11437 | 6061 | No |
| 9910 | Spectral Scholarly Tensor Signature Predictor Mod-150 | Neural operators / Deep operator networks / ETF rotation | 5968 | 2286 | No |
| 9952 | Spectral Scholarly Tensor Signature Predictor Mod-246 | Quantum machine learning / Variational circuits / Index prediction | 11461 | 6076 | No |
| 10101 | Spectral Scholarly Tensor Signature Predictor Mod-630 | Neural operators / Deep operator networks / ETF rotation | 5992 | 2309 | No |
| 10143 | Spectral Scholarly Tensor Signature Predictor Mod-726 | Quantum machine learning / Variational circuits / Index prediction | 11488 | 6093 | No |
| 10292 | Spectral Scholarly Tensor Signature Predictor Mod-1110 | Neural operators / Deep operator networks / ETF rotation | 6016 | 2332 | No |
| 10334 | Spectral Scholarly Tensor Signature Predictor Mod-1206 | Quantum machine learning / Variational circuits / Index prediction | 11515 | 6110 | No |
| 10483 | Spectral Scholarly Tensor Signature Predictor Mod-1590 | Neural operators / Deep operator networks / ETF rotation | 6040 | 2355 | No |
| 10525 | Spectral Scholarly Tensor Signature Predictor Mod-1686 | Quantum machine learning / Variational circuits / Index prediction | 11542 | 6127 | No |
| 10674 | Spectral Scholarly Tensor Signature Predictor Mod-2070 | Neural operators / Deep operator networks / ETF rotation | 6064 | 2378 | No |
| 10716 | Spectral Scholarly Tensor Signature Predictor Mod-2166 | Quantum machine learning / Variational circuits / Index prediction | 11569 | 6144 | No |
| 10865 | Spectral Scholarly Tensor Signature Predictor Mod-2550 | Neural operators / Deep operator networks / ETF rotation | 6088 | 2401 | No |
| 10907 | Spectral Scholarly Tensor Signature Predictor Mod-2646 | Quantum machine learning / Variational circuits / Index prediction | 11596 | 6161 | No |
| 11056 | Spectral Scholarly Tensor Signature Predictor Mod-3030 | Neural operators / Deep operator networks / ETF rotation | 6112 | 2424 | No |
| 11098 | Spectral Scholarly Tensor Signature Predictor Mod-3126 | Quantum machine learning / Variational circuits / Index prediction | 11623 | 6178 | No |
| 11247 | Spectral Scholarly Tensor Signature Predictor Mod-3510 | Neural operators / Deep operator networks / ETF rotation | 6136 | 2447 | No |
| 11289 | Spectral Scholarly Tensor Signature Predictor Mod-3606 | Quantum machine learning / Variational circuits / Index prediction | 11650 | 6195 | No |
| 11438 | Spectral Scholarly Tensor Signature Predictor Mod-3990 | Neural operators / Deep operator networks / ETF rotation | 6160 | 2470 | No |
