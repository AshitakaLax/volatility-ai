# Diffusion-model-based approach to path-signature time-series forecasting

**Concept page** · shared by **63** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #3,981) ·
researched 2026-10-30

| | |
|---|---|
| Task | Path-signature time-series forecasting |
| Method | Diffusion generative models |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Signature forecasting has no out-of-sample trading evidence; a better method word does not fix that. |
| Implemented in volatility-ai | Signatures are research code (`point_processes`, `cross_section`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK328 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Diffusion Scholarly Tensor
Signature Predictor Sys-162") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Encode the ordered evolution of market data with path-signature features
and forecast a target from them. The diffusion-model version trains a
denoising generative model and samples scenarios or forecasts from it. I
found no study of this method on this task.

## The CSV's description

Proposed diffusion-model-based approach to path-signature time-series
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
* Generative models trained on a few thousand days memorise more than
  they generalise; no trading evidence found.

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
| 3981 | Diffusion Scholarly Tensor Signature Predictor Sys-162 | Robust optimization / Distributionally robust CVaR / Index tracking | 1128 | 1087 | No |
| 4067 | Diffusion Scholarly Tensor Signature Predictor Sys-642 | Robust optimization / Distributionally robust CVaR / Index tracking | 1158 | 1111 | No |
| 4153 | Diffusion Scholarly Tensor Signature Predictor Sys-1122 | Robust optimization / Distributionally robust CVaR / Index tracking | 1188 | 1135 | No |
| 4239 | Diffusion Scholarly Tensor Signature Predictor Sys-1602 | Robust optimization / Distributionally robust CVaR / Index tracking | 1218 | 1159 | No |
| 4351 | Diffusion Scholarly Tensor Signature Predictor Mod-222 | Robust optimization / Distributionally robust CVaR / Index tracking | 1256 | 1190 | No |
| 4436 | Diffusion Scholarly Tensor Signature Predictor Mod-702 | Robust optimization / Distributionally robust CVaR / Index tracking | 1287 | 1214 | No |
| 4521 | Diffusion Scholarly Tensor Signature Predictor Mod-1182 | Robust optimization / Distributionally robust CVaR / Index tracking | 1318 | 1238 | No |
| 4606 | Diffusion Scholarly Tensor Signature Predictor Mod-1662 | Robust optimization / Distributionally robust CVaR / Index tracking | 1349 | 1262 | No |
| 4691 | Diffusion Scholarly Tensor Signature Predictor Mod-2142 | Robust optimization / Distributionally robust CVaR / Index tracking | 1380 | 1286 | No |
| 4776 | Diffusion Scholarly Tensor Signature Predictor Mod-2622 | Robust optimization / Distributionally robust CVaR / Index tracking | 1411 | 1310 | No |
| 4861 | Diffusion Scholarly Tensor Signature Predictor Mod-3102 | Robust optimization / Distributionally robust CVaR / Index tracking | 1442 | 1334 | No |
| 4946 | Diffusion Scholarly Tensor Signature Predictor Mod-3582 | Robust optimization / Distributionally robust CVaR / Index tracking | 1473 | 1358 | No |
| 6310 | Diffusion Scholarly Tensor Signature Predictor Sys-354 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1141 | 3325 | No |
| 6351 | Diffusion Scholarly Tensor Signature Predictor Sys-834 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1171 | 3420 | No |
| 6392 | Diffusion Scholarly Tensor Signature Predictor Sys-1314 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1201 | 3515 | No |
| 6433 | Diffusion Scholarly Tensor Signature Predictor Sys-1794 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1231 | 3610 | No |
| 6491 | Diffusion Scholarly Tensor Signature Predictor Mod-414 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1269 | 3735 | No |
| 6536 | Diffusion Scholarly Tensor Signature Predictor Mod-894 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1300 | 3830 | No |
| 6581 | Diffusion Scholarly Tensor Signature Predictor Mod-1374 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1331 | 3925 | No |
| 6626 | Diffusion Scholarly Tensor Signature Predictor Mod-1854 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1362 | 4020 | No |
| 6671 | Diffusion Scholarly Tensor Signature Predictor Mod-2334 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1393 | 4115 | No |
| 6716 | Diffusion Scholarly Tensor Signature Predictor Mod-2814 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1424 | 4210 | No |
| 6761 | Diffusion Scholarly Tensor Signature Predictor Mod-3294 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1455 | 4305 | No |
| 6806 | Diffusion Scholarly Tensor Signature Predictor Mod-3774 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1486 | 4400 | No |
| 9098 | Diffusion Scholarly Tensor Signature Predictor Sys-66 | Quantum machine learning / Variational circuits / Index prediction | 11341 | 6006 | No |
| 9174 | Diffusion Scholarly Tensor Signature Predictor Sys-258 | Attention networks / Transformer encoders / Stock alpha generation | 3256 | 6605 | No |
| 9249 | Diffusion Scholarly Tensor Signature Predictor Sys-450 | Neural operators / Deep operator networks / ETF rotation | 5895 | 2218 | No |
| 9285 | Diffusion Scholarly Tensor Signature Predictor Sys-546 | Quantum machine learning / Variational circuits / Index prediction | 11367 | 6021 | No |
| 9361 | Diffusion Scholarly Tensor Signature Predictor Sys-738 | Attention networks / Transformer encoders / Stock alpha generation | 3280 | 6641 | No |
| 9436 | Diffusion Scholarly Tensor Signature Predictor Sys-930 | Neural operators / Deep operator networks / ETF rotation | 5915 | 2237 | No |
| 9472 | Diffusion Scholarly Tensor Signature Predictor Sys-1026 | Quantum machine learning / Variational circuits / Index prediction | 11393 | 6036 | No |
| 9548 | Diffusion Scholarly Tensor Signature Predictor Sys-1218 | Attention networks / Transformer encoders / Stock alpha generation | 3304 | 6677 | No |
| 9623 | Diffusion Scholarly Tensor Signature Predictor Sys-1410 | Neural operators / Deep operator networks / ETF rotation | 5935 | 2256 | No |
| 9659 | Diffusion Scholarly Tensor Signature Predictor Sys-1506 | Quantum machine learning / Variational circuits / Index prediction | 11419 | 6051 | No |
| 9735 | Diffusion Scholarly Tensor Signature Predictor Sys-1698 | Attention networks / Transformer encoders / Stock alpha generation | 3328 | 6713 | No |
| 9810 | Diffusion Scholarly Tensor Signature Predictor Sys-1890 | Neural operators / Deep operator networks / ETF rotation | 5955 | 2275 | No |
| 9846 | Diffusion Scholarly Tensor Signature Predictor Sys-1986 | Quantum machine learning / Variational circuits / Index prediction | 11445 | 6066 | No |
| 9864 | Diffusion Scholarly Tensor Signature Predictor Mod-30 | Neural operators / Deep operator networks / ETF rotation | 5961 | 2280 | No |
| 9902 | Diffusion Scholarly Tensor Signature Predictor Mod-126 | Quantum machine learning / Variational circuits / Index prediction | 11453 | 6072 | No |
| 9979 | Diffusion Scholarly Tensor Signature Predictor Mod-318 | Attention networks / Transformer encoders / Stock alpha generation | 3356 | 6758 | No |
| 10055 | Diffusion Scholarly Tensor Signature Predictor Mod-510 | Neural operators / Deep operator networks / ETF rotation | 5985 | 2303 | No |
| 10093 | Diffusion Scholarly Tensor Signature Predictor Mod-606 | Quantum machine learning / Variational circuits / Index prediction | 11480 | 6089 | No |
| 10170 | Diffusion Scholarly Tensor Signature Predictor Mod-798 | Attention networks / Transformer encoders / Stock alpha generation | 3376 | 6792 | No |
| 10246 | Diffusion Scholarly Tensor Signature Predictor Mod-990 | Neural operators / Deep operator networks / ETF rotation | 6009 | 2326 | No |
| 10284 | Diffusion Scholarly Tensor Signature Predictor Mod-1086 | Quantum machine learning / Variational circuits / Index prediction | 11507 | 6106 | No |
| 10361 | Diffusion Scholarly Tensor Signature Predictor Mod-1278 | Attention networks / Transformer encoders / Stock alpha generation | 3396 | 6826 | No |
| 10437 | Diffusion Scholarly Tensor Signature Predictor Mod-1470 | Neural operators / Deep operator networks / ETF rotation | 6033 | 2349 | No |
| 10475 | Diffusion Scholarly Tensor Signature Predictor Mod-1566 | Quantum machine learning / Variational circuits / Index prediction | 11534 | 6123 | No |
| 10552 | Diffusion Scholarly Tensor Signature Predictor Mod-1758 | Attention networks / Transformer encoders / Stock alpha generation | 3416 | 6860 | No |
| 10628 | Diffusion Scholarly Tensor Signature Predictor Mod-1950 | Neural operators / Deep operator networks / ETF rotation | 6057 | 2372 | No |
| 10666 | Diffusion Scholarly Tensor Signature Predictor Mod-2046 | Quantum machine learning / Variational circuits / Index prediction | 11561 | 6140 | No |
| 10743 | Diffusion Scholarly Tensor Signature Predictor Mod-2238 | Attention networks / Transformer encoders / Stock alpha generation | 3436 | 6894 | No |
| 10819 | Diffusion Scholarly Tensor Signature Predictor Mod-2430 | Neural operators / Deep operator networks / ETF rotation | 6081 | 2395 | No |
| 10857 | Diffusion Scholarly Tensor Signature Predictor Mod-2526 | Quantum machine learning / Variational circuits / Index prediction | 11588 | 6157 | No |
| 10934 | Diffusion Scholarly Tensor Signature Predictor Mod-2718 | Attention networks / Transformer encoders / Stock alpha generation | 3456 | 6928 | No |
| 11010 | Diffusion Scholarly Tensor Signature Predictor Mod-2910 | Neural operators / Deep operator networks / ETF rotation | 6105 | 2418 | No |
| 11048 | Diffusion Scholarly Tensor Signature Predictor Mod-3006 | Quantum machine learning / Variational circuits / Index prediction | 11615 | 6174 | No |
| 11125 | Diffusion Scholarly Tensor Signature Predictor Mod-3198 | Attention networks / Transformer encoders / Stock alpha generation | 3476 | 6962 | No |
| 11201 | Diffusion Scholarly Tensor Signature Predictor Mod-3390 | Neural operators / Deep operator networks / ETF rotation | 6129 | 2441 | No |
| 11239 | Diffusion Scholarly Tensor Signature Predictor Mod-3486 | Quantum machine learning / Variational circuits / Index prediction | 11642 | 6191 | No |
| 11316 | Diffusion Scholarly Tensor Signature Predictor Mod-3678 | Attention networks / Transformer encoders / Stock alpha generation | 3496 | 6996 | No |
| 11392 | Diffusion Scholarly Tensor Signature Predictor Mod-3870 | Neural operators / Deep operator networks / ETF rotation | 6153 | 2464 | No |
| 11430 | Diffusion Scholarly Tensor Signature Predictor Mod-3966 | Quantum machine learning / Variational circuits / Index prediction | 11669 | 6208 | No |
