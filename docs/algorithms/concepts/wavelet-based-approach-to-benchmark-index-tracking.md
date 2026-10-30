# Wavelet-based approach to benchmark index tracking

**Concept page** · shared by **139** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,748) ·
researched 2026-10-30

| | |
|---|---|
| Task | Benchmark index tracking |
| Method | Wavelet multiscale decomposition |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** The project buys the index as an ETF; replicating it from constituents adds cost and tracking error for nothing. |
| Implemented in volatility-ai | Nothing. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK60 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Wavelet Scholarly Index
Tracking Optimizer Ref-220") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Choose weights to track a target index while controlling tracking error,
turnover and costs; an allocation objective, not a return edge. The
wavelet version decomposes series by time scale and acts scale by scale.
I found no study of this method on this task.

## The CSV's description

Proposed wavelet-based approach to benchmark index tracking: Choose
portfolio weights to track a target index while controlling tracking
error, turnover, liquidity constraints, and transaction costs; this is
an allocation objective, not inherently a return-prediction edge. This
is a concept-level interpretation of the title, not a complete trading
specification: the exact model inputs/target, calibration, entry/exit or
rebalance rules, and position sizing are not fully defined here.

## Evidence

* **Benidis, Feng & Palomar (2018), "Sparse Portfolios for
  High-Dimensional Financial Index Tracking," *IEEE Transactions on
  Signal Processing* 66(1):** track an index with a few constituents by
  penalised tracking-error minimisation. (Abstract.)

## Against, and failure modes

* Tracking with a subset of constituents adds tracking error and cost
  that buying the index ETF avoids.
* Wavelet filters see future data at the series' edge unless made
  causal, a common source of lookahead.

## Fit with volatility-ai

The project holds the index as an ETF, so tracking it with a stock
subset adds cost for nothing.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Benidis, K., Feng, Y., Palomar, D. P. (2018). *IEEE Transactions on
  Signal Processing* 66(1), 155–170. Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 1748 | Wavelet Scholarly Index Tracking Optimizer Ref-220 | Fractional order / Multi-scale ETF momentum | 2141 | 466 | No |
| 1803 | Wavelet Scholarly Index Tracking Optimizer Ref-700 | Fractional order / Multi-scale ETF momentum | 2173 | 477 | No |
| 1877 | Wavelet Scholarly Index Tracking Optimizer Sys-380 | Fractional order / Multi-scale ETF momentum | 3941 | 2214 | No |
| 1926 | Wavelet Scholarly Index Tracking Optimizer Sys-860 | Fractional order / Multi-scale ETF momentum | 3970 | 2233 | No |
| 1975 | Wavelet Scholarly Index Tracking Optimizer Sys-1340 | Fractional order / Multi-scale ETF momentum | 3999 | 2252 | No |
| 2024 | Wavelet Scholarly Index Tracking Optimizer Sys-1820 | Fractional order / Multi-scale ETF momentum | 4028 | 2271 | No |
| 2066 | Wavelet Scholarly Index Tracking Optimizer Mod-260 | Fractional order / Multi-scale ETF momentum | 4053 | 2291 | No |
| 2119 | Wavelet Scholarly Index Tracking Optimizer Mod-740 | Fractional order / Multi-scale ETF momentum | 4079 | 2314 | No |
| 2172 | Wavelet Scholarly Index Tracking Optimizer Mod-1220 | Fractional order / Multi-scale ETF momentum | 4105 | 2337 | No |
| 2225 | Wavelet Scholarly Index Tracking Optimizer Mod-1700 | Fractional order / Multi-scale ETF momentum | 4131 | 2360 | No |
| 2278 | Wavelet Scholarly Index Tracking Optimizer Mod-2180 | Fractional order / Multi-scale ETF momentum | 4157 | 2383 | No |
| 2331 | Wavelet Scholarly Index Tracking Optimizer Mod-2660 | Fractional order / Multi-scale ETF momentum | 4183 | 2406 | No |
| 2384 | Wavelet Scholarly Index Tracking Optimizer Mod-3140 | Fractional order / Multi-scale ETF momentum | 4209 | 2429 | No |
| 2437 | Wavelet Scholarly Index Tracking Optimizer Mod-3620 | Fractional order / Multi-scale ETF momentum | 4235 | 2452 | No |
| 2522 | Wavelet Scholarly Index Tracking Optimizer Eng-380 | Fractional order / Multi-scale ETF momentum | 4278 | 2488 | No |
| 2577 | Wavelet Scholarly Index Tracking Optimizer Eng-860 | Fractional order / Multi-scale ETF momentum | 4304 | 2511 | No |
| 2632 | Wavelet Scholarly Index Tracking Optimizer Eng-1340 | Fractional order / Multi-scale ETF momentum | 4330 | 2534 | No |
| 2687 | Wavelet Scholarly Index Tracking Optimizer Eng-1820 | Fractional order / Multi-scale ETF momentum | 4356 | 2557 | No |
| 2742 | Wavelet Scholarly Index Tracking Optimizer Eng-2300 | Fractional order / Multi-scale ETF momentum | 4382 | 2580 | No |
| 2797 | Wavelet Scholarly Index Tracking Optimizer Eng-2780 | Fractional order / Multi-scale ETF momentum | 4408 | 2603 | No |
| 2852 | Wavelet Scholarly Index Tracking Optimizer Eng-3260 | Fractional order / Multi-scale ETF momentum | 4434 | 2626 | No |
| 2907 | Wavelet Scholarly Index Tracking Optimizer Eng-3740 | Fractional order / Multi-scale ETF momentum | 4460 | 2649 | No |
| 2962 | Wavelet Scholarly Index Tracking Optimizer Eng-4220 | Fractional order / Multi-scale ETF momentum | 4486 | 2672 | No |
| 3017 | Wavelet Scholarly Index Tracking Optimizer Eng-4700 | Fractional order / Multi-scale ETF momentum | 4512 | 2695 | No |
| 3072 | Wavelet Scholarly Index Tracking Optimizer Eng-5180 | Fractional order / Multi-scale ETF momentum | 4538 | 2718 | No |
| 3127 | Wavelet Scholarly Index Tracking Optimizer Eng-5660 | Fractional order / Multi-scale ETF momentum | 4564 | 2741 | No |
| 8494 | Wavelet Scholarly Index Tracking Optimizer Alpha-48 | Point processes / Hawkes kernels / Stock liquidity jumps | 1004 | 6500 | No |
| 8534 | Wavelet Scholarly Index Tracking Optimizer Alpha-148 | Point processes / Hawkes kernels / Stock liquidity jumps | 1015 | 2932 | No |
| 8574 | Wavelet Scholarly Index Tracking Optimizer Alpha-248 | Point processes / Hawkes kernels / Stock liquidity jumps | 10733 | 11869 | No |
| 8614 | Wavelet Scholarly Index Tracking Optimizer Alpha-348 | Point processes / Hawkes kernels / Stock liquidity jumps | 1033 | 6519 | No |
| 8654 | Wavelet Scholarly Index Tracking Optimizer Alpha-448 | Point processes / Hawkes kernels / Stock liquidity jumps | 1044 | 3000 | No |
| 8687 | Wavelet Scholarly Index Tracking Optimizer Ref-28 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1050 | 3017 | No |
| 8724 | Wavelet Scholarly Index Tracking Optimizer Ref-124 | Operator theory / Koopman spectral expansion / ETF allocation | 3867 | 1015 | No |
| 8799 | Wavelet Scholarly Index Tracking Optimizer Ref-316 | Koopman operator / Model predictive control / ETF rebalancing | 3878 | 3088 | No |
| 8839 | Wavelet Scholarly Index Tracking Optimizer Ref-412 | Persistence landscapes / Topological contours / Equity index | 5845 | 11314 | No |
| 8878 | Wavelet Scholarly Index Tracking Optimizer Ref-508 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1084 | 3134 | No |
| 8915 | Wavelet Scholarly Index Tracking Optimizer Ref-604 | Operator theory / Koopman spectral expansion / ETF allocation | 3894 | 1050 | No |
| 8990 | Wavelet Scholarly Index Tracking Optimizer Ref-796 | Koopman operator / Model predictive control / ETF rebalancing | 3905 | 3205 | No |
| 9030 | Wavelet Scholarly Index Tracking Optimizer Ref-892 | Persistence landscapes / Topological contours / Equity index | 5870 | 11335 | No |
| 9069 | Wavelet Scholarly Index Tracking Optimizer Ref-988 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1118 | 3251 | No |
| 9110 | Wavelet Scholarly Index Tracking Optimizer Sys-92 | Persistence landscapes / Topological contours / Equity index | 2202 | 3273 | No |
| 9146 | Wavelet Scholarly Index Tracking Optimizer Sys-188 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10747 | 11930 | No |
| 9184 | Wavelet Scholarly Index Tracking Optimizer Sys-284 | Operator theory / Koopman spectral expansion / ETF allocation | 2221 | 3314 | No |
| 9260 | Wavelet Scholarly Index Tracking Optimizer Sys-476 | Koopman operator / Model predictive control / ETF rebalancing | 12079 | 13742 | No |
| 9297 | Wavelet Scholarly Index Tracking Optimizer Sys-572 | Persistence landscapes / Topological contours / Equity index | 2249 | 3368 | No |
| 9333 | Wavelet Scholarly Index Tracking Optimizer Sys-668 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10755 | 11953 | No |
| 9371 | Wavelet Scholarly Index Tracking Optimizer Sys-764 | Operator theory / Koopman spectral expansion / ETF allocation | 2268 | 3409 | No |
| 9447 | Wavelet Scholarly Index Tracking Optimizer Sys-956 | Koopman operator / Model predictive control / ETF rebalancing | 12089 | 13751 | No |
| 9484 | Wavelet Scholarly Index Tracking Optimizer Sys-1052 | Persistence landscapes / Topological contours / Equity index | 2296 | 3463 | No |
| 9520 | Wavelet Scholarly Index Tracking Optimizer Sys-1148 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10763 | 11976 | No |
| 9558 | Wavelet Scholarly Index Tracking Optimizer Sys-1244 | Operator theory / Koopman spectral expansion / ETF allocation | 2315 | 3504 | No |
| 9634 | Wavelet Scholarly Index Tracking Optimizer Sys-1436 | Koopman operator / Model predictive control / ETF rebalancing | 12099 | 13760 | No |
| 9671 | Wavelet Scholarly Index Tracking Optimizer Sys-1532 | Persistence landscapes / Topological contours / Equity index | 2343 | 3558 | No |
| 9707 | Wavelet Scholarly Index Tracking Optimizer Sys-1628 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10771 | 11999 | No |
| 9745 | Wavelet Scholarly Index Tracking Optimizer Sys-1724 | Operator theory / Koopman spectral expansion / ETF allocation | 2362 | 3599 | No |
| 9821 | Wavelet Scholarly Index Tracking Optimizer Sys-1916 | Koopman operator / Model predictive control / ETF rebalancing | 12109 | 13769 | No |
| 9878 | Wavelet Scholarly Index Tracking Optimizer Mod-68 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10777 | 12021 | No |
| 9914 | Wavelet Scholarly Index Tracking Optimizer Mod-164 | Operator theory / Koopman spectral expansion / ETF allocation | 2401 | 3682 | No |
| 9996 | Wavelet Scholarly Index Tracking Optimizer Mod-356 | Koopman operator / Model predictive control / ETF rebalancing | 12116 | 13779 | No |
| 10032 | Wavelet Scholarly Index Tracking Optimizer Mod-452 | Persistence landscapes / Topological contours / Equity index | 2424 | 3742 | No |
| 10069 | Wavelet Scholarly Index Tracking Optimizer Mod-548 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10780 | 12044 | No |
| 10105 | Wavelet Scholarly Index Tracking Optimizer Mod-644 | Operator theory / Koopman spectral expansion / ETF allocation | 2440 | 3777 | No |
| 10187 | Wavelet Scholarly Index Tracking Optimizer Mod-836 | Koopman operator / Model predictive control / ETF rebalancing | 12123 | 13788 | No |
| 10223 | Wavelet Scholarly Index Tracking Optimizer Mod-932 | Persistence landscapes / Topological contours / Equity index | 2463 | 3837 | No |
| 10260 | Wavelet Scholarly Index Tracking Optimizer Mod-1028 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10783 | 12067 | No |
| 10296 | Wavelet Scholarly Index Tracking Optimizer Mod-1124 | Operator theory / Koopman spectral expansion / ETF allocation | 2479 | 3872 | No |
| 10378 | Wavelet Scholarly Index Tracking Optimizer Mod-1316 | Koopman operator / Model predictive control / ETF rebalancing | 12130 | 13797 | No |
| 10414 | Wavelet Scholarly Index Tracking Optimizer Mod-1412 | Persistence landscapes / Topological contours / Equity index | 2502 | 3932 | No |
| 10451 | Wavelet Scholarly Index Tracking Optimizer Mod-1508 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10786 | 12090 | No |
| 10487 | Wavelet Scholarly Index Tracking Optimizer Mod-1604 | Operator theory / Koopman spectral expansion / ETF allocation | 2518 | 3967 | No |
| 10569 | Wavelet Scholarly Index Tracking Optimizer Mod-1796 | Koopman operator / Model predictive control / ETF rebalancing | 12137 | 13806 | No |
| 10605 | Wavelet Scholarly Index Tracking Optimizer Mod-1892 | Persistence landscapes / Topological contours / Equity index | 2541 | 4027 | No |
| 10642 | Wavelet Scholarly Index Tracking Optimizer Mod-1988 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10789 | 12113 | No |
| 10678 | Wavelet Scholarly Index Tracking Optimizer Mod-2084 | Operator theory / Koopman spectral expansion / ETF allocation | 2557 | 4062 | No |
| 10760 | Wavelet Scholarly Index Tracking Optimizer Mod-2276 | Koopman operator / Model predictive control / ETF rebalancing | 12144 | 13815 | No |
| 10796 | Wavelet Scholarly Index Tracking Optimizer Mod-2372 | Persistence landscapes / Topological contours / Equity index | 2580 | 4122 | No |
| 10833 | Wavelet Scholarly Index Tracking Optimizer Mod-2468 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10792 | 12136 | No |
| 10869 | Wavelet Scholarly Index Tracking Optimizer Mod-2564 | Operator theory / Koopman spectral expansion / ETF allocation | 2596 | 4157 | No |
| 10951 | Wavelet Scholarly Index Tracking Optimizer Mod-2756 | Koopman operator / Model predictive control / ETF rebalancing | 12151 | 13824 | No |
| 10987 | Wavelet Scholarly Index Tracking Optimizer Mod-2852 | Persistence landscapes / Topological contours / Equity index | 2619 | 4217 | No |
| 11024 | Wavelet Scholarly Index Tracking Optimizer Mod-2948 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10795 | 12159 | No |
| 11060 | Wavelet Scholarly Index Tracking Optimizer Mod-3044 | Operator theory / Koopman spectral expansion / ETF allocation | 2635 | 4252 | No |
| 11142 | Wavelet Scholarly Index Tracking Optimizer Mod-3236 | Koopman operator / Model predictive control / ETF rebalancing | 12158 | 13833 | No |
| 11178 | Wavelet Scholarly Index Tracking Optimizer Mod-3332 | Persistence landscapes / Topological contours / Equity index | 2658 | 4312 | No |
| 11215 | Wavelet Scholarly Index Tracking Optimizer Mod-3428 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10798 | 12182 | No |
| 11251 | Wavelet Scholarly Index Tracking Optimizer Mod-3524 | Operator theory / Koopman spectral expansion / ETF allocation | 2674 | 4347 | No |
| 11333 | Wavelet Scholarly Index Tracking Optimizer Mod-3716 | Koopman operator / Model predictive control / ETF rebalancing | 12165 | 13842 | No |
| 11369 | Wavelet Scholarly Index Tracking Optimizer Mod-3812 | Persistence landscapes / Topological contours / Equity index | 2697 | 4407 | No |
| 11406 | Wavelet Scholarly Index Tracking Optimizer Mod-3908 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10801 | 12205 | No |
| 11480 | Wavelet Scholarly Index Tracking Optimizer Eng-92 | Persistence landscapes / Topological contours / Equity index | 2719 | 4463 | No |
| 11519 | Wavelet Scholarly Index Tracking Optimizer Eng-188 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10803 | 12218 | No |
| 11556 | Wavelet Scholarly Index Tracking Optimizer Eng-284 | Operator theory / Koopman spectral expansion / ETF allocation | 2734 | 4500 | No |
| 11631 | Wavelet Scholarly Index Tracking Optimizer Eng-476 | Koopman operator / Model predictive control / ETF rebalancing | 12174 | 13855 | No |
| 11671 | Wavelet Scholarly Index Tracking Optimizer Eng-572 | Persistence landscapes / Topological contours / Equity index | 2757 | 4556 | No |
| 11710 | Wavelet Scholarly Index Tracking Optimizer Eng-668 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10807 | 12241 | No |
| 11747 | Wavelet Scholarly Index Tracking Optimizer Eng-764 | Operator theory / Koopman spectral expansion / ETF allocation | 2772 | 4593 | No |
| 11822 | Wavelet Scholarly Index Tracking Optimizer Eng-956 | Koopman operator / Model predictive control / ETF rebalancing | 12180 | 13864 | No |
| 11862 | Wavelet Scholarly Index Tracking Optimizer Eng-1052 | Persistence landscapes / Topological contours / Equity index | 2795 | 4649 | No |
| 11901 | Wavelet Scholarly Index Tracking Optimizer Eng-1148 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10811 | 12264 | No |
| 11938 | Wavelet Scholarly Index Tracking Optimizer Eng-1244 | Operator theory / Koopman spectral expansion / ETF allocation | 2810 | 4686 | No |
| 12013 | Wavelet Scholarly Index Tracking Optimizer Eng-1436 | Koopman operator / Model predictive control / ETF rebalancing | 12186 | 13873 | No |
| 12053 | Wavelet Scholarly Index Tracking Optimizer Eng-1532 | Persistence landscapes / Topological contours / Equity index | 2833 | 4742 | No |
| 12092 | Wavelet Scholarly Index Tracking Optimizer Eng-1628 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10815 | 12287 | No |
| 12129 | Wavelet Scholarly Index Tracking Optimizer Eng-1724 | Operator theory / Koopman spectral expansion / ETF allocation | 2848 | 4779 | No |
| 12204 | Wavelet Scholarly Index Tracking Optimizer Eng-1916 | Koopman operator / Model predictive control / ETF rebalancing | 12192 | 13882 | No |
| 12244 | Wavelet Scholarly Index Tracking Optimizer Eng-2012 | Persistence landscapes / Topological contours / Equity index | 2871 | 4835 | No |
| 12283 | Wavelet Scholarly Index Tracking Optimizer Eng-2108 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10819 | 12310 | No |
| 12320 | Wavelet Scholarly Index Tracking Optimizer Eng-2204 | Operator theory / Koopman spectral expansion / ETF allocation | 2886 | 4872 | No |
| 12395 | Wavelet Scholarly Index Tracking Optimizer Eng-2396 | Koopman operator / Model predictive control / ETF rebalancing | 12198 | 13891 | No |
| 12435 | Wavelet Scholarly Index Tracking Optimizer Eng-2492 | Persistence landscapes / Topological contours / Equity index | 2909 | 4928 | No |
| 12474 | Wavelet Scholarly Index Tracking Optimizer Eng-2588 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10823 | 12333 | No |
| 12511 | Wavelet Scholarly Index Tracking Optimizer Eng-2684 | Operator theory / Koopman spectral expansion / ETF allocation | 2924 | 4965 | No |
| 12586 | Wavelet Scholarly Index Tracking Optimizer Eng-2876 | Koopman operator / Model predictive control / ETF rebalancing | 12204 | 13900 | No |
| 12626 | Wavelet Scholarly Index Tracking Optimizer Eng-2972 | Persistence landscapes / Topological contours / Equity index | 2947 | 5021 | No |
| 12665 | Wavelet Scholarly Index Tracking Optimizer Eng-3068 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10827 | 12356 | No |
| 12702 | Wavelet Scholarly Index Tracking Optimizer Eng-3164 | Operator theory / Koopman spectral expansion / ETF allocation | 2962 | 5058 | No |
| 12777 | Wavelet Scholarly Index Tracking Optimizer Eng-3356 | Koopman operator / Model predictive control / ETF rebalancing | 12210 | 13909 | No |
| 12817 | Wavelet Scholarly Index Tracking Optimizer Eng-3452 | Persistence landscapes / Topological contours / Equity index | 2985 | 5114 | No |
| 12856 | Wavelet Scholarly Index Tracking Optimizer Eng-3548 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10831 | 12379 | No |
| 12893 | Wavelet Scholarly Index Tracking Optimizer Eng-3644 | Operator theory / Koopman spectral expansion / ETF allocation | 3000 | 5151 | No |
| 12968 | Wavelet Scholarly Index Tracking Optimizer Eng-3836 | Koopman operator / Model predictive control / ETF rebalancing | 12216 | 13918 | No |
| 13008 | Wavelet Scholarly Index Tracking Optimizer Eng-3932 | Persistence landscapes / Topological contours / Equity index | 3023 | 5207 | No |
| 13047 | Wavelet Scholarly Index Tracking Optimizer Eng-4028 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10835 | 12402 | No |
| 13084 | Wavelet Scholarly Index Tracking Optimizer Eng-4124 | Operator theory / Koopman spectral expansion / ETF allocation | 3038 | 5244 | No |
| 13159 | Wavelet Scholarly Index Tracking Optimizer Eng-4316 | Koopman operator / Model predictive control / ETF rebalancing | 12222 | 13927 | No |
| 13199 | Wavelet Scholarly Index Tracking Optimizer Eng-4412 | Persistence landscapes / Topological contours / Equity index | 3061 | 5300 | No |
| 13238 | Wavelet Scholarly Index Tracking Optimizer Eng-4508 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10839 | 12425 | No |
| 13275 | Wavelet Scholarly Index Tracking Optimizer Eng-4604 | Operator theory / Koopman spectral expansion / ETF allocation | 3076 | 5337 | No |
| 13350 | Wavelet Scholarly Index Tracking Optimizer Eng-4796 | Koopman operator / Model predictive control / ETF rebalancing | 12228 | 13936 | No |
| 13390 | Wavelet Scholarly Index Tracking Optimizer Eng-4892 | Persistence landscapes / Topological contours / Equity index | 3099 | 5393 | No |
| 13429 | Wavelet Scholarly Index Tracking Optimizer Eng-4988 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10843 | 12448 | No |
| 13466 | Wavelet Scholarly Index Tracking Optimizer Eng-5084 | Operator theory / Koopman spectral expansion / ETF allocation | 3114 | 5430 | No |
| 13541 | Wavelet Scholarly Index Tracking Optimizer Eng-5276 | Koopman operator / Model predictive control / ETF rebalancing | 12234 | 13945 | No |
| 13581 | Wavelet Scholarly Index Tracking Optimizer Eng-5372 | Persistence landscapes / Topological contours / Equity index | 3137 | 5486 | No |
| 13620 | Wavelet Scholarly Index Tracking Optimizer Eng-5468 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10847 | 12471 | No |
| 13657 | Wavelet Scholarly Index Tracking Optimizer Eng-5564 | Operator theory / Koopman spectral expansion / ETF allocation | 3152 | 5523 | No |
| 13732 | Wavelet Scholarly Index Tracking Optimizer Eng-5756 | Koopman operator / Model predictive control / ETF rebalancing | 12240 | 13954 | No |
| 13772 | Wavelet Scholarly Index Tracking Optimizer Eng-5852 | Persistence landscapes / Topological contours / Equity index | 3175 | 5579 | No |
| 13811 | Wavelet Scholarly Index Tracking Optimizer Eng-5948 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10851 | 12494 | No |
