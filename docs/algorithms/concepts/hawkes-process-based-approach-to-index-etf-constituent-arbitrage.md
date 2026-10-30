# Hawkes-process-based approach to index/ETF constituent arbitrage

**Concept page** · shared by **135** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,765) ·
researched 2026-10-30

| | |
|---|---|
| Task | Index / ETF constituent arbitrage |
| Method | Hawkes (self-exciting) point processes |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Constituent arbitrage needs creation/redemption access or a short leg against the basket; both are outside this book. |
| Implemented in volatility-ai | Creation/redemption arbitrage is research code in `excluded` (C-RJ6). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK24, C-RJ6 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Hawkes Scholarly Index
Arbitrage Engine Ref-360") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Estimate fair-value gaps between an index-linked instrument and its
constituent basket and trade the convergence after fees and slippage.
The Hawkes version models events (trades, jumps, crashes) as
self-exciting, each event raising the near-term chance of another. I
found no study of this method on this task.

## The CSV's description

Proposed Hawkes-process-based approach to index/ETF constituent
arbitrage: Estimate fair-value differences between an index-linked
instrument and its constituent basket, then evaluate convergence trades
only after accounting for synchronized prices, basket execution, fees,
and slippage. This is a concept-level interpretation of the title, not a
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
* Hawkes models describe intraday event clustering; daily bars hold too
  few events to fit them.

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
| 1765 | Hawkes Scholarly Index Arbitrage Engine Ref-360 | Fractional order / Multi-scale ETF momentum | 3760 | 10355 | No |
| 1820 | Hawkes Scholarly Index Arbitrage Engine Ref-840 | Fractional order / Multi-scale ETF momentum | 3762 | 10366 | No |
| 1872 | Hawkes Scholarly Index Arbitrage Engine Sys-360 | Fractional order / Multi-scale ETF momentum | 3764 | 10371 | No |
| 1921 | Hawkes Scholarly Index Arbitrage Engine Sys-840 | Fractional order / Multi-scale ETF momentum | 3766 | 10374 | No |
| 1970 | Hawkes Scholarly Index Arbitrage Engine Sys-1320 | Fractional order / Multi-scale ETF momentum | 3768 | 10377 | No |
| 2019 | Hawkes Scholarly Index Arbitrage Engine Sys-1800 | Fractional order / Multi-scale ETF momentum | 3770 | 10380 | No |
| 2052 | Hawkes Scholarly Index Arbitrage Engine Mod-120 | Fractional order / Multi-scale ETF momentum | 3771 | 10381 | No |
| 2105 | Hawkes Scholarly Index Arbitrage Engine Mod-600 | Fractional order / Multi-scale ETF momentum | 3773 | 10384 | No |
| 2158 | Hawkes Scholarly Index Arbitrage Engine Mod-1080 | Fractional order / Multi-scale ETF momentum | 3775 | 10387 | No |
| 2211 | Hawkes Scholarly Index Arbitrage Engine Mod-1560 | Fractional order / Multi-scale ETF momentum | 3777 | 10390 | No |
| 2264 | Hawkes Scholarly Index Arbitrage Engine Mod-2040 | Fractional order / Multi-scale ETF momentum | 3779 | 10393 | No |
| 2317 | Hawkes Scholarly Index Arbitrage Engine Mod-2520 | Fractional order / Multi-scale ETF momentum | 3781 | 10396 | No |
| 2370 | Hawkes Scholarly Index Arbitrage Engine Mod-3000 | Fractional order / Multi-scale ETF momentum | 3783 | 10399 | No |
| 2423 | Hawkes Scholarly Index Arbitrage Engine Mod-3480 | Fractional order / Multi-scale ETF momentum | 3785 | 10402 | No |
| 2476 | Hawkes Scholarly Index Arbitrage Engine Mod-3960 | Fractional order / Multi-scale ETF momentum | 3787 | 10405 | No |
| 2520 | Hawkes Scholarly Index Arbitrage Engine Eng-360 | Fractional order / Multi-scale ETF momentum | 3789 | 10408 | No |
| 2575 | Hawkes Scholarly Index Arbitrage Engine Eng-840 | Fractional order / Multi-scale ETF momentum | 3791 | 10411 | No |
| 2630 | Hawkes Scholarly Index Arbitrage Engine Eng-1320 | Fractional order / Multi-scale ETF momentum | 3793 | 10414 | No |
| 2685 | Hawkes Scholarly Index Arbitrage Engine Eng-1800 | Fractional order / Multi-scale ETF momentum | 3795 | 10417 | No |
| 2740 | Hawkes Scholarly Index Arbitrage Engine Eng-2280 | Fractional order / Multi-scale ETF momentum | 3797 | 10420 | No |
| 2795 | Hawkes Scholarly Index Arbitrage Engine Eng-2760 | Fractional order / Multi-scale ETF momentum | 3799 | 10423 | No |
| 2850 | Hawkes Scholarly Index Arbitrage Engine Eng-3240 | Fractional order / Multi-scale ETF momentum | 3801 | 10426 | No |
| 2905 | Hawkes Scholarly Index Arbitrage Engine Eng-3720 | Fractional order / Multi-scale ETF momentum | 3803 | 10429 | No |
| 2960 | Hawkes Scholarly Index Arbitrage Engine Eng-4200 | Fractional order / Multi-scale ETF momentum | 3805 | 10432 | No |
| 3015 | Hawkes Scholarly Index Arbitrage Engine Eng-4680 | Fractional order / Multi-scale ETF momentum | 3807 | 10435 | No |
| 3070 | Hawkes Scholarly Index Arbitrage Engine Eng-5160 | Fractional order / Multi-scale ETF momentum | 3809 | 10438 | No |
| 3125 | Hawkes Scholarly Index Arbitrage Engine Eng-5640 | Fractional order / Multi-scale ETF momentum | 3811 | 10441 | No |
| 8705 | Hawkes Scholarly Index Arbitrage Engine Ref-72 | Persistence landscapes / Topological contours / Equity index | 1054 | 10735 | No |
| 8742 | Hawkes Scholarly Index Arbitrage Engine Ref-168 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1061 | 11673 | No |
| 8778 | Hawkes Scholarly Index Arbitrage Engine Ref-264 | Operator theory / Koopman spectral expansion / ETF allocation | 4660 | 10741 | No |
| 8854 | Hawkes Scholarly Index Arbitrage Engine Ref-456 | Koopman operator / Model predictive control / ETF rebalancing | 5848 | 10750 | No |
| 8896 | Hawkes Scholarly Index Arbitrage Engine Ref-552 | Persistence landscapes / Topological contours / Equity index | 1088 | 10754 | No |
| 8933 | Hawkes Scholarly Index Arbitrage Engine Ref-648 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1095 | 11676 | No |
| 8969 | Hawkes Scholarly Index Arbitrage Engine Ref-744 | Operator theory / Koopman spectral expansion / ETF allocation | 4687 | 10760 | No |
| 9045 | Hawkes Scholarly Index Arbitrage Engine Ref-936 | Koopman operator / Model predictive control / ETF rebalancing | 5873 | 10769 | No |
| 9101 | Hawkes Scholarly Index Arbitrage Engine Sys-72 | Persistence landscapes / Topological contours / Equity index | 1123 | 10774 | No |
| 9138 | Hawkes Scholarly Index Arbitrage Engine Sys-168 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1129 | 11679 | No |
| 9177 | Hawkes Scholarly Index Arbitrage Engine Sys-264 | Operator theory / Koopman spectral expansion / ETF allocation | 4718 | 10783 | No |
| 9253 | Hawkes Scholarly Index Arbitrage Engine Sys-456 | Koopman operator / Model predictive control / ETF rebalancing | 5896 | 10793 | No |
| 9288 | Hawkes Scholarly Index Arbitrage Engine Sys-552 | Persistence landscapes / Topological contours / Equity index | 1153 | 10797 | No |
| 9325 | Hawkes Scholarly Index Arbitrage Engine Sys-648 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1159 | 11682 | No |
| 9364 | Hawkes Scholarly Index Arbitrage Engine Sys-744 | Operator theory / Koopman spectral expansion / ETF allocation | 4749 | 10806 | No |
| 9440 | Hawkes Scholarly Index Arbitrage Engine Sys-936 | Koopman operator / Model predictive control / ETF rebalancing | 5916 | 10816 | No |
| 9475 | Hawkes Scholarly Index Arbitrage Engine Sys-1032 | Persistence landscapes / Topological contours / Equity index | 1183 | 10820 | No |
| 9512 | Hawkes Scholarly Index Arbitrage Engine Sys-1128 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1189 | 11685 | No |
| 9551 | Hawkes Scholarly Index Arbitrage Engine Sys-1224 | Operator theory / Koopman spectral expansion / ETF allocation | 4780 | 10829 | No |
| 9627 | Hawkes Scholarly Index Arbitrage Engine Sys-1416 | Koopman operator / Model predictive control / ETF rebalancing | 5936 | 10839 | No |
| 9662 | Hawkes Scholarly Index Arbitrage Engine Sys-1512 | Persistence landscapes / Topological contours / Equity index | 1213 | 10843 | No |
| 9699 | Hawkes Scholarly Index Arbitrage Engine Sys-1608 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1219 | 11688 | No |
| 9738 | Hawkes Scholarly Index Arbitrage Engine Sys-1704 | Operator theory / Koopman spectral expansion / ETF allocation | 4811 | 10852 | No |
| 9814 | Hawkes Scholarly Index Arbitrage Engine Sys-1896 | Koopman operator / Model predictive control / ETF rebalancing | 5956 | 10862 | No |
| 9849 | Hawkes Scholarly Index Arbitrage Engine Sys-1992 | Persistence landscapes / Topological contours / Equity index | 1243 | 10866 | No |
| 9860 | Hawkes Scholarly Index Arbitrage Engine Mod-24 | Operator theory / Koopman spectral expansion / ETF allocation | 4832 | 10867 | No |
| 9939 | Hawkes Scholarly Index Arbitrage Engine Mod-216 | Koopman operator / Model predictive control / ETF rebalancing | 5972 | 10874 | No |
| 9976 | Hawkes Scholarly Index Arbitrage Engine Mod-312 | Persistence landscapes / Topological contours / Equity index | 1261 | 10878 | No |
| 10015 | Hawkes Scholarly Index Arbitrage Engine Mod-408 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1268 | 11693 | No |
| 10051 | Hawkes Scholarly Index Arbitrage Engine Mod-504 | Operator theory / Koopman spectral expansion / ETF allocation | 4859 | 10886 | No |
| 10130 | Hawkes Scholarly Index Arbitrage Engine Mod-696 | Koopman operator / Model predictive control / ETF rebalancing | 5996 | 10893 | No |
| 10167 | Hawkes Scholarly Index Arbitrage Engine Mod-792 | Persistence landscapes / Topological contours / Equity index | 1292 | 10897 | No |
| 10206 | Hawkes Scholarly Index Arbitrage Engine Mod-888 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1299 | 11696 | No |
| 10242 | Hawkes Scholarly Index Arbitrage Engine Mod-984 | Operator theory / Koopman spectral expansion / ETF allocation | 4886 | 10905 | No |
| 10321 | Hawkes Scholarly Index Arbitrage Engine Mod-1176 | Koopman operator / Model predictive control / ETF rebalancing | 6020 | 10912 | No |
| 10358 | Hawkes Scholarly Index Arbitrage Engine Mod-1272 | Persistence landscapes / Topological contours / Equity index | 1323 | 10916 | No |
| 10397 | Hawkes Scholarly Index Arbitrage Engine Mod-1368 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1330 | 11699 | No |
| 10433 | Hawkes Scholarly Index Arbitrage Engine Mod-1464 | Operator theory / Koopman spectral expansion / ETF allocation | 4913 | 10924 | No |
| 10512 | Hawkes Scholarly Index Arbitrage Engine Mod-1656 | Koopman operator / Model predictive control / ETF rebalancing | 6044 | 10931 | No |
| 10549 | Hawkes Scholarly Index Arbitrage Engine Mod-1752 | Persistence landscapes / Topological contours / Equity index | 1354 | 10935 | No |
| 10588 | Hawkes Scholarly Index Arbitrage Engine Mod-1848 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1361 | 11702 | No |
| 10624 | Hawkes Scholarly Index Arbitrage Engine Mod-1944 | Operator theory / Koopman spectral expansion / ETF allocation | 4940 | 10943 | No |
| 10703 | Hawkes Scholarly Index Arbitrage Engine Mod-2136 | Koopman operator / Model predictive control / ETF rebalancing | 6068 | 10950 | No |
| 10740 | Hawkes Scholarly Index Arbitrage Engine Mod-2232 | Persistence landscapes / Topological contours / Equity index | 1385 | 10954 | No |
| 10779 | Hawkes Scholarly Index Arbitrage Engine Mod-2328 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1392 | 11705 | No |
| 10815 | Hawkes Scholarly Index Arbitrage Engine Mod-2424 | Operator theory / Koopman spectral expansion / ETF allocation | 4967 | 10962 | No |
| 10894 | Hawkes Scholarly Index Arbitrage Engine Mod-2616 | Koopman operator / Model predictive control / ETF rebalancing | 6092 | 10969 | No |
| 10931 | Hawkes Scholarly Index Arbitrage Engine Mod-2712 | Persistence landscapes / Topological contours / Equity index | 1416 | 10973 | No |
| 10970 | Hawkes Scholarly Index Arbitrage Engine Mod-2808 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1423 | 11708 | No |
| 11006 | Hawkes Scholarly Index Arbitrage Engine Mod-2904 | Operator theory / Koopman spectral expansion / ETF allocation | 4994 | 10981 | No |
| 11085 | Hawkes Scholarly Index Arbitrage Engine Mod-3096 | Koopman operator / Model predictive control / ETF rebalancing | 6116 | 10988 | No |
| 11122 | Hawkes Scholarly Index Arbitrage Engine Mod-3192 | Persistence landscapes / Topological contours / Equity index | 1447 | 10992 | No |
| 11161 | Hawkes Scholarly Index Arbitrage Engine Mod-3288 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1454 | 11711 | No |
| 11197 | Hawkes Scholarly Index Arbitrage Engine Mod-3384 | Operator theory / Koopman spectral expansion / ETF allocation | 5021 | 11000 | No |
| 11276 | Hawkes Scholarly Index Arbitrage Engine Mod-3576 | Koopman operator / Model predictive control / ETF rebalancing | 6140 | 11007 | No |
| 11313 | Hawkes Scholarly Index Arbitrage Engine Mod-3672 | Persistence landscapes / Topological contours / Equity index | 1478 | 11011 | No |
| 11352 | Hawkes Scholarly Index Arbitrage Engine Mod-3768 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1485 | 11714 | No |
| 11388 | Hawkes Scholarly Index Arbitrage Engine Mod-3864 | Operator theory / Koopman spectral expansion / ETF allocation | 5048 | 11019 | No |
| 11472 | Hawkes Scholarly Index Arbitrage Engine Eng-72 | Persistence landscapes / Topological contours / Equity index | 1504 | 11026 | No |
| 11512 | Hawkes Scholarly Index Arbitrage Engine Eng-168 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1510 | 11717 | No |
| 11548 | Hawkes Scholarly Index Arbitrage Engine Eng-264 | Operator theory / Koopman spectral expansion / ETF allocation | 5069 | 11034 | No |
| 11623 | Hawkes Scholarly Index Arbitrage Engine Eng-456 | Koopman operator / Model predictive control / ETF rebalancing | 6182 | 11042 | No |
| 11663 | Hawkes Scholarly Index Arbitrage Engine Eng-552 | Persistence landscapes / Topological contours / Equity index | 1534 | 11045 | No |
| 11703 | Hawkes Scholarly Index Arbitrage Engine Eng-648 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1540 | 11720 | No |
| 11739 | Hawkes Scholarly Index Arbitrage Engine Eng-744 | Operator theory / Koopman spectral expansion / ETF allocation | 5094 | 11053 | No |
| 11814 | Hawkes Scholarly Index Arbitrage Engine Eng-936 | Koopman operator / Model predictive control / ETF rebalancing | 6204 | 11061 | No |
| 11854 | Hawkes Scholarly Index Arbitrage Engine Eng-1032 | Persistence landscapes / Topological contours / Equity index | 1564 | 11064 | No |
| 11894 | Hawkes Scholarly Index Arbitrage Engine Eng-1128 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1570 | 11723 | No |
| 11930 | Hawkes Scholarly Index Arbitrage Engine Eng-1224 | Operator theory / Koopman spectral expansion / ETF allocation | 5119 | 11072 | No |
| 12005 | Hawkes Scholarly Index Arbitrage Engine Eng-1416 | Koopman operator / Model predictive control / ETF rebalancing | 6226 | 11080 | No |
| 12045 | Hawkes Scholarly Index Arbitrage Engine Eng-1512 | Persistence landscapes / Topological contours / Equity index | 1594 | 11083 | No |
| 12085 | Hawkes Scholarly Index Arbitrage Engine Eng-1608 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1600 | 11726 | No |
| 12121 | Hawkes Scholarly Index Arbitrage Engine Eng-1704 | Operator theory / Koopman spectral expansion / ETF allocation | 5144 | 11091 | No |
| 12196 | Hawkes Scholarly Index Arbitrage Engine Eng-1896 | Koopman operator / Model predictive control / ETF rebalancing | 6248 | 11099 | No |
| 12236 | Hawkes Scholarly Index Arbitrage Engine Eng-1992 | Persistence landscapes / Topological contours / Equity index | 1624 | 11102 | No |
| 12276 | Hawkes Scholarly Index Arbitrage Engine Eng-2088 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1630 | 11729 | No |
| 12312 | Hawkes Scholarly Index Arbitrage Engine Eng-2184 | Operator theory / Koopman spectral expansion / ETF allocation | 5169 | 11110 | No |
| 12387 | Hawkes Scholarly Index Arbitrage Engine Eng-2376 | Koopman operator / Model predictive control / ETF rebalancing | 6270 | 11118 | No |
| 12427 | Hawkes Scholarly Index Arbitrage Engine Eng-2472 | Persistence landscapes / Topological contours / Equity index | 1654 | 11121 | No |
| 12467 | Hawkes Scholarly Index Arbitrage Engine Eng-2568 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1660 | 11732 | No |
| 12503 | Hawkes Scholarly Index Arbitrage Engine Eng-2664 | Operator theory / Koopman spectral expansion / ETF allocation | 5194 | 11129 | No |
| 12578 | Hawkes Scholarly Index Arbitrage Engine Eng-2856 | Koopman operator / Model predictive control / ETF rebalancing | 6292 | 11137 | No |
| 12618 | Hawkes Scholarly Index Arbitrage Engine Eng-2952 | Persistence landscapes / Topological contours / Equity index | 1684 | 11140 | No |
| 12658 | Hawkes Scholarly Index Arbitrage Engine Eng-3048 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1690 | 11735 | No |
| 12694 | Hawkes Scholarly Index Arbitrage Engine Eng-3144 | Operator theory / Koopman spectral expansion / ETF allocation | 5219 | 11148 | No |
| 12769 | Hawkes Scholarly Index Arbitrage Engine Eng-3336 | Koopman operator / Model predictive control / ETF rebalancing | 6314 | 11156 | No |
| 12809 | Hawkes Scholarly Index Arbitrage Engine Eng-3432 | Persistence landscapes / Topological contours / Equity index | 1714 | 11159 | No |
| 12849 | Hawkes Scholarly Index Arbitrage Engine Eng-3528 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1720 | 11738 | No |
| 12885 | Hawkes Scholarly Index Arbitrage Engine Eng-3624 | Operator theory / Koopman spectral expansion / ETF allocation | 5244 | 11167 | No |
| 12960 | Hawkes Scholarly Index Arbitrage Engine Eng-3816 | Koopman operator / Model predictive control / ETF rebalancing | 6336 | 11175 | No |
| 13000 | Hawkes Scholarly Index Arbitrage Engine Eng-3912 | Persistence landscapes / Topological contours / Equity index | 1744 | 11178 | No |
| 13040 | Hawkes Scholarly Index Arbitrage Engine Eng-4008 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1750 | 11741 | No |
| 13076 | Hawkes Scholarly Index Arbitrage Engine Eng-4104 | Operator theory / Koopman spectral expansion / ETF allocation | 5269 | 11186 | No |
| 13151 | Hawkes Scholarly Index Arbitrage Engine Eng-4296 | Koopman operator / Model predictive control / ETF rebalancing | 6358 | 11194 | No |
| 13191 | Hawkes Scholarly Index Arbitrage Engine Eng-4392 | Persistence landscapes / Topological contours / Equity index | 1774 | 11197 | No |
| 13231 | Hawkes Scholarly Index Arbitrage Engine Eng-4488 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1780 | 11744 | No |
| 13267 | Hawkes Scholarly Index Arbitrage Engine Eng-4584 | Operator theory / Koopman spectral expansion / ETF allocation | 5294 | 11205 | No |
| 13342 | Hawkes Scholarly Index Arbitrage Engine Eng-4776 | Koopman operator / Model predictive control / ETF rebalancing | 6380 | 11213 | No |
| 13382 | Hawkes Scholarly Index Arbitrage Engine Eng-4872 | Persistence landscapes / Topological contours / Equity index | 1804 | 11216 | No |
| 13422 | Hawkes Scholarly Index Arbitrage Engine Eng-4968 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1810 | 11747 | No |
| 13458 | Hawkes Scholarly Index Arbitrage Engine Eng-5064 | Operator theory / Koopman spectral expansion / ETF allocation | 5319 | 11224 | No |
| 13533 | Hawkes Scholarly Index Arbitrage Engine Eng-5256 | Koopman operator / Model predictive control / ETF rebalancing | 6402 | 11232 | No |
| 13573 | Hawkes Scholarly Index Arbitrage Engine Eng-5352 | Persistence landscapes / Topological contours / Equity index | 1834 | 11235 | No |
| 13613 | Hawkes Scholarly Index Arbitrage Engine Eng-5448 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1840 | 11750 | No |
| 13649 | Hawkes Scholarly Index Arbitrage Engine Eng-5544 | Operator theory / Koopman spectral expansion / ETF allocation | 5344 | 11243 | No |
| 13724 | Hawkes Scholarly Index Arbitrage Engine Eng-5736 | Koopman operator / Model predictive control / ETF rebalancing | 6424 | 11251 | No |
| 13764 | Hawkes Scholarly Index Arbitrage Engine Eng-5832 | Persistence landscapes / Topological contours / Equity index | 1864 | 11254 | No |
| 13804 | Hawkes Scholarly Index Arbitrage Engine Eng-5928 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1870 | 11753 | No |
