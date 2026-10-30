# Fractional-order approach to macro-driven index allocation

**Concept page** · shared by **62** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #3,976) ·
researched 2026-10-30

| | |
|---|---|
| Task | Macro-driven index allocation |
| Method | Fractional-order models (long memory, fractional calculus) |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of fractional-order models extracting a usable signal from macro data, where even simple predictors fail out of sample. |
| Implemented in volatility-ai | Macro series are in the warehouse with publication lags (`engine/warehouse/queries.py`); no macro allocator. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK41, RK211, RK217, N5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Fractional Scholarly
Macro-Driven Index Allocator Sys-142") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Use macroeconomic and market indicators, lagged by their publication
dates, to shift allocations among index-linked assets. The
fractional-order version models long memory with fractional differencing
or fractional-order dynamics. I found no study of this method on this
task.

## The CSV's description

Proposed fractional-order approach to macro-driven index allocation: Use
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
* Long memory in returns is weak once short-range dependence is allowed
  for (Lo 1991); in volatility, the simpler HAR model reproduces it
  (Corsi 2009).

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
| 3976 | Fractional Scholarly Macro-Driven Index Allocator Sys-142 | Robust optimization / Distributionally robust CVaR / Index tracking | 8332 | 11341 | No |
| 4062 | Fractional Scholarly Macro-Driven Index Allocator Sys-622 | Robust optimization / Distributionally robust CVaR / Index tracking | 8372 | 11351 | No |
| 4148 | Fractional Scholarly Macro-Driven Index Allocator Sys-1102 | Robust optimization / Distributionally robust CVaR / Index tracking | 8412 | 11361 | No |
| 4234 | Fractional Scholarly Macro-Driven Index Allocator Sys-1582 | Robust optimization / Distributionally robust CVaR / Index tracking | 8452 | 11371 | No |
| 4326 | Fractional Scholarly Macro-Driven Index Allocator Mod-82 | Robust optimization / Distributionally robust CVaR / Index tracking | 8494 | 11383 | No |
| 4411 | Fractional Scholarly Macro-Driven Index Allocator Mod-562 | Robust optimization / Distributionally robust CVaR / Index tracking | 8532 | 11397 | No |
| 4496 | Fractional Scholarly Macro-Driven Index Allocator Mod-1042 | Robust optimization / Distributionally robust CVaR / Index tracking | 8570 | 11411 | No |
| 4581 | Fractional Scholarly Macro-Driven Index Allocator Mod-1522 | Robust optimization / Distributionally robust CVaR / Index tracking | 8608 | 11425 | No |
| 4666 | Fractional Scholarly Macro-Driven Index Allocator Mod-2002 | Robust optimization / Distributionally robust CVaR / Index tracking | 8646 | 11439 | No |
| 4751 | Fractional Scholarly Macro-Driven Index Allocator Mod-2482 | Robust optimization / Distributionally robust CVaR / Index tracking | 8684 | 11453 | No |
| 4836 | Fractional Scholarly Macro-Driven Index Allocator Mod-2962 | Robust optimization / Distributionally robust CVaR / Index tracking | 8722 | 11467 | No |
| 4921 | Fractional Scholarly Macro-Driven Index Allocator Mod-3442 | Robust optimization / Distributionally robust CVaR / Index tracking | 8760 | 11481 | No |
| 5006 | Fractional Scholarly Macro-Driven Index Allocator Mod-3922 | Robust optimization / Distributionally robust CVaR / Index tracking | 8798 | 11495 | No |
| 6308 | Fractional Scholarly Macro-Driven Index Allocator Sys-334 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6609 | 3323 | No |
| 6349 | Fractional Scholarly Macro-Driven Index Allocator Sys-814 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6648 | 3418 | No |
| 6390 | Fractional Scholarly Macro-Driven Index Allocator Sys-1294 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6687 | 3513 | No |
| 6431 | Fractional Scholarly Macro-Driven Index Allocator Sys-1774 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6726 | 3608 | No |
| 6478 | Fractional Scholarly Macro-Driven Index Allocator Mod-274 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6767 | 3705 | No |
| 6523 | Fractional Scholarly Macro-Driven Index Allocator Mod-754 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6809 | 3800 | No |
| 6568 | Fractional Scholarly Macro-Driven Index Allocator Mod-1234 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6851 | 3895 | No |
| 6613 | Fractional Scholarly Macro-Driven Index Allocator Mod-1714 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6893 | 3990 | No |
| 6658 | Fractional Scholarly Macro-Driven Index Allocator Mod-2194 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6935 | 4085 | No |
| 6703 | Fractional Scholarly Macro-Driven Index Allocator Mod-2674 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6977 | 4180 | No |
| 6748 | Fractional Scholarly Macro-Driven Index Allocator Mod-3154 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7019 | 4275 | No |
| 6793 | Fractional Scholarly Macro-Driven Index Allocator Mod-3634 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7061 | 4370 | No |
| 9090 | Fractional Scholarly Macro-Driven Index Allocator Sys-46 | Quantum machine learning / Variational circuits / Index prediction | 11340 | 6004 | No |
| 9167 | Fractional Scholarly Macro-Driven Index Allocator Sys-238 | Attention networks / Transformer encoders / Stock alpha generation | 3254 | 3302 | No |
| 9242 | Fractional Scholarly Macro-Driven Index Allocator Sys-430 | Neural operators / Deep operator networks / ETF rotation | 7654 | 3343 | No |
| 9277 | Fractional Scholarly Macro-Driven Index Allocator Sys-526 | Quantum machine learning / Variational circuits / Index prediction | 11366 | 6019 | No |
| 9354 | Fractional Scholarly Macro-Driven Index Allocator Sys-718 | Attention networks / Transformer encoders / Stock alpha generation | 3278 | 3397 | No |
| 9429 | Fractional Scholarly Macro-Driven Index Allocator Sys-910 | Neural operators / Deep operator networks / ETF rotation | 7658 | 3438 | No |
| 9464 | Fractional Scholarly Macro-Driven Index Allocator Sys-1006 | Quantum machine learning / Variational circuits / Index prediction | 11392 | 6034 | No |
| 9541 | Fractional Scholarly Macro-Driven Index Allocator Sys-1198 | Attention networks / Transformer encoders / Stock alpha generation | 3302 | 3492 | No |
| 9616 | Fractional Scholarly Macro-Driven Index Allocator Sys-1390 | Neural operators / Deep operator networks / ETF rotation | 7662 | 3533 | No |
| 9651 | Fractional Scholarly Macro-Driven Index Allocator Sys-1486 | Quantum machine learning / Variational circuits / Index prediction | 11418 | 6049 | No |
| 9728 | Fractional Scholarly Macro-Driven Index Allocator Sys-1678 | Attention networks / Transformer encoders / Stock alpha generation | 3326 | 3587 | No |
| 9803 | Fractional Scholarly Macro-Driven Index Allocator Sys-1870 | Neural operators / Deep operator networks / ETF rotation | 7666 | 3628 | No |
| 9838 | Fractional Scholarly Macro-Driven Index Allocator Sys-1966 | Quantum machine learning / Variational circuits / Index prediction | 11444 | 6064 | No |
| 9920 | Fractional Scholarly Macro-Driven Index Allocator Mod-178 | Attention networks / Transformer encoders / Stock alpha generation | 3349 | 3685 | No |
| 10001 | Fractional Scholarly Macro-Driven Index Allocator Mod-370 | Neural operators / Deep operator networks / ETF rotation | 7671 | 3726 | No |
| 10037 | Fractional Scholarly Macro-Driven Index Allocator Mod-466 | Quantum machine learning / Variational circuits / Index prediction | 11472 | 6083 | No |
| 10111 | Fractional Scholarly Macro-Driven Index Allocator Mod-658 | Attention networks / Transformer encoders / Stock alpha generation | 3369 | 3780 | No |
| 10192 | Fractional Scholarly Macro-Driven Index Allocator Mod-850 | Neural operators / Deep operator networks / ETF rotation | 7675 | 3821 | No |
| 10228 | Fractional Scholarly Macro-Driven Index Allocator Mod-946 | Quantum machine learning / Variational circuits / Index prediction | 11499 | 6100 | No |
| 10302 | Fractional Scholarly Macro-Driven Index Allocator Mod-1138 | Attention networks / Transformer encoders / Stock alpha generation | 3389 | 3875 | No |
| 10383 | Fractional Scholarly Macro-Driven Index Allocator Mod-1330 | Neural operators / Deep operator networks / ETF rotation | 7679 | 3916 | No |
| 10419 | Fractional Scholarly Macro-Driven Index Allocator Mod-1426 | Quantum machine learning / Variational circuits / Index prediction | 11526 | 6117 | No |
| 10493 | Fractional Scholarly Macro-Driven Index Allocator Mod-1618 | Attention networks / Transformer encoders / Stock alpha generation | 3409 | 3970 | No |
| 10574 | Fractional Scholarly Macro-Driven Index Allocator Mod-1810 | Neural operators / Deep operator networks / ETF rotation | 7683 | 4011 | No |
| 10610 | Fractional Scholarly Macro-Driven Index Allocator Mod-1906 | Quantum machine learning / Variational circuits / Index prediction | 11553 | 6134 | No |
| 10684 | Fractional Scholarly Macro-Driven Index Allocator Mod-2098 | Attention networks / Transformer encoders / Stock alpha generation | 3429 | 4065 | No |
| 10765 | Fractional Scholarly Macro-Driven Index Allocator Mod-2290 | Neural operators / Deep operator networks / ETF rotation | 7687 | 4106 | No |
| 10801 | Fractional Scholarly Macro-Driven Index Allocator Mod-2386 | Quantum machine learning / Variational circuits / Index prediction | 11580 | 6151 | No |
| 10875 | Fractional Scholarly Macro-Driven Index Allocator Mod-2578 | Attention networks / Transformer encoders / Stock alpha generation | 3449 | 4160 | No |
| 10956 | Fractional Scholarly Macro-Driven Index Allocator Mod-2770 | Neural operators / Deep operator networks / ETF rotation | 7691 | 4201 | No |
| 10992 | Fractional Scholarly Macro-Driven Index Allocator Mod-2866 | Quantum machine learning / Variational circuits / Index prediction | 11607 | 6168 | No |
| 11066 | Fractional Scholarly Macro-Driven Index Allocator Mod-3058 | Attention networks / Transformer encoders / Stock alpha generation | 3469 | 4255 | No |
| 11147 | Fractional Scholarly Macro-Driven Index Allocator Mod-3250 | Neural operators / Deep operator networks / ETF rotation | 7695 | 4296 | No |
| 11183 | Fractional Scholarly Macro-Driven Index Allocator Mod-3346 | Quantum machine learning / Variational circuits / Index prediction | 11634 | 6185 | No |
| 11257 | Fractional Scholarly Macro-Driven Index Allocator Mod-3538 | Attention networks / Transformer encoders / Stock alpha generation | 3489 | 4350 | No |
| 11338 | Fractional Scholarly Macro-Driven Index Allocator Mod-3730 | Neural operators / Deep operator networks / ETF rotation | 7699 | 4391 | No |
| 11374 | Fractional Scholarly Macro-Driven Index Allocator Mod-3826 | Quantum machine learning / Variational circuits / Index prediction | 11661 | 6202 | No |
