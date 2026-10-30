# Recursive approach to cross-asset/sector contagion analysis

**Concept page** · shared by **136** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,755) ·
researched 2026-10-30

| | |
|---|---|
| Task | Cross-asset / sector contagion analysis |
| Method | Recursive (online) estimation |
| Fit with this project | ⏳ reference only · background, nothing to build now |
| Useful for volatility-ai | **Reference only.** Recursive estimation is an established way to measure spillovers, but timing exposure with it is untested and this book trades one symbol; background. |
| Implemented in volatility-ai | Nothing; the regime inputs are volatility-based (V17, N5). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK258, RK262, RK264, RK269 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Recursive Scholarly Graph
Contagion Analyzer Ref-260") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Represent assets or sectors as a network, estimate how shocks propagate,
and use that to adjust exposure or hedges. The recursive version updates
its estimates one observation at a time (recursive least squares,
Kalman-style updates). I found no study of this method on this task.

## The CSV's description

Proposed recursive approach to cross-asset/sector contagion analysis:
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
* A recursive estimate needs a forgetting rate: too slow lags, too fast
  is noise.

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
| 1755 | Recursive Scholarly Graph Contagion Analyzer Ref-260 | Fractional order / Multi-scale ETF momentum | 3875 | 2161 | No |
| 1810 | Recursive Scholarly Graph Contagion Analyzer Ref-740 | Fractional order / Multi-scale ETF momentum | 3902 | 2186 | No |
| 1846 | Recursive Scholarly Graph Contagion Analyzer Sys-100 | Fractional order / Multi-scale ETF momentum | 2204 | 489 | No |
| 1895 | Recursive Scholarly Graph Contagion Analyzer Sys-580 | Fractional order / Multi-scale ETF momentum | 2251 | 508 | No |
| 1944 | Recursive Scholarly Graph Contagion Analyzer Sys-1060 | Fractional order / Multi-scale ETF momentum | 2298 | 527 | No |
| 1993 | Recursive Scholarly Graph Contagion Analyzer Sys-1540 | Fractional order / Multi-scale ETF momentum | 2345 | 546 | No |
| 2063 | Recursive Scholarly Graph Contagion Analyzer Mod-220 | Fractional order / Multi-scale ETF momentum | 2406 | 572 | No |
| 2116 | Recursive Scholarly Graph Contagion Analyzer Mod-700 | Fractional order / Multi-scale ETF momentum | 2445 | 591 | No |
| 2169 | Recursive Scholarly Graph Contagion Analyzer Mod-1180 | Fractional order / Multi-scale ETF momentum | 2484 | 610 | No |
| 2222 | Recursive Scholarly Graph Contagion Analyzer Mod-1660 | Fractional order / Multi-scale ETF momentum | 2523 | 629 | No |
| 2275 | Recursive Scholarly Graph Contagion Analyzer Mod-2140 | Fractional order / Multi-scale ETF momentum | 2562 | 648 | No |
| 2328 | Recursive Scholarly Graph Contagion Analyzer Mod-2620 | Fractional order / Multi-scale ETF momentum | 2601 | 667 | No |
| 2381 | Recursive Scholarly Graph Contagion Analyzer Mod-3100 | Fractional order / Multi-scale ETF momentum | 2640 | 686 | No |
| 2434 | Recursive Scholarly Graph Contagion Analyzer Mod-3580 | Fractional order / Multi-scale ETF momentum | 2679 | 705 | No |
| 2490 | Recursive Scholarly Graph Contagion Analyzer Eng-100 | Fractional order / Multi-scale ETF momentum | 2722 | 725 | No |
| 2545 | Recursive Scholarly Graph Contagion Analyzer Eng-580 | Fractional order / Multi-scale ETF momentum | 2760 | 744 | No |
| 2600 | Recursive Scholarly Graph Contagion Analyzer Eng-1060 | Fractional order / Multi-scale ETF momentum | 2798 | 763 | No |
| 2655 | Recursive Scholarly Graph Contagion Analyzer Eng-1540 | Fractional order / Multi-scale ETF momentum | 2836 | 782 | No |
| 2710 | Recursive Scholarly Graph Contagion Analyzer Eng-2020 | Fractional order / Multi-scale ETF momentum | 2874 | 801 | No |
| 2765 | Recursive Scholarly Graph Contagion Analyzer Eng-2500 | Fractional order / Multi-scale ETF momentum | 2912 | 820 | No |
| 2820 | Recursive Scholarly Graph Contagion Analyzer Eng-2980 | Fractional order / Multi-scale ETF momentum | 2950 | 839 | No |
| 2875 | Recursive Scholarly Graph Contagion Analyzer Eng-3460 | Fractional order / Multi-scale ETF momentum | 2988 | 858 | No |
| 2930 | Recursive Scholarly Graph Contagion Analyzer Eng-3940 | Fractional order / Multi-scale ETF momentum | 3026 | 877 | No |
| 2985 | Recursive Scholarly Graph Contagion Analyzer Eng-4420 | Fractional order / Multi-scale ETF momentum | 3064 | 896 | No |
| 3040 | Recursive Scholarly Graph Contagion Analyzer Eng-4900 | Fractional order / Multi-scale ETF momentum | 3102 | 915 | No |
| 3095 | Recursive Scholarly Graph Contagion Analyzer Eng-5380 | Fractional order / Multi-scale ETF momentum | 3140 | 934 | No |
| 3150 | Recursive Scholarly Graph Contagion Analyzer Eng-5860 | Fractional order / Multi-scale ETF momentum | 3178 | 953 | No |
| 8703 | Recursive Scholarly Graph Contagion Analyzer Ref-68 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10740 | 11876 | No |
| 8740 | Recursive Scholarly Graph Contagion Analyzer Ref-164 | Operator theory / Koopman spectral expansion / ETF allocation | 2137 | 3051 | No |
| 8816 | Recursive Scholarly Graph Contagion Analyzer Ref-356 | Koopman operator / Model predictive control / ETF rebalancing | 12066 | 13720 | No |
| 8852 | Recursive Scholarly Graph Contagion Analyzer Ref-452 | Persistence landscapes / Topological contours / Equity index | 2156 | 3122 | No |
| 8894 | Recursive Scholarly Graph Contagion Analyzer Ref-548 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10742 | 11899 | No |
| 8931 | Recursive Scholarly Graph Contagion Analyzer Ref-644 | Operator theory / Koopman spectral expansion / ETF allocation | 2169 | 3168 | No |
| 9007 | Recursive Scholarly Graph Contagion Analyzer Ref-836 | Koopman operator / Model predictive control / ETF rebalancing | 12069 | 13731 | No |
| 9043 | Recursive Scholarly Graph Contagion Analyzer Ref-932 | Persistence landscapes / Topological contours / Equity index | 2188 | 3239 | No |
| 9075 | Recursive Scholarly Graph Contagion Analyzer Sys-4 | Operator theory / Koopman spectral expansion / ETF allocation | 3919 | 1080 | No |
| 9149 | Recursive Scholarly Graph Contagion Analyzer Sys-196 | Koopman operator / Model predictive control / ETF rebalancing | 3929 | 3295 | No |
| 9188 | Recursive Scholarly Graph Contagion Analyzer Sys-292 | Persistence landscapes / Topological contours / Equity index | 5888 | 11345 | No |
| 9227 | Recursive Scholarly Graph Contagion Analyzer Sys-388 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1142 | 3334 | No |
| 9262 | Recursive Scholarly Graph Contagion Analyzer Sys-484 | Operator theory / Koopman spectral expansion / ETF allocation | 3948 | 1104 | No |
| 9336 | Recursive Scholarly Graph Contagion Analyzer Sys-676 | Koopman operator / Model predictive control / ETF rebalancing | 3958 | 3390 | No |
| 9375 | Recursive Scholarly Graph Contagion Analyzer Sys-772 | Persistence landscapes / Topological contours / Equity index | 5908 | 11355 | No |
| 9414 | Recursive Scholarly Graph Contagion Analyzer Sys-868 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1172 | 3429 | No |
| 9449 | Recursive Scholarly Graph Contagion Analyzer Sys-964 | Operator theory / Koopman spectral expansion / ETF allocation | 3977 | 1128 | No |
| 9523 | Recursive Scholarly Graph Contagion Analyzer Sys-1156 | Koopman operator / Model predictive control / ETF rebalancing | 3987 | 3485 | No |
| 9562 | Recursive Scholarly Graph Contagion Analyzer Sys-1252 | Persistence landscapes / Topological contours / Equity index | 5928 | 11365 | No |
| 9601 | Recursive Scholarly Graph Contagion Analyzer Sys-1348 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1202 | 3524 | No |
| 9636 | Recursive Scholarly Graph Contagion Analyzer Sys-1444 | Operator theory / Koopman spectral expansion / ETF allocation | 4006 | 1152 | No |
| 9710 | Recursive Scholarly Graph Contagion Analyzer Sys-1636 | Koopman operator / Model predictive control / ETF rebalancing | 4016 | 3580 | No |
| 9749 | Recursive Scholarly Graph Contagion Analyzer Sys-1732 | Persistence landscapes / Topological contours / Equity index | 5948 | 11375 | No |
| 9788 | Recursive Scholarly Graph Contagion Analyzer Sys-1828 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1232 | 3619 | No |
| 9823 | Recursive Scholarly Graph Contagion Analyzer Sys-1924 | Operator theory / Koopman spectral expansion / ETF allocation | 4035 | 1176 | No |
| 9863 | Recursive Scholarly Graph Contagion Analyzer Mod-28 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1244 | 3656 | No |
| 9901 | Recursive Scholarly Graph Contagion Analyzer Mod-124 | Operator theory / Koopman spectral expansion / ETF allocation | 4045 | 1186 | No |
| 9978 | Recursive Scholarly Graph Contagion Analyzer Mod-316 | Koopman operator / Model predictive control / ETF rebalancing | 4057 | 3714 | No |
| 10017 | Recursive Scholarly Graph Contagion Analyzer Mod-412 | Persistence landscapes / Topological contours / Equity index | 5980 | 11393 | No |
| 10054 | Recursive Scholarly Graph Contagion Analyzer Mod-508 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1275 | 3751 | No |
| 10092 | Recursive Scholarly Graph Contagion Analyzer Mod-604 | Operator theory / Koopman spectral expansion / ETF allocation | 4071 | 1210 | No |
| 10169 | Recursive Scholarly Graph Contagion Analyzer Mod-796 | Koopman operator / Model predictive control / ETF rebalancing | 4083 | 3809 | No |
| 10208 | Recursive Scholarly Graph Contagion Analyzer Mod-892 | Persistence landscapes / Topological contours / Equity index | 6004 | 11407 | No |
| 10245 | Recursive Scholarly Graph Contagion Analyzer Mod-988 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1306 | 3846 | No |
| 10283 | Recursive Scholarly Graph Contagion Analyzer Mod-1084 | Operator theory / Koopman spectral expansion / ETF allocation | 4097 | 1234 | No |
| 10360 | Recursive Scholarly Graph Contagion Analyzer Mod-1276 | Koopman operator / Model predictive control / ETF rebalancing | 4109 | 3904 | No |
| 10399 | Recursive Scholarly Graph Contagion Analyzer Mod-1372 | Persistence landscapes / Topological contours / Equity index | 6028 | 11421 | No |
| 10436 | Recursive Scholarly Graph Contagion Analyzer Mod-1468 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1337 | 3941 | No |
| 10474 | Recursive Scholarly Graph Contagion Analyzer Mod-1564 | Operator theory / Koopman spectral expansion / ETF allocation | 4123 | 1258 | No |
| 10551 | Recursive Scholarly Graph Contagion Analyzer Mod-1756 | Koopman operator / Model predictive control / ETF rebalancing | 4135 | 3999 | No |
| 10590 | Recursive Scholarly Graph Contagion Analyzer Mod-1852 | Persistence landscapes / Topological contours / Equity index | 6052 | 11435 | No |
| 10627 | Recursive Scholarly Graph Contagion Analyzer Mod-1948 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1368 | 4036 | No |
| 10665 | Recursive Scholarly Graph Contagion Analyzer Mod-2044 | Operator theory / Koopman spectral expansion / ETF allocation | 4149 | 1282 | No |
| 10742 | Recursive Scholarly Graph Contagion Analyzer Mod-2236 | Koopman operator / Model predictive control / ETF rebalancing | 4161 | 4094 | No |
| 10781 | Recursive Scholarly Graph Contagion Analyzer Mod-2332 | Persistence landscapes / Topological contours / Equity index | 6076 | 11449 | No |
| 10818 | Recursive Scholarly Graph Contagion Analyzer Mod-2428 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1399 | 4131 | No |
| 10856 | Recursive Scholarly Graph Contagion Analyzer Mod-2524 | Operator theory / Koopman spectral expansion / ETF allocation | 4175 | 1306 | No |
| 10933 | Recursive Scholarly Graph Contagion Analyzer Mod-2716 | Koopman operator / Model predictive control / ETF rebalancing | 4187 | 4189 | No |
| 10972 | Recursive Scholarly Graph Contagion Analyzer Mod-2812 | Persistence landscapes / Topological contours / Equity index | 6100 | 11463 | No |
| 11009 | Recursive Scholarly Graph Contagion Analyzer Mod-2908 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1430 | 4226 | No |
| 11047 | Recursive Scholarly Graph Contagion Analyzer Mod-3004 | Operator theory / Koopman spectral expansion / ETF allocation | 4201 | 1330 | No |
| 11124 | Recursive Scholarly Graph Contagion Analyzer Mod-3196 | Koopman operator / Model predictive control / ETF rebalancing | 4213 | 4284 | No |
| 11163 | Recursive Scholarly Graph Contagion Analyzer Mod-3292 | Persistence landscapes / Topological contours / Equity index | 6124 | 11477 | No |
| 11200 | Recursive Scholarly Graph Contagion Analyzer Mod-3388 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1461 | 4321 | No |
| 11238 | Recursive Scholarly Graph Contagion Analyzer Mod-3484 | Operator theory / Koopman spectral expansion / ETF allocation | 4227 | 1354 | No |
| 11315 | Recursive Scholarly Graph Contagion Analyzer Mod-3676 | Koopman operator / Model predictive control / ETF rebalancing | 4239 | 4379 | No |
| 11354 | Recursive Scholarly Graph Contagion Analyzer Mod-3772 | Persistence landscapes / Topological contours / Equity index | 6148 | 11491 | No |
| 11391 | Recursive Scholarly Graph Contagion Analyzer Mod-3868 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1492 | 4416 | No |
| 11429 | Recursive Scholarly Graph Contagion Analyzer Mod-3964 | Operator theory / Koopman spectral expansion / ETF allocation | 4253 | 1378 | No |
| 11443 | Recursive Scholarly Graph Contagion Analyzer Eng-4 | Operator theory / Koopman spectral expansion / ETF allocation | 4257 | 1382 | No |
| 11522 | Recursive Scholarly Graph Contagion Analyzer Eng-196 | Koopman operator / Model predictive control / ETF rebalancing | 4268 | 4483 | No |
| 11560 | Recursive Scholarly Graph Contagion Analyzer Eng-292 | Persistence landscapes / Topological contours / Equity index | 6173 | 11503 | No |
| 11597 | Recursive Scholarly Graph Contagion Analyzer Eng-388 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1523 | 4519 | No |
| 11634 | Recursive Scholarly Graph Contagion Analyzer Eng-484 | Operator theory / Koopman spectral expansion / ETF allocation | 4283 | 1408 | No |
| 11713 | Recursive Scholarly Graph Contagion Analyzer Eng-676 | Koopman operator / Model predictive control / ETF rebalancing | 4294 | 4576 | No |
| 11751 | Recursive Scholarly Graph Contagion Analyzer Eng-772 | Persistence landscapes / Topological contours / Equity index | 6195 | 11517 | No |
| 11788 | Recursive Scholarly Graph Contagion Analyzer Eng-868 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1553 | 4612 | No |
| 11825 | Recursive Scholarly Graph Contagion Analyzer Eng-964 | Operator theory / Koopman spectral expansion / ETF allocation | 4309 | 1434 | No |
| 11904 | Recursive Scholarly Graph Contagion Analyzer Eng-1156 | Koopman operator / Model predictive control / ETF rebalancing | 4320 | 4669 | No |
| 11942 | Recursive Scholarly Graph Contagion Analyzer Eng-1252 | Persistence landscapes / Topological contours / Equity index | 6217 | 11531 | No |
| 11979 | Recursive Scholarly Graph Contagion Analyzer Eng-1348 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1583 | 4705 | No |
| 12016 | Recursive Scholarly Graph Contagion Analyzer Eng-1444 | Operator theory / Koopman spectral expansion / ETF allocation | 4335 | 1460 | No |
| 12095 | Recursive Scholarly Graph Contagion Analyzer Eng-1636 | Koopman operator / Model predictive control / ETF rebalancing | 4346 | 4762 | No |
| 12133 | Recursive Scholarly Graph Contagion Analyzer Eng-1732 | Persistence landscapes / Topological contours / Equity index | 6239 | 11545 | No |
| 12170 | Recursive Scholarly Graph Contagion Analyzer Eng-1828 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1613 | 4798 | No |
| 12207 | Recursive Scholarly Graph Contagion Analyzer Eng-1924 | Operator theory / Koopman spectral expansion / ETF allocation | 4361 | 1486 | No |
| 12286 | Recursive Scholarly Graph Contagion Analyzer Eng-2116 | Koopman operator / Model predictive control / ETF rebalancing | 4372 | 4855 | No |
| 12324 | Recursive Scholarly Graph Contagion Analyzer Eng-2212 | Persistence landscapes / Topological contours / Equity index | 6261 | 11559 | No |
| 12361 | Recursive Scholarly Graph Contagion Analyzer Eng-2308 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1643 | 4891 | No |
| 12398 | Recursive Scholarly Graph Contagion Analyzer Eng-2404 | Operator theory / Koopman spectral expansion / ETF allocation | 4387 | 1512 | No |
| 12477 | Recursive Scholarly Graph Contagion Analyzer Eng-2596 | Koopman operator / Model predictive control / ETF rebalancing | 4398 | 4948 | No |
| 12515 | Recursive Scholarly Graph Contagion Analyzer Eng-2692 | Persistence landscapes / Topological contours / Equity index | 6283 | 11573 | No |
| 12552 | Recursive Scholarly Graph Contagion Analyzer Eng-2788 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1673 | 4984 | No |
| 12589 | Recursive Scholarly Graph Contagion Analyzer Eng-2884 | Operator theory / Koopman spectral expansion / ETF allocation | 4413 | 1538 | No |
| 12668 | Recursive Scholarly Graph Contagion Analyzer Eng-3076 | Koopman operator / Model predictive control / ETF rebalancing | 4424 | 5041 | No |
| 12706 | Recursive Scholarly Graph Contagion Analyzer Eng-3172 | Persistence landscapes / Topological contours / Equity index | 6305 | 11587 | No |
| 12743 | Recursive Scholarly Graph Contagion Analyzer Eng-3268 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1703 | 5077 | No |
| 12780 | Recursive Scholarly Graph Contagion Analyzer Eng-3364 | Operator theory / Koopman spectral expansion / ETF allocation | 4439 | 1564 | No |
| 12859 | Recursive Scholarly Graph Contagion Analyzer Eng-3556 | Koopman operator / Model predictive control / ETF rebalancing | 4450 | 5134 | No |
| 12897 | Recursive Scholarly Graph Contagion Analyzer Eng-3652 | Persistence landscapes / Topological contours / Equity index | 6327 | 11601 | No |
| 12934 | Recursive Scholarly Graph Contagion Analyzer Eng-3748 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1733 | 5170 | No |
| 12971 | Recursive Scholarly Graph Contagion Analyzer Eng-3844 | Operator theory / Koopman spectral expansion / ETF allocation | 4465 | 1590 | No |
| 13050 | Recursive Scholarly Graph Contagion Analyzer Eng-4036 | Koopman operator / Model predictive control / ETF rebalancing | 4476 | 5227 | No |
| 13088 | Recursive Scholarly Graph Contagion Analyzer Eng-4132 | Persistence landscapes / Topological contours / Equity index | 6349 | 11615 | No |
| 13125 | Recursive Scholarly Graph Contagion Analyzer Eng-4228 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1763 | 5263 | No |
| 13162 | Recursive Scholarly Graph Contagion Analyzer Eng-4324 | Operator theory / Koopman spectral expansion / ETF allocation | 4491 | 1616 | No |
| 13241 | Recursive Scholarly Graph Contagion Analyzer Eng-4516 | Koopman operator / Model predictive control / ETF rebalancing | 4502 | 5320 | No |
| 13279 | Recursive Scholarly Graph Contagion Analyzer Eng-4612 | Persistence landscapes / Topological contours / Equity index | 6371 | 11629 | No |
| 13316 | Recursive Scholarly Graph Contagion Analyzer Eng-4708 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1793 | 5356 | No |
| 13353 | Recursive Scholarly Graph Contagion Analyzer Eng-4804 | Operator theory / Koopman spectral expansion / ETF allocation | 4517 | 1642 | No |
| 13432 | Recursive Scholarly Graph Contagion Analyzer Eng-4996 | Koopman operator / Model predictive control / ETF rebalancing | 4528 | 5413 | No |
| 13470 | Recursive Scholarly Graph Contagion Analyzer Eng-5092 | Persistence landscapes / Topological contours / Equity index | 6393 | 11643 | No |
| 13507 | Recursive Scholarly Graph Contagion Analyzer Eng-5188 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1823 | 5449 | No |
| 13544 | Recursive Scholarly Graph Contagion Analyzer Eng-5284 | Operator theory / Koopman spectral expansion / ETF allocation | 4543 | 1668 | No |
| 13623 | Recursive Scholarly Graph Contagion Analyzer Eng-5476 | Koopman operator / Model predictive control / ETF rebalancing | 4554 | 5506 | No |
| 13661 | Recursive Scholarly Graph Contagion Analyzer Eng-5572 | Persistence landscapes / Topological contours / Equity index | 6415 | 11657 | No |
| 13698 | Recursive Scholarly Graph Contagion Analyzer Eng-5668 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1853 | 5542 | No |
| 13735 | Recursive Scholarly Graph Contagion Analyzer Eng-5764 | Operator theory / Koopman spectral expansion / ETF allocation | 4569 | 1694 | No |
| 13814 | Recursive Scholarly Graph Contagion Analyzer Eng-5956 | Koopman operator / Model predictive control / ETF rebalancing | 4580 | 5599 | No |
