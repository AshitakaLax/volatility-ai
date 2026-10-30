# Wavelet-based approach to cross-asset/sector contagion analysis

**Concept page** · shared by **136** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,767) ·
researched 2026-10-30

| | |
|---|---|
| Task | Cross-asset / sector contagion analysis |
| Method | Wavelet multiscale decomposition |
| Fit with this project | ⏳ reference only · background, nothing to build now |
| Useful for volatility-ai | **Reference only.** Wavelet decomposition is an established way to measure spillovers, but timing exposure with it is untested and this book trades one symbol; background. |
| Implemented in volatility-ai | Nothing; the regime inputs are volatility-based (V17, N5). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK258, RK262, RK264, RK269 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Wavelet Scholarly Graph
Contagion Analyzer Ref-380") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Represent assets or sectors as a network, estimate how shocks propagate,
and use that to adjust exposure or hedges. The wavelet version
decomposes series by time scale and acts scale by scale. I found no
study of this method on this task.

## The CSV's description

Proposed wavelet-based approach to cross-asset/sector contagion
analysis: Represent assets or sectors as a network and estimate how
shocks or changing correlations may propagate, then use that information
to adjust exposure or hedges. This is a concept-level interpretation of
the title, not a complete trading specification: the exact model
inputs/target, calibration, entry/exit or rebalance rules, and position
sizing are not fully defined here.

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
* Wavelet filters see future data at the series' edge unless made
  causal, a common source of lookahead.

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
| 1767 | Wavelet Scholarly Graph Contagion Analyzer Ref-380 | Fractional order / Multi-scale ETF momentum | 3882 | 2166 | No |
| 1822 | Wavelet Scholarly Graph Contagion Analyzer Ref-860 | Fractional order / Multi-scale ETF momentum | 3909 | 2191 | No |
| 1857 | Wavelet Scholarly Graph Contagion Analyzer Sys-220 | Fractional order / Multi-scale ETF momentum | 2216 | 493 | No |
| 1906 | Wavelet Scholarly Graph Contagion Analyzer Sys-700 | Fractional order / Multi-scale ETF momentum | 2263 | 512 | No |
| 1955 | Wavelet Scholarly Graph Contagion Analyzer Sys-1180 | Fractional order / Multi-scale ETF momentum | 2310 | 531 | No |
| 2004 | Wavelet Scholarly Graph Contagion Analyzer Sys-1660 | Fractional order / Multi-scale ETF momentum | 2357 | 550 | No |
| 2049 | Wavelet Scholarly Graph Contagion Analyzer Mod-100 | Fractional order / Multi-scale ETF momentum | 2397 | 568 | No |
| 2102 | Wavelet Scholarly Graph Contagion Analyzer Mod-580 | Fractional order / Multi-scale ETF momentum | 2436 | 587 | No |
| 2155 | Wavelet Scholarly Graph Contagion Analyzer Mod-1060 | Fractional order / Multi-scale ETF momentum | 2475 | 606 | No |
| 2208 | Wavelet Scholarly Graph Contagion Analyzer Mod-1540 | Fractional order / Multi-scale ETF momentum | 2514 | 625 | No |
| 2261 | Wavelet Scholarly Graph Contagion Analyzer Mod-2020 | Fractional order / Multi-scale ETF momentum | 2553 | 644 | No |
| 2314 | Wavelet Scholarly Graph Contagion Analyzer Mod-2500 | Fractional order / Multi-scale ETF momentum | 2592 | 663 | No |
| 2367 | Wavelet Scholarly Graph Contagion Analyzer Mod-2980 | Fractional order / Multi-scale ETF momentum | 2631 | 682 | No |
| 2420 | Wavelet Scholarly Graph Contagion Analyzer Mod-3460 | Fractional order / Multi-scale ETF momentum | 2670 | 701 | No |
| 2473 | Wavelet Scholarly Graph Contagion Analyzer Mod-3940 | Fractional order / Multi-scale ETF momentum | 2709 | 720 | No |
| 2503 | Wavelet Scholarly Graph Contagion Analyzer Eng-220 | Fractional order / Multi-scale ETF momentum | 2731 | 729 | No |
| 2558 | Wavelet Scholarly Graph Contagion Analyzer Eng-700 | Fractional order / Multi-scale ETF momentum | 2769 | 748 | No |
| 2613 | Wavelet Scholarly Graph Contagion Analyzer Eng-1180 | Fractional order / Multi-scale ETF momentum | 2807 | 767 | No |
| 2668 | Wavelet Scholarly Graph Contagion Analyzer Eng-1660 | Fractional order / Multi-scale ETF momentum | 2845 | 786 | No |
| 2723 | Wavelet Scholarly Graph Contagion Analyzer Eng-2140 | Fractional order / Multi-scale ETF momentum | 2883 | 805 | No |
| 2778 | Wavelet Scholarly Graph Contagion Analyzer Eng-2620 | Fractional order / Multi-scale ETF momentum | 2921 | 824 | No |
| 2833 | Wavelet Scholarly Graph Contagion Analyzer Eng-3100 | Fractional order / Multi-scale ETF momentum | 2959 | 843 | No |
| 2888 | Wavelet Scholarly Graph Contagion Analyzer Eng-3580 | Fractional order / Multi-scale ETF momentum | 2997 | 862 | No |
| 2943 | Wavelet Scholarly Graph Contagion Analyzer Eng-4060 | Fractional order / Multi-scale ETF momentum | 3035 | 881 | No |
| 2998 | Wavelet Scholarly Graph Contagion Analyzer Eng-4540 | Fractional order / Multi-scale ETF momentum | 3073 | 900 | No |
| 3053 | Wavelet Scholarly Graph Contagion Analyzer Eng-5020 | Fractional order / Multi-scale ETF momentum | 3111 | 919 | No |
| 3108 | Wavelet Scholarly Graph Contagion Analyzer Eng-5500 | Fractional order / Multi-scale ETF momentum | 3149 | 938 | No |
| 3163 | Wavelet Scholarly Graph Contagion Analyzer Eng-5980 | Fractional order / Multi-scale ETF momentum | 3187 | 957 | No |
| 8711 | Wavelet Scholarly Graph Contagion Analyzer Ref-92 | Persistence landscapes / Topological contours / Equity index | 2132 | 3034 | No |
| 8750 | Wavelet Scholarly Graph Contagion Analyzer Ref-188 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12523 | 11881 | No |
| 8788 | Wavelet Scholarly Graph Contagion Analyzer Ref-284 | Operator theory / Koopman spectral expansion / ETF allocation | 6515 | 3080 | No |
| 8864 | Wavelet Scholarly Graph Contagion Analyzer Ref-476 | Koopman operator / Model predictive control / ETF rebalancing | 13180 | 13722 | No |
| 8902 | Wavelet Scholarly Graph Contagion Analyzer Ref-572 | Persistence landscapes / Topological contours / Equity index | 2164 | 3151 | No |
| 8941 | Wavelet Scholarly Graph Contagion Analyzer Ref-668 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12534 | 11904 | No |
| 8979 | Wavelet Scholarly Graph Contagion Analyzer Ref-764 | Operator theory / Koopman spectral expansion / ETF allocation | 6558 | 3197 | No |
| 9055 | Wavelet Scholarly Graph Contagion Analyzer Ref-956 | Koopman operator / Model predictive control / ETF rebalancing | 13187 | 13733 | No |
| 9085 | Wavelet Scholarly Graph Contagion Analyzer Sys-28 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1119 | 3261 | No |
| 9121 | Wavelet Scholarly Graph Contagion Analyzer Sys-124 | Operator theory / Koopman spectral expansion / ETF allocation | 8329 | 1085 | No |
| 9197 | Wavelet Scholarly Graph Contagion Analyzer Sys-316 | Koopman operator / Model predictive control / ETF rebalancing | 3937 | 3320 | No |
| 9236 | Wavelet Scholarly Graph Contagion Analyzer Sys-412 | Persistence landscapes / Topological contours / Equity index | 5893 | 11348 | No |
| 9272 | Wavelet Scholarly Graph Contagion Analyzer Sys-508 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1149 | 3356 | No |
| 9308 | Wavelet Scholarly Graph Contagion Analyzer Sys-604 | Operator theory / Koopman spectral expansion / ETF allocation | 8369 | 1109 | No |
| 9384 | Wavelet Scholarly Graph Contagion Analyzer Sys-796 | Koopman operator / Model predictive control / ETF rebalancing | 3966 | 3415 | No |
| 9423 | Wavelet Scholarly Graph Contagion Analyzer Sys-892 | Persistence landscapes / Topological contours / Equity index | 5913 | 11358 | No |
| 9459 | Wavelet Scholarly Graph Contagion Analyzer Sys-988 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1179 | 3451 | No |
| 9495 | Wavelet Scholarly Graph Contagion Analyzer Sys-1084 | Operator theory / Koopman spectral expansion / ETF allocation | 8409 | 1133 | No |
| 9571 | Wavelet Scholarly Graph Contagion Analyzer Sys-1276 | Koopman operator / Model predictive control / ETF rebalancing | 3995 | 3510 | No |
| 9610 | Wavelet Scholarly Graph Contagion Analyzer Sys-1372 | Persistence landscapes / Topological contours / Equity index | 5933 | 11368 | No |
| 9646 | Wavelet Scholarly Graph Contagion Analyzer Sys-1468 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1209 | 3546 | No |
| 9682 | Wavelet Scholarly Graph Contagion Analyzer Sys-1564 | Operator theory / Koopman spectral expansion / ETF allocation | 8449 | 1157 | No |
| 9758 | Wavelet Scholarly Graph Contagion Analyzer Sys-1756 | Koopman operator / Model predictive control / ETF rebalancing | 4024 | 3605 | No |
| 9797 | Wavelet Scholarly Graph Contagion Analyzer Sys-1852 | Persistence landscapes / Topological contours / Equity index | 5953 | 11378 | No |
| 9833 | Wavelet Scholarly Graph Contagion Analyzer Sys-1948 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1239 | 3641 | No |
| 9854 | Wavelet Scholarly Graph Contagion Analyzer Mod-4 | Operator theory / Koopman spectral expansion / ETF allocation | 8487 | 1180 | No |
| 9929 | Wavelet Scholarly Graph Contagion Analyzer Mod-196 | Koopman operator / Model predictive control / ETF rebalancing | 4050 | 3689 | No |
| 9968 | Wavelet Scholarly Graph Contagion Analyzer Mod-292 | Persistence landscapes / Topological contours / Equity index | 5974 | 11389 | No |
| 10008 | Wavelet Scholarly Graph Contagion Analyzer Mod-388 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1266 | 3728 | No |
| 10045 | Wavelet Scholarly Graph Contagion Analyzer Mod-484 | Operator theory / Koopman spectral expansion / ETF allocation | 8525 | 1204 | No |
| 10120 | Wavelet Scholarly Graph Contagion Analyzer Mod-676 | Koopman operator / Model predictive control / ETF rebalancing | 4076 | 3784 | No |
| 10159 | Wavelet Scholarly Graph Contagion Analyzer Mod-772 | Persistence landscapes / Topological contours / Equity index | 5998 | 11403 | No |
| 10199 | Wavelet Scholarly Graph Contagion Analyzer Mod-868 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1297 | 3823 | No |
| 10236 | Wavelet Scholarly Graph Contagion Analyzer Mod-964 | Operator theory / Koopman spectral expansion / ETF allocation | 8563 | 1228 | No |
| 10311 | Wavelet Scholarly Graph Contagion Analyzer Mod-1156 | Koopman operator / Model predictive control / ETF rebalancing | 4102 | 3879 | No |
| 10350 | Wavelet Scholarly Graph Contagion Analyzer Mod-1252 | Persistence landscapes / Topological contours / Equity index | 6022 | 11417 | No |
| 10390 | Wavelet Scholarly Graph Contagion Analyzer Mod-1348 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1328 | 3918 | No |
| 10427 | Wavelet Scholarly Graph Contagion Analyzer Mod-1444 | Operator theory / Koopman spectral expansion / ETF allocation | 8601 | 1252 | No |
| 10502 | Wavelet Scholarly Graph Contagion Analyzer Mod-1636 | Koopman operator / Model predictive control / ETF rebalancing | 4128 | 3974 | No |
| 10541 | Wavelet Scholarly Graph Contagion Analyzer Mod-1732 | Persistence landscapes / Topological contours / Equity index | 6046 | 11431 | No |
| 10581 | Wavelet Scholarly Graph Contagion Analyzer Mod-1828 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1359 | 4013 | No |
| 10618 | Wavelet Scholarly Graph Contagion Analyzer Mod-1924 | Operator theory / Koopman spectral expansion / ETF allocation | 8639 | 1276 | No |
| 10693 | Wavelet Scholarly Graph Contagion Analyzer Mod-2116 | Koopman operator / Model predictive control / ETF rebalancing | 4154 | 4069 | No |
| 10732 | Wavelet Scholarly Graph Contagion Analyzer Mod-2212 | Persistence landscapes / Topological contours / Equity index | 6070 | 11445 | No |
| 10772 | Wavelet Scholarly Graph Contagion Analyzer Mod-2308 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1390 | 4108 | No |
| 10809 | Wavelet Scholarly Graph Contagion Analyzer Mod-2404 | Operator theory / Koopman spectral expansion / ETF allocation | 8677 | 1300 | No |
| 10884 | Wavelet Scholarly Graph Contagion Analyzer Mod-2596 | Koopman operator / Model predictive control / ETF rebalancing | 4180 | 4164 | No |
| 10923 | Wavelet Scholarly Graph Contagion Analyzer Mod-2692 | Persistence landscapes / Topological contours / Equity index | 6094 | 11459 | No |
| 10963 | Wavelet Scholarly Graph Contagion Analyzer Mod-2788 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1421 | 4203 | No |
| 11000 | Wavelet Scholarly Graph Contagion Analyzer Mod-2884 | Operator theory / Koopman spectral expansion / ETF allocation | 8715 | 1324 | No |
| 11075 | Wavelet Scholarly Graph Contagion Analyzer Mod-3076 | Koopman operator / Model predictive control / ETF rebalancing | 4206 | 4259 | No |
| 11114 | Wavelet Scholarly Graph Contagion Analyzer Mod-3172 | Persistence landscapes / Topological contours / Equity index | 6118 | 11473 | No |
| 11154 | Wavelet Scholarly Graph Contagion Analyzer Mod-3268 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1452 | 4298 | No |
| 11191 | Wavelet Scholarly Graph Contagion Analyzer Mod-3364 | Operator theory / Koopman spectral expansion / ETF allocation | 8753 | 1348 | No |
| 11266 | Wavelet Scholarly Graph Contagion Analyzer Mod-3556 | Koopman operator / Model predictive control / ETF rebalancing | 4232 | 4354 | No |
| 11305 | Wavelet Scholarly Graph Contagion Analyzer Mod-3652 | Persistence landscapes / Topological contours / Equity index | 6142 | 11487 | No |
| 11345 | Wavelet Scholarly Graph Contagion Analyzer Mod-3748 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1483 | 4393 | No |
| 11382 | Wavelet Scholarly Graph Contagion Analyzer Mod-3844 | Operator theory / Koopman spectral expansion / ETF allocation | 8791 | 1372 | No |
| 11455 | Wavelet Scholarly Graph Contagion Analyzer Eng-28 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1500 | 4448 | No |
| 11493 | Wavelet Scholarly Graph Contagion Analyzer Eng-124 | Operator theory / Koopman spectral expansion / ETF allocation | 8814 | 1388 | No |
| 11567 | Wavelet Scholarly Graph Contagion Analyzer Eng-316 | Koopman operator / Model predictive control / ETF rebalancing | 4275 | 4507 | No |
| 11609 | Wavelet Scholarly Graph Contagion Analyzer Eng-412 | Persistence landscapes / Topological contours / Equity index | 6179 | 11507 | No |
| 11646 | Wavelet Scholarly Graph Contagion Analyzer Eng-508 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1530 | 4541 | No |
| 11684 | Wavelet Scholarly Graph Contagion Analyzer Eng-604 | Operator theory / Koopman spectral expansion / ETF allocation | 8850 | 1414 | No |
| 11758 | Wavelet Scholarly Graph Contagion Analyzer Eng-796 | Koopman operator / Model predictive control / ETF rebalancing | 4301 | 4600 | No |
| 11800 | Wavelet Scholarly Graph Contagion Analyzer Eng-892 | Persistence landscapes / Topological contours / Equity index | 6201 | 11521 | No |
| 11837 | Wavelet Scholarly Graph Contagion Analyzer Eng-988 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1560 | 4634 | No |
| 11875 | Wavelet Scholarly Graph Contagion Analyzer Eng-1084 | Operator theory / Koopman spectral expansion / ETF allocation | 8886 | 1440 | No |
| 11949 | Wavelet Scholarly Graph Contagion Analyzer Eng-1276 | Koopman operator / Model predictive control / ETF rebalancing | 4327 | 4693 | No |
| 11991 | Wavelet Scholarly Graph Contagion Analyzer Eng-1372 | Persistence landscapes / Topological contours / Equity index | 6223 | 11535 | No |
| 12028 | Wavelet Scholarly Graph Contagion Analyzer Eng-1468 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1590 | 4727 | No |
| 12066 | Wavelet Scholarly Graph Contagion Analyzer Eng-1564 | Operator theory / Koopman spectral expansion / ETF allocation | 8922 | 1466 | No |
| 12140 | Wavelet Scholarly Graph Contagion Analyzer Eng-1756 | Koopman operator / Model predictive control / ETF rebalancing | 4353 | 4786 | No |
| 12182 | Wavelet Scholarly Graph Contagion Analyzer Eng-1852 | Persistence landscapes / Topological contours / Equity index | 6245 | 11549 | No |
| 12219 | Wavelet Scholarly Graph Contagion Analyzer Eng-1948 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1620 | 4820 | No |
| 12257 | Wavelet Scholarly Graph Contagion Analyzer Eng-2044 | Operator theory / Koopman spectral expansion / ETF allocation | 8958 | 1492 | No |
| 12331 | Wavelet Scholarly Graph Contagion Analyzer Eng-2236 | Koopman operator / Model predictive control / ETF rebalancing | 4379 | 4879 | No |
| 12373 | Wavelet Scholarly Graph Contagion Analyzer Eng-2332 | Persistence landscapes / Topological contours / Equity index | 6267 | 11563 | No |
| 12410 | Wavelet Scholarly Graph Contagion Analyzer Eng-2428 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1650 | 4913 | No |
| 12448 | Wavelet Scholarly Graph Contagion Analyzer Eng-2524 | Operator theory / Koopman spectral expansion / ETF allocation | 8994 | 1518 | No |
| 12522 | Wavelet Scholarly Graph Contagion Analyzer Eng-2716 | Koopman operator / Model predictive control / ETF rebalancing | 4405 | 4972 | No |
| 12564 | Wavelet Scholarly Graph Contagion Analyzer Eng-2812 | Persistence landscapes / Topological contours / Equity index | 6289 | 11577 | No |
| 12601 | Wavelet Scholarly Graph Contagion Analyzer Eng-2908 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1680 | 5006 | No |
| 12639 | Wavelet Scholarly Graph Contagion Analyzer Eng-3004 | Operator theory / Koopman spectral expansion / ETF allocation | 9030 | 1544 | No |
| 12713 | Wavelet Scholarly Graph Contagion Analyzer Eng-3196 | Koopman operator / Model predictive control / ETF rebalancing | 4431 | 5065 | No |
| 12755 | Wavelet Scholarly Graph Contagion Analyzer Eng-3292 | Persistence landscapes / Topological contours / Equity index | 6311 | 11591 | No |
| 12792 | Wavelet Scholarly Graph Contagion Analyzer Eng-3388 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1710 | 5099 | No |
| 12830 | Wavelet Scholarly Graph Contagion Analyzer Eng-3484 | Operator theory / Koopman spectral expansion / ETF allocation | 9066 | 1570 | No |
| 12904 | Wavelet Scholarly Graph Contagion Analyzer Eng-3676 | Koopman operator / Model predictive control / ETF rebalancing | 4457 | 5158 | No |
| 12946 | Wavelet Scholarly Graph Contagion Analyzer Eng-3772 | Persistence landscapes / Topological contours / Equity index | 6333 | 11605 | No |
| 12983 | Wavelet Scholarly Graph Contagion Analyzer Eng-3868 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1740 | 5192 | No |
| 13021 | Wavelet Scholarly Graph Contagion Analyzer Eng-3964 | Operator theory / Koopman spectral expansion / ETF allocation | 9102 | 1596 | No |
| 13095 | Wavelet Scholarly Graph Contagion Analyzer Eng-4156 | Koopman operator / Model predictive control / ETF rebalancing | 4483 | 5251 | No |
| 13137 | Wavelet Scholarly Graph Contagion Analyzer Eng-4252 | Persistence landscapes / Topological contours / Equity index | 6355 | 11619 | No |
| 13174 | Wavelet Scholarly Graph Contagion Analyzer Eng-4348 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1770 | 5285 | No |
| 13212 | Wavelet Scholarly Graph Contagion Analyzer Eng-4444 | Operator theory / Koopman spectral expansion / ETF allocation | 9138 | 1622 | No |
| 13286 | Wavelet Scholarly Graph Contagion Analyzer Eng-4636 | Koopman operator / Model predictive control / ETF rebalancing | 4509 | 5344 | No |
| 13328 | Wavelet Scholarly Graph Contagion Analyzer Eng-4732 | Persistence landscapes / Topological contours / Equity index | 6377 | 11633 | No |
| 13365 | Wavelet Scholarly Graph Contagion Analyzer Eng-4828 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1800 | 5378 | No |
| 13403 | Wavelet Scholarly Graph Contagion Analyzer Eng-4924 | Operator theory / Koopman spectral expansion / ETF allocation | 9174 | 1648 | No |
| 13477 | Wavelet Scholarly Graph Contagion Analyzer Eng-5116 | Koopman operator / Model predictive control / ETF rebalancing | 4535 | 5437 | No |
| 13519 | Wavelet Scholarly Graph Contagion Analyzer Eng-5212 | Persistence landscapes / Topological contours / Equity index | 6399 | 11647 | No |
| 13556 | Wavelet Scholarly Graph Contagion Analyzer Eng-5308 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1830 | 5471 | No |
| 13594 | Wavelet Scholarly Graph Contagion Analyzer Eng-5404 | Operator theory / Koopman spectral expansion / ETF allocation | 9210 | 1674 | No |
| 13668 | Wavelet Scholarly Graph Contagion Analyzer Eng-5596 | Koopman operator / Model predictive control / ETF rebalancing | 4561 | 5530 | No |
| 13710 | Wavelet Scholarly Graph Contagion Analyzer Eng-5692 | Persistence landscapes / Topological contours / Equity index | 6421 | 11661 | No |
| 13747 | Wavelet Scholarly Graph Contagion Analyzer Eng-5788 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1860 | 5564 | No |
| 13785 | Wavelet Scholarly Graph Contagion Analyzer Eng-5884 | Operator theory / Koopman spectral expansion / ETF allocation | 9246 | 1700 | No |
