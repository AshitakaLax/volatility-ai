# Integrated approach to index/ETF constituent arbitrage

**Concept page** · shared by **136** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,738) ·
researched 2026-10-30

| | |
|---|---|
| Task | Index / ETF constituent arbitrage |
| Method | Integrated (combined) models |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Constituent arbitrage needs creation/redemption access or a short leg against the basket; both are outside this book. |
| Implemented in volatility-ai | Creation/redemption arbitrage is research code in `excluded` (C-RJ6). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK24, C-RJ6 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Holistic Scholarly Index
Arbitrage Engine Ref-120") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Estimate fair-value gaps between an index-linked instrument and its
constituent basket and trade the convergence after fees and slippage.
The integrated version chains several models or data sources into one
pipeline; the title does not say which. I found no study of this method
on this task.

## The CSV's description

Proposed integrated approach to index/ETF constituent arbitrage:
Estimate fair-value differences between an index-linked instrument and
its constituent basket, then evaluate convergence trades only after
accounting for synchronized prices, basket execution, fees, and
slippage. This is a concept-level interpretation of the title, not a
complete trading specification: the exact model inputs/target,
calibration, entry/exit or rebalance rules, and position sizing are not
fully defined here.

## Evidence

* **Petajisto (2017), "Inefficiencies in the Pricing of Exchange-Traded
  Funds," *Financial Analysts Journal*:** ETF prices deviate from NAV in
  a band about 100 bp wide after correcting for stale NAVs (see RK24).
  (Abstract.)
* **Ben-David, Franzoni & Moussawi (2018), "Do ETFs Increase
  Volatility?" *Journal of Finance* 73(6), 2471–2535:** arbitrage
  between ETFs and their constituents passes ETF demand shocks into the
  stocks, raising their volatility. (Abstract.)

## Against, and failure modes

* The gaps are a few basis points for liquid ETFs and are closed by
  authorised participants with creation/redemption access.
* An unspecified combination cannot be tested as stated; each part would
  need its own evidence.

## Fit with volatility-ai

Requires authorised-participant access or a hedged basket with a short
leg (C-RJ6, RK24). Out of scope.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Petajisto, A. (2017). *Financial Analysts Journal* 73(1). See RK24.
* Ben-David, I., Franzoni, F., Moussawi, R. (2018). *Journal of Finance*
  73(6), 2471–2535. Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 1738 | Holistic Scholarly Index Arbitrage Engine Ref-120 | Fractional order / Multi-scale ETF momentum | 1902 | 10349 | No |
| 1793 | Holistic Scholarly Index Arbitrage Engine Ref-600 | Fractional order / Multi-scale ETF momentum | 1907 | 10360 | No |
| 1849 | Holistic Scholarly Index Arbitrage Engine Sys-120 | Fractional order / Multi-scale ETF momentum | 1912 | 10369 | No |
| 1898 | Holistic Scholarly Index Arbitrage Engine Sys-600 | Fractional order / Multi-scale ETF momentum | 1917 | 10372 | No |
| 1947 | Holistic Scholarly Index Arbitrage Engine Sys-1080 | Fractional order / Multi-scale ETF momentum | 1922 | 10375 | No |
| 1996 | Holistic Scholarly Index Arbitrage Engine Sys-1560 | Fractional order / Multi-scale ETF momentum | 1927 | 10378 | No |
| 2080 | Holistic Scholarly Index Arbitrage Engine Mod-360 | Fractional order / Multi-scale ETF momentum | 1935 | 10383 | No |
| 2133 | Holistic Scholarly Index Arbitrage Engine Mod-840 | Fractional order / Multi-scale ETF momentum | 1940 | 10386 | No |
| 2186 | Holistic Scholarly Index Arbitrage Engine Mod-1320 | Fractional order / Multi-scale ETF momentum | 1945 | 10389 | No |
| 2239 | Holistic Scholarly Index Arbitrage Engine Mod-1800 | Fractional order / Multi-scale ETF momentum | 1950 | 10392 | No |
| 2292 | Holistic Scholarly Index Arbitrage Engine Mod-2280 | Fractional order / Multi-scale ETF momentum | 1955 | 10395 | No |
| 2345 | Holistic Scholarly Index Arbitrage Engine Mod-2760 | Fractional order / Multi-scale ETF momentum | 1960 | 10398 | No |
| 2398 | Holistic Scholarly Index Arbitrage Engine Mod-3240 | Fractional order / Multi-scale ETF momentum | 1965 | 10401 | No |
| 2451 | Holistic Scholarly Index Arbitrage Engine Mod-3720 | Fractional order / Multi-scale ETF momentum | 1970 | 10404 | No |
| 2493 | Holistic Scholarly Index Arbitrage Engine Eng-120 | Fractional order / Multi-scale ETF momentum | 1974 | 10406 | No |
| 2548 | Holistic Scholarly Index Arbitrage Engine Eng-600 | Fractional order / Multi-scale ETF momentum | 1979 | 10409 | No |
| 2603 | Holistic Scholarly Index Arbitrage Engine Eng-1080 | Fractional order / Multi-scale ETF momentum | 1984 | 10412 | No |
| 2658 | Holistic Scholarly Index Arbitrage Engine Eng-1560 | Fractional order / Multi-scale ETF momentum | 1989 | 10415 | No |
| 2713 | Holistic Scholarly Index Arbitrage Engine Eng-2040 | Fractional order / Multi-scale ETF momentum | 1994 | 10418 | No |
| 2768 | Holistic Scholarly Index Arbitrage Engine Eng-2520 | Fractional order / Multi-scale ETF momentum | 1999 | 10421 | No |
| 2823 | Holistic Scholarly Index Arbitrage Engine Eng-3000 | Fractional order / Multi-scale ETF momentum | 2004 | 10424 | No |
| 2878 | Holistic Scholarly Index Arbitrage Engine Eng-3480 | Fractional order / Multi-scale ETF momentum | 2009 | 10427 | No |
| 2933 | Holistic Scholarly Index Arbitrage Engine Eng-3960 | Fractional order / Multi-scale ETF momentum | 2014 | 10430 | No |
| 2988 | Holistic Scholarly Index Arbitrage Engine Eng-4440 | Fractional order / Multi-scale ETF momentum | 2019 | 10433 | No |
| 3043 | Holistic Scholarly Index Arbitrage Engine Eng-4920 | Fractional order / Multi-scale ETF momentum | 2024 | 10436 | No |
| 3098 | Holistic Scholarly Index Arbitrage Engine Eng-5400 | Fractional order / Multi-scale ETF momentum | 2029 | 10439 | No |
| 3153 | Holistic Scholarly Index Arbitrage Engine Eng-5880 | Fractional order / Multi-scale ETF momentum | 2034 | 10442 | No |
| 8684 | Holistic Scholarly Index Arbitrage Engine Ref-24 | Operator theory / Koopman spectral expansion / ETF allocation | 2127 | 10500 | No |
| 8760 | Holistic Scholarly Index Arbitrage Engine Ref-216 | Koopman operator / Model predictive control / ETF rebalancing | 3873 | 10740 | No |
| 8798 | Holistic Scholarly Index Arbitrage Engine Ref-312 | Persistence landscapes / Topological contours / Equity index | 405 | 10501 | No |
| 8837 | Holistic Scholarly Index Arbitrage Engine Ref-408 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1078 | 11674 | No |
| 8875 | Holistic Scholarly Index Arbitrage Engine Ref-504 | Operator theory / Koopman spectral expansion / ETF allocation | 2159 | 10502 | No |
| 8951 | Holistic Scholarly Index Arbitrage Engine Ref-696 | Koopman operator / Model predictive control / ETF rebalancing | 3900 | 10759 | No |
| 8989 | Holistic Scholarly Index Arbitrage Engine Ref-792 | Persistence landscapes / Topological contours / Equity index | 417 | 10503 | No |
| 9028 | Holistic Scholarly Index Arbitrage Engine Ref-888 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1112 | 11677 | No |
| 9066 | Holistic Scholarly Index Arbitrage Engine Ref-984 | Operator theory / Koopman spectral expansion / ETF allocation | 2191 | 10504 | No |
| 9082 | Holistic Scholarly Index Arbitrage Engine Sys-24 | Operator theory / Koopman spectral expansion / ETF allocation | 2194 | 10505 | No |
| 9159 | Holistic Scholarly Index Arbitrage Engine Sys-216 | Koopman operator / Model predictive control / ETF rebalancing | 3931 | 10781 | No |
| 9196 | Holistic Scholarly Index Arbitrage Engine Sys-312 | Persistence landscapes / Topological contours / Equity index | 428 | 10506 | No |
| 9233 | Holistic Scholarly Index Arbitrage Engine Sys-408 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1144 | 11680 | No |
| 9269 | Holistic Scholarly Index Arbitrage Engine Sys-504 | Operator theory / Koopman spectral expansion / ETF allocation | 2241 | 10507 | No |
| 9346 | Holistic Scholarly Index Arbitrage Engine Sys-696 | Koopman operator / Model predictive control / ETF rebalancing | 3960 | 10804 | No |
| 9383 | Holistic Scholarly Index Arbitrage Engine Sys-792 | Persistence landscapes / Topological contours / Equity index | 436 | 10508 | No |
| 9420 | Holistic Scholarly Index Arbitrage Engine Sys-888 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1174 | 11683 | No |
| 9456 | Holistic Scholarly Index Arbitrage Engine Sys-984 | Operator theory / Koopman spectral expansion / ETF allocation | 2288 | 10509 | No |
| 9533 | Holistic Scholarly Index Arbitrage Engine Sys-1176 | Koopman operator / Model predictive control / ETF rebalancing | 3989 | 10827 | No |
| 9570 | Holistic Scholarly Index Arbitrage Engine Sys-1272 | Persistence landscapes / Topological contours / Equity index | 444 | 10510 | No |
| 9607 | Holistic Scholarly Index Arbitrage Engine Sys-1368 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1204 | 11686 | No |
| 9643 | Holistic Scholarly Index Arbitrage Engine Sys-1464 | Operator theory / Koopman spectral expansion / ETF allocation | 2335 | 10511 | No |
| 9720 | Holistic Scholarly Index Arbitrage Engine Sys-1656 | Koopman operator / Model predictive control / ETF rebalancing | 4018 | 10850 | No |
| 9757 | Holistic Scholarly Index Arbitrage Engine Sys-1752 | Persistence landscapes / Topological contours / Equity index | 452 | 10512 | No |
| 9794 | Holistic Scholarly Index Arbitrage Engine Sys-1848 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1234 | 11689 | No |
| 9830 | Holistic Scholarly Index Arbitrage Engine Sys-1944 | Operator theory / Koopman spectral expansion / ETF allocation | 2382 | 10513 | No |
| 9880 | Holistic Scholarly Index Arbitrage Engine Mod-72 | Persistence landscapes / Topological contours / Equity index | 457 | 10514 | No |
| 9916 | Holistic Scholarly Index Arbitrage Engine Mod-168 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1253 | 11692 | No |
| 9958 | Holistic Scholarly Index Arbitrage Engine Mod-264 | Operator theory / Koopman spectral expansion / ETF allocation | 2408 | 10515 | No |
| 10034 | Holistic Scholarly Index Arbitrage Engine Mod-456 | Koopman operator / Model predictive control / ETF rebalancing | 4064 | 10884 | No |
| 10071 | Holistic Scholarly Index Arbitrage Engine Mod-552 | Persistence landscapes / Topological contours / Equity index | 467 | 10516 | No |
| 10107 | Holistic Scholarly Index Arbitrage Engine Mod-648 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1284 | 11695 | No |
| 10149 | Holistic Scholarly Index Arbitrage Engine Mod-744 | Operator theory / Koopman spectral expansion / ETF allocation | 2447 | 10517 | No |
| 10225 | Holistic Scholarly Index Arbitrage Engine Mod-936 | Koopman operator / Model predictive control / ETF rebalancing | 4090 | 10903 | No |
| 10262 | Holistic Scholarly Index Arbitrage Engine Mod-1032 | Persistence landscapes / Topological contours / Equity index | 477 | 10518 | No |
| 10298 | Holistic Scholarly Index Arbitrage Engine Mod-1128 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1315 | 11698 | No |
| 10340 | Holistic Scholarly Index Arbitrage Engine Mod-1224 | Operator theory / Koopman spectral expansion / ETF allocation | 2486 | 10519 | No |
| 10416 | Holistic Scholarly Index Arbitrage Engine Mod-1416 | Koopman operator / Model predictive control / ETF rebalancing | 4116 | 10922 | No |
| 10453 | Holistic Scholarly Index Arbitrage Engine Mod-1512 | Persistence landscapes / Topological contours / Equity index | 487 | 10520 | No |
| 10489 | Holistic Scholarly Index Arbitrage Engine Mod-1608 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1346 | 11701 | No |
| 10531 | Holistic Scholarly Index Arbitrage Engine Mod-1704 | Operator theory / Koopman spectral expansion / ETF allocation | 2525 | 10521 | No |
| 10607 | Holistic Scholarly Index Arbitrage Engine Mod-1896 | Koopman operator / Model predictive control / ETF rebalancing | 4142 | 10941 | No |
| 10644 | Holistic Scholarly Index Arbitrage Engine Mod-1992 | Persistence landscapes / Topological contours / Equity index | 497 | 10522 | No |
| 10680 | Holistic Scholarly Index Arbitrage Engine Mod-2088 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1377 | 11704 | No |
| 10722 | Holistic Scholarly Index Arbitrage Engine Mod-2184 | Operator theory / Koopman spectral expansion / ETF allocation | 2564 | 10523 | No |
| 10798 | Holistic Scholarly Index Arbitrage Engine Mod-2376 | Koopman operator / Model predictive control / ETF rebalancing | 4168 | 10960 | No |
| 10835 | Holistic Scholarly Index Arbitrage Engine Mod-2472 | Persistence landscapes / Topological contours / Equity index | 507 | 10524 | No |
| 10871 | Holistic Scholarly Index Arbitrage Engine Mod-2568 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1408 | 11707 | No |
| 10913 | Holistic Scholarly Index Arbitrage Engine Mod-2664 | Operator theory / Koopman spectral expansion / ETF allocation | 2603 | 10525 | No |
| 10989 | Holistic Scholarly Index Arbitrage Engine Mod-2856 | Koopman operator / Model predictive control / ETF rebalancing | 4194 | 10979 | No |
| 11026 | Holistic Scholarly Index Arbitrage Engine Mod-2952 | Persistence landscapes / Topological contours / Equity index | 517 | 10526 | No |
| 11062 | Holistic Scholarly Index Arbitrage Engine Mod-3048 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1439 | 11710 | No |
| 11104 | Holistic Scholarly Index Arbitrage Engine Mod-3144 | Operator theory / Koopman spectral expansion / ETF allocation | 2642 | 10527 | No |
| 11180 | Holistic Scholarly Index Arbitrage Engine Mod-3336 | Koopman operator / Model predictive control / ETF rebalancing | 4220 | 10998 | No |
| 11217 | Holistic Scholarly Index Arbitrage Engine Mod-3432 | Persistence landscapes / Topological contours / Equity index | 527 | 10528 | No |
| 11253 | Holistic Scholarly Index Arbitrage Engine Mod-3528 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1470 | 11713 | No |
| 11295 | Holistic Scholarly Index Arbitrage Engine Mod-3624 | Operator theory / Koopman spectral expansion / ETF allocation | 2681 | 10529 | No |
| 11371 | Holistic Scholarly Index Arbitrage Engine Mod-3816 | Koopman operator / Model predictive control / ETF rebalancing | 4246 | 11017 | No |
| 11408 | Holistic Scholarly Index Arbitrage Engine Mod-3912 | Persistence landscapes / Topological contours / Equity index | 537 | 10530 | No |
| 11452 | Holistic Scholarly Index Arbitrage Engine Eng-24 | Operator theory / Koopman spectral expansion / ETF allocation | 2714 | 10531 | No |
| 11529 | Holistic Scholarly Index Arbitrage Engine Eng-216 | Koopman operator / Model predictive control / ETF rebalancing | 4270 | 11032 | No |
| 11566 | Holistic Scholarly Index Arbitrage Engine Eng-312 | Persistence landscapes / Topological contours / Equity index | 548 | 10532 | No |
| 11606 | Holistic Scholarly Index Arbitrage Engine Eng-408 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1525 | 11718 | No |
| 11643 | Holistic Scholarly Index Arbitrage Engine Eng-504 | Operator theory / Koopman spectral expansion / ETF allocation | 2752 | 10533 | No |
| 11720 | Holistic Scholarly Index Arbitrage Engine Eng-696 | Koopman operator / Model predictive control / ETF rebalancing | 4296 | 11051 | No |
| 11757 | Holistic Scholarly Index Arbitrage Engine Eng-792 | Persistence landscapes / Topological contours / Equity index | 560 | 10534 | No |
| 11797 | Holistic Scholarly Index Arbitrage Engine Eng-888 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1555 | 11721 | No |
| 11834 | Holistic Scholarly Index Arbitrage Engine Eng-984 | Operator theory / Koopman spectral expansion / ETF allocation | 2790 | 10535 | No |
| 11911 | Holistic Scholarly Index Arbitrage Engine Eng-1176 | Koopman operator / Model predictive control / ETF rebalancing | 4322 | 11070 | No |
| 11948 | Holistic Scholarly Index Arbitrage Engine Eng-1272 | Persistence landscapes / Topological contours / Equity index | 572 | 10536 | No |
| 11988 | Holistic Scholarly Index Arbitrage Engine Eng-1368 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1585 | 11724 | No |
| 12025 | Holistic Scholarly Index Arbitrage Engine Eng-1464 | Operator theory / Koopman spectral expansion / ETF allocation | 2828 | 10537 | No |
| 12102 | Holistic Scholarly Index Arbitrage Engine Eng-1656 | Koopman operator / Model predictive control / ETF rebalancing | 4348 | 11089 | No |
| 12139 | Holistic Scholarly Index Arbitrage Engine Eng-1752 | Persistence landscapes / Topological contours / Equity index | 584 | 10538 | No |
| 12179 | Holistic Scholarly Index Arbitrage Engine Eng-1848 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1615 | 11727 | No |
| 12216 | Holistic Scholarly Index Arbitrage Engine Eng-1944 | Operator theory / Koopman spectral expansion / ETF allocation | 2866 | 10539 | No |
| 12293 | Holistic Scholarly Index Arbitrage Engine Eng-2136 | Koopman operator / Model predictive control / ETF rebalancing | 4374 | 11108 | No |
| 12330 | Holistic Scholarly Index Arbitrage Engine Eng-2232 | Persistence landscapes / Topological contours / Equity index | 596 | 10540 | No |
| 12370 | Holistic Scholarly Index Arbitrage Engine Eng-2328 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1645 | 11730 | No |
| 12407 | Holistic Scholarly Index Arbitrage Engine Eng-2424 | Operator theory / Koopman spectral expansion / ETF allocation | 2904 | 10541 | No |
| 12484 | Holistic Scholarly Index Arbitrage Engine Eng-2616 | Koopman operator / Model predictive control / ETF rebalancing | 4400 | 11127 | No |
| 12521 | Holistic Scholarly Index Arbitrage Engine Eng-2712 | Persistence landscapes / Topological contours / Equity index | 608 | 10542 | No |
| 12561 | Holistic Scholarly Index Arbitrage Engine Eng-2808 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1675 | 11733 | No |
| 12598 | Holistic Scholarly Index Arbitrage Engine Eng-2904 | Operator theory / Koopman spectral expansion / ETF allocation | 2942 | 10543 | No |
| 12675 | Holistic Scholarly Index Arbitrage Engine Eng-3096 | Koopman operator / Model predictive control / ETF rebalancing | 4426 | 11146 | No |
| 12712 | Holistic Scholarly Index Arbitrage Engine Eng-3192 | Persistence landscapes / Topological contours / Equity index | 620 | 10544 | No |
| 12752 | Holistic Scholarly Index Arbitrage Engine Eng-3288 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1705 | 11736 | No |
| 12789 | Holistic Scholarly Index Arbitrage Engine Eng-3384 | Operator theory / Koopman spectral expansion / ETF allocation | 2980 | 10545 | No |
| 12866 | Holistic Scholarly Index Arbitrage Engine Eng-3576 | Koopman operator / Model predictive control / ETF rebalancing | 4452 | 11165 | No |
| 12903 | Holistic Scholarly Index Arbitrage Engine Eng-3672 | Persistence landscapes / Topological contours / Equity index | 632 | 10546 | No |
| 12943 | Holistic Scholarly Index Arbitrage Engine Eng-3768 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1735 | 11739 | No |
| 12980 | Holistic Scholarly Index Arbitrage Engine Eng-3864 | Operator theory / Koopman spectral expansion / ETF allocation | 3018 | 10547 | No |
| 13057 | Holistic Scholarly Index Arbitrage Engine Eng-4056 | Koopman operator / Model predictive control / ETF rebalancing | 4478 | 11184 | No |
| 13094 | Holistic Scholarly Index Arbitrage Engine Eng-4152 | Persistence landscapes / Topological contours / Equity index | 644 | 10548 | No |
| 13134 | Holistic Scholarly Index Arbitrage Engine Eng-4248 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1765 | 11742 | No |
| 13171 | Holistic Scholarly Index Arbitrage Engine Eng-4344 | Operator theory / Koopman spectral expansion / ETF allocation | 3056 | 10549 | No |
| 13248 | Holistic Scholarly Index Arbitrage Engine Eng-4536 | Koopman operator / Model predictive control / ETF rebalancing | 4504 | 11203 | No |
| 13285 | Holistic Scholarly Index Arbitrage Engine Eng-4632 | Persistence landscapes / Topological contours / Equity index | 656 | 10550 | No |
| 13325 | Holistic Scholarly Index Arbitrage Engine Eng-4728 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1795 | 11745 | No |
| 13362 | Holistic Scholarly Index Arbitrage Engine Eng-4824 | Operator theory / Koopman spectral expansion / ETF allocation | 3094 | 10551 | No |
| 13439 | Holistic Scholarly Index Arbitrage Engine Eng-5016 | Koopman operator / Model predictive control / ETF rebalancing | 4530 | 11222 | No |
| 13476 | Holistic Scholarly Index Arbitrage Engine Eng-5112 | Persistence landscapes / Topological contours / Equity index | 668 | 10552 | No |
| 13516 | Holistic Scholarly Index Arbitrage Engine Eng-5208 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1825 | 11748 | No |
| 13553 | Holistic Scholarly Index Arbitrage Engine Eng-5304 | Operator theory / Koopman spectral expansion / ETF allocation | 3132 | 10553 | No |
| 13630 | Holistic Scholarly Index Arbitrage Engine Eng-5496 | Koopman operator / Model predictive control / ETF rebalancing | 4556 | 11241 | No |
| 13667 | Holistic Scholarly Index Arbitrage Engine Eng-5592 | Persistence landscapes / Topological contours / Equity index | 680 | 10554 | No |
| 13707 | Holistic Scholarly Index Arbitrage Engine Eng-5688 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1855 | 11751 | No |
| 13744 | Holistic Scholarly Index Arbitrage Engine Eng-5784 | Operator theory / Koopman spectral expansion / ETF allocation | 3170 | 10555 | No |
| 13821 | Holistic Scholarly Index Arbitrage Engine Eng-5976 | Koopman operator / Model predictive control / ETF rebalancing | 4582 | 11260 | No |
