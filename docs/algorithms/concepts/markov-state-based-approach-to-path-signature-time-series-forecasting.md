# Markov-state-based approach to path-signature time-series forecasting

**Concept page** · shared by **78** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,733) ·
researched 2026-10-30

| | |
|---|---|
| Task | Path-signature time-series forecasting |
| Method | Hidden Markov / regime-switching states |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Signature forecasting has no out-of-sample trading evidence; a better method word does not fix that. |
| Implemented in volatility-ai | Signatures are research code (`point_processes`, `cross_section`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK328 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Markovian Scholarly Tensor
Signature Predictor Ref-102") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Encode the ordered evolution of market data with path-signature features
and forecast a target from them. The Markov-state version infers hidden
states (calm, turbulent, crisis) and conditions on the current one. I
found no study of this method on this task.

## The CSV's description

Proposed Markov-state-based approach to path-signature time-series
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
* States are clear only after the fact; causal (filtered) state
  probabilities lag turning points.

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
| 1733 | Markovian Scholarly Tensor Signature Predictor Ref-102 | Robust optimization / Distributionally robust CVaR / Index tracking | 1056 | 1013 | No |
| 1788 | Markovian Scholarly Tensor Signature Predictor Ref-582 | Robust optimization / Distributionally robust CVaR / Index tracking | 1090 | 1048 | No |
| 2518 | Markovian Scholarly Tensor Signature Predictor Eng-342 | Robust optimization / Distributionally robust CVaR / Index tracking | 1520 | 1400 | No |
| 2573 | Markovian Scholarly Tensor Signature Predictor Eng-822 | Robust optimization / Distributionally robust CVaR / Index tracking | 1550 | 1426 | No |
| 2628 | Markovian Scholarly Tensor Signature Predictor Eng-1302 | Robust optimization / Distributionally robust CVaR / Index tracking | 1580 | 1452 | No |
| 2683 | Markovian Scholarly Tensor Signature Predictor Eng-1782 | Robust optimization / Distributionally robust CVaR / Index tracking | 1610 | 1478 | No |
| 2738 | Markovian Scholarly Tensor Signature Predictor Eng-2262 | Robust optimization / Distributionally robust CVaR / Index tracking | 1640 | 1504 | No |
| 2793 | Markovian Scholarly Tensor Signature Predictor Eng-2742 | Robust optimization / Distributionally robust CVaR / Index tracking | 1670 | 1530 | No |
| 2848 | Markovian Scholarly Tensor Signature Predictor Eng-3222 | Robust optimization / Distributionally robust CVaR / Index tracking | 1700 | 1556 | No |
| 2903 | Markovian Scholarly Tensor Signature Predictor Eng-3702 | Robust optimization / Distributionally robust CVaR / Index tracking | 1730 | 1582 | No |
| 2958 | Markovian Scholarly Tensor Signature Predictor Eng-4182 | Robust optimization / Distributionally robust CVaR / Index tracking | 1760 | 1608 | No |
| 3013 | Markovian Scholarly Tensor Signature Predictor Eng-4662 | Robust optimization / Distributionally robust CVaR / Index tracking | 1790 | 1634 | No |
| 3068 | Markovian Scholarly Tensor Signature Predictor Eng-5142 | Robust optimization / Distributionally robust CVaR / Index tracking | 1820 | 1660 | No |
| 3123 | Markovian Scholarly Tensor Signature Predictor Eng-5622 | Robust optimization / Distributionally robust CVaR / Index tracking | 1850 | 1686 | No |
| 3185 | Markovian Scholarly Tensor Signature Predictor Ref-294 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1070 | 3083 | No |
| 3201 | Markovian Scholarly Tensor Signature Predictor Ref-774 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1104 | 3200 | No |
| 3454 | Markovian Scholarly Tensor Signature Predictor Eng-54 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1503 | 4455 | No |
| 3470 | Markovian Scholarly Tensor Signature Predictor Eng-534 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1533 | 4548 | No |
| 3486 | Markovian Scholarly Tensor Signature Predictor Eng-1014 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1563 | 4641 | No |
| 3502 | Markovian Scholarly Tensor Signature Predictor Eng-1494 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1593 | 4734 | No |
| 3518 | Markovian Scholarly Tensor Signature Predictor Eng-1974 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1623 | 4827 | No |
| 3534 | Markovian Scholarly Tensor Signature Predictor Eng-2454 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1653 | 4920 | No |
| 3550 | Markovian Scholarly Tensor Signature Predictor Eng-2934 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1683 | 5013 | No |
| 3566 | Markovian Scholarly Tensor Signature Predictor Eng-3414 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1713 | 5106 | No |
| 3582 | Markovian Scholarly Tensor Signature Predictor Eng-3894 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1743 | 5199 | No |
| 3598 | Markovian Scholarly Tensor Signature Predictor Eng-4374 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1773 | 5292 | No |
| 3614 | Markovian Scholarly Tensor Signature Predictor Eng-4854 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1803 | 5385 | No |
| 3630 | Markovian Scholarly Tensor Signature Predictor Eng-5334 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1833 | 5478 | No |
| 3646 | Markovian Scholarly Tensor Signature Predictor Eng-5814 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1863 | 5571 | No |
| 7465 | Markovian Scholarly Tensor Signature Predictor Ref-198 | Attention networks / Transformer encoders / Stock alpha generation | 3216 | 6540 | No |
| 7499 | Markovian Scholarly Tensor Signature Predictor Ref-678 | Attention networks / Transformer encoders / Stock alpha generation | 3232 | 6566 | No |
| 7947 | Markovian Scholarly Tensor Signature Predictor Eng-438 | Attention networks / Transformer encoders / Stock alpha generation | 3527 | 7049 | No |
| 7981 | Markovian Scholarly Tensor Signature Predictor Eng-918 | Attention networks / Transformer encoders / Stock alpha generation | 3547 | 7081 | No |
| 8015 | Markovian Scholarly Tensor Signature Predictor Eng-1398 | Attention networks / Transformer encoders / Stock alpha generation | 3567 | 7113 | No |
| 8049 | Markovian Scholarly Tensor Signature Predictor Eng-1878 | Attention networks / Transformer encoders / Stock alpha generation | 3587 | 7145 | No |
| 8083 | Markovian Scholarly Tensor Signature Predictor Eng-2358 | Attention networks / Transformer encoders / Stock alpha generation | 3607 | 7177 | No |
| 8117 | Markovian Scholarly Tensor Signature Predictor Eng-2838 | Attention networks / Transformer encoders / Stock alpha generation | 3627 | 7209 | No |
| 8151 | Markovian Scholarly Tensor Signature Predictor Eng-3318 | Attention networks / Transformer encoders / Stock alpha generation | 3647 | 7241 | No |
| 8185 | Markovian Scholarly Tensor Signature Predictor Eng-3798 | Attention networks / Transformer encoders / Stock alpha generation | 3667 | 7273 | No |
| 8219 | Markovian Scholarly Tensor Signature Predictor Eng-4278 | Attention networks / Transformer encoders / Stock alpha generation | 3687 | 7305 | No |
| 8253 | Markovian Scholarly Tensor Signature Predictor Eng-4758 | Attention networks / Transformer encoders / Stock alpha generation | 3707 | 7337 | No |
| 8287 | Markovian Scholarly Tensor Signature Predictor Eng-5238 | Attention networks / Transformer encoders / Stock alpha generation | 3727 | 7369 | No |
| 8321 | Markovian Scholarly Tensor Signature Predictor Eng-5718 | Attention networks / Transformer encoders / Stock alpha generation | 3747 | 7401 | No |
| 8477 | Markovian Scholarly Tensor Signature Predictor Alpha-6 | Quantum machine learning / Parametrized circuits / Index forecasting | 11263 | 5939 | No |
| 8517 | Markovian Scholarly Tensor Signature Predictor Alpha-106 | Quantum machine learning / Parametrized circuits / Index forecasting | 11267 | 5943 | No |
| 8557 | Markovian Scholarly Tensor Signature Predictor Alpha-206 | Quantum machine learning / Parametrized circuits / Index forecasting | 13979 | 13977 | No |
| 8597 | Markovian Scholarly Tensor Signature Predictor Alpha-306 | Quantum machine learning / Parametrized circuits / Index forecasting | 11276 | 5952 | No |
| 8637 | Markovian Scholarly Tensor Signature Predictor Alpha-406 | Quantum machine learning / Parametrized circuits / Index forecasting | 11280 | 5956 | No |
| 8677 | Markovian Scholarly Tensor Signature Predictor Ref-6 | Quantum machine learning / Variational circuits / Index prediction | 11284 | 5961 | No |
| 8829 | Markovian Scholarly Tensor Signature Predictor Ref-390 | Neural operators / Deep operator networks / ETF rotation | 5843 | 2167 | No |
| 8868 | Markovian Scholarly Tensor Signature Predictor Ref-486 | Quantum machine learning / Variational circuits / Index prediction | 11309 | 5981 | No |
| 9020 | Markovian Scholarly Tensor Signature Predictor Ref-870 | Neural operators / Deep operator networks / ETF rotation | 5868 | 2192 | No |
| 9059 | Markovian Scholarly Tensor Signature Predictor Ref-966 | Quantum machine learning / Variational circuits / Index prediction | 11334 | 6001 | No |
| 11506 | Markovian Scholarly Tensor Signature Predictor Eng-150 | Neural operators / Deep operator networks / ETF rotation | 6166 | 2478 | No |
| 11540 | Markovian Scholarly Tensor Signature Predictor Eng-246 | Quantum machine learning / Variational circuits / Index prediction | 11686 | 6221 | No |
| 11697 | Markovian Scholarly Tensor Signature Predictor Eng-630 | Neural operators / Deep operator networks / ETF rotation | 6188 | 2501 | No |
| 11731 | Markovian Scholarly Tensor Signature Predictor Eng-726 | Quantum machine learning / Variational circuits / Index prediction | 11711 | 6242 | No |
| 11888 | Markovian Scholarly Tensor Signature Predictor Eng-1110 | Neural operators / Deep operator networks / ETF rotation | 6210 | 2524 | No |
| 11922 | Markovian Scholarly Tensor Signature Predictor Eng-1206 | Quantum machine learning / Variational circuits / Index prediction | 11736 | 6263 | No |
| 12079 | Markovian Scholarly Tensor Signature Predictor Eng-1590 | Neural operators / Deep operator networks / ETF rotation | 6232 | 2547 | No |
| 12113 | Markovian Scholarly Tensor Signature Predictor Eng-1686 | Quantum machine learning / Variational circuits / Index prediction | 11761 | 6284 | No |
| 12270 | Markovian Scholarly Tensor Signature Predictor Eng-2070 | Neural operators / Deep operator networks / ETF rotation | 6254 | 2570 | No |
| 12304 | Markovian Scholarly Tensor Signature Predictor Eng-2166 | Quantum machine learning / Variational circuits / Index prediction | 11786 | 6305 | No |
| 12461 | Markovian Scholarly Tensor Signature Predictor Eng-2550 | Neural operators / Deep operator networks / ETF rotation | 6276 | 2593 | No |
| 12495 | Markovian Scholarly Tensor Signature Predictor Eng-2646 | Quantum machine learning / Variational circuits / Index prediction | 11811 | 6326 | No |
| 12652 | Markovian Scholarly Tensor Signature Predictor Eng-3030 | Neural operators / Deep operator networks / ETF rotation | 6298 | 2616 | No |
| 12686 | Markovian Scholarly Tensor Signature Predictor Eng-3126 | Quantum machine learning / Variational circuits / Index prediction | 11836 | 6347 | No |
| 12843 | Markovian Scholarly Tensor Signature Predictor Eng-3510 | Neural operators / Deep operator networks / ETF rotation | 6320 | 2639 | No |
| 12877 | Markovian Scholarly Tensor Signature Predictor Eng-3606 | Quantum machine learning / Variational circuits / Index prediction | 11861 | 6368 | No |
| 13034 | Markovian Scholarly Tensor Signature Predictor Eng-3990 | Neural operators / Deep operator networks / ETF rotation | 6342 | 2662 | No |
| 13068 | Markovian Scholarly Tensor Signature Predictor Eng-4086 | Quantum machine learning / Variational circuits / Index prediction | 11886 | 6389 | No |
| 13225 | Markovian Scholarly Tensor Signature Predictor Eng-4470 | Neural operators / Deep operator networks / ETF rotation | 6364 | 2685 | No |
| 13259 | Markovian Scholarly Tensor Signature Predictor Eng-4566 | Quantum machine learning / Variational circuits / Index prediction | 11911 | 6410 | No |
| 13416 | Markovian Scholarly Tensor Signature Predictor Eng-4950 | Neural operators / Deep operator networks / ETF rotation | 6386 | 2708 | No |
| 13450 | Markovian Scholarly Tensor Signature Predictor Eng-5046 | Quantum machine learning / Variational circuits / Index prediction | 11936 | 6431 | No |
| 13607 | Markovian Scholarly Tensor Signature Predictor Eng-5430 | Neural operators / Deep operator networks / ETF rotation | 6408 | 2731 | No |
| 13641 | Markovian Scholarly Tensor Signature Predictor Eng-5526 | Quantum machine learning / Variational circuits / Index prediction | 11961 | 6452 | No |
| 13798 | Markovian Scholarly Tensor Signature Predictor Eng-5910 | Neural operators / Deep operator networks / ETF rotation | 6430 | 2754 | No |
