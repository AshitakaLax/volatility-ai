# Dynamical-systems/geometric approach to benchmark index tracking

**Concept page** · shared by **136** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,772) ·
researched 2026-10-30

| | |
|---|---|
| Task | Benchmark index tracking |
| Method | Dynamical-systems / geometric (e.g. Hamiltonian) models |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** The project buys the index as an ETF; replicating it from constituents adds cost and tracking error for nothing. |
| Implemented in volatility-ai | Nothing. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK60 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Symplectic Scholarly Index
Tracking Optimizer Ref-460") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Choose weights to track a target index while controlling tracking error,
turnover and costs; an allocation objective, not a return edge. The
dynamical-systems version models the market as a Hamiltonian or
delay-differential system and acts on its fitted state. I found no study
of this method on this task.

## The CSV's description

Proposed dynamical-systems/geometric approach to benchmark index
tracking: Choose portfolio weights to track a target index while
controlling tracking error, turnover, liquidity constraints, and
transaction costs; this is an allocation objective, not inherently a
return-prediction edge. This is a concept-level interpretation of the
title, not a complete trading specification: the exact model
inputs/target, calibration, entry/exit or rebalance rules, and position
sizing are not fully defined here.

## Evidence

* **Benidis, Feng & Palomar (2018), "Sparse Portfolios for
  High-Dimensional Financial Index Tracking," *IEEE Transactions on
  Signal Processing* 66(1):** track an index with a few constituents by
  penalised tracking-error minimisation. (Abstract.)

## Against, and failure modes

* Tracking with a subset of constituents adds tracking error and cost
  that buying the index ETF avoids.
* The physics is imposed, not estimated from evidence; no trading study
  found.

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
| 1772 | Symplectic Scholarly Index Tracking Optimizer Ref-460 | Fractional order / Multi-scale ETF momentum | 2157 | 472 | No |
| 1827 | Symplectic Scholarly Index Tracking Optimizer Ref-940 | Fractional order / Multi-scale ETF momentum | 2189 | 483 | No |
| 1852 | Symplectic Scholarly Index Tracking Optimizer Sys-140 | Fractional order / Multi-scale ETF momentum | 3926 | 2205 | No |
| 1901 | Symplectic Scholarly Index Tracking Optimizer Sys-620 | Fractional order / Multi-scale ETF momentum | 3955 | 2224 | No |
| 1950 | Symplectic Scholarly Index Tracking Optimizer Sys-1100 | Fractional order / Multi-scale ETF momentum | 3984 | 2243 | No |
| 1999 | Symplectic Scholarly Index Tracking Optimizer Sys-1580 | Fractional order / Multi-scale ETF momentum | 4013 | 2262 | No |
| 2042 | Symplectic Scholarly Index Tracking Optimizer Mod-20 | Fractional order / Multi-scale ETF momentum | 4040 | 2279 | No |
| 2095 | Symplectic Scholarly Index Tracking Optimizer Mod-500 | Fractional order / Multi-scale ETF momentum | 4066 | 2302 | No |
| 2148 | Symplectic Scholarly Index Tracking Optimizer Mod-980 | Fractional order / Multi-scale ETF momentum | 4092 | 2325 | No |
| 2201 | Symplectic Scholarly Index Tracking Optimizer Mod-1460 | Fractional order / Multi-scale ETF momentum | 4118 | 2348 | No |
| 2254 | Symplectic Scholarly Index Tracking Optimizer Mod-1940 | Fractional order / Multi-scale ETF momentum | 4144 | 2371 | No |
| 2307 | Symplectic Scholarly Index Tracking Optimizer Mod-2420 | Fractional order / Multi-scale ETF momentum | 4170 | 2394 | No |
| 2360 | Symplectic Scholarly Index Tracking Optimizer Mod-2900 | Fractional order / Multi-scale ETF momentum | 4196 | 2417 | No |
| 2413 | Symplectic Scholarly Index Tracking Optimizer Mod-3380 | Fractional order / Multi-scale ETF momentum | 4222 | 2440 | No |
| 2466 | Symplectic Scholarly Index Tracking Optimizer Mod-3860 | Fractional order / Multi-scale ETF momentum | 4248 | 2463 | No |
| 2495 | Symplectic Scholarly Index Tracking Optimizer Eng-140 | Fractional order / Multi-scale ETF momentum | 4265 | 2477 | No |
| 2550 | Symplectic Scholarly Index Tracking Optimizer Eng-620 | Fractional order / Multi-scale ETF momentum | 4291 | 2500 | No |
| 2605 | Symplectic Scholarly Index Tracking Optimizer Eng-1100 | Fractional order / Multi-scale ETF momentum | 4317 | 2523 | No |
| 2660 | Symplectic Scholarly Index Tracking Optimizer Eng-1580 | Fractional order / Multi-scale ETF momentum | 4343 | 2546 | No |
| 2715 | Symplectic Scholarly Index Tracking Optimizer Eng-2060 | Fractional order / Multi-scale ETF momentum | 4369 | 2569 | No |
| 2770 | Symplectic Scholarly Index Tracking Optimizer Eng-2540 | Fractional order / Multi-scale ETF momentum | 4395 | 2592 | No |
| 2825 | Symplectic Scholarly Index Tracking Optimizer Eng-3020 | Fractional order / Multi-scale ETF momentum | 4421 | 2615 | No |
| 2880 | Symplectic Scholarly Index Tracking Optimizer Eng-3500 | Fractional order / Multi-scale ETF momentum | 4447 | 2638 | No |
| 2935 | Symplectic Scholarly Index Tracking Optimizer Eng-3980 | Fractional order / Multi-scale ETF momentum | 4473 | 2661 | No |
| 2990 | Symplectic Scholarly Index Tracking Optimizer Eng-4460 | Fractional order / Multi-scale ETF momentum | 4499 | 2684 | No |
| 3045 | Symplectic Scholarly Index Tracking Optimizer Eng-4940 | Fractional order / Multi-scale ETF momentum | 4525 | 2707 | No |
| 3100 | Symplectic Scholarly Index Tracking Optimizer Eng-5420 | Fractional order / Multi-scale ETF momentum | 4551 | 2730 | No |
| 3155 | Symplectic Scholarly Index Tracking Optimizer Eng-5900 | Fractional order / Multi-scale ETF momentum | 4577 | 2753 | No |
| 8706 | Symplectic Scholarly Index Tracking Optimizer Ref-76 | Koopman operator / Model predictive control / ETF rebalancing | 3864 | 3029 | No |
| 8744 | Symplectic Scholarly Index Tracking Optimizer Ref-172 | Persistence landscapes / Topological contours / Equity index | 5832 | 11302 | No |
| 8781 | Symplectic Scholarly Index Tracking Optimizer Ref-268 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1068 | 3075 | No |
| 8818 | Symplectic Scholarly Index Tracking Optimizer Ref-364 | Operator theory / Koopman spectral expansion / ETF allocation | 3881 | 1034 | No |
| 8897 | Symplectic Scholarly Index Tracking Optimizer Ref-556 | Koopman operator / Model predictive control / ETF rebalancing | 3891 | 3146 | No |
| 8935 | Symplectic Scholarly Index Tracking Optimizer Ref-652 | Persistence landscapes / Topological contours / Equity index | 5857 | 11323 | No |
| 8972 | Symplectic Scholarly Index Tracking Optimizer Ref-748 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1102 | 3192 | No |
| 9009 | Symplectic Scholarly Index Tracking Optimizer Ref-844 | Operator theory / Koopman spectral expansion / ETF allocation | 3908 | 1069 | No |
| 9089 | Symplectic Scholarly Index Tracking Optimizer Sys-44 | Operator theory / Koopman spectral expansion / ETF allocation | 2198 | 3265 | No |
| 9166 | Symplectic Scholarly Index Tracking Optimizer Sys-236 | Koopman operator / Model predictive control / ETF rebalancing | 12073 | 13738 | No |
| 9206 | Symplectic Scholarly Index Tracking Optimizer Sys-332 | Persistence landscapes / Topological contours / Equity index | 2224 | 3322 | No |
| 9241 | Symplectic Scholarly Index Tracking Optimizer Sys-428 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10750 | 11942 | No |
| 9276 | Symplectic Scholarly Index Tracking Optimizer Sys-524 | Operator theory / Koopman spectral expansion / ETF allocation | 2245 | 3360 | No |
| 9353 | Symplectic Scholarly Index Tracking Optimizer Sys-716 | Koopman operator / Model predictive control / ETF rebalancing | 12083 | 13747 | No |
| 9393 | Symplectic Scholarly Index Tracking Optimizer Sys-812 | Persistence landscapes / Topological contours / Equity index | 2271 | 3417 | No |
| 9428 | Symplectic Scholarly Index Tracking Optimizer Sys-908 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10758 | 11965 | No |
| 9463 | Symplectic Scholarly Index Tracking Optimizer Sys-1004 | Operator theory / Koopman spectral expansion / ETF allocation | 2292 | 3455 | No |
| 9540 | Symplectic Scholarly Index Tracking Optimizer Sys-1196 | Koopman operator / Model predictive control / ETF rebalancing | 12093 | 13756 | No |
| 9580 | Symplectic Scholarly Index Tracking Optimizer Sys-1292 | Persistence landscapes / Topological contours / Equity index | 2318 | 3512 | No |
| 9615 | Symplectic Scholarly Index Tracking Optimizer Sys-1388 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10766 | 11988 | No |
| 9650 | Symplectic Scholarly Index Tracking Optimizer Sys-1484 | Operator theory / Koopman spectral expansion / ETF allocation | 2339 | 3550 | No |
| 9727 | Symplectic Scholarly Index Tracking Optimizer Sys-1676 | Koopman operator / Model predictive control / ETF rebalancing | 12103 | 13765 | No |
| 9767 | Symplectic Scholarly Index Tracking Optimizer Sys-1772 | Persistence landscapes / Topological contours / Equity index | 2365 | 3607 | No |
| 9802 | Symplectic Scholarly Index Tracking Optimizer Sys-1868 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10774 | 12011 | No |
| 9837 | Symplectic Scholarly Index Tracking Optimizer Sys-1964 | Operator theory / Koopman spectral expansion / ETF allocation | 2386 | 3645 | No |
| 9898 | Symplectic Scholarly Index Tracking Optimizer Mod-116 | Koopman operator / Model predictive control / ETF rebalancing | 12112 | 13774 | No |
| 9937 | Symplectic Scholarly Index Tracking Optimizer Mod-212 | Persistence landscapes / Topological contours / Equity index | 2404 | 3695 | No |
| 9974 | Symplectic Scholarly Index Tracking Optimizer Mod-308 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10779 | 12032 | No |
| 10013 | Symplectic Scholarly Index Tracking Optimizer Mod-404 | Operator theory / Koopman spectral expansion / ETF allocation | 2421 | 3733 | No |
| 10089 | Symplectic Scholarly Index Tracking Optimizer Mod-596 | Koopman operator / Model predictive control / ETF rebalancing | 12119 | 13783 | No |
| 10128 | Symplectic Scholarly Index Tracking Optimizer Mod-692 | Persistence landscapes / Topological contours / Equity index | 2443 | 3790 | No |
| 10165 | Symplectic Scholarly Index Tracking Optimizer Mod-788 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10782 | 12055 | No |
| 10204 | Symplectic Scholarly Index Tracking Optimizer Mod-884 | Operator theory / Koopman spectral expansion / ETF allocation | 2460 | 3828 | No |
| 10280 | Symplectic Scholarly Index Tracking Optimizer Mod-1076 | Koopman operator / Model predictive control / ETF rebalancing | 12126 | 13792 | No |
| 10319 | Symplectic Scholarly Index Tracking Optimizer Mod-1172 | Persistence landscapes / Topological contours / Equity index | 2482 | 3885 | No |
| 10356 | Symplectic Scholarly Index Tracking Optimizer Mod-1268 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10785 | 12078 | No |
| 10395 | Symplectic Scholarly Index Tracking Optimizer Mod-1364 | Operator theory / Koopman spectral expansion / ETF allocation | 2499 | 3923 | No |
| 10471 | Symplectic Scholarly Index Tracking Optimizer Mod-1556 | Koopman operator / Model predictive control / ETF rebalancing | 12133 | 13801 | No |
| 10510 | Symplectic Scholarly Index Tracking Optimizer Mod-1652 | Persistence landscapes / Topological contours / Equity index | 2521 | 3980 | No |
| 10547 | Symplectic Scholarly Index Tracking Optimizer Mod-1748 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10788 | 12101 | No |
| 10586 | Symplectic Scholarly Index Tracking Optimizer Mod-1844 | Operator theory / Koopman spectral expansion / ETF allocation | 2538 | 4018 | No |
| 10662 | Symplectic Scholarly Index Tracking Optimizer Mod-2036 | Koopman operator / Model predictive control / ETF rebalancing | 12140 | 13810 | No |
| 10701 | Symplectic Scholarly Index Tracking Optimizer Mod-2132 | Persistence landscapes / Topological contours / Equity index | 2560 | 4075 | No |
| 10738 | Symplectic Scholarly Index Tracking Optimizer Mod-2228 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10791 | 12124 | No |
| 10777 | Symplectic Scholarly Index Tracking Optimizer Mod-2324 | Operator theory / Koopman spectral expansion / ETF allocation | 2577 | 4113 | No |
| 10853 | Symplectic Scholarly Index Tracking Optimizer Mod-2516 | Koopman operator / Model predictive control / ETF rebalancing | 12147 | 13819 | No |
| 10892 | Symplectic Scholarly Index Tracking Optimizer Mod-2612 | Persistence landscapes / Topological contours / Equity index | 2599 | 4170 | No |
| 10929 | Symplectic Scholarly Index Tracking Optimizer Mod-2708 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10794 | 12147 | No |
| 10968 | Symplectic Scholarly Index Tracking Optimizer Mod-2804 | Operator theory / Koopman spectral expansion / ETF allocation | 2616 | 4208 | No |
| 11044 | Symplectic Scholarly Index Tracking Optimizer Mod-2996 | Koopman operator / Model predictive control / ETF rebalancing | 12154 | 13828 | No |
| 11083 | Symplectic Scholarly Index Tracking Optimizer Mod-3092 | Persistence landscapes / Topological contours / Equity index | 2638 | 4265 | No |
| 11120 | Symplectic Scholarly Index Tracking Optimizer Mod-3188 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10797 | 12170 | No |
| 11159 | Symplectic Scholarly Index Tracking Optimizer Mod-3284 | Operator theory / Koopman spectral expansion / ETF allocation | 2655 | 4303 | No |
| 11235 | Symplectic Scholarly Index Tracking Optimizer Mod-3476 | Koopman operator / Model predictive control / ETF rebalancing | 12161 | 13837 | No |
| 11274 | Symplectic Scholarly Index Tracking Optimizer Mod-3572 | Persistence landscapes / Topological contours / Equity index | 2677 | 4360 | No |
| 11311 | Symplectic Scholarly Index Tracking Optimizer Mod-3668 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10800 | 12193 | No |
| 11350 | Symplectic Scholarly Index Tracking Optimizer Mod-3764 | Operator theory / Koopman spectral expansion / ETF allocation | 2694 | 4398 | No |
| 11426 | Symplectic Scholarly Index Tracking Optimizer Mod-3956 | Koopman operator / Model predictive control / ETF rebalancing | 12168 | 13846 | No |
| 11460 | Symplectic Scholarly Index Tracking Optimizer Eng-44 | Operator theory / Koopman spectral expansion / ETF allocation | 2716 | 4453 | No |
| 11537 | Symplectic Scholarly Index Tracking Optimizer Eng-236 | Koopman operator / Model predictive control / ETF rebalancing | 12170 | 13851 | No |
| 11572 | Symplectic Scholarly Index Tracking Optimizer Eng-332 | Persistence landscapes / Topological contours / Equity index | 2737 | 4510 | No |
| 11614 | Symplectic Scholarly Index Tracking Optimizer Eng-428 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10805 | 12230 | No |
| 11651 | Symplectic Scholarly Index Tracking Optimizer Eng-524 | Operator theory / Koopman spectral expansion / ETF allocation | 2754 | 4546 | No |
| 11728 | Symplectic Scholarly Index Tracking Optimizer Eng-716 | Koopman operator / Model predictive control / ETF rebalancing | 12176 | 13860 | No |
| 11763 | Symplectic Scholarly Index Tracking Optimizer Eng-812 | Persistence landscapes / Topological contours / Equity index | 2775 | 4603 | No |
| 11805 | Symplectic Scholarly Index Tracking Optimizer Eng-908 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10809 | 12253 | No |
| 11842 | Symplectic Scholarly Index Tracking Optimizer Eng-1004 | Operator theory / Koopman spectral expansion / ETF allocation | 2792 | 4639 | No |
| 11919 | Symplectic Scholarly Index Tracking Optimizer Eng-1196 | Koopman operator / Model predictive control / ETF rebalancing | 12182 | 13869 | No |
| 11954 | Symplectic Scholarly Index Tracking Optimizer Eng-1292 | Persistence landscapes / Topological contours / Equity index | 2813 | 4696 | No |
| 11996 | Symplectic Scholarly Index Tracking Optimizer Eng-1388 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10813 | 12276 | No |
| 12033 | Symplectic Scholarly Index Tracking Optimizer Eng-1484 | Operator theory / Koopman spectral expansion / ETF allocation | 2830 | 4732 | No |
| 12110 | Symplectic Scholarly Index Tracking Optimizer Eng-1676 | Koopman operator / Model predictive control / ETF rebalancing | 12188 | 13878 | No |
| 12145 | Symplectic Scholarly Index Tracking Optimizer Eng-1772 | Persistence landscapes / Topological contours / Equity index | 2851 | 4789 | No |
| 12187 | Symplectic Scholarly Index Tracking Optimizer Eng-1868 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10817 | 12299 | No |
| 12224 | Symplectic Scholarly Index Tracking Optimizer Eng-1964 | Operator theory / Koopman spectral expansion / ETF allocation | 2868 | 4825 | No |
| 12301 | Symplectic Scholarly Index Tracking Optimizer Eng-2156 | Koopman operator / Model predictive control / ETF rebalancing | 12194 | 13887 | No |
| 12336 | Symplectic Scholarly Index Tracking Optimizer Eng-2252 | Persistence landscapes / Topological contours / Equity index | 2889 | 4882 | No |
| 12378 | Symplectic Scholarly Index Tracking Optimizer Eng-2348 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10821 | 12322 | No |
| 12415 | Symplectic Scholarly Index Tracking Optimizer Eng-2444 | Operator theory / Koopman spectral expansion / ETF allocation | 2906 | 4918 | No |
| 12492 | Symplectic Scholarly Index Tracking Optimizer Eng-2636 | Koopman operator / Model predictive control / ETF rebalancing | 12200 | 13896 | No |
| 12527 | Symplectic Scholarly Index Tracking Optimizer Eng-2732 | Persistence landscapes / Topological contours / Equity index | 2927 | 4975 | No |
| 12569 | Symplectic Scholarly Index Tracking Optimizer Eng-2828 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10825 | 12345 | No |
| 12606 | Symplectic Scholarly Index Tracking Optimizer Eng-2924 | Operator theory / Koopman spectral expansion / ETF allocation | 2944 | 5011 | No |
| 12683 | Symplectic Scholarly Index Tracking Optimizer Eng-3116 | Koopman operator / Model predictive control / ETF rebalancing | 12206 | 13905 | No |
| 12718 | Symplectic Scholarly Index Tracking Optimizer Eng-3212 | Persistence landscapes / Topological contours / Equity index | 2965 | 5068 | No |
| 12760 | Symplectic Scholarly Index Tracking Optimizer Eng-3308 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10829 | 12368 | No |
| 12797 | Symplectic Scholarly Index Tracking Optimizer Eng-3404 | Operator theory / Koopman spectral expansion / ETF allocation | 2982 | 5104 | No |
| 12874 | Symplectic Scholarly Index Tracking Optimizer Eng-3596 | Koopman operator / Model predictive control / ETF rebalancing | 12212 | 13914 | No |
| 12909 | Symplectic Scholarly Index Tracking Optimizer Eng-3692 | Persistence landscapes / Topological contours / Equity index | 3003 | 5161 | No |
| 12951 | Symplectic Scholarly Index Tracking Optimizer Eng-3788 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10833 | 12391 | No |
| 12988 | Symplectic Scholarly Index Tracking Optimizer Eng-3884 | Operator theory / Koopman spectral expansion / ETF allocation | 3020 | 5197 | No |
| 13065 | Symplectic Scholarly Index Tracking Optimizer Eng-4076 | Koopman operator / Model predictive control / ETF rebalancing | 12218 | 13923 | No |
| 13100 | Symplectic Scholarly Index Tracking Optimizer Eng-4172 | Persistence landscapes / Topological contours / Equity index | 3041 | 5254 | No |
| 13142 | Symplectic Scholarly Index Tracking Optimizer Eng-4268 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10837 | 12414 | No |
| 13179 | Symplectic Scholarly Index Tracking Optimizer Eng-4364 | Operator theory / Koopman spectral expansion / ETF allocation | 3058 | 5290 | No |
| 13256 | Symplectic Scholarly Index Tracking Optimizer Eng-4556 | Koopman operator / Model predictive control / ETF rebalancing | 12224 | 13932 | No |
| 13291 | Symplectic Scholarly Index Tracking Optimizer Eng-4652 | Persistence landscapes / Topological contours / Equity index | 3079 | 5347 | No |
| 13333 | Symplectic Scholarly Index Tracking Optimizer Eng-4748 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10841 | 12437 | No |
| 13370 | Symplectic Scholarly Index Tracking Optimizer Eng-4844 | Operator theory / Koopman spectral expansion / ETF allocation | 3096 | 5383 | No |
| 13447 | Symplectic Scholarly Index Tracking Optimizer Eng-5036 | Koopman operator / Model predictive control / ETF rebalancing | 12230 | 13941 | No |
| 13482 | Symplectic Scholarly Index Tracking Optimizer Eng-5132 | Persistence landscapes / Topological contours / Equity index | 3117 | 5440 | No |
| 13524 | Symplectic Scholarly Index Tracking Optimizer Eng-5228 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10845 | 12460 | No |
| 13561 | Symplectic Scholarly Index Tracking Optimizer Eng-5324 | Operator theory / Koopman spectral expansion / ETF allocation | 3134 | 5476 | No |
| 13638 | Symplectic Scholarly Index Tracking Optimizer Eng-5516 | Koopman operator / Model predictive control / ETF rebalancing | 12236 | 13950 | No |
| 13673 | Symplectic Scholarly Index Tracking Optimizer Eng-5612 | Persistence landscapes / Topological contours / Equity index | 3155 | 5533 | No |
| 13715 | Symplectic Scholarly Index Tracking Optimizer Eng-5708 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10849 | 12483 | No |
| 13752 | Symplectic Scholarly Index Tracking Optimizer Eng-5804 | Operator theory / Koopman spectral expansion / ETF allocation | 3172 | 5569 | No |
| 13829 | Symplectic Scholarly Index Tracking Optimizer Eng-5996 | Koopman operator / Model predictive control / ETF rebalancing | 12242 | 13959 | No |
