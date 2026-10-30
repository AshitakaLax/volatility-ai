# Adaptive approach to macro-driven index allocation

**Concept page** · shared by **67** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,878) ·
researched 2026-10-30

| | |
|---|---|
| Task | Macro-driven index allocation |
| Method | Adaptive (time-varying parameters or thresholds) |
| Fit with this project | ⏳ reference only · background, nothing to build now |
| Useful for volatility-ai | **Reference only.** An adaptive rule is a sound way to combine macro inputs, but single macro predictors fail out of sample (Welch & Goyal 2008); background beside RK41. |
| Implemented in volatility-ai | Macro series are in the warehouse with publication lags (`engine/warehouse/queries.py`); no macro allocator. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK41, RK211, RK217, N5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Adaptive Scholarly
Macro-Driven Index Allocator Sys-382") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Use macroeconomic and market indicators, lagged by their publication
dates, to shift allocations among index-linked assets. The adaptive
version lets its parameters or thresholds move with recent data. I found
no study of this method on this task.

## The CSV's description

Proposed adaptive approach to macro-driven index allocation: Use
macroeconomic and market indicators to adjust allocations among
index-linked assets, with explicit publication lags and rebalance rules
needed to prevent look-ahead bias. This is a concept-level
interpretation of the title, not a complete trading specification: the
exact model inputs/target, calibration, entry/exit or rebalance rules,
and position sizing are not fully defined here.

## Evidence

* **Welch & Goyal (2008), "A Comprehensive Look at the Empirical
  Performance of Equity Premium Prediction," *Review of Financial
  Studies* 21(4), 1455–1508:** the standard macro and valuation
  predictors of the equity premium performed poorly out of sample.
  (Standard reference.)
* **Rapach, Strauss & Zhou (2010), *Review of Financial Studies* 23(2),
  821–862:** combining the individual predictors' forecasts gives small
  but consistent out-of-sample gains, linked to the business cycle.
  (Abstract.)

## Against, and failure modes

* Macro data are monthly or quarterly, revised and published with lags;
  a few decades give few independent observations.
* Each predictor alone has failed out of sample (Welch & Goyal); gains
  come only from combining many, and they are small.
* Parameters re-fitted often chase the recent past unless the adaptation
  itself is tested out of sample.

## Fit with volatility-ai

The warehouse already holds macro series, shifted by their publication
lag before the as-of join (`engine/warehouse/queries.py`), so a macro
input is possible. The evidence says expect little; a macro signal would
be one more regime input, tested against the NATR exit like any other.
The inflation-regime rotation (RK41) is the researched candidate.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Welch, I., Goyal, A. (2008). *Review of Financial Studies* 21(4),
  1455–1508. Standard reference.
* Rapach, D. E., Strauss, J. K., Zhou, G. (2010). *Review of Financial
  Studies* 23(2), 821–862. Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 1878 | Adaptive Scholarly Macro-Driven Index Allocator Sys-382 | Robust optimization / Distributionally robust CVaR / Index tracking | 8354 | 11346 | No |
| 1927 | Adaptive Scholarly Macro-Driven Index Allocator Sys-862 | Robust optimization / Distributionally robust CVaR / Index tracking | 8394 | 11356 | No |
| 1976 | Adaptive Scholarly Macro-Driven Index Allocator Sys-1342 | Robust optimization / Distributionally robust CVaR / Index tracking | 8434 | 11366 | No |
| 2025 | Adaptive Scholarly Macro-Driven Index Allocator Sys-1822 | Robust optimization / Distributionally robust CVaR / Index tracking | 8474 | 11376 | No |
| 2074 | Adaptive Scholarly Macro-Driven Index Allocator Mod-322 | Robust optimization / Distributionally robust CVaR / Index tracking | 8513 | 11390 | No |
| 2127 | Adaptive Scholarly Macro-Driven Index Allocator Mod-802 | Robust optimization / Distributionally robust CVaR / Index tracking | 8551 | 11404 | No |
| 2180 | Adaptive Scholarly Macro-Driven Index Allocator Mod-1282 | Robust optimization / Distributionally robust CVaR / Index tracking | 8589 | 11418 | No |
| 2233 | Adaptive Scholarly Macro-Driven Index Allocator Mod-1762 | Robust optimization / Distributionally robust CVaR / Index tracking | 8627 | 11432 | No |
| 2286 | Adaptive Scholarly Macro-Driven Index Allocator Mod-2242 | Robust optimization / Distributionally robust CVaR / Index tracking | 8665 | 11446 | No |
| 2339 | Adaptive Scholarly Macro-Driven Index Allocator Mod-2722 | Robust optimization / Distributionally robust CVaR / Index tracking | 8703 | 11460 | No |
| 2392 | Adaptive Scholarly Macro-Driven Index Allocator Mod-3202 | Robust optimization / Distributionally robust CVaR / Index tracking | 8741 | 11474 | No |
| 2445 | Adaptive Scholarly Macro-Driven Index Allocator Mod-3682 | Robust optimization / Distributionally robust CVaR / Index tracking | 8779 | 11488 | No |
| 3214 | Adaptive Scholarly Macro-Driven Index Allocator Sys-94 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6588 | 3274 | No |
| 3236 | Adaptive Scholarly Macro-Driven Index Allocator Sys-574 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6627 | 3369 | No |
| 3258 | Adaptive Scholarly Macro-Driven Index Allocator Sys-1054 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6666 | 3464 | No |
| 3280 | Adaptive Scholarly Macro-Driven Index Allocator Sys-1534 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6705 | 3559 | No |
| 3303 | Adaptive Scholarly Macro-Driven Index Allocator Mod-34 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6746 | 3658 | No |
| 3321 | Adaptive Scholarly Macro-Driven Index Allocator Mod-514 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6788 | 3753 | No |
| 3339 | Adaptive Scholarly Macro-Driven Index Allocator Mod-994 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6830 | 3848 | No |
| 3357 | Adaptive Scholarly Macro-Driven Index Allocator Mod-1474 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6872 | 3943 | No |
| 3375 | Adaptive Scholarly Macro-Driven Index Allocator Mod-1954 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6914 | 4038 | No |
| 3393 | Adaptive Scholarly Macro-Driven Index Allocator Mod-2434 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6956 | 4133 | No |
| 3411 | Adaptive Scholarly Macro-Driven Index Allocator Mod-2914 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6998 | 4228 | No |
| 3429 | Adaptive Scholarly Macro-Driven Index Allocator Mod-3394 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7040 | 4323 | No |
| 3447 | Adaptive Scholarly Macro-Driven Index Allocator Mod-3874 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7082 | 4418 | No |
| 7432 | Adaptive Scholarly Macro-Driven Index Allocator Alpha-38 | Attention networks / Self-attention / Stock alpha generation | 12811 | 11263 | No |
| 7436 | Adaptive Scholarly Macro-Driven Index Allocator Alpha-138 | Attention networks / Self-attention / Stock alpha generation | 3196 | 1830 | No |
| 7440 | Adaptive Scholarly Macro-Driven Index Allocator Alpha-238 | Attention networks / Self-attention / Stock alpha generation | 3199 | 990 | No |
| 7444 | Adaptive Scholarly Macro-Driven Index Allocator Alpha-338 | Attention networks / Self-attention / Stock alpha generation | 12818 | 11268 | No |
| 7448 | Adaptive Scholarly Macro-Driven Index Allocator Alpha-438 | Attention networks / Self-attention / Stock alpha generation | 3207 | 1841 | No |
| 7552 | Adaptive Scholarly Macro-Driven Index Allocator Sys-478 | Attention networks / Transformer encoders / Stock alpha generation | 3266 | 3349 | No |
| 7583 | Adaptive Scholarly Macro-Driven Index Allocator Sys-958 | Attention networks / Transformer encoders / Stock alpha generation | 3290 | 3444 | No |
| 7614 | Adaptive Scholarly Macro-Driven Index Allocator Sys-1438 | Attention networks / Transformer encoders / Stock alpha generation | 3314 | 3539 | No |
| 7645 | Adaptive Scholarly Macro-Driven Index Allocator Sys-1918 | Attention networks / Transformer encoders / Stock alpha generation | 3338 | 3634 | No |
| 7677 | Adaptive Scholarly Macro-Driven Index Allocator Mod-418 | Attention networks / Transformer encoders / Stock alpha generation | 3359 | 3736 | No |
| 7709 | Adaptive Scholarly Macro-Driven Index Allocator Mod-898 | Attention networks / Transformer encoders / Stock alpha generation | 3379 | 3831 | No |
| 7741 | Adaptive Scholarly Macro-Driven Index Allocator Mod-1378 | Attention networks / Transformer encoders / Stock alpha generation | 3399 | 3926 | No |
| 7773 | Adaptive Scholarly Macro-Driven Index Allocator Mod-1858 | Attention networks / Transformer encoders / Stock alpha generation | 3419 | 4021 | No |
| 7805 | Adaptive Scholarly Macro-Driven Index Allocator Mod-2338 | Attention networks / Transformer encoders / Stock alpha generation | 3439 | 4116 | No |
| 7837 | Adaptive Scholarly Macro-Driven Index Allocator Mod-2818 | Attention networks / Transformer encoders / Stock alpha generation | 3459 | 4211 | No |
| 7869 | Adaptive Scholarly Macro-Driven Index Allocator Mod-3298 | Attention networks / Transformer encoders / Stock alpha generation | 3479 | 4306 | No |
| 7901 | Adaptive Scholarly Macro-Driven Index Allocator Mod-3778 | Attention networks / Transformer encoders / Stock alpha generation | 3499 | 4401 | No |
| 9147 | Adaptive Scholarly Macro-Driven Index Allocator Sys-190 | Neural operators / Deep operator networks / ETF rotation | 7652 | 3294 | No |
| 9185 | Adaptive Scholarly Macro-Driven Index Allocator Sys-286 | Quantum machine learning / Variational circuits / Index prediction | 11352 | 6012 | No |
| 9334 | Adaptive Scholarly Macro-Driven Index Allocator Sys-670 | Neural operators / Deep operator networks / ETF rotation | 7656 | 3389 | No |
| 9372 | Adaptive Scholarly Macro-Driven Index Allocator Sys-766 | Quantum machine learning / Variational circuits / Index prediction | 11378 | 6027 | No |
| 9521 | Adaptive Scholarly Macro-Driven Index Allocator Sys-1150 | Neural operators / Deep operator networks / ETF rotation | 7660 | 3484 | No |
| 9559 | Adaptive Scholarly Macro-Driven Index Allocator Sys-1246 | Quantum machine learning / Variational circuits / Index prediction | 11404 | 6042 | No |
| 9708 | Adaptive Scholarly Macro-Driven Index Allocator Sys-1630 | Neural operators / Deep operator networks / ETF rotation | 7664 | 3579 | No |
| 9746 | Adaptive Scholarly Macro-Driven Index Allocator Sys-1726 | Quantum machine learning / Variational circuits / Index prediction | 11430 | 6057 | No |
| 9903 | Adaptive Scholarly Macro-Driven Index Allocator Mod-130 | Neural operators / Deep operator networks / ETF rotation | 7669 | 3675 | No |
| 9942 | Adaptive Scholarly Macro-Driven Index Allocator Mod-226 | Quantum machine learning / Variational circuits / Index prediction | 11460 | 6074 | No |
| 10094 | Adaptive Scholarly Macro-Driven Index Allocator Mod-610 | Neural operators / Deep operator networks / ETF rotation | 7673 | 3770 | No |
| 10133 | Adaptive Scholarly Macro-Driven Index Allocator Mod-706 | Quantum machine learning / Variational circuits / Index prediction | 11487 | 6091 | No |
| 10285 | Adaptive Scholarly Macro-Driven Index Allocator Mod-1090 | Neural operators / Deep operator networks / ETF rotation | 7677 | 3865 | No |
| 10324 | Adaptive Scholarly Macro-Driven Index Allocator Mod-1186 | Quantum machine learning / Variational circuits / Index prediction | 11514 | 6108 | No |
| 10476 | Adaptive Scholarly Macro-Driven Index Allocator Mod-1570 | Neural operators / Deep operator networks / ETF rotation | 7681 | 3960 | No |
| 10515 | Adaptive Scholarly Macro-Driven Index Allocator Mod-1666 | Quantum machine learning / Variational circuits / Index prediction | 11541 | 6125 | No |
| 10667 | Adaptive Scholarly Macro-Driven Index Allocator Mod-2050 | Neural operators / Deep operator networks / ETF rotation | 7685 | 4055 | No |
| 10706 | Adaptive Scholarly Macro-Driven Index Allocator Mod-2146 | Quantum machine learning / Variational circuits / Index prediction | 11568 | 6142 | No |
| 10858 | Adaptive Scholarly Macro-Driven Index Allocator Mod-2530 | Neural operators / Deep operator networks / ETF rotation | 7689 | 4150 | No |
| 10897 | Adaptive Scholarly Macro-Driven Index Allocator Mod-2626 | Quantum machine learning / Variational circuits / Index prediction | 11595 | 6159 | No |
| 11049 | Adaptive Scholarly Macro-Driven Index Allocator Mod-3010 | Neural operators / Deep operator networks / ETF rotation | 7693 | 4245 | No |
| 11088 | Adaptive Scholarly Macro-Driven Index Allocator Mod-3106 | Quantum machine learning / Variational circuits / Index prediction | 11622 | 6176 | No |
| 11240 | Adaptive Scholarly Macro-Driven Index Allocator Mod-3490 | Neural operators / Deep operator networks / ETF rotation | 7697 | 4340 | No |
| 11279 | Adaptive Scholarly Macro-Driven Index Allocator Mod-3586 | Quantum machine learning / Variational circuits / Index prediction | 11649 | 6193 | No |
| 11431 | Adaptive Scholarly Macro-Driven Index Allocator Mod-3970 | Neural operators / Deep operator networks / ETF rotation | 7701 | 4435 | No |
