# Adaptive approach to path-signature time-series forecasting

**Concept page** · shared by **73** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,773) ·
researched 2026-10-30

| | |
|---|---|
| Task | Path-signature time-series forecasting |
| Method | Adaptive (time-varying parameters or thresholds) |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Signature forecasting has no out-of-sample trading evidence; a better method word does not fix that. |
| Implemented in volatility-ai | Signatures are research code (`point_processes`, `cross_section`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK328 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Adaptive Scholarly Tensor
Signature Predictor Ref-462") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Encode the ordered evolution of market data with path-signature features
and forecast a target from them. The adaptive version lets its
parameters or thresholds move with recent data. I found no study of this
method on this task.

## The CSV's description

Proposed adaptive approach to path-signature time-series forecasting:
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
* Parameters re-fitted often chase the recent past unless the adaptation
  itself is tested out of sample.

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
| 1773 | Adaptive Scholarly Tensor Signature Predictor Ref-462 | Robust optimization / Distributionally robust CVaR / Index tracking | 1081 | 1040 | No |
| 1828 | Adaptive Scholarly Tensor Signature Predictor Ref-942 | Robust optimization / Distributionally robust CVaR / Index tracking | 1115 | 1075 | No |
| 2504 | Adaptive Scholarly Tensor Signature Predictor Eng-222 | Robust optimization / Distributionally robust CVaR / Index tracking | 1513 | 1394 | No |
| 2559 | Adaptive Scholarly Tensor Signature Predictor Eng-702 | Robust optimization / Distributionally robust CVaR / Index tracking | 1543 | 1420 | No |
| 2614 | Adaptive Scholarly Tensor Signature Predictor Eng-1182 | Robust optimization / Distributionally robust CVaR / Index tracking | 1573 | 1446 | No |
| 2669 | Adaptive Scholarly Tensor Signature Predictor Eng-1662 | Robust optimization / Distributionally robust CVaR / Index tracking | 1603 | 1472 | No |
| 2724 | Adaptive Scholarly Tensor Signature Predictor Eng-2142 | Robust optimization / Distributionally robust CVaR / Index tracking | 1633 | 1498 | No |
| 2779 | Adaptive Scholarly Tensor Signature Predictor Eng-2622 | Robust optimization / Distributionally robust CVaR / Index tracking | 1663 | 1524 | No |
| 2834 | Adaptive Scholarly Tensor Signature Predictor Eng-3102 | Robust optimization / Distributionally robust CVaR / Index tracking | 1693 | 1550 | No |
| 2889 | Adaptive Scholarly Tensor Signature Predictor Eng-3582 | Robust optimization / Distributionally robust CVaR / Index tracking | 1723 | 1576 | No |
| 2944 | Adaptive Scholarly Tensor Signature Predictor Eng-4062 | Robust optimization / Distributionally robust CVaR / Index tracking | 1753 | 1602 | No |
| 2999 | Adaptive Scholarly Tensor Signature Predictor Eng-4542 | Robust optimization / Distributionally robust CVaR / Index tracking | 1783 | 1628 | No |
| 3054 | Adaptive Scholarly Tensor Signature Predictor Eng-5022 | Robust optimization / Distributionally robust CVaR / Index tracking | 1813 | 1654 | No |
| 3109 | Adaptive Scholarly Tensor Signature Predictor Eng-5502 | Robust optimization / Distributionally robust CVaR / Index tracking | 1843 | 1680 | No |
| 3164 | Adaptive Scholarly Tensor Signature Predictor Eng-5982 | Robust optimization / Distributionally robust CVaR / Index tracking | 1873 | 1706 | No |
| 3180 | Adaptive Scholarly Tensor Signature Predictor Ref-174 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1062 | 3054 | No |
| 3196 | Adaptive Scholarly Tensor Signature Predictor Ref-654 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1096 | 3171 | No |
| 3467 | Adaptive Scholarly Tensor Signature Predictor Eng-414 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1526 | 4526 | No |
| 3483 | Adaptive Scholarly Tensor Signature Predictor Eng-894 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1556 | 4619 | No |
| 3499 | Adaptive Scholarly Tensor Signature Predictor Eng-1374 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1586 | 4712 | No |
| 3515 | Adaptive Scholarly Tensor Signature Predictor Eng-1854 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1616 | 4805 | No |
| 3531 | Adaptive Scholarly Tensor Signature Predictor Eng-2334 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1646 | 4898 | No |
| 3547 | Adaptive Scholarly Tensor Signature Predictor Eng-2814 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1676 | 4991 | No |
| 3563 | Adaptive Scholarly Tensor Signature Predictor Eng-3294 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1706 | 5084 | No |
| 3579 | Adaptive Scholarly Tensor Signature Predictor Eng-3774 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1736 | 5177 | No |
| 3595 | Adaptive Scholarly Tensor Signature Predictor Eng-4254 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1766 | 5270 | No |
| 3611 | Adaptive Scholarly Tensor Signature Predictor Eng-4734 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1796 | 5363 | No |
| 3627 | Adaptive Scholarly Tensor Signature Predictor Eng-5214 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1826 | 5456 | No |
| 3643 | Adaptive Scholarly Tensor Signature Predictor Eng-5694 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1856 | 5549 | No |
| 7456 | Adaptive Scholarly Tensor Signature Predictor Ref-78 | Attention networks / Transformer encoders / Stock alpha generation | 3212 | 6534 | No |
| 7490 | Adaptive Scholarly Tensor Signature Predictor Ref-558 | Attention networks / Transformer encoders / Stock alpha generation | 3228 | 6560 | No |
| 7940 | Adaptive Scholarly Tensor Signature Predictor Eng-318 | Attention networks / Transformer encoders / Stock alpha generation | 3522 | 7041 | No |
| 7974 | Adaptive Scholarly Tensor Signature Predictor Eng-798 | Attention networks / Transformer encoders / Stock alpha generation | 3542 | 7073 | No |
| 8008 | Adaptive Scholarly Tensor Signature Predictor Eng-1278 | Attention networks / Transformer encoders / Stock alpha generation | 3562 | 7105 | No |
| 8042 | Adaptive Scholarly Tensor Signature Predictor Eng-1758 | Attention networks / Transformer encoders / Stock alpha generation | 3582 | 7137 | No |
| 8076 | Adaptive Scholarly Tensor Signature Predictor Eng-2238 | Attention networks / Transformer encoders / Stock alpha generation | 3602 | 7169 | No |
| 8110 | Adaptive Scholarly Tensor Signature Predictor Eng-2718 | Attention networks / Transformer encoders / Stock alpha generation | 3622 | 7201 | No |
| 8144 | Adaptive Scholarly Tensor Signature Predictor Eng-3198 | Attention networks / Transformer encoders / Stock alpha generation | 3642 | 7233 | No |
| 8178 | Adaptive Scholarly Tensor Signature Predictor Eng-3678 | Attention networks / Transformer encoders / Stock alpha generation | 3662 | 7265 | No |
| 8212 | Adaptive Scholarly Tensor Signature Predictor Eng-4158 | Attention networks / Transformer encoders / Stock alpha generation | 3682 | 7297 | No |
| 8246 | Adaptive Scholarly Tensor Signature Predictor Eng-4638 | Attention networks / Transformer encoders / Stock alpha generation | 3702 | 7329 | No |
| 8280 | Adaptive Scholarly Tensor Signature Predictor Eng-5118 | Attention networks / Transformer encoders / Stock alpha generation | 3722 | 7361 | No |
| 8314 | Adaptive Scholarly Tensor Signature Predictor Eng-5598 | Attention networks / Transformer encoders / Stock alpha generation | 3742 | 7393 | No |
| 8782 | Adaptive Scholarly Tensor Signature Predictor Ref-270 | Neural operators / Deep operator networks / ETF rotation | 5837 | 2162 | No |
| 8819 | Adaptive Scholarly Tensor Signature Predictor Ref-366 | Quantum machine learning / Variational circuits / Index prediction | 11303 | 5976 | No |
| 8973 | Adaptive Scholarly Tensor Signature Predictor Ref-750 | Neural operators / Deep operator networks / ETF rotation | 5862 | 2187 | No |
| 9010 | Adaptive Scholarly Tensor Signature Predictor Ref-846 | Quantum machine learning / Variational circuits / Index prediction | 11328 | 5996 | No |
| 11456 | Adaptive Scholarly Tensor Signature Predictor Eng-30 | Neural operators / Deep operator networks / ETF rotation | 6162 | 2472 | No |
| 11494 | Adaptive Scholarly Tensor Signature Predictor Eng-126 | Quantum machine learning / Variational circuits / Index prediction | 11679 | 6216 | No |
| 11647 | Adaptive Scholarly Tensor Signature Predictor Eng-510 | Neural operators / Deep operator networks / ETF rotation | 6184 | 2495 | No |
| 11685 | Adaptive Scholarly Tensor Signature Predictor Eng-606 | Quantum machine learning / Variational circuits / Index prediction | 11704 | 6237 | No |
| 11838 | Adaptive Scholarly Tensor Signature Predictor Eng-990 | Neural operators / Deep operator networks / ETF rotation | 6206 | 2518 | No |
| 11876 | Adaptive Scholarly Tensor Signature Predictor Eng-1086 | Quantum machine learning / Variational circuits / Index prediction | 11729 | 6258 | No |
| 12029 | Adaptive Scholarly Tensor Signature Predictor Eng-1470 | Neural operators / Deep operator networks / ETF rotation | 6228 | 2541 | No |
| 12067 | Adaptive Scholarly Tensor Signature Predictor Eng-1566 | Quantum machine learning / Variational circuits / Index prediction | 11754 | 6279 | No |
| 12220 | Adaptive Scholarly Tensor Signature Predictor Eng-1950 | Neural operators / Deep operator networks / ETF rotation | 6250 | 2564 | No |
| 12258 | Adaptive Scholarly Tensor Signature Predictor Eng-2046 | Quantum machine learning / Variational circuits / Index prediction | 11779 | 6300 | No |
| 12411 | Adaptive Scholarly Tensor Signature Predictor Eng-2430 | Neural operators / Deep operator networks / ETF rotation | 6272 | 2587 | No |
| 12449 | Adaptive Scholarly Tensor Signature Predictor Eng-2526 | Quantum machine learning / Variational circuits / Index prediction | 11804 | 6321 | No |
| 12602 | Adaptive Scholarly Tensor Signature Predictor Eng-2910 | Neural operators / Deep operator networks / ETF rotation | 6294 | 2610 | No |
| 12640 | Adaptive Scholarly Tensor Signature Predictor Eng-3006 | Quantum machine learning / Variational circuits / Index prediction | 11829 | 6342 | No |
| 12793 | Adaptive Scholarly Tensor Signature Predictor Eng-3390 | Neural operators / Deep operator networks / ETF rotation | 6316 | 2633 | No |
| 12831 | Adaptive Scholarly Tensor Signature Predictor Eng-3486 | Quantum machine learning / Variational circuits / Index prediction | 11854 | 6363 | No |
| 12984 | Adaptive Scholarly Tensor Signature Predictor Eng-3870 | Neural operators / Deep operator networks / ETF rotation | 6338 | 2656 | No |
| 13022 | Adaptive Scholarly Tensor Signature Predictor Eng-3966 | Quantum machine learning / Variational circuits / Index prediction | 11879 | 6384 | No |
| 13175 | Adaptive Scholarly Tensor Signature Predictor Eng-4350 | Neural operators / Deep operator networks / ETF rotation | 6360 | 2679 | No |
| 13213 | Adaptive Scholarly Tensor Signature Predictor Eng-4446 | Quantum machine learning / Variational circuits / Index prediction | 11904 | 6405 | No |
| 13366 | Adaptive Scholarly Tensor Signature Predictor Eng-4830 | Neural operators / Deep operator networks / ETF rotation | 6382 | 2702 | No |
| 13404 | Adaptive Scholarly Tensor Signature Predictor Eng-4926 | Quantum machine learning / Variational circuits / Index prediction | 11929 | 6426 | No |
| 13557 | Adaptive Scholarly Tensor Signature Predictor Eng-5310 | Neural operators / Deep operator networks / ETF rotation | 6404 | 2725 | No |
| 13595 | Adaptive Scholarly Tensor Signature Predictor Eng-5406 | Quantum machine learning / Variational circuits / Index prediction | 11954 | 6447 | No |
| 13748 | Adaptive Scholarly Tensor Signature Predictor Eng-5790 | Neural operators / Deep operator networks / ETF rotation | 6426 | 2748 | No |
| 13786 | Adaptive Scholarly Tensor Signature Predictor Eng-5886 | Quantum machine learning / Variational circuits / Index prediction | 11979 | 6468 | No |
