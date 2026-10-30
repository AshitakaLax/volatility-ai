# Adaptive approach to topological-feature portfolio allocation

**Concept page** · shared by **63** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #3,962) ·
researched 2026-10-30

| | |
|---|---|
| Task | Topological-feature portfolio allocation |
| Method | Adaptive (time-varying parameters or thresholds) |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** The task is defined by topological features, which have no out-of-sample evidence (RK262); the method word does not change that. |
| Implemented in volatility-ai | Persistence diagrams and landscapes are research code (`topology`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK262, RK265, RK269 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Adaptive Scholarly
Topological Betti Allocator Sys-62") combine a method word, "Scholarly",
a task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Derive persistent-homology or Betti-number features from asset
relationships and test whether they improve allocation beyond simpler
baselines. The adaptive version lets its parameters or thresholds move
with recent data. I found no study of this method on this task.

## The CSV's description

Proposed adaptive approach to topological-feature portfolio allocation:
Derive persistent-homology or Betti-number features from market/asset
relationships and test whether they improve allocation or risk control
beyond simpler baselines. This is a concept-level interpretation of the
title, not a complete trading specification: the exact model
inputs/target, calibration, entry/exit or rebalance rules, and position
sizing are not fully defined here.

## Evidence

* **Gidea & Katz (2018), "Topological data analysis of financial time
  series: Landscapes of crashes," *Physica A* 491, 820–834:**
  persistence landscapes of index returns rose before the 2000 and 2008
  crashes, shown in sample (see RK262). (Abstract.)

## Against, and failure modes

* The best-known topological crash signal is in sample, and the ledger's
  TDA entries found no out-of-sample evidence.
* Parameters re-fitted often chase the recent past unless the adaptation
  itself is tested out of sample.

## Fit with volatility-ai

The ledger's topological entries are ⛔ for want of evidence (RK262,
RK265, RK269), and the book has one asset to allocate.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Gidea, M., Katz, Y. (2018). *Physica A* 491, 820–834. Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 3962 | Adaptive Scholarly Topological Betti Allocator Sys-62 | Robust optimization / Distributionally robust CVaR / Index tracking | 4706 | 3267 | No |
| 4048 | Adaptive Scholarly Topological Betti Allocator Sys-542 | Robust optimization / Distributionally robust CVaR / Index tracking | 4737 | 3362 | No |
| 4134 | Adaptive Scholarly Topological Betti Allocator Sys-1022 | Robust optimization / Distributionally robust CVaR / Index tracking | 4768 | 3457 | No |
| 4220 | Adaptive Scholarly Topological Betti Allocator Sys-1502 | Robust optimization / Distributionally robust CVaR / Index tracking | 4799 | 3552 | No |
| 4306 | Adaptive Scholarly Topological Betti Allocator Sys-1982 | Robust optimization / Distributionally robust CVaR / Index tracking | 4830 | 3647 | No |
| 4311 | Adaptive Scholarly Topological Betti Allocator Mod-2 | Robust optimization / Distributionally robust CVaR / Index tracking | 4831 | 3651 | No |
| 4396 | Adaptive Scholarly Topological Betti Allocator Mod-482 | Robust optimization / Distributionally robust CVaR / Index tracking | 4858 | 3746 | No |
| 4481 | Adaptive Scholarly Topological Betti Allocator Mod-962 | Robust optimization / Distributionally robust CVaR / Index tracking | 4885 | 3841 | No |
| 4566 | Adaptive Scholarly Topological Betti Allocator Mod-1442 | Robust optimization / Distributionally robust CVaR / Index tracking | 4912 | 3936 | No |
| 4651 | Adaptive Scholarly Topological Betti Allocator Mod-1922 | Robust optimization / Distributionally robust CVaR / Index tracking | 4939 | 4031 | No |
| 4736 | Adaptive Scholarly Topological Betti Allocator Mod-2402 | Robust optimization / Distributionally robust CVaR / Index tracking | 4966 | 4126 | No |
| 4821 | Adaptive Scholarly Topological Betti Allocator Mod-2882 | Robust optimization / Distributionally robust CVaR / Index tracking | 4993 | 4221 | No |
| 4906 | Adaptive Scholarly Topological Betti Allocator Mod-3362 | Robust optimization / Distributionally robust CVaR / Index tracking | 5020 | 4316 | No |
| 4991 | Adaptive Scholarly Topological Betti Allocator Mod-3842 | Robust optimization / Distributionally robust CVaR / Index tracking | 5047 | 4411 | No |
| 6302 | Adaptive Scholarly Topological Betti Allocator Sys-254 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5403 | 8485 | No |
| 6343 | Adaptive Scholarly Topological Betti Allocator Sys-734 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5411 | 8520 | No |
| 6384 | Adaptive Scholarly Topological Betti Allocator Sys-1214 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5419 | 8555 | No |
| 6425 | Adaptive Scholarly Topological Betti Allocator Sys-1694 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5427 | 8590 | No |
| 6471 | Adaptive Scholarly Topological Betti Allocator Mod-194 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5436 | 8627 | No |
| 6516 | Adaptive Scholarly Topological Betti Allocator Mod-674 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5444 | 8664 | No |
| 6561 | Adaptive Scholarly Topological Betti Allocator Mod-1154 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5452 | 8701 | No |
| 6606 | Adaptive Scholarly Topological Betti Allocator Mod-1634 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5460 | 8738 | No |
| 6651 | Adaptive Scholarly Topological Betti Allocator Mod-2114 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5468 | 8775 | No |
| 6696 | Adaptive Scholarly Topological Betti Allocator Mod-2594 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5476 | 8812 | No |
| 6741 | Adaptive Scholarly Topological Betti Allocator Mod-3074 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5484 | 8849 | No |
| 6786 | Adaptive Scholarly Topological Betti Allocator Mod-3554 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5492 | 8886 | No |
| 9133 | Adaptive Scholarly Topological Betti Allocator Sys-158 | Attention networks / Transformer encoders / Stock alpha generation | 12836 | 11929 | No |
| 9211 | Adaptive Scholarly Topological Betti Allocator Sys-350 | Neural operators / Deep operator networks / ETF rotation | 9335 | 7652 | No |
| 9247 | Adaptive Scholarly Topological Betti Allocator Sys-446 | Quantum machine learning / Variational circuits / Index prediction | 14000 | 14005 | No |
| 9320 | Adaptive Scholarly Topological Betti Allocator Sys-638 | Attention networks / Transformer encoders / Stock alpha generation | 12846 | 11952 | No |
| 9398 | Adaptive Scholarly Topological Betti Allocator Sys-830 | Neural operators / Deep operator networks / ETF rotation | 9351 | 7674 | No |
| 9434 | Adaptive Scholarly Topological Betti Allocator Sys-926 | Quantum machine learning / Variational circuits / Index prediction | 14009 | 14013 | No |
| 9507 | Adaptive Scholarly Topological Betti Allocator Sys-1118 | Attention networks / Transformer encoders / Stock alpha generation | 12856 | 11975 | No |
| 9585 | Adaptive Scholarly Topological Betti Allocator Sys-1310 | Neural operators / Deep operator networks / ETF rotation | 9367 | 7696 | No |
| 9621 | Adaptive Scholarly Topological Betti Allocator Sys-1406 | Quantum machine learning / Variational circuits / Index prediction | 14018 | 14021 | No |
| 9694 | Adaptive Scholarly Topological Betti Allocator Sys-1598 | Attention networks / Transformer encoders / Stock alpha generation | 12866 | 11998 | No |
| 9772 | Adaptive Scholarly Topological Betti Allocator Sys-1790 | Neural operators / Deep operator networks / ETF rotation | 9383 | 7718 | No |
| 9808 | Adaptive Scholarly Topological Betti Allocator Sys-1886 | Quantum machine learning / Variational circuits / Index prediction | 14027 | 14029 | No |
| 9892 | Adaptive Scholarly Topological Betti Allocator Mod-98 | Attention networks / Transformer encoders / Stock alpha generation | 12877 | 12023 | No |
| 9967 | Adaptive Scholarly Topological Betti Allocator Mod-290 | Neural operators / Deep operator networks / ETF rotation | 9398 | 7746 | No |
| 10006 | Adaptive Scholarly Topological Betti Allocator Mod-386 | Quantum machine learning / Variational circuits / Index prediction | 14036 | 14037 | No |
| 10083 | Adaptive Scholarly Topological Betti Allocator Mod-578 | Attention networks / Transformer encoders / Stock alpha generation | 12889 | 12046 | No |
| 10158 | Adaptive Scholarly Topological Betti Allocator Mod-770 | Neural operators / Deep operator networks / ETF rotation | 9415 | 7776 | No |
| 10197 | Adaptive Scholarly Topological Betti Allocator Mod-866 | Quantum machine learning / Variational circuits / Index prediction | 14044 | 14045 | No |
| 10274 | Adaptive Scholarly Topological Betti Allocator Mod-1058 | Attention networks / Transformer encoders / Stock alpha generation | 12901 | 12069 | No |
| 10349 | Adaptive Scholarly Topological Betti Allocator Mod-1250 | Neural operators / Deep operator networks / ETF rotation | 9432 | 7806 | No |
| 10388 | Adaptive Scholarly Topological Betti Allocator Mod-1346 | Quantum machine learning / Variational circuits / Index prediction | 14052 | 14053 | No |
| 10465 | Adaptive Scholarly Topological Betti Allocator Mod-1538 | Attention networks / Transformer encoders / Stock alpha generation | 12913 | 12092 | No |
| 10540 | Adaptive Scholarly Topological Betti Allocator Mod-1730 | Neural operators / Deep operator networks / ETF rotation | 9449 | 7836 | No |
| 10579 | Adaptive Scholarly Topological Betti Allocator Mod-1826 | Quantum machine learning / Variational circuits / Index prediction | 14060 | 14061 | No |
| 10656 | Adaptive Scholarly Topological Betti Allocator Mod-2018 | Attention networks / Transformer encoders / Stock alpha generation | 12925 | 12115 | No |
| 10731 | Adaptive Scholarly Topological Betti Allocator Mod-2210 | Neural operators / Deep operator networks / ETF rotation | 9466 | 7866 | No |
| 10770 | Adaptive Scholarly Topological Betti Allocator Mod-2306 | Quantum machine learning / Variational circuits / Index prediction | 14068 | 14069 | No |
| 10847 | Adaptive Scholarly Topological Betti Allocator Mod-2498 | Attention networks / Transformer encoders / Stock alpha generation | 12937 | 12138 | No |
| 10922 | Adaptive Scholarly Topological Betti Allocator Mod-2690 | Neural operators / Deep operator networks / ETF rotation | 9483 | 7896 | No |
| 10961 | Adaptive Scholarly Topological Betti Allocator Mod-2786 | Quantum machine learning / Variational circuits / Index prediction | 14076 | 14077 | No |
| 11038 | Adaptive Scholarly Topological Betti Allocator Mod-2978 | Attention networks / Transformer encoders / Stock alpha generation | 12949 | 12161 | No |
| 11113 | Adaptive Scholarly Topological Betti Allocator Mod-3170 | Neural operators / Deep operator networks / ETF rotation | 9500 | 7926 | No |
| 11152 | Adaptive Scholarly Topological Betti Allocator Mod-3266 | Quantum machine learning / Variational circuits / Index prediction | 14084 | 14085 | No |
| 11229 | Adaptive Scholarly Topological Betti Allocator Mod-3458 | Attention networks / Transformer encoders / Stock alpha generation | 12961 | 12184 | No |
| 11304 | Adaptive Scholarly Topological Betti Allocator Mod-3650 | Neural operators / Deep operator networks / ETF rotation | 9517 | 7956 | No |
| 11343 | Adaptive Scholarly Topological Betti Allocator Mod-3746 | Quantum machine learning / Variational circuits / Index prediction | 14092 | 14093 | No |
| 11420 | Adaptive Scholarly Topological Betti Allocator Mod-3938 | Attention networks / Transformer encoders / Stock alpha generation | 12973 | 12207 | No |
