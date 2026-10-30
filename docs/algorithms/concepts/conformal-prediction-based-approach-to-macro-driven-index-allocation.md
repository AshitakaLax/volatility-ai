# Conformal-prediction-based approach to macro-driven index allocation

**Concept page** · shared by **73** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,724) ·
researched 2026-10-30

| | |
|---|---|
| Task | Macro-driven index allocation |
| Method | Conformal prediction intervals |
| Fit with this project | ⏳ reference only · background, nothing to build now |
| Useful for volatility-ai | **Reference only.** Conformal prediction is a sound way to combine macro inputs, but single macro predictors fail out of sample (Welch & Goyal 2008); background beside RK41. |
| Implemented in volatility-ai | Macro series are in the warehouse with publication lags (`engine/warehouse/queries.py`); no macro allocator. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK41, RK211, RK217, N5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Conformal Scholarly
Macro-Driven Index Allocator Ref-2") combine a method word, "Scholarly",
a task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Use macroeconomic and market indicators, lagged by their publication
dates, to shift allocations among index-linked assets. The conformal
version wraps a forecast in distribution-free prediction intervals and
acts only when the interval is decisive. I found no study of this method
on this task.

## The CSV's description

Proposed conformal-prediction-based approach to macro-driven index
allocation: Use macroeconomic and market indicators to adjust
allocations among index-linked assets, with explicit publication lags
and rebalance rules needed to prevent look-ahead bias. This is a
concept-level interpretation of the title, not a complete trading
specification: the exact model inputs/target, calibration, entry/exit or
rebalance rules, and position sizing are not fully defined here.

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
* Conformal intervals measure a forecast's uncertainty; they do not
  create a forecast where none exists.

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
| 1724 | Conformal Scholarly Macro-Driven Index Allocator Ref-2 | Robust optimization / Distributionally robust CVaR / Index tracking | 4645 | 3011 | No |
| 1779 | Conformal Scholarly Macro-Driven Index Allocator Ref-482 | Robust optimization / Distributionally robust CVaR / Index tracking | 4672 | 3128 | No |
| 1834 | Conformal Scholarly Macro-Driven Index Allocator Ref-962 | Robust optimization / Distributionally robust CVaR / Index tracking | 4699 | 3245 | No |
| 2488 | Conformal Scholarly Macro-Driven Index Allocator Eng-82 | Robust optimization / Distributionally robust CVaR / Index tracking | 8811 | 11497 | No |
| 2543 | Conformal Scholarly Macro-Driven Index Allocator Eng-562 | Robust optimization / Distributionally robust CVaR / Index tracking | 8847 | 11511 | No |
| 2598 | Conformal Scholarly Macro-Driven Index Allocator Eng-1042 | Robust optimization / Distributionally robust CVaR / Index tracking | 8883 | 11525 | No |
| 2653 | Conformal Scholarly Macro-Driven Index Allocator Eng-1522 | Robust optimization / Distributionally robust CVaR / Index tracking | 8919 | 11539 | No |
| 2708 | Conformal Scholarly Macro-Driven Index Allocator Eng-2002 | Robust optimization / Distributionally robust CVaR / Index tracking | 8955 | 11553 | No |
| 2763 | Conformal Scholarly Macro-Driven Index Allocator Eng-2482 | Robust optimization / Distributionally robust CVaR / Index tracking | 8991 | 11567 | No |
| 2818 | Conformal Scholarly Macro-Driven Index Allocator Eng-2962 | Robust optimization / Distributionally robust CVaR / Index tracking | 9027 | 11581 | No |
| 2873 | Conformal Scholarly Macro-Driven Index Allocator Eng-3442 | Robust optimization / Distributionally robust CVaR / Index tracking | 9063 | 11595 | No |
| 2928 | Conformal Scholarly Macro-Driven Index Allocator Eng-3922 | Robust optimization / Distributionally robust CVaR / Index tracking | 9099 | 11609 | No |
| 2983 | Conformal Scholarly Macro-Driven Index Allocator Eng-4402 | Robust optimization / Distributionally robust CVaR / Index tracking | 9135 | 11623 | No |
| 3038 | Conformal Scholarly Macro-Driven Index Allocator Eng-4882 | Robust optimization / Distributionally robust CVaR / Index tracking | 9171 | 11637 | No |
| 3093 | Conformal Scholarly Macro-Driven Index Allocator Eng-5362 | Robust optimization / Distributionally robust CVaR / Index tracking | 9207 | 11651 | No |
| 3148 | Conformal Scholarly Macro-Driven Index Allocator Eng-5842 | Robust optimization / Distributionally robust CVaR / Index tracking | 9243 | 11665 | No |
| 3181 | Conformal Scholarly Macro-Driven Index Allocator Ref-194 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5392 | 8433 | No |
| 3197 | Conformal Scholarly Macro-Driven Index Allocator Ref-674 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5396 | 8453 | No |
| 3461 | Conformal Scholarly Macro-Driven Index Allocator Eng-274 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7118 | 4496 | No |
| 3477 | Conformal Scholarly Macro-Driven Index Allocator Eng-754 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7160 | 4589 | No |
| 3493 | Conformal Scholarly Macro-Driven Index Allocator Eng-1234 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7202 | 4682 | No |
| 3509 | Conformal Scholarly Macro-Driven Index Allocator Eng-1714 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7244 | 4775 | No |
| 3525 | Conformal Scholarly Macro-Driven Index Allocator Eng-2194 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7286 | 4868 | No |
| 3541 | Conformal Scholarly Macro-Driven Index Allocator Eng-2674 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7328 | 4961 | No |
| 3557 | Conformal Scholarly Macro-Driven Index Allocator Eng-3154 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7370 | 5054 | No |
| 3573 | Conformal Scholarly Macro-Driven Index Allocator Eng-3634 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7412 | 5147 | No |
| 3589 | Conformal Scholarly Macro-Driven Index Allocator Eng-4114 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7454 | 5240 | No |
| 3605 | Conformal Scholarly Macro-Driven Index Allocator Eng-4594 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7496 | 5333 | No |
| 3621 | Conformal Scholarly Macro-Driven Index Allocator Eng-5074 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7538 | 5426 | No |
| 3637 | Conformal Scholarly Macro-Driven Index Allocator Eng-5554 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7580 | 5519 | No |
| 7458 | Conformal Scholarly Macro-Driven Index Allocator Ref-98 | Attention networks / Transformer encoders / Stock alpha generation | 12823 | 11878 | No |
| 7492 | Conformal Scholarly Macro-Driven Index Allocator Ref-578 | Attention networks / Transformer encoders / Stock alpha generation | 12828 | 11901 | No |
| 7928 | Conformal Scholarly Macro-Driven Index Allocator Eng-178 | Attention networks / Transformer encoders / Stock alpha generation | 3515 | 4480 | No |
| 7962 | Conformal Scholarly Macro-Driven Index Allocator Eng-658 | Attention networks / Transformer encoders / Stock alpha generation | 3535 | 4573 | No |
| 7996 | Conformal Scholarly Macro-Driven Index Allocator Eng-1138 | Attention networks / Transformer encoders / Stock alpha generation | 3555 | 4666 | No |
| 8030 | Conformal Scholarly Macro-Driven Index Allocator Eng-1618 | Attention networks / Transformer encoders / Stock alpha generation | 3575 | 4759 | No |
| 8064 | Conformal Scholarly Macro-Driven Index Allocator Eng-2098 | Attention networks / Transformer encoders / Stock alpha generation | 3595 | 4852 | No |
| 8098 | Conformal Scholarly Macro-Driven Index Allocator Eng-2578 | Attention networks / Transformer encoders / Stock alpha generation | 3615 | 4945 | No |
| 8132 | Conformal Scholarly Macro-Driven Index Allocator Eng-3058 | Attention networks / Transformer encoders / Stock alpha generation | 3635 | 5038 | No |
| 8166 | Conformal Scholarly Macro-Driven Index Allocator Eng-3538 | Attention networks / Transformer encoders / Stock alpha generation | 3655 | 5131 | No |
| 8200 | Conformal Scholarly Macro-Driven Index Allocator Eng-4018 | Attention networks / Transformer encoders / Stock alpha generation | 3675 | 5224 | No |
| 8234 | Conformal Scholarly Macro-Driven Index Allocator Eng-4498 | Attention networks / Transformer encoders / Stock alpha generation | 3695 | 5317 | No |
| 8268 | Conformal Scholarly Macro-Driven Index Allocator Eng-4978 | Attention networks / Transformer encoders / Stock alpha generation | 3715 | 5410 | No |
| 8302 | Conformal Scholarly Macro-Driven Index Allocator Eng-5458 | Attention networks / Transformer encoders / Stock alpha generation | 3735 | 5503 | No |
| 8336 | Conformal Scholarly Macro-Driven Index Allocator Eng-5938 | Attention networks / Transformer encoders / Stock alpha generation | 3755 | 5596 | No |
| 8790 | Conformal Scholarly Macro-Driven Index Allocator Ref-290 | Neural operators / Deep operator networks / ETF rotation | 9299 | 7600 | No |
| 8826 | Conformal Scholarly Macro-Driven Index Allocator Ref-386 | Quantum machine learning / Variational circuits / Index prediction | 13986 | 13987 | No |
| 8981 | Conformal Scholarly Macro-Driven Index Allocator Ref-770 | Neural operators / Deep operator networks / ETF rotation | 9315 | 7624 | No |
| 9017 | Conformal Scholarly Macro-Driven Index Allocator Ref-866 | Quantum machine learning / Variational circuits / Index prediction | 13990 | 13995 | No |
| 11588 | Conformal Scholarly Macro-Driven Index Allocator Eng-370 | Neural operators / Deep operator networks / ETF rotation | 7705 | 4514 | No |
| 11626 | Conformal Scholarly Macro-Driven Index Allocator Eng-466 | Quantum machine learning / Variational circuits / Index prediction | 11696 | 6230 | No |
| 11779 | Conformal Scholarly Macro-Driven Index Allocator Eng-850 | Neural operators / Deep operator networks / ETF rotation | 7709 | 4607 | No |
| 11817 | Conformal Scholarly Macro-Driven Index Allocator Eng-946 | Quantum machine learning / Variational circuits / Index prediction | 11721 | 6251 | No |
| 11970 | Conformal Scholarly Macro-Driven Index Allocator Eng-1330 | Neural operators / Deep operator networks / ETF rotation | 7713 | 4700 | No |
| 12008 | Conformal Scholarly Macro-Driven Index Allocator Eng-1426 | Quantum machine learning / Variational circuits / Index prediction | 11746 | 6272 | No |
| 12161 | Conformal Scholarly Macro-Driven Index Allocator Eng-1810 | Neural operators / Deep operator networks / ETF rotation | 7717 | 4793 | No |
| 12199 | Conformal Scholarly Macro-Driven Index Allocator Eng-1906 | Quantum machine learning / Variational circuits / Index prediction | 11771 | 6293 | No |
| 12352 | Conformal Scholarly Macro-Driven Index Allocator Eng-2290 | Neural operators / Deep operator networks / ETF rotation | 7721 | 4886 | No |
| 12390 | Conformal Scholarly Macro-Driven Index Allocator Eng-2386 | Quantum machine learning / Variational circuits / Index prediction | 11796 | 6314 | No |
| 12543 | Conformal Scholarly Macro-Driven Index Allocator Eng-2770 | Neural operators / Deep operator networks / ETF rotation | 7725 | 4979 | No |
| 12581 | Conformal Scholarly Macro-Driven Index Allocator Eng-2866 | Quantum machine learning / Variational circuits / Index prediction | 11821 | 6335 | No |
| 12734 | Conformal Scholarly Macro-Driven Index Allocator Eng-3250 | Neural operators / Deep operator networks / ETF rotation | 7729 | 5072 | No |
| 12772 | Conformal Scholarly Macro-Driven Index Allocator Eng-3346 | Quantum machine learning / Variational circuits / Index prediction | 11846 | 6356 | No |
| 12925 | Conformal Scholarly Macro-Driven Index Allocator Eng-3730 | Neural operators / Deep operator networks / ETF rotation | 7733 | 5165 | No |
| 12963 | Conformal Scholarly Macro-Driven Index Allocator Eng-3826 | Quantum machine learning / Variational circuits / Index prediction | 11871 | 6377 | No |
| 13116 | Conformal Scholarly Macro-Driven Index Allocator Eng-4210 | Neural operators / Deep operator networks / ETF rotation | 7737 | 5258 | No |
| 13154 | Conformal Scholarly Macro-Driven Index Allocator Eng-4306 | Quantum machine learning / Variational circuits / Index prediction | 11896 | 6398 | No |
| 13307 | Conformal Scholarly Macro-Driven Index Allocator Eng-4690 | Neural operators / Deep operator networks / ETF rotation | 7741 | 5351 | No |
| 13345 | Conformal Scholarly Macro-Driven Index Allocator Eng-4786 | Quantum machine learning / Variational circuits / Index prediction | 11921 | 6419 | No |
| 13498 | Conformal Scholarly Macro-Driven Index Allocator Eng-5170 | Neural operators / Deep operator networks / ETF rotation | 7745 | 5444 | No |
| 13536 | Conformal Scholarly Macro-Driven Index Allocator Eng-5266 | Quantum machine learning / Variational circuits / Index prediction | 11946 | 6440 | No |
| 13689 | Conformal Scholarly Macro-Driven Index Allocator Eng-5650 | Neural operators / Deep operator networks / ETF rotation | 7749 | 5537 | No |
| 13727 | Conformal Scholarly Macro-Driven Index Allocator Eng-5746 | Quantum machine learning / Variational circuits / Index prediction | 11971 | 6461 | No |
