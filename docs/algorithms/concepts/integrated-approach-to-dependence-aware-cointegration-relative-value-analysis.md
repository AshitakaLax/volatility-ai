# Integrated approach to dependence-aware cointegration / relative-value analysis

**Concept page** · shared by **135** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #889) ·
researched 2026-10-30

| | |
|---|---|
| Task | Dependence-aware cointegration / relative-value analysis |
| Method | Integrated (combined) models |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Relative-value positions need a short leg, which the owner's rules exclude; modelling the dependence better does not change that. |
| Implemented in volatility-ai | Pairs rules are research code (`stat_arb`, RK72–RK74). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK74, RK94, RK37 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Holistic Scholarly Copula
Cointegration System Ref-280") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Model joint and tail dependence among assets and test for a stable
long-run spread before taking relative-value positions. The integrated
version chains several models or data sources into one pipeline; the
title does not say which. I found no study of this method on this task.

## The CSV's description

Proposed integrated approach to dependence-aware cointegration /
relative-value analysis: Model joint and tail dependence among assets
and assess whether a stable long-run spread exists before considering
relative-value positions. This is a concept-level interpretation of the
title, not a complete trading specification: the exact model
inputs/target, calibration, entry/exit or rebalance rules, and position
sizing are not fully defined here.

## Evidence

* **Gatev, Goetzmann & Rouwenhorst (2006), "Pairs Trading," *Review of
  Financial Studies* 19(3), 797–827:** matched pairs earned up to 11% a
  year in excess returns over 1962–2002, with lower raw profits in the
  later years (see RK72). (Abstract and summaries.)

## Against, and failure modes

* Pairs profits have fallen since the 1980s and relationships break down
  without warning.
* An unspecified combination cannot be tested as stated; each part would
  need its own evidence.

## Fit with volatility-ai

A relative-value trade needs a short leg and a universe of related
instruments; the engine trades one leveraged ETF long-only. Out of scope
as a strategy.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Gatev, E., Goetzmann, W. N., Rouwenhorst, K. G. (2006). *Review of
  Financial Studies* 19(3), 797–827. Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 889 | Holistic Scholarly Copula Cointegration System Ref-280 | Fractional order / Multi-scale ETF momentum | 4662 | 467 | No |
| 899 | Holistic Scholarly Copula Cointegration System Ref-760 | Fractional order / Multi-scale ETF momentum | 4689 | 478 | No |
| 914 | Holistic Scholarly Copula Cointegration System Sys-440 | Fractional order / Multi-scale ETF momentum | 5894 | 2216 | No |
| 926 | Holistic Scholarly Copula Cointegration System Sys-920 | Fractional order / Multi-scale ETF momentum | 5914 | 2235 | No |
| 938 | Holistic Scholarly Copula Cointegration System Sys-1400 | Fractional order / Multi-scale ETF momentum | 5934 | 2254 | No |
| 950 | Holistic Scholarly Copula Cointegration System Sys-1880 | Fractional order / Multi-scale ETF momentum | 5954 | 2273 | No |
| 960 | Holistic Scholarly Copula Cointegration System Mod-200 | Fractional order / Multi-scale ETF momentum | 5969 | 2288 | No |
| 973 | Holistic Scholarly Copula Cointegration System Mod-680 | Fractional order / Multi-scale ETF momentum | 5993 | 2311 | No |
| 986 | Holistic Scholarly Copula Cointegration System Mod-1160 | Fractional order / Multi-scale ETF momentum | 6017 | 2334 | No |
| 999 | Holistic Scholarly Copula Cointegration System Mod-1640 | Fractional order / Multi-scale ETF momentum | 6041 | 2357 | No |
| 1012 | Holistic Scholarly Copula Cointegration System Mod-2120 | Fractional order / Multi-scale ETF momentum | 6065 | 2380 | No |
| 1025 | Holistic Scholarly Copula Cointegration System Mod-2600 | Fractional order / Multi-scale ETF momentum | 6089 | 2403 | No |
| 1038 | Holistic Scholarly Copula Cointegration System Mod-3080 | Fractional order / Multi-scale ETF momentum | 6113 | 2426 | No |
| 1051 | Holistic Scholarly Copula Cointegration System Mod-3560 | Fractional order / Multi-scale ETF momentum | 6137 | 2449 | No |
| 1072 | Holistic Scholarly Copula Cointegration System Eng-440 | Fractional order / Multi-scale ETF momentum | 6180 | 2492 | No |
| 1082 | Holistic Scholarly Copula Cointegration System Eng-920 | Fractional order / Multi-scale ETF momentum | 6202 | 2515 | No |
| 1092 | Holistic Scholarly Copula Cointegration System Eng-1400 | Fractional order / Multi-scale ETF momentum | 6224 | 2538 | No |
| 1102 | Holistic Scholarly Copula Cointegration System Eng-1880 | Fractional order / Multi-scale ETF momentum | 6246 | 2561 | No |
| 1112 | Holistic Scholarly Copula Cointegration System Eng-2360 | Fractional order / Multi-scale ETF momentum | 6268 | 2584 | No |
| 1122 | Holistic Scholarly Copula Cointegration System Eng-2840 | Fractional order / Multi-scale ETF momentum | 6290 | 2607 | No |
| 1132 | Holistic Scholarly Copula Cointegration System Eng-3320 | Fractional order / Multi-scale ETF momentum | 6312 | 2630 | No |
| 1142 | Holistic Scholarly Copula Cointegration System Eng-3800 | Fractional order / Multi-scale ETF momentum | 6334 | 2653 | No |
| 1152 | Holistic Scholarly Copula Cointegration System Eng-4280 | Fractional order / Multi-scale ETF momentum | 6356 | 2676 | No |
| 1162 | Holistic Scholarly Copula Cointegration System Eng-4760 | Fractional order / Multi-scale ETF momentum | 6378 | 2699 | No |
| 1172 | Holistic Scholarly Copula Cointegration System Eng-5240 | Fractional order / Multi-scale ETF momentum | 6400 | 2722 | No |
| 1182 | Holistic Scholarly Copula Cointegration System Eng-5720 | Fractional order / Multi-scale ETF momentum | 6422 | 2745 | No |
| 6195 | Holistic Scholarly Copula Cointegration System Ref-88 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1055 | 3033 | No |
| 6205 | Holistic Scholarly Copula Cointegration System Ref-184 | Operator theory / Koopman spectral expansion / ETF allocation | 10049 | 3056 | No |
| 6222 | Holistic Scholarly Copula Cointegration System Ref-376 | Koopman operator / Model predictive control / ETF rebalancing | 5842 | 3103 | No |
| 6231 | Holistic Scholarly Copula Cointegration System Ref-472 | Persistence landscapes / Topological contours / Equity index | 8275 | 12545 | No |
| 6241 | Holistic Scholarly Copula Cointegration System Ref-568 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1089 | 3150 | No |
| 6251 | Holistic Scholarly Copula Cointegration System Ref-664 | Operator theory / Koopman spectral expansion / ETF allocation | 10059 | 3173 | No |
| 6268 | Holistic Scholarly Copula Cointegration System Ref-856 | Koopman operator / Model predictive control / ETF rebalancing | 5867 | 3220 | No |
| 6277 | Holistic Scholarly Copula Cointegration System Ref-952 | Persistence landscapes / Topological contours / Equity index | 8316 | 12558 | No |
| 6287 | Holistic Scholarly Copula Cointegration System Sys-56 | Koopman operator / Model predictive control / ETF rebalancing | 13627 | 13734 | No |
| 6295 | Holistic Scholarly Copula Cointegration System Sys-152 | Persistence landscapes / Topological contours / Equity index | 4713 | 3286 | No |
| 6301 | Holistic Scholarly Copula Cointegration System Sys-248 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12546 | 11933 | No |
| 6309 | Holistic Scholarly Copula Cointegration System Sys-344 | Operator theory / Koopman spectral expansion / ETF allocation | 9334 | 8492 | No |
| 6328 | Holistic Scholarly Copula Cointegration System Sys-536 | Koopman operator / Model predictive control / ETF rebalancing | 13630 | 13743 | No |
| 6336 | Holistic Scholarly Copula Cointegration System Sys-632 | Persistence landscapes / Topological contours / Equity index | 4744 | 3381 | No |
| 6342 | Holistic Scholarly Copula Cointegration System Sys-728 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12553 | 11956 | No |
| 6350 | Holistic Scholarly Copula Cointegration System Sys-824 | Operator theory / Koopman spectral expansion / ETF allocation | 9350 | 8527 | No |
| 6369 | Holistic Scholarly Copula Cointegration System Sys-1016 | Koopman operator / Model predictive control / ETF rebalancing | 13633 | 13752 | No |
| 6377 | Holistic Scholarly Copula Cointegration System Sys-1112 | Persistence landscapes / Topological contours / Equity index | 4775 | 3476 | No |
| 6383 | Holistic Scholarly Copula Cointegration System Sys-1208 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12560 | 11979 | No |
| 6391 | Holistic Scholarly Copula Cointegration System Sys-1304 | Operator theory / Koopman spectral expansion / ETF allocation | 9366 | 8562 | No |
| 6410 | Holistic Scholarly Copula Cointegration System Sys-1496 | Koopman operator / Model predictive control / ETF rebalancing | 13636 | 13761 | No |
| 6418 | Holistic Scholarly Copula Cointegration System Sys-1592 | Persistence landscapes / Topological contours / Equity index | 4806 | 3571 | No |
| 6424 | Holistic Scholarly Copula Cointegration System Sys-1688 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12567 | 12002 | No |
| 6432 | Holistic Scholarly Copula Cointegration System Sys-1784 | Operator theory / Koopman spectral expansion / ETF allocation | 9382 | 8597 | No |
| 6451 | Holistic Scholarly Copula Cointegration System Sys-1976 | Koopman operator / Model predictive control / ETF rebalancing | 13639 | 13770 | No |
| 6454 | Holistic Scholarly Copula Cointegration System Mod-8 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12573 | 12018 | No |
| 6464 | Holistic Scholarly Copula Cointegration System Mod-104 | Operator theory / Koopman spectral expansion / ETF allocation | 9391 | 8621 | No |
| 6481 | Holistic Scholarly Copula Cointegration System Mod-296 | Koopman operator / Model predictive control / ETF rebalancing | 13643 | 13778 | No |
| 6489 | Holistic Scholarly Copula Cointegration System Mod-392 | Persistence landscapes / Topological contours / Equity index | 4853 | 3730 | No |
| 6499 | Holistic Scholarly Copula Cointegration System Mod-488 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12576 | 12041 | No |
| 6509 | Holistic Scholarly Copula Cointegration System Mod-584 | Operator theory / Koopman spectral expansion / ETF allocation | 9408 | 8658 | No |
| 6526 | Holistic Scholarly Copula Cointegration System Mod-776 | Koopman operator / Model predictive control / ETF rebalancing | 13647 | 13787 | No |
| 6534 | Holistic Scholarly Copula Cointegration System Mod-872 | Persistence landscapes / Topological contours / Equity index | 4880 | 3825 | No |
| 6544 | Holistic Scholarly Copula Cointegration System Mod-968 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12579 | 12064 | No |
| 6554 | Holistic Scholarly Copula Cointegration System Mod-1064 | Operator theory / Koopman spectral expansion / ETF allocation | 9425 | 8695 | No |
| 6571 | Holistic Scholarly Copula Cointegration System Mod-1256 | Koopman operator / Model predictive control / ETF rebalancing | 13651 | 13796 | No |
| 6579 | Holistic Scholarly Copula Cointegration System Mod-1352 | Persistence landscapes / Topological contours / Equity index | 4907 | 3920 | No |
| 6589 | Holistic Scholarly Copula Cointegration System Mod-1448 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12582 | 12087 | No |
| 6599 | Holistic Scholarly Copula Cointegration System Mod-1544 | Operator theory / Koopman spectral expansion / ETF allocation | 9442 | 8732 | No |
| 6616 | Holistic Scholarly Copula Cointegration System Mod-1736 | Koopman operator / Model predictive control / ETF rebalancing | 13655 | 13805 | No |
| 6624 | Holistic Scholarly Copula Cointegration System Mod-1832 | Persistence landscapes / Topological contours / Equity index | 4934 | 4015 | No |
| 6634 | Holistic Scholarly Copula Cointegration System Mod-1928 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12585 | 12110 | No |
| 6644 | Holistic Scholarly Copula Cointegration System Mod-2024 | Operator theory / Koopman spectral expansion / ETF allocation | 9459 | 8769 | No |
| 6661 | Holistic Scholarly Copula Cointegration System Mod-2216 | Koopman operator / Model predictive control / ETF rebalancing | 13659 | 13814 | No |
| 6669 | Holistic Scholarly Copula Cointegration System Mod-2312 | Persistence landscapes / Topological contours / Equity index | 4961 | 4110 | No |
| 6679 | Holistic Scholarly Copula Cointegration System Mod-2408 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12588 | 12133 | No |
| 6689 | Holistic Scholarly Copula Cointegration System Mod-2504 | Operator theory / Koopman spectral expansion / ETF allocation | 9476 | 8806 | No |
| 6706 | Holistic Scholarly Copula Cointegration System Mod-2696 | Koopman operator / Model predictive control / ETF rebalancing | 13663 | 13823 | No |
| 6714 | Holistic Scholarly Copula Cointegration System Mod-2792 | Persistence landscapes / Topological contours / Equity index | 4988 | 4205 | No |
| 6724 | Holistic Scholarly Copula Cointegration System Mod-2888 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12591 | 12156 | No |
| 6734 | Holistic Scholarly Copula Cointegration System Mod-2984 | Operator theory / Koopman spectral expansion / ETF allocation | 9493 | 8843 | No |
| 6751 | Holistic Scholarly Copula Cointegration System Mod-3176 | Koopman operator / Model predictive control / ETF rebalancing | 13667 | 13832 | No |
| 6759 | Holistic Scholarly Copula Cointegration System Mod-3272 | Persistence landscapes / Topological contours / Equity index | 5015 | 4300 | No |
| 6769 | Holistic Scholarly Copula Cointegration System Mod-3368 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12594 | 12179 | No |
| 6779 | Holistic Scholarly Copula Cointegration System Mod-3464 | Operator theory / Koopman spectral expansion / ETF allocation | 9510 | 8880 | No |
| 6796 | Holistic Scholarly Copula Cointegration System Mod-3656 | Koopman operator / Model predictive control / ETF rebalancing | 13671 | 13841 | No |
| 6804 | Holistic Scholarly Copula Cointegration System Mod-3752 | Persistence landscapes / Topological contours / Equity index | 5042 | 4395 | No |
| 6814 | Holistic Scholarly Copula Cointegration System Mod-3848 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12597 | 12202 | No |
| 6824 | Holistic Scholarly Copula Cointegration System Mod-3944 | Operator theory / Koopman spectral expansion / ETF allocation | 9527 | 8917 | No |
| 6834 | Holistic Scholarly Copula Cointegration System Eng-56 | Koopman operator / Model predictive control / ETF rebalancing | 13674 | 13847 | No |
| 6841 | Holistic Scholarly Copula Cointegration System Eng-152 | Persistence landscapes / Topological contours / Equity index | 5066 | 4472 | No |
| 6853 | Holistic Scholarly Copula Cointegration System Eng-248 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12599 | 12221 | No |
| 6861 | Holistic Scholarly Copula Cointegration System Eng-344 | Operator theory / Koopman spectral expansion / ETF allocation | 9541 | 8945 | No |
| 6880 | Holistic Scholarly Copula Cointegration System Eng-536 | Koopman operator / Model predictive control / ETF rebalancing | 13678 | 13856 | No |
| 6887 | Holistic Scholarly Copula Cointegration System Eng-632 | Persistence landscapes / Topological contours / Equity index | 5091 | 4565 | No |
| 6899 | Holistic Scholarly Copula Cointegration System Eng-728 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12602 | 12244 | No |
| 6907 | Holistic Scholarly Copula Cointegration System Eng-824 | Operator theory / Koopman spectral expansion / ETF allocation | 9557 | 8980 | No |
| 6926 | Holistic Scholarly Copula Cointegration System Eng-1016 | Koopman operator / Model predictive control / ETF rebalancing | 13682 | 13865 | No |
| 6933 | Holistic Scholarly Copula Cointegration System Eng-1112 | Persistence landscapes / Topological contours / Equity index | 5116 | 4658 | No |
| 6945 | Holistic Scholarly Copula Cointegration System Eng-1208 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12605 | 12267 | No |
| 6953 | Holistic Scholarly Copula Cointegration System Eng-1304 | Operator theory / Koopman spectral expansion / ETF allocation | 9573 | 9015 | No |
| 6972 | Holistic Scholarly Copula Cointegration System Eng-1496 | Koopman operator / Model predictive control / ETF rebalancing | 13686 | 13874 | No |
| 6979 | Holistic Scholarly Copula Cointegration System Eng-1592 | Persistence landscapes / Topological contours / Equity index | 5141 | 4751 | No |
| 6991 | Holistic Scholarly Copula Cointegration System Eng-1688 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12608 | 12290 | No |
| 6999 | Holistic Scholarly Copula Cointegration System Eng-1784 | Operator theory / Koopman spectral expansion / ETF allocation | 9589 | 9050 | No |
| 7018 | Holistic Scholarly Copula Cointegration System Eng-1976 | Koopman operator / Model predictive control / ETF rebalancing | 13690 | 13883 | No |
| 7025 | Holistic Scholarly Copula Cointegration System Eng-2072 | Persistence landscapes / Topological contours / Equity index | 5166 | 4844 | No |
| 7037 | Holistic Scholarly Copula Cointegration System Eng-2168 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12611 | 12313 | No |
| 7045 | Holistic Scholarly Copula Cointegration System Eng-2264 | Operator theory / Koopman spectral expansion / ETF allocation | 9605 | 9085 | No |
| 7064 | Holistic Scholarly Copula Cointegration System Eng-2456 | Koopman operator / Model predictive control / ETF rebalancing | 13694 | 13892 | No |
| 7071 | Holistic Scholarly Copula Cointegration System Eng-2552 | Persistence landscapes / Topological contours / Equity index | 5191 | 4937 | No |
| 7083 | Holistic Scholarly Copula Cointegration System Eng-2648 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12614 | 12336 | No |
| 7091 | Holistic Scholarly Copula Cointegration System Eng-2744 | Operator theory / Koopman spectral expansion / ETF allocation | 9621 | 9120 | No |
| 7110 | Holistic Scholarly Copula Cointegration System Eng-2936 | Koopman operator / Model predictive control / ETF rebalancing | 13698 | 13901 | No |
| 7117 | Holistic Scholarly Copula Cointegration System Eng-3032 | Persistence landscapes / Topological contours / Equity index | 5216 | 5030 | No |
| 7129 | Holistic Scholarly Copula Cointegration System Eng-3128 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12617 | 12359 | No |
| 7137 | Holistic Scholarly Copula Cointegration System Eng-3224 | Operator theory / Koopman spectral expansion / ETF allocation | 9637 | 9155 | No |
| 7156 | Holistic Scholarly Copula Cointegration System Eng-3416 | Koopman operator / Model predictive control / ETF rebalancing | 13702 | 13910 | No |
| 7163 | Holistic Scholarly Copula Cointegration System Eng-3512 | Persistence landscapes / Topological contours / Equity index | 5241 | 5123 | No |
| 7175 | Holistic Scholarly Copula Cointegration System Eng-3608 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12620 | 12382 | No |
| 7183 | Holistic Scholarly Copula Cointegration System Eng-3704 | Operator theory / Koopman spectral expansion / ETF allocation | 9653 | 9190 | No |
| 7202 | Holistic Scholarly Copula Cointegration System Eng-3896 | Koopman operator / Model predictive control / ETF rebalancing | 13706 | 13919 | No |
| 7209 | Holistic Scholarly Copula Cointegration System Eng-3992 | Persistence landscapes / Topological contours / Equity index | 5266 | 5216 | No |
| 7221 | Holistic Scholarly Copula Cointegration System Eng-4088 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12623 | 12405 | No |
| 7229 | Holistic Scholarly Copula Cointegration System Eng-4184 | Operator theory / Koopman spectral expansion / ETF allocation | 9669 | 9225 | No |
| 7248 | Holistic Scholarly Copula Cointegration System Eng-4376 | Koopman operator / Model predictive control / ETF rebalancing | 13710 | 13928 | No |
| 7255 | Holistic Scholarly Copula Cointegration System Eng-4472 | Persistence landscapes / Topological contours / Equity index | 5291 | 5309 | No |
| 7267 | Holistic Scholarly Copula Cointegration System Eng-4568 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12626 | 12428 | No |
| 7275 | Holistic Scholarly Copula Cointegration System Eng-4664 | Operator theory / Koopman spectral expansion / ETF allocation | 9685 | 9260 | No |
| 7294 | Holistic Scholarly Copula Cointegration System Eng-4856 | Koopman operator / Model predictive control / ETF rebalancing | 13714 | 13937 | No |
| 7301 | Holistic Scholarly Copula Cointegration System Eng-4952 | Persistence landscapes / Topological contours / Equity index | 5316 | 5402 | No |
| 7313 | Holistic Scholarly Copula Cointegration System Eng-5048 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12629 | 12451 | No |
| 7321 | Holistic Scholarly Copula Cointegration System Eng-5144 | Operator theory / Koopman spectral expansion / ETF allocation | 9701 | 9295 | No |
| 7340 | Holistic Scholarly Copula Cointegration System Eng-5336 | Koopman operator / Model predictive control / ETF rebalancing | 13718 | 13946 | No |
| 7347 | Holistic Scholarly Copula Cointegration System Eng-5432 | Persistence landscapes / Topological contours / Equity index | 5341 | 5495 | No |
| 7359 | Holistic Scholarly Copula Cointegration System Eng-5528 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12632 | 12474 | No |
| 7367 | Holistic Scholarly Copula Cointegration System Eng-5624 | Operator theory / Koopman spectral expansion / ETF allocation | 9717 | 9330 | No |
| 7386 | Holistic Scholarly Copula Cointegration System Eng-5816 | Koopman operator / Model predictive control / ETF rebalancing | 13722 | 13955 | No |
| 7393 | Holistic Scholarly Copula Cointegration System Eng-5912 | Persistence landscapes / Topological contours / Equity index | 5366 | 5588 | No |
