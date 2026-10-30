# Fractional-order approach to path-signature time-series forecasting

**Concept page** · shared by **73** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #3,809) ·
researched 2026-10-30

| | |
|---|---|
| Task | Path-signature time-series forecasting |
| Method | Fractional-order models (long memory, fractional calculus) |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Signature forecasting has no out-of-sample trading evidence; a better method word does not fix that. |
| Implemented in volatility-ai | Signatures are research code (`point_processes`, `cross_section`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK328 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Fractional Scholarly Tensor
Signature Predictor Ref-222") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Encode the ordered evolution of market data with path-signature features
and forecast a target from them. The fractional-order version models
long memory with fractional differencing or fractional-order dynamics. I
found no study of this method on this task.

## The CSV's description

Proposed fractional-order approach to path-signature time-series
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
* Long memory in returns is weak once short-range dependence is allowed
  for (Lo 1991); in volatility, the simpler HAR model reproduces it
  (Corsi 2009).

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
| 3809 | Fractional Scholarly Tensor Signature Predictor Ref-222 | Robust optimization / Distributionally robust CVaR / Index tracking | 1064 | 1023 | No |
| 3895 | Fractional Scholarly Tensor Signature Predictor Ref-702 | Robust optimization / Distributionally robust CVaR / Index tracking | 1098 | 1058 | No |
| 5106 | Fractional Scholarly Tensor Signature Predictor Eng-462 | Robust optimization / Distributionally robust CVaR / Index tracking | 1528 | 1406 | No |
| 5192 | Fractional Scholarly Tensor Signature Predictor Eng-942 | Robust optimization / Distributionally robust CVaR / Index tracking | 1558 | 1432 | No |
| 5278 | Fractional Scholarly Tensor Signature Predictor Eng-1422 | Robust optimization / Distributionally robust CVaR / Index tracking | 1588 | 1458 | No |
| 5364 | Fractional Scholarly Tensor Signature Predictor Eng-1902 | Robust optimization / Distributionally robust CVaR / Index tracking | 1618 | 1484 | No |
| 5450 | Fractional Scholarly Tensor Signature Predictor Eng-2382 | Robust optimization / Distributionally robust CVaR / Index tracking | 1648 | 1510 | No |
| 5536 | Fractional Scholarly Tensor Signature Predictor Eng-2862 | Robust optimization / Distributionally robust CVaR / Index tracking | 1678 | 1536 | No |
| 5622 | Fractional Scholarly Tensor Signature Predictor Eng-3342 | Robust optimization / Distributionally robust CVaR / Index tracking | 1708 | 1562 | No |
| 5708 | Fractional Scholarly Tensor Signature Predictor Eng-3822 | Robust optimization / Distributionally robust CVaR / Index tracking | 1738 | 1588 | No |
| 5794 | Fractional Scholarly Tensor Signature Predictor Eng-4302 | Robust optimization / Distributionally robust CVaR / Index tracking | 1768 | 1614 | No |
| 5880 | Fractional Scholarly Tensor Signature Predictor Eng-4782 | Robust optimization / Distributionally robust CVaR / Index tracking | 1798 | 1640 | No |
| 5966 | Fractional Scholarly Tensor Signature Predictor Eng-5262 | Robust optimization / Distributionally robust CVaR / Index tracking | 1828 | 1666 | No |
| 6052 | Fractional Scholarly Tensor Signature Predictor Eng-5742 | Robust optimization / Distributionally robust CVaR / Index tracking | 1858 | 1692 | No |
| 6225 | Fractional Scholarly Tensor Signature Predictor Ref-414 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1079 | 3114 | No |
| 6271 | Fractional Scholarly Tensor Signature Predictor Ref-894 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1113 | 3231 | No |
| 6844 | Fractional Scholarly Tensor Signature Predictor Eng-174 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1511 | 4479 | No |
| 6890 | Fractional Scholarly Tensor Signature Predictor Eng-654 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1541 | 4572 | No |
| 6936 | Fractional Scholarly Tensor Signature Predictor Eng-1134 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1571 | 4665 | No |
| 6982 | Fractional Scholarly Tensor Signature Predictor Eng-1614 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1601 | 4758 | No |
| 7028 | Fractional Scholarly Tensor Signature Predictor Eng-2094 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1631 | 4851 | No |
| 7074 | Fractional Scholarly Tensor Signature Predictor Eng-2574 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1661 | 4944 | No |
| 7120 | Fractional Scholarly Tensor Signature Predictor Eng-3054 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1691 | 5037 | No |
| 7166 | Fractional Scholarly Tensor Signature Predictor Eng-3534 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1721 | 5130 | No |
| 7212 | Fractional Scholarly Tensor Signature Predictor Eng-4014 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1751 | 5223 | No |
| 7258 | Fractional Scholarly Tensor Signature Predictor Eng-4494 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1781 | 5316 | No |
| 7304 | Fractional Scholarly Tensor Signature Predictor Eng-4974 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1811 | 5409 | No |
| 7350 | Fractional Scholarly Tensor Signature Predictor Eng-5454 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1841 | 5502 | No |
| 7396 | Fractional Scholarly Tensor Signature Predictor Eng-5934 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1871 | 5595 | No |
| 8688 | Fractional Scholarly Tensor Signature Predictor Ref-30 | Neural operators / Deep operator networks / ETF rotation | 5826 | 2149 | No |
| 8725 | Fractional Scholarly Tensor Signature Predictor Ref-126 | Quantum machine learning / Variational circuits / Index prediction | 11291 | 5966 | No |
| 8800 | Fractional Scholarly Tensor Signature Predictor Ref-318 | Attention networks / Transformer encoders / Stock alpha generation | 3220 | 6546 | No |
| 8879 | Fractional Scholarly Tensor Signature Predictor Ref-510 | Neural operators / Deep operator networks / ETF rotation | 5851 | 2174 | No |
| 8916 | Fractional Scholarly Tensor Signature Predictor Ref-606 | Quantum machine learning / Variational circuits / Index prediction | 11316 | 5986 | No |
| 8991 | Fractional Scholarly Tensor Signature Predictor Ref-798 | Attention networks / Transformer encoders / Stock alpha generation | 3236 | 6572 | No |
| 9070 | Fractional Scholarly Tensor Signature Predictor Ref-990 | Neural operators / Deep operator networks / ETF rotation | 5876 | 2199 | No |
| 11474 | Fractional Scholarly Tensor Signature Predictor Eng-78 | Attention networks / Transformer encoders / Stock alpha generation | 3512 | 7025 | No |
| 11552 | Fractional Scholarly Tensor Signature Predictor Eng-270 | Neural operators / Deep operator networks / ETF rotation | 6171 | 2484 | No |
| 11586 | Fractional Scholarly Tensor Signature Predictor Eng-366 | Quantum machine learning / Variational circuits / Index prediction | 11692 | 6226 | No |
| 11665 | Fractional Scholarly Tensor Signature Predictor Eng-558 | Attention networks / Transformer encoders / Stock alpha generation | 3532 | 7057 | No |
| 11743 | Fractional Scholarly Tensor Signature Predictor Eng-750 | Neural operators / Deep operator networks / ETF rotation | 6193 | 2507 | No |
| 11777 | Fractional Scholarly Tensor Signature Predictor Eng-846 | Quantum machine learning / Variational circuits / Index prediction | 11717 | 6247 | No |
| 11856 | Fractional Scholarly Tensor Signature Predictor Eng-1038 | Attention networks / Transformer encoders / Stock alpha generation | 3552 | 7089 | No |
| 11934 | Fractional Scholarly Tensor Signature Predictor Eng-1230 | Neural operators / Deep operator networks / ETF rotation | 6215 | 2530 | No |
| 11968 | Fractional Scholarly Tensor Signature Predictor Eng-1326 | Quantum machine learning / Variational circuits / Index prediction | 11742 | 6268 | No |
| 12047 | Fractional Scholarly Tensor Signature Predictor Eng-1518 | Attention networks / Transformer encoders / Stock alpha generation | 3572 | 7121 | No |
| 12125 | Fractional Scholarly Tensor Signature Predictor Eng-1710 | Neural operators / Deep operator networks / ETF rotation | 6237 | 2553 | No |
| 12159 | Fractional Scholarly Tensor Signature Predictor Eng-1806 | Quantum machine learning / Variational circuits / Index prediction | 11767 | 6289 | No |
| 12238 | Fractional Scholarly Tensor Signature Predictor Eng-1998 | Attention networks / Transformer encoders / Stock alpha generation | 3592 | 7153 | No |
| 12316 | Fractional Scholarly Tensor Signature Predictor Eng-2190 | Neural operators / Deep operator networks / ETF rotation | 6259 | 2576 | No |
| 12350 | Fractional Scholarly Tensor Signature Predictor Eng-2286 | Quantum machine learning / Variational circuits / Index prediction | 11792 | 6310 | No |
| 12429 | Fractional Scholarly Tensor Signature Predictor Eng-2478 | Attention networks / Transformer encoders / Stock alpha generation | 3612 | 7185 | No |
| 12507 | Fractional Scholarly Tensor Signature Predictor Eng-2670 | Neural operators / Deep operator networks / ETF rotation | 6281 | 2599 | No |
| 12541 | Fractional Scholarly Tensor Signature Predictor Eng-2766 | Quantum machine learning / Variational circuits / Index prediction | 11817 | 6331 | No |
| 12620 | Fractional Scholarly Tensor Signature Predictor Eng-2958 | Attention networks / Transformer encoders / Stock alpha generation | 3632 | 7217 | No |
| 12698 | Fractional Scholarly Tensor Signature Predictor Eng-3150 | Neural operators / Deep operator networks / ETF rotation | 6303 | 2622 | No |
| 12732 | Fractional Scholarly Tensor Signature Predictor Eng-3246 | Quantum machine learning / Variational circuits / Index prediction | 11842 | 6352 | No |
| 12811 | Fractional Scholarly Tensor Signature Predictor Eng-3438 | Attention networks / Transformer encoders / Stock alpha generation | 3652 | 7249 | No |
| 12889 | Fractional Scholarly Tensor Signature Predictor Eng-3630 | Neural operators / Deep operator networks / ETF rotation | 6325 | 2645 | No |
| 12923 | Fractional Scholarly Tensor Signature Predictor Eng-3726 | Quantum machine learning / Variational circuits / Index prediction | 11867 | 6373 | No |
| 13002 | Fractional Scholarly Tensor Signature Predictor Eng-3918 | Attention networks / Transformer encoders / Stock alpha generation | 3672 | 7281 | No |
| 13080 | Fractional Scholarly Tensor Signature Predictor Eng-4110 | Neural operators / Deep operator networks / ETF rotation | 6347 | 2668 | No |
| 13114 | Fractional Scholarly Tensor Signature Predictor Eng-4206 | Quantum machine learning / Variational circuits / Index prediction | 11892 | 6394 | No |
| 13193 | Fractional Scholarly Tensor Signature Predictor Eng-4398 | Attention networks / Transformer encoders / Stock alpha generation | 3692 | 7313 | No |
| 13271 | Fractional Scholarly Tensor Signature Predictor Eng-4590 | Neural operators / Deep operator networks / ETF rotation | 6369 | 2691 | No |
| 13305 | Fractional Scholarly Tensor Signature Predictor Eng-4686 | Quantum machine learning / Variational circuits / Index prediction | 11917 | 6415 | No |
| 13384 | Fractional Scholarly Tensor Signature Predictor Eng-4878 | Attention networks / Transformer encoders / Stock alpha generation | 3712 | 7345 | No |
| 13462 | Fractional Scholarly Tensor Signature Predictor Eng-5070 | Neural operators / Deep operator networks / ETF rotation | 6391 | 2714 | No |
| 13496 | Fractional Scholarly Tensor Signature Predictor Eng-5166 | Quantum machine learning / Variational circuits / Index prediction | 11942 | 6436 | No |
| 13575 | Fractional Scholarly Tensor Signature Predictor Eng-5358 | Attention networks / Transformer encoders / Stock alpha generation | 3732 | 7377 | No |
| 13653 | Fractional Scholarly Tensor Signature Predictor Eng-5550 | Neural operators / Deep operator networks / ETF rotation | 6413 | 2737 | No |
| 13687 | Fractional Scholarly Tensor Signature Predictor Eng-5646 | Quantum machine learning / Variational circuits / Index prediction | 11967 | 6457 | No |
| 13766 | Fractional Scholarly Tensor Signature Predictor Eng-5838 | Attention networks / Transformer encoders / Stock alpha generation | 3752 | 7409 | No |
