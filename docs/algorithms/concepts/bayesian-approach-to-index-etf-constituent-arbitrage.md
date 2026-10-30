# Bayesian approach to index/ETF constituent arbitrage

**Concept page** · shared by **136** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,753) ·
researched 2026-10-30

| | |
|---|---|
| Task | Index / ETF constituent arbitrage |
| Method | Bayesian estimation |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Constituent arbitrage needs creation/redemption access or a short leg against the basket; both are outside this book. |
| Implemented in volatility-ai | Creation/redemption arbitrage is research code in `excluded` (C-RJ6). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK24, C-RJ6 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Bayesian Scholarly Index
Arbitrage Engine Ref-240") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Estimate fair-value gaps between an index-linked instrument and its
constituent basket and trade the convergence after fees and slippage.
The Bayesian version puts priors on the parameters and acts on the
posterior. I found no study of this method on this task.

## The CSV's description

Proposed Bayesian approach to index/ETF constituent arbitrage: Estimate
fair-value differences between an index-linked instrument and its
constituent basket, then evaluate convergence trades only after
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
* The prior decides a lot: a weak one returns the plain estimate, a
  strong one imposes the answer.

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
| 1753 | Bayesian Scholarly Index Arbitrage Engine Ref-240 | Fractional order / Multi-scale ETF momentum | 3759 | 10352 | No |
| 1808 | Bayesian Scholarly Index Arbitrage Engine Ref-720 | Fractional order / Multi-scale ETF momentum | 3761 | 10363 | No |
| 1861 | Bayesian Scholarly Index Arbitrage Engine Sys-240 | Fractional order / Multi-scale ETF momentum | 3763 | 10370 | No |
| 1910 | Bayesian Scholarly Index Arbitrage Engine Sys-720 | Fractional order / Multi-scale ETF momentum | 3765 | 10373 | No |
| 1959 | Bayesian Scholarly Index Arbitrage Engine Sys-1200 | Fractional order / Multi-scale ETF momentum | 3767 | 10376 | No |
| 2008 | Bayesian Scholarly Index Arbitrage Engine Sys-1680 | Fractional order / Multi-scale ETF momentum | 3769 | 10379 | No |
| 2065 | Bayesian Scholarly Index Arbitrage Engine Mod-240 | Fractional order / Multi-scale ETF momentum | 3772 | 10382 | No |
| 2118 | Bayesian Scholarly Index Arbitrage Engine Mod-720 | Fractional order / Multi-scale ETF momentum | 3774 | 10385 | No |
| 2171 | Bayesian Scholarly Index Arbitrage Engine Mod-1200 | Fractional order / Multi-scale ETF momentum | 3776 | 10388 | No |
| 2224 | Bayesian Scholarly Index Arbitrage Engine Mod-1680 | Fractional order / Multi-scale ETF momentum | 3778 | 10391 | No |
| 2277 | Bayesian Scholarly Index Arbitrage Engine Mod-2160 | Fractional order / Multi-scale ETF momentum | 3780 | 10394 | No |
| 2330 | Bayesian Scholarly Index Arbitrage Engine Mod-2640 | Fractional order / Multi-scale ETF momentum | 3782 | 10397 | No |
| 2383 | Bayesian Scholarly Index Arbitrage Engine Mod-3120 | Fractional order / Multi-scale ETF momentum | 3784 | 10400 | No |
| 2436 | Bayesian Scholarly Index Arbitrage Engine Mod-3600 | Fractional order / Multi-scale ETF momentum | 3786 | 10403 | No |
| 2506 | Bayesian Scholarly Index Arbitrage Engine Eng-240 | Fractional order / Multi-scale ETF momentum | 3788 | 10407 | No |
| 2561 | Bayesian Scholarly Index Arbitrage Engine Eng-720 | Fractional order / Multi-scale ETF momentum | 3790 | 10410 | No |
| 2616 | Bayesian Scholarly Index Arbitrage Engine Eng-1200 | Fractional order / Multi-scale ETF momentum | 3792 | 10413 | No |
| 2671 | Bayesian Scholarly Index Arbitrage Engine Eng-1680 | Fractional order / Multi-scale ETF momentum | 3794 | 10416 | No |
| 2726 | Bayesian Scholarly Index Arbitrage Engine Eng-2160 | Fractional order / Multi-scale ETF momentum | 3796 | 10419 | No |
| 2781 | Bayesian Scholarly Index Arbitrage Engine Eng-2640 | Fractional order / Multi-scale ETF momentum | 3798 | 10422 | No |
| 2836 | Bayesian Scholarly Index Arbitrage Engine Eng-3120 | Fractional order / Multi-scale ETF momentum | 3800 | 10425 | No |
| 2891 | Bayesian Scholarly Index Arbitrage Engine Eng-3600 | Fractional order / Multi-scale ETF momentum | 3802 | 10428 | No |
| 2946 | Bayesian Scholarly Index Arbitrage Engine Eng-4080 | Fractional order / Multi-scale ETF momentum | 3804 | 10431 | No |
| 3001 | Bayesian Scholarly Index Arbitrage Engine Eng-4560 | Fractional order / Multi-scale ETF momentum | 3806 | 10434 | No |
| 3056 | Bayesian Scholarly Index Arbitrage Engine Eng-5040 | Fractional order / Multi-scale ETF momentum | 3808 | 10437 | No |
| 3111 | Bayesian Scholarly Index Arbitrage Engine Eng-5520 | Fractional order / Multi-scale ETF momentum | 3810 | 10440 | No |
| 3166 | Bayesian Scholarly Index Arbitrage Engine Eng-6000 | Fractional order / Multi-scale ETF momentum | 3812 | 10443 | No |
| 8696 | Bayesian Scholarly Index Arbitrage Engine Ref-48 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1052 | 11672 | No |
| 8730 | Bayesian Scholarly Index Arbitrage Engine Ref-144 | Operator theory / Koopman spectral expansion / ETF allocation | 4653 | 10736 | No |
| 8807 | Bayesian Scholarly Index Arbitrage Engine Ref-336 | Koopman operator / Model predictive control / ETF rebalancing | 5840 | 10745 | No |
| 8846 | Bayesian Scholarly Index Arbitrage Engine Ref-432 | Persistence landscapes / Topological contours / Equity index | 1080 | 10749 | No |
| 8887 | Bayesian Scholarly Index Arbitrage Engine Ref-528 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1086 | 11675 | No |
| 8921 | Bayesian Scholarly Index Arbitrage Engine Ref-624 | Operator theory / Koopman spectral expansion / ETF allocation | 4680 | 10755 | No |
| 8998 | Bayesian Scholarly Index Arbitrage Engine Ref-816 | Koopman operator / Model predictive control / ETF rebalancing | 5865 | 10764 | No |
| 9037 | Bayesian Scholarly Index Arbitrage Engine Ref-912 | Persistence landscapes / Topological contours / Equity index | 1114 | 10768 | No |
| 9091 | Bayesian Scholarly Index Arbitrage Engine Sys-48 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1121 | 11678 | No |
| 9128 | Bayesian Scholarly Index Arbitrage Engine Sys-144 | Operator theory / Koopman spectral expansion / ETF allocation | 4710 | 10777 | No |
| 9208 | Bayesian Scholarly Index Arbitrage Engine Sys-336 | Koopman operator / Model predictive control / ETF rebalancing | 5890 | 10787 | No |
| 9243 | Bayesian Scholarly Index Arbitrage Engine Sys-432 | Persistence landscapes / Topological contours / Equity index | 1146 | 10791 | No |
| 9278 | Bayesian Scholarly Index Arbitrage Engine Sys-528 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1151 | 11681 | No |
| 9315 | Bayesian Scholarly Index Arbitrage Engine Sys-624 | Operator theory / Koopman spectral expansion / ETF allocation | 4741 | 10800 | No |
| 9395 | Bayesian Scholarly Index Arbitrage Engine Sys-816 | Koopman operator / Model predictive control / ETF rebalancing | 5910 | 10810 | No |
| 9430 | Bayesian Scholarly Index Arbitrage Engine Sys-912 | Persistence landscapes / Topological contours / Equity index | 1176 | 10814 | No |
| 9465 | Bayesian Scholarly Index Arbitrage Engine Sys-1008 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1181 | 11684 | No |
| 9502 | Bayesian Scholarly Index Arbitrage Engine Sys-1104 | Operator theory / Koopman spectral expansion / ETF allocation | 4772 | 10823 | No |
| 9582 | Bayesian Scholarly Index Arbitrage Engine Sys-1296 | Koopman operator / Model predictive control / ETF rebalancing | 5930 | 10833 | No |
| 9617 | Bayesian Scholarly Index Arbitrage Engine Sys-1392 | Persistence landscapes / Topological contours / Equity index | 1206 | 10837 | No |
| 9652 | Bayesian Scholarly Index Arbitrage Engine Sys-1488 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1211 | 11687 | No |
| 9689 | Bayesian Scholarly Index Arbitrage Engine Sys-1584 | Operator theory / Koopman spectral expansion / ETF allocation | 4803 | 10846 | No |
| 9769 | Bayesian Scholarly Index Arbitrage Engine Sys-1776 | Koopman operator / Model predictive control / ETF rebalancing | 5950 | 10856 | No |
| 9804 | Bayesian Scholarly Index Arbitrage Engine Sys-1872 | Persistence landscapes / Topological contours / Equity index | 1236 | 10860 | No |
| 9839 | Bayesian Scholarly Index Arbitrage Engine Sys-1968 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1241 | 11690 | No |
| 9870 | Bayesian Scholarly Index Arbitrage Engine Mod-48 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1246 | 11691 | No |
| 9906 | Bayesian Scholarly Index Arbitrage Engine Mod-144 | Operator theory / Koopman spectral expansion / ETF allocation | 4839 | 10871 | No |
| 9988 | Bayesian Scholarly Index Arbitrage Engine Mod-336 | Koopman operator / Model predictive control / ETF rebalancing | 5977 | 10879 | No |
| 10025 | Bayesian Scholarly Index Arbitrage Engine Mod-432 | Persistence landscapes / Topological contours / Equity index | 1271 | 10883 | No |
| 10061 | Bayesian Scholarly Index Arbitrage Engine Mod-528 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1277 | 11694 | No |
| 10097 | Bayesian Scholarly Index Arbitrage Engine Mod-624 | Operator theory / Koopman spectral expansion / ETF allocation | 4866 | 10890 | No |
| 10179 | Bayesian Scholarly Index Arbitrage Engine Mod-816 | Koopman operator / Model predictive control / ETF rebalancing | 6001 | 10898 | No |
| 10216 | Bayesian Scholarly Index Arbitrage Engine Mod-912 | Persistence landscapes / Topological contours / Equity index | 1302 | 10902 | No |
| 10252 | Bayesian Scholarly Index Arbitrage Engine Mod-1008 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1308 | 11697 | No |
| 10288 | Bayesian Scholarly Index Arbitrage Engine Mod-1104 | Operator theory / Koopman spectral expansion / ETF allocation | 4893 | 10909 | No |
| 10370 | Bayesian Scholarly Index Arbitrage Engine Mod-1296 | Koopman operator / Model predictive control / ETF rebalancing | 6025 | 10917 | No |
| 10407 | Bayesian Scholarly Index Arbitrage Engine Mod-1392 | Persistence landscapes / Topological contours / Equity index | 1333 | 10921 | No |
| 10443 | Bayesian Scholarly Index Arbitrage Engine Mod-1488 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1339 | 11700 | No |
| 10479 | Bayesian Scholarly Index Arbitrage Engine Mod-1584 | Operator theory / Koopman spectral expansion / ETF allocation | 4920 | 10928 | No |
| 10561 | Bayesian Scholarly Index Arbitrage Engine Mod-1776 | Koopman operator / Model predictive control / ETF rebalancing | 6049 | 10936 | No |
| 10598 | Bayesian Scholarly Index Arbitrage Engine Mod-1872 | Persistence landscapes / Topological contours / Equity index | 1364 | 10940 | No |
| 10634 | Bayesian Scholarly Index Arbitrage Engine Mod-1968 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1370 | 11703 | No |
| 10670 | Bayesian Scholarly Index Arbitrage Engine Mod-2064 | Operator theory / Koopman spectral expansion / ETF allocation | 4947 | 10947 | No |
| 10752 | Bayesian Scholarly Index Arbitrage Engine Mod-2256 | Koopman operator / Model predictive control / ETF rebalancing | 6073 | 10955 | No |
| 10789 | Bayesian Scholarly Index Arbitrage Engine Mod-2352 | Persistence landscapes / Topological contours / Equity index | 1395 | 10959 | No |
| 10825 | Bayesian Scholarly Index Arbitrage Engine Mod-2448 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1401 | 11706 | No |
| 10861 | Bayesian Scholarly Index Arbitrage Engine Mod-2544 | Operator theory / Koopman spectral expansion / ETF allocation | 4974 | 10966 | No |
| 10943 | Bayesian Scholarly Index Arbitrage Engine Mod-2736 | Koopman operator / Model predictive control / ETF rebalancing | 6097 | 10974 | No |
| 10980 | Bayesian Scholarly Index Arbitrage Engine Mod-2832 | Persistence landscapes / Topological contours / Equity index | 1426 | 10978 | No |
| 11016 | Bayesian Scholarly Index Arbitrage Engine Mod-2928 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1432 | 11709 | No |
| 11052 | Bayesian Scholarly Index Arbitrage Engine Mod-3024 | Operator theory / Koopman spectral expansion / ETF allocation | 5001 | 10985 | No |
| 11134 | Bayesian Scholarly Index Arbitrage Engine Mod-3216 | Koopman operator / Model predictive control / ETF rebalancing | 6121 | 10993 | No |
| 11171 | Bayesian Scholarly Index Arbitrage Engine Mod-3312 | Persistence landscapes / Topological contours / Equity index | 1457 | 10997 | No |
| 11207 | Bayesian Scholarly Index Arbitrage Engine Mod-3408 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1463 | 11712 | No |
| 11243 | Bayesian Scholarly Index Arbitrage Engine Mod-3504 | Operator theory / Koopman spectral expansion / ETF allocation | 5028 | 11004 | No |
| 11325 | Bayesian Scholarly Index Arbitrage Engine Mod-3696 | Koopman operator / Model predictive control / ETF rebalancing | 6145 | 11012 | No |
| 11362 | Bayesian Scholarly Index Arbitrage Engine Mod-3792 | Persistence landscapes / Topological contours / Equity index | 1488 | 11016 | No |
| 11398 | Bayesian Scholarly Index Arbitrage Engine Mod-3888 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1494 | 11715 | No |
| 11434 | Bayesian Scholarly Index Arbitrage Engine Mod-3984 | Operator theory / Koopman spectral expansion / ETF allocation | 5055 | 11023 | No |
| 11462 | Bayesian Scholarly Index Arbitrage Engine Eng-48 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1502 | 11716 | No |
| 11502 | Bayesian Scholarly Index Arbitrage Engine Eng-144 | Operator theory / Koopman spectral expansion / ETF allocation | 5063 | 11029 | No |
| 11574 | Bayesian Scholarly Index Arbitrage Engine Eng-336 | Koopman operator / Model predictive control / ETF rebalancing | 6175 | 11037 | No |
| 11616 | Bayesian Scholarly Index Arbitrage Engine Eng-432 | Persistence landscapes / Topological contours / Equity index | 1527 | 11040 | No |
| 11653 | Bayesian Scholarly Index Arbitrage Engine Eng-528 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1532 | 11719 | No |
| 11693 | Bayesian Scholarly Index Arbitrage Engine Eng-624 | Operator theory / Koopman spectral expansion / ETF allocation | 5088 | 11048 | No |
| 11765 | Bayesian Scholarly Index Arbitrage Engine Eng-816 | Koopman operator / Model predictive control / ETF rebalancing | 6197 | 11056 | No |
| 11807 | Bayesian Scholarly Index Arbitrage Engine Eng-912 | Persistence landscapes / Topological contours / Equity index | 1557 | 11059 | No |
| 11844 | Bayesian Scholarly Index Arbitrage Engine Eng-1008 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1562 | 11722 | No |
| 11884 | Bayesian Scholarly Index Arbitrage Engine Eng-1104 | Operator theory / Koopman spectral expansion / ETF allocation | 5113 | 11067 | No |
| 11956 | Bayesian Scholarly Index Arbitrage Engine Eng-1296 | Koopman operator / Model predictive control / ETF rebalancing | 6219 | 11075 | No |
| 11998 | Bayesian Scholarly Index Arbitrage Engine Eng-1392 | Persistence landscapes / Topological contours / Equity index | 1587 | 11078 | No |
| 12035 | Bayesian Scholarly Index Arbitrage Engine Eng-1488 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1592 | 11725 | No |
| 12075 | Bayesian Scholarly Index Arbitrage Engine Eng-1584 | Operator theory / Koopman spectral expansion / ETF allocation | 5138 | 11086 | No |
| 12147 | Bayesian Scholarly Index Arbitrage Engine Eng-1776 | Koopman operator / Model predictive control / ETF rebalancing | 6241 | 11094 | No |
| 12189 | Bayesian Scholarly Index Arbitrage Engine Eng-1872 | Persistence landscapes / Topological contours / Equity index | 1617 | 11097 | No |
| 12226 | Bayesian Scholarly Index Arbitrage Engine Eng-1968 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1622 | 11728 | No |
| 12266 | Bayesian Scholarly Index Arbitrage Engine Eng-2064 | Operator theory / Koopman spectral expansion / ETF allocation | 5163 | 11105 | No |
| 12338 | Bayesian Scholarly Index Arbitrage Engine Eng-2256 | Koopman operator / Model predictive control / ETF rebalancing | 6263 | 11113 | No |
| 12380 | Bayesian Scholarly Index Arbitrage Engine Eng-2352 | Persistence landscapes / Topological contours / Equity index | 1647 | 11116 | No |
| 12417 | Bayesian Scholarly Index Arbitrage Engine Eng-2448 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1652 | 11731 | No |
| 12457 | Bayesian Scholarly Index Arbitrage Engine Eng-2544 | Operator theory / Koopman spectral expansion / ETF allocation | 5188 | 11124 | No |
| 12529 | Bayesian Scholarly Index Arbitrage Engine Eng-2736 | Koopman operator / Model predictive control / ETF rebalancing | 6285 | 11132 | No |
| 12571 | Bayesian Scholarly Index Arbitrage Engine Eng-2832 | Persistence landscapes / Topological contours / Equity index | 1677 | 11135 | No |
| 12608 | Bayesian Scholarly Index Arbitrage Engine Eng-2928 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1682 | 11734 | No |
| 12648 | Bayesian Scholarly Index Arbitrage Engine Eng-3024 | Operator theory / Koopman spectral expansion / ETF allocation | 5213 | 11143 | No |
| 12720 | Bayesian Scholarly Index Arbitrage Engine Eng-3216 | Koopman operator / Model predictive control / ETF rebalancing | 6307 | 11151 | No |
| 12762 | Bayesian Scholarly Index Arbitrage Engine Eng-3312 | Persistence landscapes / Topological contours / Equity index | 1707 | 11154 | No |
| 12799 | Bayesian Scholarly Index Arbitrage Engine Eng-3408 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1712 | 11737 | No |
| 12839 | Bayesian Scholarly Index Arbitrage Engine Eng-3504 | Operator theory / Koopman spectral expansion / ETF allocation | 5238 | 11162 | No |
| 12911 | Bayesian Scholarly Index Arbitrage Engine Eng-3696 | Koopman operator / Model predictive control / ETF rebalancing | 6329 | 11170 | No |
| 12953 | Bayesian Scholarly Index Arbitrage Engine Eng-3792 | Persistence landscapes / Topological contours / Equity index | 1737 | 11173 | No |
| 12990 | Bayesian Scholarly Index Arbitrage Engine Eng-3888 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1742 | 11740 | No |
| 13030 | Bayesian Scholarly Index Arbitrage Engine Eng-3984 | Operator theory / Koopman spectral expansion / ETF allocation | 5263 | 11181 | No |
| 13102 | Bayesian Scholarly Index Arbitrage Engine Eng-4176 | Koopman operator / Model predictive control / ETF rebalancing | 6351 | 11189 | No |
| 13144 | Bayesian Scholarly Index Arbitrage Engine Eng-4272 | Persistence landscapes / Topological contours / Equity index | 1767 | 11192 | No |
| 13181 | Bayesian Scholarly Index Arbitrage Engine Eng-4368 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1772 | 11743 | No |
| 13221 | Bayesian Scholarly Index Arbitrage Engine Eng-4464 | Operator theory / Koopman spectral expansion / ETF allocation | 5288 | 11200 | No |
| 13293 | Bayesian Scholarly Index Arbitrage Engine Eng-4656 | Koopman operator / Model predictive control / ETF rebalancing | 6373 | 11208 | No |
| 13335 | Bayesian Scholarly Index Arbitrage Engine Eng-4752 | Persistence landscapes / Topological contours / Equity index | 1797 | 11211 | No |
| 13372 | Bayesian Scholarly Index Arbitrage Engine Eng-4848 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1802 | 11746 | No |
| 13412 | Bayesian Scholarly Index Arbitrage Engine Eng-4944 | Operator theory / Koopman spectral expansion / ETF allocation | 5313 | 11219 | No |
| 13484 | Bayesian Scholarly Index Arbitrage Engine Eng-5136 | Koopman operator / Model predictive control / ETF rebalancing | 6395 | 11227 | No |
| 13526 | Bayesian Scholarly Index Arbitrage Engine Eng-5232 | Persistence landscapes / Topological contours / Equity index | 1827 | 11230 | No |
| 13563 | Bayesian Scholarly Index Arbitrage Engine Eng-5328 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1832 | 11749 | No |
| 13603 | Bayesian Scholarly Index Arbitrage Engine Eng-5424 | Operator theory / Koopman spectral expansion / ETF allocation | 5338 | 11238 | No |
| 13675 | Bayesian Scholarly Index Arbitrage Engine Eng-5616 | Koopman operator / Model predictive control / ETF rebalancing | 6417 | 11246 | No |
| 13717 | Bayesian Scholarly Index Arbitrage Engine Eng-5712 | Persistence landscapes / Topological contours / Equity index | 1857 | 11249 | No |
| 13754 | Bayesian Scholarly Index Arbitrage Engine Eng-5808 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1862 | 11752 | No |
| 13794 | Bayesian Scholarly Index Arbitrage Engine Eng-5904 | Operator theory / Koopman spectral expansion / ETF allocation | 5363 | 11257 | No |
