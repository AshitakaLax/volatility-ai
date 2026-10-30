# Topology-aware approach to macro-driven index allocation

**Concept page** · shared by **77** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #3,836) ·
researched 2026-10-30

| | |
|---|---|
| Task | Macro-driven index allocation |
| Method | Topological data analysis (persistent homology) |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of topological data analysis extracting a usable signal from macro data, where even simple predictors fail out of sample. |
| Implemented in volatility-ai | Macro series are in the warehouse with publication lags (`engine/warehouse/queries.py`); no macro allocator. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK41, RK211, RK217, N5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Topological Scholarly
Macro-Driven Index Allocator Ref-362") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Use macroeconomic and market indicators, lagged by their publication
dates, to shift allocations among index-linked assets. The
topology-aware version derives persistent-homology features (Betti
numbers, persistence landscapes) from sliding windows of returns. I
found no study of this method on this task.

## The CSV's description

Proposed topology-aware approach to macro-driven index allocation: Use
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
* The best-known topological crash study is in sample (Gidea & Katz
  2018), and the features depend on window and scale choices.

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
| 3836 | Topological Scholarly Macro-Driven Index Allocator Ref-362 | Robust optimization / Distributionally robust CVaR / Index tracking | 4665 | 3099 | No |
| 3922 | Topological Scholarly Macro-Driven Index Allocator Ref-842 | Robust optimization / Distributionally robust CVaR / Index tracking | 4692 | 3216 | No |
| 5101 | Topological Scholarly Macro-Driven Index Allocator Eng-442 | Robust optimization / Distributionally robust CVaR / Index tracking | 8837 | 11508 | No |
| 5187 | Topological Scholarly Macro-Driven Index Allocator Eng-922 | Robust optimization / Distributionally robust CVaR / Index tracking | 8873 | 11522 | No |
| 5273 | Topological Scholarly Macro-Driven Index Allocator Eng-1402 | Robust optimization / Distributionally robust CVaR / Index tracking | 8909 | 11536 | No |
| 5359 | Topological Scholarly Macro-Driven Index Allocator Eng-1882 | Robust optimization / Distributionally robust CVaR / Index tracking | 8945 | 11550 | No |
| 5445 | Topological Scholarly Macro-Driven Index Allocator Eng-2362 | Robust optimization / Distributionally robust CVaR / Index tracking | 8981 | 11564 | No |
| 5531 | Topological Scholarly Macro-Driven Index Allocator Eng-2842 | Robust optimization / Distributionally robust CVaR / Index tracking | 9017 | 11578 | No |
| 5617 | Topological Scholarly Macro-Driven Index Allocator Eng-3322 | Robust optimization / Distributionally robust CVaR / Index tracking | 9053 | 11592 | No |
| 5703 | Topological Scholarly Macro-Driven Index Allocator Eng-3802 | Robust optimization / Distributionally robust CVaR / Index tracking | 9089 | 11606 | No |
| 5789 | Topological Scholarly Macro-Driven Index Allocator Eng-4282 | Robust optimization / Distributionally robust CVaR / Index tracking | 9125 | 11620 | No |
| 5875 | Topological Scholarly Macro-Driven Index Allocator Eng-4762 | Robust optimization / Distributionally robust CVaR / Index tracking | 9161 | 11634 | No |
| 5961 | Topological Scholarly Macro-Driven Index Allocator Eng-5242 | Robust optimization / Distributionally robust CVaR / Index tracking | 9197 | 11648 | No |
| 6047 | Topological Scholarly Macro-Driven Index Allocator Eng-5722 | Robust optimization / Distributionally robust CVaR / Index tracking | 9233 | 11662 | No |
| 6193 | Topological Scholarly Macro-Driven Index Allocator Ref-74 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5391 | 8428 | No |
| 6239 | Topological Scholarly Macro-Driven Index Allocator Ref-554 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5395 | 8448 | No |
| 6842 | Topological Scholarly Macro-Driven Index Allocator Eng-154 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7107 | 4473 | No |
| 6888 | Topological Scholarly Macro-Driven Index Allocator Eng-634 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7149 | 4566 | No |
| 6934 | Topological Scholarly Macro-Driven Index Allocator Eng-1114 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7191 | 4659 | No |
| 6980 | Topological Scholarly Macro-Driven Index Allocator Eng-1594 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7233 | 4752 | No |
| 7026 | Topological Scholarly Macro-Driven Index Allocator Eng-2074 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7275 | 4845 | No |
| 7072 | Topological Scholarly Macro-Driven Index Allocator Eng-2554 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7317 | 4938 | No |
| 7118 | Topological Scholarly Macro-Driven Index Allocator Eng-3034 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7359 | 5031 | No |
| 7164 | Topological Scholarly Macro-Driven Index Allocator Eng-3514 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7401 | 5124 | No |
| 7210 | Topological Scholarly Macro-Driven Index Allocator Eng-3994 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7443 | 5217 | No |
| 7256 | Topological Scholarly Macro-Driven Index Allocator Eng-4474 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7485 | 5310 | No |
| 7302 | Topological Scholarly Macro-Driven Index Allocator Eng-4954 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7527 | 5403 | No |
| 7348 | Topological Scholarly Macro-Driven Index Allocator Eng-5434 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7569 | 5496 | No |
| 7394 | Topological Scholarly Macro-Driven Index Allocator Eng-5914 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7611 | 5589 | No |
| 8498 | Topological Scholarly Macro-Driven Index Allocator Alpha-58 | Attention networks / Self-attention / Stock alpha generation | 3192 | 978 | No |
| 8538 | Topological Scholarly Macro-Driven Index Allocator Alpha-158 | Attention networks / Self-attention / Stock alpha generation | 12813 | 11265 | No |
| 8578 | Topological Scholarly Macro-Driven Index Allocator Alpha-258 | Attention networks / Self-attention / Stock alpha generation | 3200 | 1834 | No |
| 8618 | Topological Scholarly Macro-Driven Index Allocator Alpha-358 | Attention networks / Self-attention / Stock alpha generation | 3203 | 997 | No |
| 8658 | Topological Scholarly Macro-Driven Index Allocator Alpha-458 | Attention networks / Self-attention / Stock alpha generation | 12820 | 11270 | No |
| 8743 | Topological Scholarly Macro-Driven Index Allocator Ref-170 | Neural operators / Deep operator networks / ETF rotation | 9296 | 7594 | No |
| 8779 | Topological Scholarly Macro-Driven Index Allocator Ref-266 | Quantum machine learning / Variational circuits / Index prediction | 13985 | 13985 | No |
| 8855 | Topological Scholarly Macro-Driven Index Allocator Ref-458 | Attention networks / Transformer encoders / Stock alpha generation | 12826 | 11895 | No |
| 8934 | Topological Scholarly Macro-Driven Index Allocator Ref-650 | Neural operators / Deep operator networks / ETF rotation | 9312 | 7618 | No |
| 8970 | Topological Scholarly Macro-Driven Index Allocator Ref-746 | Quantum machine learning / Variational circuits / Index prediction | 13989 | 13993 | No |
| 9046 | Topological Scholarly Macro-Driven Index Allocator Ref-938 | Attention networks / Transformer encoders / Stock alpha generation | 12831 | 11918 | No |
| 11466 | Topological Scholarly Macro-Driven Index Allocator Eng-58 | Attention networks / Transformer encoders / Stock alpha generation | 3510 | 4456 | No |
| 11542 | Topological Scholarly Macro-Driven Index Allocator Eng-250 | Neural operators / Deep operator networks / ETF rotation | 7704 | 4491 | No |
| 11577 | Topological Scholarly Macro-Driven Index Allocator Eng-346 | Quantum machine learning / Variational circuits / Index prediction | 11691 | 6225 | No |
| 11657 | Topological Scholarly Macro-Driven Index Allocator Eng-538 | Attention networks / Transformer encoders / Stock alpha generation | 3530 | 4549 | No |
| 11733 | Topological Scholarly Macro-Driven Index Allocator Eng-730 | Neural operators / Deep operator networks / ETF rotation | 7708 | 4584 | No |
| 11768 | Topological Scholarly Macro-Driven Index Allocator Eng-826 | Quantum machine learning / Variational circuits / Index prediction | 11716 | 6246 | No |
| 11848 | Topological Scholarly Macro-Driven Index Allocator Eng-1018 | Attention networks / Transformer encoders / Stock alpha generation | 3550 | 4642 | No |
| 11924 | Topological Scholarly Macro-Driven Index Allocator Eng-1210 | Neural operators / Deep operator networks / ETF rotation | 7712 | 4677 | No |
| 11959 | Topological Scholarly Macro-Driven Index Allocator Eng-1306 | Quantum machine learning / Variational circuits / Index prediction | 11741 | 6267 | No |
| 12039 | Topological Scholarly Macro-Driven Index Allocator Eng-1498 | Attention networks / Transformer encoders / Stock alpha generation | 3570 | 4735 | No |
| 12115 | Topological Scholarly Macro-Driven Index Allocator Eng-1690 | Neural operators / Deep operator networks / ETF rotation | 7716 | 4770 | No |
| 12150 | Topological Scholarly Macro-Driven Index Allocator Eng-1786 | Quantum machine learning / Variational circuits / Index prediction | 11766 | 6288 | No |
| 12230 | Topological Scholarly Macro-Driven Index Allocator Eng-1978 | Attention networks / Transformer encoders / Stock alpha generation | 3590 | 4828 | No |
| 12306 | Topological Scholarly Macro-Driven Index Allocator Eng-2170 | Neural operators / Deep operator networks / ETF rotation | 7720 | 4863 | No |
| 12341 | Topological Scholarly Macro-Driven Index Allocator Eng-2266 | Quantum machine learning / Variational circuits / Index prediction | 11791 | 6309 | No |
| 12421 | Topological Scholarly Macro-Driven Index Allocator Eng-2458 | Attention networks / Transformer encoders / Stock alpha generation | 3610 | 4921 | No |
| 12497 | Topological Scholarly Macro-Driven Index Allocator Eng-2650 | Neural operators / Deep operator networks / ETF rotation | 7724 | 4956 | No |
| 12532 | Topological Scholarly Macro-Driven Index Allocator Eng-2746 | Quantum machine learning / Variational circuits / Index prediction | 11816 | 6330 | No |
| 12612 | Topological Scholarly Macro-Driven Index Allocator Eng-2938 | Attention networks / Transformer encoders / Stock alpha generation | 3630 | 5014 | No |
| 12688 | Topological Scholarly Macro-Driven Index Allocator Eng-3130 | Neural operators / Deep operator networks / ETF rotation | 7728 | 5049 | No |
| 12723 | Topological Scholarly Macro-Driven Index Allocator Eng-3226 | Quantum machine learning / Variational circuits / Index prediction | 11841 | 6351 | No |
| 12803 | Topological Scholarly Macro-Driven Index Allocator Eng-3418 | Attention networks / Transformer encoders / Stock alpha generation | 3650 | 5107 | No |
| 12879 | Topological Scholarly Macro-Driven Index Allocator Eng-3610 | Neural operators / Deep operator networks / ETF rotation | 7732 | 5142 | No |
| 12914 | Topological Scholarly Macro-Driven Index Allocator Eng-3706 | Quantum machine learning / Variational circuits / Index prediction | 11866 | 6372 | No |
| 12994 | Topological Scholarly Macro-Driven Index Allocator Eng-3898 | Attention networks / Transformer encoders / Stock alpha generation | 3670 | 5200 | No |
| 13070 | Topological Scholarly Macro-Driven Index Allocator Eng-4090 | Neural operators / Deep operator networks / ETF rotation | 7736 | 5235 | No |
| 13105 | Topological Scholarly Macro-Driven Index Allocator Eng-4186 | Quantum machine learning / Variational circuits / Index prediction | 11891 | 6393 | No |
| 13185 | Topological Scholarly Macro-Driven Index Allocator Eng-4378 | Attention networks / Transformer encoders / Stock alpha generation | 3690 | 5293 | No |
| 13261 | Topological Scholarly Macro-Driven Index Allocator Eng-4570 | Neural operators / Deep operator networks / ETF rotation | 7740 | 5328 | No |
| 13296 | Topological Scholarly Macro-Driven Index Allocator Eng-4666 | Quantum machine learning / Variational circuits / Index prediction | 11916 | 6414 | No |
| 13376 | Topological Scholarly Macro-Driven Index Allocator Eng-4858 | Attention networks / Transformer encoders / Stock alpha generation | 3710 | 5386 | No |
| 13452 | Topological Scholarly Macro-Driven Index Allocator Eng-5050 | Neural operators / Deep operator networks / ETF rotation | 7744 | 5421 | No |
| 13487 | Topological Scholarly Macro-Driven Index Allocator Eng-5146 | Quantum machine learning / Variational circuits / Index prediction | 11941 | 6435 | No |
| 13567 | Topological Scholarly Macro-Driven Index Allocator Eng-5338 | Attention networks / Transformer encoders / Stock alpha generation | 3730 | 5479 | No |
| 13643 | Topological Scholarly Macro-Driven Index Allocator Eng-5530 | Neural operators / Deep operator networks / ETF rotation | 7748 | 5514 | No |
| 13678 | Topological Scholarly Macro-Driven Index Allocator Eng-5626 | Quantum machine learning / Variational circuits / Index prediction | 11966 | 6456 | No |
| 13758 | Topological Scholarly Macro-Driven Index Allocator Eng-5818 | Attention networks / Transformer encoders / Stock alpha generation | 3750 | 5572 | No |
