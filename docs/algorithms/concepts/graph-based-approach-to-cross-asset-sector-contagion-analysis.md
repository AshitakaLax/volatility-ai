# Graph-based approach to cross-asset/sector contagion analysis

**Concept page** · shared by **135** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,726) ·
researched 2026-10-30

| | |
|---|---|
| Task | Cross-asset / sector contagion analysis |
| Method | Graph / network models |
| Fit with this project | ⏳ reference only · background, nothing to build now |
| Useful for volatility-ai | **Reference only.** A network model is an established way to measure spillovers, but timing exposure with it is untested and this book trades one symbol; background. |
| Implemented in volatility-ai | Nothing; the regime inputs are volatility-based (V17, N5). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK258, RK262, RK264, RK269 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Wasserstein Scholarly Graph
Contagion Analyzer Ref-20") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Represent assets or sectors as a network, estimate how shocks propagate,
and use that to adjust exposure or hedges. The graph-based version
represents assets as a network of correlation or causality links and
acts on its structure. I found no study of this method on this task.

## The CSV's description

Proposed graph-based approach to cross-asset/sector contagion analysis:
Represent assets or sectors as a network and estimate how shocks or
changing correlations may propagate, then use that information to adjust
exposure or hedges. This is a concept-level interpretation of the title,
not a complete trading specification: the exact model inputs/target,
calibration, entry/exit or rebalance rules, and position sizing are not
fully defined here.

## Evidence

* **Forbes & Rigobon (2002), "No Contagion, Only Interdependence,"
  *Journal of Finance* 57(5), 2223–2261:** crisis correlations are
  biased upward by volatility; corrected, the 1987, 1994 and 1997 crises
  show interdependence, not contagion. (Abstract.)
* **Diebold & Yilmaz (2012), "Better to give than to receive,"
  *International Journal of Forecasting* 28(1), 57–66:** a
  variance-decomposition index of directional volatility spillovers
  across asset classes. (Standard reference.)
* **Billio, Getmansky, Lo & Pelizzon (2012), *Journal of Financial
  Economics* 104(3), 535–559:** Granger-causality networks of hedge
  funds, banks, brokers and insurers grew more connected before crises.
  (Abstract.)

## Against, and failure modes

* Measured crisis correlation is biased upward by volatility (Forbes &
  Rigobon); much apparent contagion is interdependence.
* Connectedness indices describe crises well; using them to time
  exposure is much less tested.
* Networks estimated from correlations are noisy and change with the
  window.

## Fit with volatility-ai

A single-ETF book has nothing to propagate shocks between; a contagion
measure could at most feed the regime input, where it competes with
volatility itself.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Forbes, K. J., Rigobon, R. (2002). *Journal of Finance* 57(5),
  2223–2261. Abstract.
* Diebold, F. X., Yilmaz, K. (2012). *International Journal of
  Forecasting* 28(1), 57–66. Standard reference.
* Billio, M., Getmansky, M., Lo, A. W., Pelizzon, L. (2012). *Journal of
  Financial Economics* 104(3), 535–559. Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 1726 | Wasserstein Scholarly Graph Contagion Analyzer Ref-20 | Fractional order / Multi-scale ETF momentum | 3861 | 2148 | No |
| 1781 | Wasserstein Scholarly Graph Contagion Analyzer Ref-500 | Fractional order / Multi-scale ETF momentum | 3888 | 2173 | No |
| 1836 | Wasserstein Scholarly Graph Contagion Analyzer Ref-980 | Fractional order / Multi-scale ETF momentum | 3915 | 2198 | No |
| 1869 | Wasserstein Scholarly Graph Contagion Analyzer Sys-340 | Fractional order / Multi-scale ETF momentum | 2226 | 498 | No |
| 1918 | Wasserstein Scholarly Graph Contagion Analyzer Sys-820 | Fractional order / Multi-scale ETF momentum | 2273 | 517 | No |
| 1967 | Wasserstein Scholarly Graph Contagion Analyzer Sys-1300 | Fractional order / Multi-scale ETF momentum | 2320 | 536 | No |
| 2016 | Wasserstein Scholarly Graph Contagion Analyzer Sys-1780 | Fractional order / Multi-scale ETF momentum | 2367 | 555 | No |
| 2090 | Wasserstein Scholarly Graph Contagion Analyzer Mod-460 | Fractional order / Multi-scale ETF momentum | 2426 | 582 | No |
| 2143 | Wasserstein Scholarly Graph Contagion Analyzer Mod-940 | Fractional order / Multi-scale ETF momentum | 2465 | 601 | No |
| 2196 | Wasserstein Scholarly Graph Contagion Analyzer Mod-1420 | Fractional order / Multi-scale ETF momentum | 2504 | 620 | No |
| 2249 | Wasserstein Scholarly Graph Contagion Analyzer Mod-1900 | Fractional order / Multi-scale ETF momentum | 2543 | 639 | No |
| 2302 | Wasserstein Scholarly Graph Contagion Analyzer Mod-2380 | Fractional order / Multi-scale ETF momentum | 2582 | 658 | No |
| 2355 | Wasserstein Scholarly Graph Contagion Analyzer Mod-2860 | Fractional order / Multi-scale ETF momentum | 2621 | 677 | No |
| 2408 | Wasserstein Scholarly Graph Contagion Analyzer Mod-3340 | Fractional order / Multi-scale ETF momentum | 2660 | 696 | No |
| 2461 | Wasserstein Scholarly Graph Contagion Analyzer Mod-3820 | Fractional order / Multi-scale ETF momentum | 2699 | 715 | No |
| 2516 | Wasserstein Scholarly Graph Contagion Analyzer Eng-340 | Fractional order / Multi-scale ETF momentum | 2740 | 734 | No |
| 2571 | Wasserstein Scholarly Graph Contagion Analyzer Eng-820 | Fractional order / Multi-scale ETF momentum | 2778 | 753 | No |
| 2626 | Wasserstein Scholarly Graph Contagion Analyzer Eng-1300 | Fractional order / Multi-scale ETF momentum | 2816 | 772 | No |
| 2681 | Wasserstein Scholarly Graph Contagion Analyzer Eng-1780 | Fractional order / Multi-scale ETF momentum | 2854 | 791 | No |
| 2736 | Wasserstein Scholarly Graph Contagion Analyzer Eng-2260 | Fractional order / Multi-scale ETF momentum | 2892 | 810 | No |
| 2791 | Wasserstein Scholarly Graph Contagion Analyzer Eng-2740 | Fractional order / Multi-scale ETF momentum | 2930 | 829 | No |
| 2846 | Wasserstein Scholarly Graph Contagion Analyzer Eng-3220 | Fractional order / Multi-scale ETF momentum | 2968 | 848 | No |
| 2901 | Wasserstein Scholarly Graph Contagion Analyzer Eng-3700 | Fractional order / Multi-scale ETF momentum | 3006 | 867 | No |
| 2956 | Wasserstein Scholarly Graph Contagion Analyzer Eng-4180 | Fractional order / Multi-scale ETF momentum | 3044 | 886 | No |
| 3011 | Wasserstein Scholarly Graph Contagion Analyzer Eng-4660 | Fractional order / Multi-scale ETF momentum | 3082 | 905 | No |
| 3066 | Wasserstein Scholarly Graph Contagion Analyzer Eng-5140 | Fractional order / Multi-scale ETF momentum | 3120 | 924 | No |
| 3121 | Wasserstein Scholarly Graph Contagion Analyzer Eng-5620 | Fractional order / Multi-scale ETF momentum | 3158 | 943 | No |
| 8722 | Wasserstein Scholarly Graph Contagion Analyzer Ref-116 | Koopman operator / Model predictive control / ETF rebalancing | 13175 | 13714 | No |
| 8758 | Wasserstein Scholarly Graph Contagion Analyzer Ref-212 | Persistence landscapes / Topological contours / Equity index | 2140 | 3063 | No |
| 8796 | Wasserstein Scholarly Graph Contagion Analyzer Ref-308 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 13477 | 11887 | No |
| 8835 | Wasserstein Scholarly Graph Contagion Analyzer Ref-404 | Operator theory / Koopman spectral expansion / ETF allocation | 6526 | 8442 | No |
| 8913 | Wasserstein Scholarly Graph Contagion Analyzer Ref-596 | Koopman operator / Model predictive control / ETF rebalancing | 13182 | 13725 | No |
| 8949 | Wasserstein Scholarly Graph Contagion Analyzer Ref-692 | Persistence landscapes / Topological contours / Equity index | 2172 | 3180 | No |
| 8987 | Wasserstein Scholarly Graph Contagion Analyzer Ref-788 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 13479 | 11910 | No |
| 9026 | Wasserstein Scholarly Graph Contagion Analyzer Ref-884 | Operator theory / Koopman spectral expansion / ETF allocation | 6569 | 8462 | No |
| 9094 | Wasserstein Scholarly Graph Contagion Analyzer Sys-52 | Persistence landscapes / Topological contours / Equity index | 9902 | 12560 | No |
| 9131 | Wasserstein Scholarly Graph Contagion Analyzer Sys-148 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 4712 | 3285 | No |
| 9169 | Wasserstein Scholarly Graph Contagion Analyzer Sys-244 | Operator theory / Koopman spectral expansion / ETF allocation | 8339 | 3305 | No |
| 9244 | Wasserstein Scholarly Graph Contagion Analyzer Sys-436 | Koopman operator / Model predictive control / ETF rebalancing | 3944 | 3344 | No |
| 9281 | Wasserstein Scholarly Graph Contagion Analyzer Sys-532 | Persistence landscapes / Topological contours / Equity index | 9913 | 12572 | No |
| 9318 | Wasserstein Scholarly Graph Contagion Analyzer Sys-628 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 4743 | 3380 | No |
| 9356 | Wasserstein Scholarly Graph Contagion Analyzer Sys-724 | Operator theory / Koopman spectral expansion / ETF allocation | 8379 | 3400 | No |
| 9431 | Wasserstein Scholarly Graph Contagion Analyzer Sys-916 | Koopman operator / Model predictive control / ETF rebalancing | 3973 | 3439 | No |
| 9468 | Wasserstein Scholarly Graph Contagion Analyzer Sys-1012 | Persistence landscapes / Topological contours / Equity index | 9924 | 12584 | No |
| 9505 | Wasserstein Scholarly Graph Contagion Analyzer Sys-1108 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 4774 | 3475 | No |
| 9543 | Wasserstein Scholarly Graph Contagion Analyzer Sys-1204 | Operator theory / Koopman spectral expansion / ETF allocation | 8419 | 3495 | No |
| 9618 | Wasserstein Scholarly Graph Contagion Analyzer Sys-1396 | Koopman operator / Model predictive control / ETF rebalancing | 4002 | 3534 | No |
| 9655 | Wasserstein Scholarly Graph Contagion Analyzer Sys-1492 | Persistence landscapes / Topological contours / Equity index | 9935 | 12596 | No |
| 9692 | Wasserstein Scholarly Graph Contagion Analyzer Sys-1588 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 4805 | 3570 | No |
| 9730 | Wasserstein Scholarly Graph Contagion Analyzer Sys-1684 | Operator theory / Koopman spectral expansion / ETF allocation | 8459 | 3590 | No |
| 9805 | Wasserstein Scholarly Graph Contagion Analyzer Sys-1876 | Koopman operator / Model predictive control / ETF rebalancing | 4031 | 3629 | No |
| 9842 | Wasserstein Scholarly Graph Contagion Analyzer Sys-1972 | Persistence landscapes / Topological contours / Equity index | 9946 | 12608 | No |
| 9882 | Wasserstein Scholarly Graph Contagion Analyzer Mod-76 | Koopman operator / Model predictive control / ETF rebalancing | 4043 | 3665 | No |
| 9918 | Wasserstein Scholarly Graph Contagion Analyzer Mod-172 | Persistence landscapes / Topological contours / Equity index | 9948 | 12614 | No |
| 9961 | Wasserstein Scholarly Graph Contagion Analyzer Mod-268 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 4846 | 3702 | No |
| 9999 | Wasserstein Scholarly Graph Contagion Analyzer Mod-364 | Operator theory / Koopman spectral expansion / ETF allocation | 8515 | 3724 | No |
| 10073 | Wasserstein Scholarly Graph Contagion Analyzer Mod-556 | Koopman operator / Model predictive control / ETF rebalancing | 4069 | 3760 | No |
| 10109 | Wasserstein Scholarly Graph Contagion Analyzer Mod-652 | Persistence landscapes / Topological contours / Equity index | 9953 | 12622 | No |
| 10152 | Wasserstein Scholarly Graph Contagion Analyzer Mod-748 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 4873 | 3797 | No |
| 10190 | Wasserstein Scholarly Graph Contagion Analyzer Mod-844 | Operator theory / Koopman spectral expansion / ETF allocation | 8553 | 3819 | No |
| 10264 | Wasserstein Scholarly Graph Contagion Analyzer Mod-1036 | Koopman operator / Model predictive control / ETF rebalancing | 4095 | 3855 | No |
| 10300 | Wasserstein Scholarly Graph Contagion Analyzer Mod-1132 | Persistence landscapes / Topological contours / Equity index | 9958 | 12630 | No |
| 10343 | Wasserstein Scholarly Graph Contagion Analyzer Mod-1228 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 4900 | 3892 | No |
| 10381 | Wasserstein Scholarly Graph Contagion Analyzer Mod-1324 | Operator theory / Koopman spectral expansion / ETF allocation | 8591 | 3914 | No |
| 10455 | Wasserstein Scholarly Graph Contagion Analyzer Mod-1516 | Koopman operator / Model predictive control / ETF rebalancing | 4121 | 3950 | No |
| 10491 | Wasserstein Scholarly Graph Contagion Analyzer Mod-1612 | Persistence landscapes / Topological contours / Equity index | 9963 | 12638 | No |
| 10534 | Wasserstein Scholarly Graph Contagion Analyzer Mod-1708 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 4927 | 3987 | No |
| 10572 | Wasserstein Scholarly Graph Contagion Analyzer Mod-1804 | Operator theory / Koopman spectral expansion / ETF allocation | 8629 | 4009 | No |
| 10646 | Wasserstein Scholarly Graph Contagion Analyzer Mod-1996 | Koopman operator / Model predictive control / ETF rebalancing | 4147 | 4045 | No |
| 10682 | Wasserstein Scholarly Graph Contagion Analyzer Mod-2092 | Persistence landscapes / Topological contours / Equity index | 9968 | 12646 | No |
| 10725 | Wasserstein Scholarly Graph Contagion Analyzer Mod-2188 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 4954 | 4082 | No |
| 10763 | Wasserstein Scholarly Graph Contagion Analyzer Mod-2284 | Operator theory / Koopman spectral expansion / ETF allocation | 8667 | 4104 | No |
| 10837 | Wasserstein Scholarly Graph Contagion Analyzer Mod-2476 | Koopman operator / Model predictive control / ETF rebalancing | 4173 | 4140 | No |
| 10873 | Wasserstein Scholarly Graph Contagion Analyzer Mod-2572 | Persistence landscapes / Topological contours / Equity index | 9973 | 12654 | No |
| 10916 | Wasserstein Scholarly Graph Contagion Analyzer Mod-2668 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 4981 | 4177 | No |
| 10954 | Wasserstein Scholarly Graph Contagion Analyzer Mod-2764 | Operator theory / Koopman spectral expansion / ETF allocation | 8705 | 4199 | No |
| 11028 | Wasserstein Scholarly Graph Contagion Analyzer Mod-2956 | Koopman operator / Model predictive control / ETF rebalancing | 4199 | 4235 | No |
| 11064 | Wasserstein Scholarly Graph Contagion Analyzer Mod-3052 | Persistence landscapes / Topological contours / Equity index | 9978 | 12662 | No |
| 11107 | Wasserstein Scholarly Graph Contagion Analyzer Mod-3148 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 5008 | 4272 | No |
| 11145 | Wasserstein Scholarly Graph Contagion Analyzer Mod-3244 | Operator theory / Koopman spectral expansion / ETF allocation | 8743 | 4294 | No |
| 11219 | Wasserstein Scholarly Graph Contagion Analyzer Mod-3436 | Koopman operator / Model predictive control / ETF rebalancing | 4225 | 4330 | No |
| 11255 | Wasserstein Scholarly Graph Contagion Analyzer Mod-3532 | Persistence landscapes / Topological contours / Equity index | 9983 | 12670 | No |
| 11298 | Wasserstein Scholarly Graph Contagion Analyzer Mod-3628 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 5035 | 4367 | No |
| 11336 | Wasserstein Scholarly Graph Contagion Analyzer Mod-3724 | Operator theory / Koopman spectral expansion / ETF allocation | 8781 | 4389 | No |
| 11410 | Wasserstein Scholarly Graph Contagion Analyzer Mod-3916 | Koopman operator / Model predictive control / ETF rebalancing | 4251 | 4425 | No |
| 11465 | Wasserstein Scholarly Graph Contagion Analyzer Eng-52 | Persistence landscapes / Topological contours / Equity index | 9988 | 12678 | No |
| 11505 | Wasserstein Scholarly Graph Contagion Analyzer Eng-148 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 5065 | 4471 | No |
| 11539 | Wasserstein Scholarly Graph Contagion Analyzer Eng-244 | Operator theory / Koopman spectral expansion / ETF allocation | 8824 | 4489 | No |
| 11617 | Wasserstein Scholarly Graph Contagion Analyzer Eng-436 | Koopman operator / Model predictive control / ETF rebalancing | 4281 | 4531 | No |
| 11656 | Wasserstein Scholarly Graph Contagion Analyzer Eng-532 | Persistence landscapes / Topological contours / Equity index | 9991 | 12686 | No |
| 11696 | Wasserstein Scholarly Graph Contagion Analyzer Eng-628 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 5090 | 4564 | No |
| 11730 | Wasserstein Scholarly Graph Contagion Analyzer Eng-724 | Operator theory / Koopman spectral expansion / ETF allocation | 8860 | 4582 | No |
| 11808 | Wasserstein Scholarly Graph Contagion Analyzer Eng-916 | Koopman operator / Model predictive control / ETF rebalancing | 4307 | 4624 | No |
| 11847 | Wasserstein Scholarly Graph Contagion Analyzer Eng-1012 | Persistence landscapes / Topological contours / Equity index | 9994 | 12694 | No |
| 11887 | Wasserstein Scholarly Graph Contagion Analyzer Eng-1108 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 5115 | 4657 | No |
| 11921 | Wasserstein Scholarly Graph Contagion Analyzer Eng-1204 | Operator theory / Koopman spectral expansion / ETF allocation | 8896 | 4675 | No |
| 11999 | Wasserstein Scholarly Graph Contagion Analyzer Eng-1396 | Koopman operator / Model predictive control / ETF rebalancing | 4333 | 4717 | No |
| 12038 | Wasserstein Scholarly Graph Contagion Analyzer Eng-1492 | Persistence landscapes / Topological contours / Equity index | 9997 | 12702 | No |
| 12078 | Wasserstein Scholarly Graph Contagion Analyzer Eng-1588 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 5140 | 4750 | No |
| 12112 | Wasserstein Scholarly Graph Contagion Analyzer Eng-1684 | Operator theory / Koopman spectral expansion / ETF allocation | 8932 | 4768 | No |
| 12190 | Wasserstein Scholarly Graph Contagion Analyzer Eng-1876 | Koopman operator / Model predictive control / ETF rebalancing | 4359 | 4810 | No |
| 12229 | Wasserstein Scholarly Graph Contagion Analyzer Eng-1972 | Persistence landscapes / Topological contours / Equity index | 10000 | 12710 | No |
| 12269 | Wasserstein Scholarly Graph Contagion Analyzer Eng-2068 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 5165 | 4843 | No |
| 12303 | Wasserstein Scholarly Graph Contagion Analyzer Eng-2164 | Operator theory / Koopman spectral expansion / ETF allocation | 8968 | 4861 | No |
| 12381 | Wasserstein Scholarly Graph Contagion Analyzer Eng-2356 | Koopman operator / Model predictive control / ETF rebalancing | 4385 | 4903 | No |
| 12420 | Wasserstein Scholarly Graph Contagion Analyzer Eng-2452 | Persistence landscapes / Topological contours / Equity index | 10003 | 12718 | No |
| 12460 | Wasserstein Scholarly Graph Contagion Analyzer Eng-2548 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 5190 | 4936 | No |
| 12494 | Wasserstein Scholarly Graph Contagion Analyzer Eng-2644 | Operator theory / Koopman spectral expansion / ETF allocation | 9004 | 4954 | No |
| 12572 | Wasserstein Scholarly Graph Contagion Analyzer Eng-2836 | Koopman operator / Model predictive control / ETF rebalancing | 4411 | 4996 | No |
| 12611 | Wasserstein Scholarly Graph Contagion Analyzer Eng-2932 | Persistence landscapes / Topological contours / Equity index | 10006 | 12726 | No |
| 12651 | Wasserstein Scholarly Graph Contagion Analyzer Eng-3028 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 5215 | 5029 | No |
| 12685 | Wasserstein Scholarly Graph Contagion Analyzer Eng-3124 | Operator theory / Koopman spectral expansion / ETF allocation | 9040 | 5047 | No |
| 12763 | Wasserstein Scholarly Graph Contagion Analyzer Eng-3316 | Koopman operator / Model predictive control / ETF rebalancing | 4437 | 5089 | No |
| 12802 | Wasserstein Scholarly Graph Contagion Analyzer Eng-3412 | Persistence landscapes / Topological contours / Equity index | 10009 | 12734 | No |
| 12842 | Wasserstein Scholarly Graph Contagion Analyzer Eng-3508 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 5240 | 5122 | No |
| 12876 | Wasserstein Scholarly Graph Contagion Analyzer Eng-3604 | Operator theory / Koopman spectral expansion / ETF allocation | 9076 | 5140 | No |
| 12954 | Wasserstein Scholarly Graph Contagion Analyzer Eng-3796 | Koopman operator / Model predictive control / ETF rebalancing | 4463 | 5182 | No |
| 12993 | Wasserstein Scholarly Graph Contagion Analyzer Eng-3892 | Persistence landscapes / Topological contours / Equity index | 10012 | 12742 | No |
| 13033 | Wasserstein Scholarly Graph Contagion Analyzer Eng-3988 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 5265 | 5215 | No |
| 13067 | Wasserstein Scholarly Graph Contagion Analyzer Eng-4084 | Operator theory / Koopman spectral expansion / ETF allocation | 9112 | 5233 | No |
| 13145 | Wasserstein Scholarly Graph Contagion Analyzer Eng-4276 | Koopman operator / Model predictive control / ETF rebalancing | 4489 | 5275 | No |
| 13184 | Wasserstein Scholarly Graph Contagion Analyzer Eng-4372 | Persistence landscapes / Topological contours / Equity index | 10015 | 12750 | No |
| 13224 | Wasserstein Scholarly Graph Contagion Analyzer Eng-4468 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 5290 | 5308 | No |
| 13258 | Wasserstein Scholarly Graph Contagion Analyzer Eng-4564 | Operator theory / Koopman spectral expansion / ETF allocation | 9148 | 5326 | No |
| 13336 | Wasserstein Scholarly Graph Contagion Analyzer Eng-4756 | Koopman operator / Model predictive control / ETF rebalancing | 4515 | 5368 | No |
| 13375 | Wasserstein Scholarly Graph Contagion Analyzer Eng-4852 | Persistence landscapes / Topological contours / Equity index | 10018 | 12758 | No |
| 13415 | Wasserstein Scholarly Graph Contagion Analyzer Eng-4948 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 5315 | 5401 | No |
| 13449 | Wasserstein Scholarly Graph Contagion Analyzer Eng-5044 | Operator theory / Koopman spectral expansion / ETF allocation | 9184 | 5419 | No |
| 13527 | Wasserstein Scholarly Graph Contagion Analyzer Eng-5236 | Koopman operator / Model predictive control / ETF rebalancing | 4541 | 5461 | No |
| 13566 | Wasserstein Scholarly Graph Contagion Analyzer Eng-5332 | Persistence landscapes / Topological contours / Equity index | 10021 | 12766 | No |
| 13606 | Wasserstein Scholarly Graph Contagion Analyzer Eng-5428 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 5340 | 5494 | No |
| 13640 | Wasserstein Scholarly Graph Contagion Analyzer Eng-5524 | Operator theory / Koopman spectral expansion / ETF allocation | 9220 | 5512 | No |
| 13718 | Wasserstein Scholarly Graph Contagion Analyzer Eng-5716 | Koopman operator / Model predictive control / ETF rebalancing | 4567 | 5554 | No |
| 13757 | Wasserstein Scholarly Graph Contagion Analyzer Eng-5812 | Persistence landscapes / Topological contours / Equity index | 10024 | 12774 | No |
| 13797 | Wasserstein Scholarly Graph Contagion Analyzer Eng-5908 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 5365 | 5587 | No |
