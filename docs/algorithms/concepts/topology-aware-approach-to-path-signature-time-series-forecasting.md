# Topology-aware approach to path-signature time-series forecasting

**Concept page** · shared by **62** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #4,002) ·
researched 2026-10-30

| | |
|---|---|
| Task | Path-signature time-series forecasting |
| Method | Topological data analysis (persistent homology) |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Signature forecasting has no out-of-sample trading evidence; a better method word does not fix that. |
| Implemented in volatility-ai | Signatures are research code (`point_processes`, `cross_section`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK328 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Topological Scholarly
Tensor Signature Predictor Sys-282") combine a method word, "Scholarly",
a task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Encode the ordered evolution of market data with path-signature features
and forecast a target from them. The topology-aware version derives
persistent-homology features (Betti numbers, persistence landscapes)
from sliding windows of returns. I found no study of this method on this
task.

## The CSV's description

Proposed topology-aware approach to path-signature time-series
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
* The best-known topological crash study is in sample (Gidea & Katz
  2018), and the features depend on window and scale choices.

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
| 4002 | Topological Scholarly Tensor Signature Predictor Sys-282 | Robust optimization / Distributionally robust CVaR / Index tracking | 1136 | 1093 | No |
| 4088 | Topological Scholarly Tensor Signature Predictor Sys-762 | Robust optimization / Distributionally robust CVaR / Index tracking | 1166 | 1117 | No |
| 4174 | Topological Scholarly Tensor Signature Predictor Sys-1242 | Robust optimization / Distributionally robust CVaR / Index tracking | 1196 | 1141 | No |
| 4260 | Topological Scholarly Tensor Signature Predictor Sys-1722 | Robust optimization / Distributionally robust CVaR / Index tracking | 1226 | 1165 | No |
| 4330 | Topological Scholarly Tensor Signature Predictor Mod-102 | Robust optimization / Distributionally robust CVaR / Index tracking | 1249 | 1185 | No |
| 4415 | Topological Scholarly Tensor Signature Predictor Mod-582 | Robust optimization / Distributionally robust CVaR / Index tracking | 1280 | 1209 | No |
| 4500 | Topological Scholarly Tensor Signature Predictor Mod-1062 | Robust optimization / Distributionally robust CVaR / Index tracking | 1311 | 1233 | No |
| 4585 | Topological Scholarly Tensor Signature Predictor Mod-1542 | Robust optimization / Distributionally robust CVaR / Index tracking | 1342 | 1257 | No |
| 4670 | Topological Scholarly Tensor Signature Predictor Mod-2022 | Robust optimization / Distributionally robust CVaR / Index tracking | 1373 | 1281 | No |
| 4755 | Topological Scholarly Tensor Signature Predictor Mod-2502 | Robust optimization / Distributionally robust CVaR / Index tracking | 1404 | 1305 | No |
| 4840 | Topological Scholarly Tensor Signature Predictor Mod-2982 | Robust optimization / Distributionally robust CVaR / Index tracking | 1435 | 1329 | No |
| 4925 | Topological Scholarly Tensor Signature Predictor Mod-3462 | Robust optimization / Distributionally robust CVaR / Index tracking | 1466 | 1353 | No |
| 5010 | Topological Scholarly Tensor Signature Predictor Mod-3942 | Robust optimization / Distributionally robust CVaR / Index tracking | 1497 | 1377 | No |
| 6321 | Topological Scholarly Tensor Signature Predictor Sys-474 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1148 | 3348 | No |
| 6362 | Topological Scholarly Tensor Signature Predictor Sys-954 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1178 | 3443 | No |
| 6403 | Topological Scholarly Tensor Signature Predictor Sys-1434 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1208 | 3538 | No |
| 6444 | Topological Scholarly Tensor Signature Predictor Sys-1914 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1238 | 3633 | No |
| 6480 | Topological Scholarly Tensor Signature Predictor Mod-294 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1260 | 3709 | No |
| 6525 | Topological Scholarly Tensor Signature Predictor Mod-774 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1291 | 3804 | No |
| 6570 | Topological Scholarly Tensor Signature Predictor Mod-1254 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1322 | 3899 | No |
| 6615 | Topological Scholarly Tensor Signature Predictor Mod-1734 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1353 | 3994 | No |
| 6660 | Topological Scholarly Tensor Signature Predictor Mod-2214 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1384 | 4089 | No |
| 6705 | Topological Scholarly Tensor Signature Predictor Mod-2694 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1415 | 4184 | No |
| 6750 | Topological Scholarly Tensor Signature Predictor Mod-3174 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1446 | 4279 | No |
| 6795 | Topological Scholarly Tensor Signature Predictor Mod-3654 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1477 | 4374 | No |
| 9108 | Topological Scholarly Tensor Signature Predictor Sys-90 | Neural operators / Deep operator networks / ETF rotation | 5880 | 2204 | No |
| 9145 | Topological Scholarly Tensor Signature Predictor Sys-186 | Quantum machine learning / Variational circuits / Index prediction | 11347 | 6010 | No |
| 9221 | Topological Scholarly Tensor Signature Predictor Sys-378 | Attention networks / Transformer encoders / Stock alpha generation | 3262 | 6614 | No |
| 9295 | Topological Scholarly Tensor Signature Predictor Sys-570 | Neural operators / Deep operator networks / ETF rotation | 5900 | 2223 | No |
| 9332 | Topological Scholarly Tensor Signature Predictor Sys-666 | Quantum machine learning / Variational circuits / Index prediction | 11373 | 6025 | No |
| 9408 | Topological Scholarly Tensor Signature Predictor Sys-858 | Attention networks / Transformer encoders / Stock alpha generation | 3286 | 6650 | No |
| 9482 | Topological Scholarly Tensor Signature Predictor Sys-1050 | Neural operators / Deep operator networks / ETF rotation | 5920 | 2242 | No |
| 9519 | Topological Scholarly Tensor Signature Predictor Sys-1146 | Quantum machine learning / Variational circuits / Index prediction | 11399 | 6040 | No |
| 9595 | Topological Scholarly Tensor Signature Predictor Sys-1338 | Attention networks / Transformer encoders / Stock alpha generation | 3310 | 6686 | No |
| 9669 | Topological Scholarly Tensor Signature Predictor Sys-1530 | Neural operators / Deep operator networks / ETF rotation | 5940 | 2261 | No |
| 9706 | Topological Scholarly Tensor Signature Predictor Sys-1626 | Quantum machine learning / Variational circuits / Index prediction | 11425 | 6055 | No |
| 9782 | Topological Scholarly Tensor Signature Predictor Sys-1818 | Attention networks / Transformer encoders / Stock alpha generation | 3334 | 6722 | No |
| 9855 | Topological Scholarly Tensor Signature Predictor Mod-6 | Quantum machine learning / Variational circuits / Index prediction | 11446 | 6067 | No |
| 9930 | Topological Scholarly Tensor Signature Predictor Mod-198 | Attention networks / Transformer encoders / Stock alpha generation | 3351 | 6749 | No |
| 10009 | Topological Scholarly Tensor Signature Predictor Mod-390 | Neural operators / Deep operator networks / ETF rotation | 5979 | 2297 | No |
| 10046 | Topological Scholarly Tensor Signature Predictor Mod-486 | Quantum machine learning / Variational circuits / Index prediction | 11473 | 6084 | No |
| 10121 | Topological Scholarly Tensor Signature Predictor Mod-678 | Attention networks / Transformer encoders / Stock alpha generation | 3371 | 6783 | No |
| 10200 | Topological Scholarly Tensor Signature Predictor Mod-870 | Neural operators / Deep operator networks / ETF rotation | 6003 | 2320 | No |
| 10237 | Topological Scholarly Tensor Signature Predictor Mod-966 | Quantum machine learning / Variational circuits / Index prediction | 11500 | 6101 | No |
| 10312 | Topological Scholarly Tensor Signature Predictor Mod-1158 | Attention networks / Transformer encoders / Stock alpha generation | 3391 | 6817 | No |
| 10391 | Topological Scholarly Tensor Signature Predictor Mod-1350 | Neural operators / Deep operator networks / ETF rotation | 6027 | 2343 | No |
| 10428 | Topological Scholarly Tensor Signature Predictor Mod-1446 | Quantum machine learning / Variational circuits / Index prediction | 11527 | 6118 | No |
| 10503 | Topological Scholarly Tensor Signature Predictor Mod-1638 | Attention networks / Transformer encoders / Stock alpha generation | 3411 | 6851 | No |
| 10582 | Topological Scholarly Tensor Signature Predictor Mod-1830 | Neural operators / Deep operator networks / ETF rotation | 6051 | 2366 | No |
| 10619 | Topological Scholarly Tensor Signature Predictor Mod-1926 | Quantum machine learning / Variational circuits / Index prediction | 11554 | 6135 | No |
| 10694 | Topological Scholarly Tensor Signature Predictor Mod-2118 | Attention networks / Transformer encoders / Stock alpha generation | 3431 | 6885 | No |
| 10773 | Topological Scholarly Tensor Signature Predictor Mod-2310 | Neural operators / Deep operator networks / ETF rotation | 6075 | 2389 | No |
| 10810 | Topological Scholarly Tensor Signature Predictor Mod-2406 | Quantum machine learning / Variational circuits / Index prediction | 11581 | 6152 | No |
| 10885 | Topological Scholarly Tensor Signature Predictor Mod-2598 | Attention networks / Transformer encoders / Stock alpha generation | 3451 | 6919 | No |
| 10964 | Topological Scholarly Tensor Signature Predictor Mod-2790 | Neural operators / Deep operator networks / ETF rotation | 6099 | 2412 | No |
| 11001 | Topological Scholarly Tensor Signature Predictor Mod-2886 | Quantum machine learning / Variational circuits / Index prediction | 11608 | 6169 | No |
| 11076 | Topological Scholarly Tensor Signature Predictor Mod-3078 | Attention networks / Transformer encoders / Stock alpha generation | 3471 | 6953 | No |
| 11155 | Topological Scholarly Tensor Signature Predictor Mod-3270 | Neural operators / Deep operator networks / ETF rotation | 6123 | 2435 | No |
| 11192 | Topological Scholarly Tensor Signature Predictor Mod-3366 | Quantum machine learning / Variational circuits / Index prediction | 11635 | 6186 | No |
| 11267 | Topological Scholarly Tensor Signature Predictor Mod-3558 | Attention networks / Transformer encoders / Stock alpha generation | 3491 | 6987 | No |
| 11346 | Topological Scholarly Tensor Signature Predictor Mod-3750 | Neural operators / Deep operator networks / ETF rotation | 6147 | 2458 | No |
| 11383 | Topological Scholarly Tensor Signature Predictor Mod-3846 | Quantum machine learning / Variational circuits / Index prediction | 11662 | 6203 | No |
