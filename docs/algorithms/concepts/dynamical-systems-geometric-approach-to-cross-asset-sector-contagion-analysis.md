# Dynamical-systems/geometric approach to cross-asset/sector contagion analysis

**Concept page** · shared by **135** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,742) ·
researched 2026-10-30

| | |
|---|---|
| Task | Cross-asset / sector contagion analysis |
| Method | Dynamical-systems / geometric (e.g. Hamiltonian) models |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of imposed dynamical-systems models measuring contagion usefully, and the book has nothing for a shock to propagate between. |
| Implemented in volatility-ai | Nothing; the regime inputs are volatility-based (V17, N5). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK258, RK262, RK264, RK269 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Symplectic Scholarly Graph
Contagion Analyzer Ref-140") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Represent assets or sectors as a network, estimate how shocks propagate,
and use that to adjust exposure or hedges. The dynamical-systems version
models the market as a Hamiltonian or delay-differential system and acts
on its fitted state. I found no study of this method on this task.

## The CSV's description

Proposed dynamical-systems/geometric approach to cross-asset/sector
contagion analysis: Represent assets or sectors as a network and
estimate how shocks or changing correlations may propagate, then use
that information to adjust exposure or hedges. This is a concept-level
interpretation of the title, not a complete trading specification: the
exact model inputs/target, calibration, entry/exit or rebalance rules,
and position sizing are not fully defined here.

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
* The physics is imposed, not estimated from evidence; no trading study
  found.

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
| 1742 | Symplectic Scholarly Graph Contagion Analyzer Ref-140 | Fractional order / Multi-scale ETF momentum | 3868 | 2155 | No |
| 1797 | Symplectic Scholarly Graph Contagion Analyzer Ref-620 | Fractional order / Multi-scale ETF momentum | 3895 | 2180 | No |
| 1883 | Symplectic Scholarly Graph Contagion Analyzer Sys-460 | Fractional order / Multi-scale ETF momentum | 2238 | 503 | No |
| 1932 | Symplectic Scholarly Graph Contagion Analyzer Sys-940 | Fractional order / Multi-scale ETF momentum | 2285 | 522 | No |
| 1981 | Symplectic Scholarly Graph Contagion Analyzer Sys-1420 | Fractional order / Multi-scale ETF momentum | 2332 | 541 | No |
| 2030 | Symplectic Scholarly Graph Contagion Analyzer Sys-1900 | Fractional order / Multi-scale ETF momentum | 2379 | 560 | No |
| 2076 | Symplectic Scholarly Graph Contagion Analyzer Mod-340 | Fractional order / Multi-scale ETF momentum | 2417 | 577 | No |
| 2129 | Symplectic Scholarly Graph Contagion Analyzer Mod-820 | Fractional order / Multi-scale ETF momentum | 2456 | 596 | No |
| 2182 | Symplectic Scholarly Graph Contagion Analyzer Mod-1300 | Fractional order / Multi-scale ETF momentum | 2495 | 615 | No |
| 2235 | Symplectic Scholarly Graph Contagion Analyzer Mod-1780 | Fractional order / Multi-scale ETF momentum | 2534 | 634 | No |
| 2288 | Symplectic Scholarly Graph Contagion Analyzer Mod-2260 | Fractional order / Multi-scale ETF momentum | 2573 | 653 | No |
| 2341 | Symplectic Scholarly Graph Contagion Analyzer Mod-2740 | Fractional order / Multi-scale ETF momentum | 2612 | 672 | No |
| 2394 | Symplectic Scholarly Graph Contagion Analyzer Mod-3220 | Fractional order / Multi-scale ETF momentum | 2651 | 691 | No |
| 2447 | Symplectic Scholarly Graph Contagion Analyzer Mod-3700 | Fractional order / Multi-scale ETF momentum | 2690 | 710 | No |
| 2530 | Symplectic Scholarly Graph Contagion Analyzer Eng-460 | Fractional order / Multi-scale ETF momentum | 2750 | 739 | No |
| 2585 | Symplectic Scholarly Graph Contagion Analyzer Eng-940 | Fractional order / Multi-scale ETF momentum | 2788 | 758 | No |
| 2640 | Symplectic Scholarly Graph Contagion Analyzer Eng-1420 | Fractional order / Multi-scale ETF momentum | 2826 | 777 | No |
| 2695 | Symplectic Scholarly Graph Contagion Analyzer Eng-1900 | Fractional order / Multi-scale ETF momentum | 2864 | 796 | No |
| 2750 | Symplectic Scholarly Graph Contagion Analyzer Eng-2380 | Fractional order / Multi-scale ETF momentum | 2902 | 815 | No |
| 2805 | Symplectic Scholarly Graph Contagion Analyzer Eng-2860 | Fractional order / Multi-scale ETF momentum | 2940 | 834 | No |
| 2860 | Symplectic Scholarly Graph Contagion Analyzer Eng-3340 | Fractional order / Multi-scale ETF momentum | 2978 | 853 | No |
| 2915 | Symplectic Scholarly Graph Contagion Analyzer Eng-3820 | Fractional order / Multi-scale ETF momentum | 3016 | 872 | No |
| 2970 | Symplectic Scholarly Graph Contagion Analyzer Eng-4300 | Fractional order / Multi-scale ETF momentum | 3054 | 891 | No |
| 3025 | Symplectic Scholarly Graph Contagion Analyzer Eng-4780 | Fractional order / Multi-scale ETF momentum | 3092 | 910 | No |
| 3080 | Symplectic Scholarly Graph Contagion Analyzer Eng-5260 | Fractional order / Multi-scale ETF momentum | 3130 | 929 | No |
| 3135 | Symplectic Scholarly Graph Contagion Analyzer Eng-5740 | Fractional order / Multi-scale ETF momentum | 3168 | 948 | No |
| 8694 | Symplectic Scholarly Graph Contagion Analyzer Ref-44 | Operator theory / Koopman spectral expansion / ETF allocation | 6494 | 3022 | No |
| 8769 | Symplectic Scholarly Graph Contagion Analyzer Ref-236 | Koopman operator / Model predictive control / ETF rebalancing | 13177 | 13717 | No |
| 8805 | Symplectic Scholarly Graph Contagion Analyzer Ref-332 | Persistence landscapes / Topological contours / Equity index | 2148 | 3092 | No |
| 8844 | Symplectic Scholarly Graph Contagion Analyzer Ref-428 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12530 | 11893 | No |
| 8885 | Symplectic Scholarly Graph Contagion Analyzer Ref-524 | Operator theory / Koopman spectral expansion / ETF allocation | 6537 | 3139 | No |
| 8960 | Symplectic Scholarly Graph Contagion Analyzer Ref-716 | Koopman operator / Model predictive control / ETF rebalancing | 13184 | 13728 | No |
| 8996 | Symplectic Scholarly Graph Contagion Analyzer Ref-812 | Persistence landscapes / Topological contours / Equity index | 2180 | 3209 | No |
| 9035 | Symplectic Scholarly Graph Contagion Analyzer Ref-908 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12541 | 11916 | No |
| 9102 | Symplectic Scholarly Graph Contagion Analyzer Sys-76 | Koopman operator / Model predictive control / ETF rebalancing | 3923 | 3270 | No |
| 9141 | Symplectic Scholarly Graph Contagion Analyzer Sys-172 | Persistence landscapes / Topological contours / Equity index | 5884 | 11342 | No |
| 9180 | Symplectic Scholarly Graph Contagion Analyzer Sys-268 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1135 | 3309 | No |
| 9216 | Symplectic Scholarly Graph Contagion Analyzer Sys-364 | Operator theory / Koopman spectral expansion / ETF allocation | 8350 | 1098 | No |
| 9289 | Symplectic Scholarly Graph Contagion Analyzer Sys-556 | Koopman operator / Model predictive control / ETF rebalancing | 3952 | 3365 | No |
| 9328 | Symplectic Scholarly Graph Contagion Analyzer Sys-652 | Persistence landscapes / Topological contours / Equity index | 5904 | 11352 | No |
| 9367 | Symplectic Scholarly Graph Contagion Analyzer Sys-748 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1165 | 3404 | No |
| 9403 | Symplectic Scholarly Graph Contagion Analyzer Sys-844 | Operator theory / Koopman spectral expansion / ETF allocation | 8390 | 1122 | No |
| 9476 | Symplectic Scholarly Graph Contagion Analyzer Sys-1036 | Koopman operator / Model predictive control / ETF rebalancing | 3981 | 3460 | No |
| 9515 | Symplectic Scholarly Graph Contagion Analyzer Sys-1132 | Persistence landscapes / Topological contours / Equity index | 5924 | 11362 | No |
| 9554 | Symplectic Scholarly Graph Contagion Analyzer Sys-1228 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1195 | 3499 | No |
| 9590 | Symplectic Scholarly Graph Contagion Analyzer Sys-1324 | Operator theory / Koopman spectral expansion / ETF allocation | 8430 | 1146 | No |
| 9663 | Symplectic Scholarly Graph Contagion Analyzer Sys-1516 | Koopman operator / Model predictive control / ETF rebalancing | 4010 | 3555 | No |
| 9702 | Symplectic Scholarly Graph Contagion Analyzer Sys-1612 | Persistence landscapes / Topological contours / Equity index | 5944 | 11372 | No |
| 9741 | Symplectic Scholarly Graph Contagion Analyzer Sys-1708 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1225 | 3594 | No |
| 9777 | Symplectic Scholarly Graph Contagion Analyzer Sys-1804 | Operator theory / Koopman spectral expansion / ETF allocation | 8470 | 1170 | No |
| 9850 | Symplectic Scholarly Graph Contagion Analyzer Sys-1996 | Koopman operator / Model predictive control / ETF rebalancing | 4039 | 3650 | No |
| 9872 | Symplectic Scholarly Graph Contagion Analyzer Mod-52 | Persistence landscapes / Topological contours / Equity index | 5962 | 11382 | No |
| 9909 | Symplectic Scholarly Graph Contagion Analyzer Mod-148 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1251 | 3677 | No |
| 9951 | Symplectic Scholarly Graph Contagion Analyzer Mod-244 | Operator theory / Koopman spectral expansion / ETF allocation | 8506 | 1191 | No |
| 10027 | Symplectic Scholarly Graph Contagion Analyzer Mod-436 | Koopman operator / Model predictive control / ETF rebalancing | 4063 | 3739 | No |
| 10063 | Symplectic Scholarly Graph Contagion Analyzer Mod-532 | Persistence landscapes / Topological contours / Equity index | 5986 | 11396 | No |
| 10100 | Symplectic Scholarly Graph Contagion Analyzer Mod-628 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1282 | 3772 | No |
| 10142 | Symplectic Scholarly Graph Contagion Analyzer Mod-724 | Operator theory / Koopman spectral expansion / ETF allocation | 8544 | 1215 | No |
| 10218 | Symplectic Scholarly Graph Contagion Analyzer Mod-916 | Koopman operator / Model predictive control / ETF rebalancing | 4089 | 3834 | No |
| 10254 | Symplectic Scholarly Graph Contagion Analyzer Mod-1012 | Persistence landscapes / Topological contours / Equity index | 6010 | 11410 | No |
| 10291 | Symplectic Scholarly Graph Contagion Analyzer Mod-1108 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1313 | 3867 | No |
| 10333 | Symplectic Scholarly Graph Contagion Analyzer Mod-1204 | Operator theory / Koopman spectral expansion / ETF allocation | 8582 | 1239 | No |
| 10409 | Symplectic Scholarly Graph Contagion Analyzer Mod-1396 | Koopman operator / Model predictive control / ETF rebalancing | 4115 | 3929 | No |
| 10445 | Symplectic Scholarly Graph Contagion Analyzer Mod-1492 | Persistence landscapes / Topological contours / Equity index | 6034 | 11424 | No |
| 10482 | Symplectic Scholarly Graph Contagion Analyzer Mod-1588 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1344 | 3962 | No |
| 10524 | Symplectic Scholarly Graph Contagion Analyzer Mod-1684 | Operator theory / Koopman spectral expansion / ETF allocation | 8620 | 1263 | No |
| 10600 | Symplectic Scholarly Graph Contagion Analyzer Mod-1876 | Koopman operator / Model predictive control / ETF rebalancing | 4141 | 4024 | No |
| 10636 | Symplectic Scholarly Graph Contagion Analyzer Mod-1972 | Persistence landscapes / Topological contours / Equity index | 6058 | 11438 | No |
| 10673 | Symplectic Scholarly Graph Contagion Analyzer Mod-2068 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1375 | 4057 | No |
| 10715 | Symplectic Scholarly Graph Contagion Analyzer Mod-2164 | Operator theory / Koopman spectral expansion / ETF allocation | 8658 | 1287 | No |
| 10791 | Symplectic Scholarly Graph Contagion Analyzer Mod-2356 | Koopman operator / Model predictive control / ETF rebalancing | 4167 | 4119 | No |
| 10827 | Symplectic Scholarly Graph Contagion Analyzer Mod-2452 | Persistence landscapes / Topological contours / Equity index | 6082 | 11452 | No |
| 10864 | Symplectic Scholarly Graph Contagion Analyzer Mod-2548 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1406 | 4152 | No |
| 10906 | Symplectic Scholarly Graph Contagion Analyzer Mod-2644 | Operator theory / Koopman spectral expansion / ETF allocation | 8696 | 1311 | No |
| 10982 | Symplectic Scholarly Graph Contagion Analyzer Mod-2836 | Koopman operator / Model predictive control / ETF rebalancing | 4193 | 4214 | No |
| 11018 | Symplectic Scholarly Graph Contagion Analyzer Mod-2932 | Persistence landscapes / Topological contours / Equity index | 6106 | 11466 | No |
| 11055 | Symplectic Scholarly Graph Contagion Analyzer Mod-3028 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1437 | 4247 | No |
| 11097 | Symplectic Scholarly Graph Contagion Analyzer Mod-3124 | Operator theory / Koopman spectral expansion / ETF allocation | 8734 | 1335 | No |
| 11173 | Symplectic Scholarly Graph Contagion Analyzer Mod-3316 | Koopman operator / Model predictive control / ETF rebalancing | 4219 | 4309 | No |
| 11209 | Symplectic Scholarly Graph Contagion Analyzer Mod-3412 | Persistence landscapes / Topological contours / Equity index | 6130 | 11480 | No |
| 11246 | Symplectic Scholarly Graph Contagion Analyzer Mod-3508 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1468 | 4342 | No |
| 11288 | Symplectic Scholarly Graph Contagion Analyzer Mod-3604 | Operator theory / Koopman spectral expansion / ETF allocation | 8772 | 1359 | No |
| 11364 | Symplectic Scholarly Graph Contagion Analyzer Mod-3796 | Koopman operator / Model predictive control / ETF rebalancing | 4245 | 4404 | No |
| 11400 | Symplectic Scholarly Graph Contagion Analyzer Mod-3892 | Persistence landscapes / Topological contours / Equity index | 6154 | 11494 | No |
| 11437 | Symplectic Scholarly Graph Contagion Analyzer Mod-3988 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1499 | 4437 | No |
| 11473 | Symplectic Scholarly Graph Contagion Analyzer Eng-76 | Koopman operator / Model predictive control / ETF rebalancing | 4262 | 4459 | No |
| 11515 | Symplectic Scholarly Graph Contagion Analyzer Eng-172 | Persistence landscapes / Topological contours / Equity index | 6168 | 11499 | No |
| 11551 | Symplectic Scholarly Graph Contagion Analyzer Eng-268 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1516 | 4494 | No |
| 11585 | Symplectic Scholarly Graph Contagion Analyzer Eng-364 | Operator theory / Koopman spectral expansion / ETF allocation | 8831 | 1402 | No |
| 11664 | Symplectic Scholarly Graph Contagion Analyzer Eng-556 | Koopman operator / Model predictive control / ETF rebalancing | 4288 | 4552 | No |
| 11706 | Symplectic Scholarly Graph Contagion Analyzer Eng-652 | Persistence landscapes / Topological contours / Equity index | 6190 | 11513 | No |
| 11742 | Symplectic Scholarly Graph Contagion Analyzer Eng-748 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1546 | 4587 | No |
| 11776 | Symplectic Scholarly Graph Contagion Analyzer Eng-844 | Operator theory / Koopman spectral expansion / ETF allocation | 8867 | 1428 | No |
| 11855 | Symplectic Scholarly Graph Contagion Analyzer Eng-1036 | Koopman operator / Model predictive control / ETF rebalancing | 4314 | 4645 | No |
| 11897 | Symplectic Scholarly Graph Contagion Analyzer Eng-1132 | Persistence landscapes / Topological contours / Equity index | 6212 | 11527 | No |
| 11933 | Symplectic Scholarly Graph Contagion Analyzer Eng-1228 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1576 | 4680 | No |
| 11967 | Symplectic Scholarly Graph Contagion Analyzer Eng-1324 | Operator theory / Koopman spectral expansion / ETF allocation | 8903 | 1454 | No |
| 12046 | Symplectic Scholarly Graph Contagion Analyzer Eng-1516 | Koopman operator / Model predictive control / ETF rebalancing | 4340 | 4738 | No |
| 12088 | Symplectic Scholarly Graph Contagion Analyzer Eng-1612 | Persistence landscapes / Topological contours / Equity index | 6234 | 11541 | No |
| 12124 | Symplectic Scholarly Graph Contagion Analyzer Eng-1708 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1606 | 4773 | No |
| 12158 | Symplectic Scholarly Graph Contagion Analyzer Eng-1804 | Operator theory / Koopman spectral expansion / ETF allocation | 8939 | 1480 | No |
| 12237 | Symplectic Scholarly Graph Contagion Analyzer Eng-1996 | Koopman operator / Model predictive control / ETF rebalancing | 4366 | 4831 | No |
| 12279 | Symplectic Scholarly Graph Contagion Analyzer Eng-2092 | Persistence landscapes / Topological contours / Equity index | 6256 | 11555 | No |
| 12315 | Symplectic Scholarly Graph Contagion Analyzer Eng-2188 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1636 | 4866 | No |
| 12349 | Symplectic Scholarly Graph Contagion Analyzer Eng-2284 | Operator theory / Koopman spectral expansion / ETF allocation | 8975 | 1506 | No |
| 12428 | Symplectic Scholarly Graph Contagion Analyzer Eng-2476 | Koopman operator / Model predictive control / ETF rebalancing | 4392 | 4924 | No |
| 12470 | Symplectic Scholarly Graph Contagion Analyzer Eng-2572 | Persistence landscapes / Topological contours / Equity index | 6278 | 11569 | No |
| 12506 | Symplectic Scholarly Graph Contagion Analyzer Eng-2668 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1666 | 4959 | No |
| 12540 | Symplectic Scholarly Graph Contagion Analyzer Eng-2764 | Operator theory / Koopman spectral expansion / ETF allocation | 9011 | 1532 | No |
| 12619 | Symplectic Scholarly Graph Contagion Analyzer Eng-2956 | Koopman operator / Model predictive control / ETF rebalancing | 4418 | 5017 | No |
| 12661 | Symplectic Scholarly Graph Contagion Analyzer Eng-3052 | Persistence landscapes / Topological contours / Equity index | 6300 | 11583 | No |
| 12697 | Symplectic Scholarly Graph Contagion Analyzer Eng-3148 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1696 | 5052 | No |
| 12731 | Symplectic Scholarly Graph Contagion Analyzer Eng-3244 | Operator theory / Koopman spectral expansion / ETF allocation | 9047 | 1558 | No |
| 12810 | Symplectic Scholarly Graph Contagion Analyzer Eng-3436 | Koopman operator / Model predictive control / ETF rebalancing | 4444 | 5110 | No |
| 12852 | Symplectic Scholarly Graph Contagion Analyzer Eng-3532 | Persistence landscapes / Topological contours / Equity index | 6322 | 11597 | No |
| 12888 | Symplectic Scholarly Graph Contagion Analyzer Eng-3628 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1726 | 5145 | No |
| 12922 | Symplectic Scholarly Graph Contagion Analyzer Eng-3724 | Operator theory / Koopman spectral expansion / ETF allocation | 9083 | 1584 | No |
| 13001 | Symplectic Scholarly Graph Contagion Analyzer Eng-3916 | Koopman operator / Model predictive control / ETF rebalancing | 4470 | 5203 | No |
| 13043 | Symplectic Scholarly Graph Contagion Analyzer Eng-4012 | Persistence landscapes / Topological contours / Equity index | 6344 | 11611 | No |
| 13079 | Symplectic Scholarly Graph Contagion Analyzer Eng-4108 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1756 | 5238 | No |
| 13113 | Symplectic Scholarly Graph Contagion Analyzer Eng-4204 | Operator theory / Koopman spectral expansion / ETF allocation | 9119 | 1610 | No |
| 13192 | Symplectic Scholarly Graph Contagion Analyzer Eng-4396 | Koopman operator / Model predictive control / ETF rebalancing | 4496 | 5296 | No |
| 13234 | Symplectic Scholarly Graph Contagion Analyzer Eng-4492 | Persistence landscapes / Topological contours / Equity index | 6366 | 11625 | No |
| 13270 | Symplectic Scholarly Graph Contagion Analyzer Eng-4588 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1786 | 5331 | No |
| 13304 | Symplectic Scholarly Graph Contagion Analyzer Eng-4684 | Operator theory / Koopman spectral expansion / ETF allocation | 9155 | 1636 | No |
| 13383 | Symplectic Scholarly Graph Contagion Analyzer Eng-4876 | Koopman operator / Model predictive control / ETF rebalancing | 4522 | 5389 | No |
| 13425 | Symplectic Scholarly Graph Contagion Analyzer Eng-4972 | Persistence landscapes / Topological contours / Equity index | 6388 | 11639 | No |
| 13461 | Symplectic Scholarly Graph Contagion Analyzer Eng-5068 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1816 | 5424 | No |
| 13495 | Symplectic Scholarly Graph Contagion Analyzer Eng-5164 | Operator theory / Koopman spectral expansion / ETF allocation | 9191 | 1662 | No |
| 13574 | Symplectic Scholarly Graph Contagion Analyzer Eng-5356 | Koopman operator / Model predictive control / ETF rebalancing | 4548 | 5482 | No |
| 13616 | Symplectic Scholarly Graph Contagion Analyzer Eng-5452 | Persistence landscapes / Topological contours / Equity index | 6410 | 11653 | No |
| 13652 | Symplectic Scholarly Graph Contagion Analyzer Eng-5548 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1846 | 5517 | No |
| 13686 | Symplectic Scholarly Graph Contagion Analyzer Eng-5644 | Operator theory / Koopman spectral expansion / ETF allocation | 9227 | 1688 | No |
| 13765 | Symplectic Scholarly Graph Contagion Analyzer Eng-5836 | Koopman operator / Model predictive control / ETF rebalancing | 4574 | 5575 | No |
| 13807 | Symplectic Scholarly Graph Contagion Analyzer Eng-5932 | Persistence landscapes / Topological contours / Equity index | 6432 | 11667 | No |
