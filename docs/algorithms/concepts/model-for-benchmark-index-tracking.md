# Model for benchmark index tracking

**Concept page** · shared by **140** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,760) ·
researched 2026-10-30

| | |
|---|---|
| Task | Benchmark index tracking |
| Method | Unspecified model |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** The project buys the index as an ETF; replicating it from constituents adds cost and tracking error for nothing. |
| Implemented in volatility-ai | Nothing. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK60 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Wasserstein Scholarly Index
Tracking Optimizer Ref-340") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Choose weights to track a target index while controlling tracking error,
turnover and costs; an allocation objective, not a return edge. The
title names no method beyond "model", so this page judges the task
itself. The task itself is out of scope here; see the fit section.

## The CSV's description

Proposed model for benchmark index tracking: Choose portfolio weights to
track a target index while controlling tracking error, turnover,
liquidity constraints, and transaction costs; this is an allocation
objective, not inherently a return-prediction edge. This is a
concept-level interpretation of the title, not a complete trading
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
| 1760 | Wasserstein Scholarly Index Tracking Optimizer Ref-340 | Fractional order / Multi-scale ETF momentum | 2149 | 469 | No |
| 1815 | Wasserstein Scholarly Index Tracking Optimizer Ref-820 | Fractional order / Multi-scale ETF momentum | 2181 | 480 | No |
| 1839 | Wasserstein Scholarly Index Tracking Optimizer Sys-20 | Fractional order / Multi-scale ETF momentum | 3920 | 2200 | No |
| 1888 | Wasserstein Scholarly Index Tracking Optimizer Sys-500 | Fractional order / Multi-scale ETF momentum | 3949 | 2219 | No |
| 1937 | Wasserstein Scholarly Index Tracking Optimizer Sys-980 | Fractional order / Multi-scale ETF momentum | 3978 | 2238 | No |
| 1986 | Wasserstein Scholarly Index Tracking Optimizer Sys-1460 | Fractional order / Multi-scale ETF momentum | 4007 | 2257 | No |
| 2035 | Wasserstein Scholarly Index Tracking Optimizer Sys-1940 | Fractional order / Multi-scale ETF momentum | 4036 | 2276 | No |
| 2053 | Wasserstein Scholarly Index Tracking Optimizer Mod-140 | Fractional order / Multi-scale ETF momentum | 4046 | 2285 | No |
| 2106 | Wasserstein Scholarly Index Tracking Optimizer Mod-620 | Fractional order / Multi-scale ETF momentum | 4072 | 2308 | No |
| 2159 | Wasserstein Scholarly Index Tracking Optimizer Mod-1100 | Fractional order / Multi-scale ETF momentum | 4098 | 2331 | No |
| 2212 | Wasserstein Scholarly Index Tracking Optimizer Mod-1580 | Fractional order / Multi-scale ETF momentum | 4124 | 2354 | No |
| 2265 | Wasserstein Scholarly Index Tracking Optimizer Mod-2060 | Fractional order / Multi-scale ETF momentum | 4150 | 2377 | No |
| 2318 | Wasserstein Scholarly Index Tracking Optimizer Mod-2540 | Fractional order / Multi-scale ETF momentum | 4176 | 2400 | No |
| 2371 | Wasserstein Scholarly Index Tracking Optimizer Mod-3020 | Fractional order / Multi-scale ETF momentum | 4202 | 2423 | No |
| 2424 | Wasserstein Scholarly Index Tracking Optimizer Mod-3500 | Fractional order / Multi-scale ETF momentum | 4228 | 2446 | No |
| 2477 | Wasserstein Scholarly Index Tracking Optimizer Mod-3980 | Fractional order / Multi-scale ETF momentum | 4254 | 2469 | No |
| 2481 | Wasserstein Scholarly Index Tracking Optimizer Eng-20 | Fractional order / Multi-scale ETF momentum | 4259 | 2471 | No |
| 2536 | Wasserstein Scholarly Index Tracking Optimizer Eng-500 | Fractional order / Multi-scale ETF momentum | 4285 | 2494 | No |
| 2591 | Wasserstein Scholarly Index Tracking Optimizer Eng-980 | Fractional order / Multi-scale ETF momentum | 4311 | 2517 | No |
| 2646 | Wasserstein Scholarly Index Tracking Optimizer Eng-1460 | Fractional order / Multi-scale ETF momentum | 4337 | 2540 | No |
| 2701 | Wasserstein Scholarly Index Tracking Optimizer Eng-1940 | Fractional order / Multi-scale ETF momentum | 4363 | 2563 | No |
| 2756 | Wasserstein Scholarly Index Tracking Optimizer Eng-2420 | Fractional order / Multi-scale ETF momentum | 4389 | 2586 | No |
| 2811 | Wasserstein Scholarly Index Tracking Optimizer Eng-2900 | Fractional order / Multi-scale ETF momentum | 4415 | 2609 | No |
| 2866 | Wasserstein Scholarly Index Tracking Optimizer Eng-3380 | Fractional order / Multi-scale ETF momentum | 4441 | 2632 | No |
| 2921 | Wasserstein Scholarly Index Tracking Optimizer Eng-3860 | Fractional order / Multi-scale ETF momentum | 4467 | 2655 | No |
| 2976 | Wasserstein Scholarly Index Tracking Optimizer Eng-4340 | Fractional order / Multi-scale ETF momentum | 4493 | 2678 | No |
| 3031 | Wasserstein Scholarly Index Tracking Optimizer Eng-4820 | Fractional order / Multi-scale ETF momentum | 4519 | 2701 | No |
| 3086 | Wasserstein Scholarly Index Tracking Optimizer Eng-5300 | Fractional order / Multi-scale ETF momentum | 4545 | 2724 | No |
| 3141 | Wasserstein Scholarly Index Tracking Optimizer Eng-5780 | Fractional order / Multi-scale ETF momentum | 4571 | 2747 | No |
| 3670 | Deep Scholarly Index Tracking Optimizer Ver-15 | Neural SDEs / Robust statistics / Stock options hedging | 3820 | 2766 | No |
| 3675 | Advanced Scholarly Index Tracking Optimizer Ver-75 | Neural SDEs / Robust statistics / Stock options hedging | 3827 | 2770 | No |
| 3679 | Deep Scholarly Index Tracking Optimizer Ver-115 | Neural SDEs / Robust statistics / Stock options hedging | 5385 | 5605 | No |
| 3684 | Advanced Scholarly Index Tracking Optimizer Ver-175 | Neural SDEs / Robust statistics / Stock options hedging | 5388 | 5606 | No |
| 8698 | Wasserstein Scholarly Index Tracking Optimizer Ref-52 | Persistence landscapes / Topological contours / Equity index | 9894 | 12534 | No |
| 8733 | Wasserstein Scholarly Index Tracking Optimizer Ref-148 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 4654 | 3046 | No |
| 8771 | Wasserstein Scholarly Index Tracking Optimizer Ref-244 | Operator theory / Koopman spectral expansion / ETF allocation | 3874 | 3070 | No |
| 8847 | Wasserstein Scholarly Index Tracking Optimizer Ref-436 | Koopman operator / Model predictive control / ETF rebalancing | 3884 | 3119 | No |
| 8889 | Wasserstein Scholarly Index Tracking Optimizer Ref-532 | Persistence landscapes / Topological contours / Equity index | 9897 | 12547 | No |
| 8924 | Wasserstein Scholarly Index Tracking Optimizer Ref-628 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 4681 | 3163 | No |
| 8962 | Wasserstein Scholarly Index Tracking Optimizer Ref-724 | Operator theory / Koopman spectral expansion / ETF allocation | 3901 | 3187 | No |
| 9038 | Wasserstein Scholarly Index Tracking Optimizer Ref-916 | Koopman operator / Model predictive control / ETF rebalancing | 3911 | 3236 | No |
| 9119 | Wasserstein Scholarly Index Tracking Optimizer Sys-116 | Koopman operator / Model predictive control / ETF rebalancing | 12071 | 13736 | No |
| 9157 | Wasserstein Scholarly Index Tracking Optimizer Sys-212 | Persistence landscapes / Topological contours / Equity index | 2214 | 3297 | No |
| 9194 | Wasserstein Scholarly Index Tracking Optimizer Sys-308 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12282 | 11936 | No |
| 9231 | Wasserstein Scholarly Index Tracking Optimizer Sys-404 | Operator theory / Koopman spectral expansion / ETF allocation | 2232 | 8497 | No |
| 9306 | Wasserstein Scholarly Index Tracking Optimizer Sys-596 | Koopman operator / Model predictive control / ETF rebalancing | 12081 | 13745 | No |
| 9344 | Wasserstein Scholarly Index Tracking Optimizer Sys-692 | Persistence landscapes / Topological contours / Equity index | 2261 | 3392 | No |
| 9381 | Wasserstein Scholarly Index Tracking Optimizer Sys-788 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12292 | 11959 | No |
| 9418 | Wasserstein Scholarly Index Tracking Optimizer Sys-884 | Operator theory / Koopman spectral expansion / ETF allocation | 2279 | 8532 | No |
| 9493 | Wasserstein Scholarly Index Tracking Optimizer Sys-1076 | Koopman operator / Model predictive control / ETF rebalancing | 12091 | 13754 | No |
| 9531 | Wasserstein Scholarly Index Tracking Optimizer Sys-1172 | Persistence landscapes / Topological contours / Equity index | 2308 | 3487 | No |
| 9568 | Wasserstein Scholarly Index Tracking Optimizer Sys-1268 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12302 | 11982 | No |
| 9605 | Wasserstein Scholarly Index Tracking Optimizer Sys-1364 | Operator theory / Koopman spectral expansion / ETF allocation | 2326 | 8567 | No |
| 9680 | Wasserstein Scholarly Index Tracking Optimizer Sys-1556 | Koopman operator / Model predictive control / ETF rebalancing | 12101 | 13763 | No |
| 9718 | Wasserstein Scholarly Index Tracking Optimizer Sys-1652 | Persistence landscapes / Topological contours / Equity index | 2355 | 3582 | No |
| 9755 | Wasserstein Scholarly Index Tracking Optimizer Sys-1748 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12312 | 12005 | No |
| 9792 | Wasserstein Scholarly Index Tracking Optimizer Sys-1844 | Operator theory / Koopman spectral expansion / ETF allocation | 2373 | 8602 | No |
| 9868 | Wasserstein Scholarly Index Tracking Optimizer Mod-44 | Operator theory / Koopman spectral expansion / ETF allocation | 2392 | 8616 | No |
| 9947 | Wasserstein Scholarly Index Tracking Optimizer Mod-236 | Koopman operator / Model predictive control / ETF rebalancing | 12113 | 13777 | No |
| 9986 | Wasserstein Scholarly Index Tracking Optimizer Mod-332 | Persistence landscapes / Topological contours / Equity index | 2415 | 3719 | No |
| 10024 | Wasserstein Scholarly Index Tracking Optimizer Mod-428 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12323 | 12038 | No |
| 10059 | Wasserstein Scholarly Index Tracking Optimizer Mod-524 | Operator theory / Koopman spectral expansion / ETF allocation | 2431 | 8653 | No |
| 10138 | Wasserstein Scholarly Index Tracking Optimizer Mod-716 | Koopman operator / Model predictive control / ETF rebalancing | 12120 | 13786 | No |
| 10177 | Wasserstein Scholarly Index Tracking Optimizer Mod-812 | Persistence landscapes / Topological contours / Equity index | 2454 | 3814 | No |
| 10215 | Wasserstein Scholarly Index Tracking Optimizer Mod-908 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12331 | 12061 | No |
| 10250 | Wasserstein Scholarly Index Tracking Optimizer Mod-1004 | Operator theory / Koopman spectral expansion / ETF allocation | 2470 | 8690 | No |
| 10329 | Wasserstein Scholarly Index Tracking Optimizer Mod-1196 | Koopman operator / Model predictive control / ETF rebalancing | 12127 | 13795 | No |
| 10368 | Wasserstein Scholarly Index Tracking Optimizer Mod-1292 | Persistence landscapes / Topological contours / Equity index | 2493 | 3909 | No |
| 10406 | Wasserstein Scholarly Index Tracking Optimizer Mod-1388 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12339 | 12084 | No |
| 10441 | Wasserstein Scholarly Index Tracking Optimizer Mod-1484 | Operator theory / Koopman spectral expansion / ETF allocation | 2509 | 8727 | No |
| 10520 | Wasserstein Scholarly Index Tracking Optimizer Mod-1676 | Koopman operator / Model predictive control / ETF rebalancing | 12134 | 13804 | No |
| 10559 | Wasserstein Scholarly Index Tracking Optimizer Mod-1772 | Persistence landscapes / Topological contours / Equity index | 2532 | 4004 | No |
| 10597 | Wasserstein Scholarly Index Tracking Optimizer Mod-1868 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12347 | 12107 | No |
| 10632 | Wasserstein Scholarly Index Tracking Optimizer Mod-1964 | Operator theory / Koopman spectral expansion / ETF allocation | 2548 | 8764 | No |
| 10711 | Wasserstein Scholarly Index Tracking Optimizer Mod-2156 | Koopman operator / Model predictive control / ETF rebalancing | 12141 | 13813 | No |
| 10750 | Wasserstein Scholarly Index Tracking Optimizer Mod-2252 | Persistence landscapes / Topological contours / Equity index | 2571 | 4099 | No |
| 10788 | Wasserstein Scholarly Index Tracking Optimizer Mod-2348 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12355 | 12130 | No |
| 10823 | Wasserstein Scholarly Index Tracking Optimizer Mod-2444 | Operator theory / Koopman spectral expansion / ETF allocation | 2587 | 8801 | No |
| 10902 | Wasserstein Scholarly Index Tracking Optimizer Mod-2636 | Koopman operator / Model predictive control / ETF rebalancing | 12148 | 13822 | No |
| 10941 | Wasserstein Scholarly Index Tracking Optimizer Mod-2732 | Persistence landscapes / Topological contours / Equity index | 2610 | 4194 | No |
| 10979 | Wasserstein Scholarly Index Tracking Optimizer Mod-2828 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12363 | 12153 | No |
| 11014 | Wasserstein Scholarly Index Tracking Optimizer Mod-2924 | Operator theory / Koopman spectral expansion / ETF allocation | 2626 | 8838 | No |
| 11093 | Wasserstein Scholarly Index Tracking Optimizer Mod-3116 | Koopman operator / Model predictive control / ETF rebalancing | 12155 | 13831 | No |
| 11132 | Wasserstein Scholarly Index Tracking Optimizer Mod-3212 | Persistence landscapes / Topological contours / Equity index | 2649 | 4289 | No |
| 11170 | Wasserstein Scholarly Index Tracking Optimizer Mod-3308 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12371 | 12176 | No |
| 11205 | Wasserstein Scholarly Index Tracking Optimizer Mod-3404 | Operator theory / Koopman spectral expansion / ETF allocation | 2665 | 8875 | No |
| 11284 | Wasserstein Scholarly Index Tracking Optimizer Mod-3596 | Koopman operator / Model predictive control / ETF rebalancing | 12162 | 13840 | No |
| 11323 | Wasserstein Scholarly Index Tracking Optimizer Mod-3692 | Persistence landscapes / Topological contours / Equity index | 2688 | 4384 | No |
| 11361 | Wasserstein Scholarly Index Tracking Optimizer Mod-3788 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12379 | 12199 | No |
| 11396 | Wasserstein Scholarly Index Tracking Optimizer Mod-3884 | Operator theory / Koopman spectral expansion / ETF allocation | 2704 | 8912 | No |
| 11490 | Wasserstein Scholarly Index Tracking Optimizer Eng-116 | Koopman operator / Model predictive control / ETF rebalancing | 12169 | 13848 | No |
| 11527 | Wasserstein Scholarly Index Tracking Optimizer Eng-212 | Persistence landscapes / Topological contours / Equity index | 2728 | 4486 | No |
| 11564 | Wasserstein Scholarly Index Tracking Optimizer Eng-308 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12389 | 12224 | No |
| 11604 | Wasserstein Scholarly Index Tracking Optimizer Eng-404 | Operator theory / Koopman spectral expansion / ETF allocation | 2744 | 8950 | No |
| 11681 | Wasserstein Scholarly Index Tracking Optimizer Eng-596 | Koopman operator / Model predictive control / ETF rebalancing | 12175 | 13857 | No |
| 11718 | Wasserstein Scholarly Index Tracking Optimizer Eng-692 | Persistence landscapes / Topological contours / Equity index | 2766 | 4579 | No |
| 11755 | Wasserstein Scholarly Index Tracking Optimizer Eng-788 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12399 | 12247 | No |
| 11795 | Wasserstein Scholarly Index Tracking Optimizer Eng-884 | Operator theory / Koopman spectral expansion / ETF allocation | 2782 | 8985 | No |
| 11872 | Wasserstein Scholarly Index Tracking Optimizer Eng-1076 | Koopman operator / Model predictive control / ETF rebalancing | 12181 | 13866 | No |
| 11909 | Wasserstein Scholarly Index Tracking Optimizer Eng-1172 | Persistence landscapes / Topological contours / Equity index | 2804 | 4672 | No |
| 11946 | Wasserstein Scholarly Index Tracking Optimizer Eng-1268 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12409 | 12270 | No |
| 11986 | Wasserstein Scholarly Index Tracking Optimizer Eng-1364 | Operator theory / Koopman spectral expansion / ETF allocation | 2820 | 9020 | No |
| 12063 | Wasserstein Scholarly Index Tracking Optimizer Eng-1556 | Koopman operator / Model predictive control / ETF rebalancing | 12187 | 13875 | No |
| 12100 | Wasserstein Scholarly Index Tracking Optimizer Eng-1652 | Persistence landscapes / Topological contours / Equity index | 2842 | 4765 | No |
| 12137 | Wasserstein Scholarly Index Tracking Optimizer Eng-1748 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12419 | 12293 | No |
| 12177 | Wasserstein Scholarly Index Tracking Optimizer Eng-1844 | Operator theory / Koopman spectral expansion / ETF allocation | 2858 | 9055 | No |
| 12254 | Wasserstein Scholarly Index Tracking Optimizer Eng-2036 | Koopman operator / Model predictive control / ETF rebalancing | 12193 | 13884 | No |
| 12291 | Wasserstein Scholarly Index Tracking Optimizer Eng-2132 | Persistence landscapes / Topological contours / Equity index | 2880 | 4858 | No |
| 12328 | Wasserstein Scholarly Index Tracking Optimizer Eng-2228 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12429 | 12316 | No |
| 12368 | Wasserstein Scholarly Index Tracking Optimizer Eng-2324 | Operator theory / Koopman spectral expansion / ETF allocation | 2896 | 9090 | No |
| 12445 | Wasserstein Scholarly Index Tracking Optimizer Eng-2516 | Koopman operator / Model predictive control / ETF rebalancing | 12199 | 13893 | No |
| 12482 | Wasserstein Scholarly Index Tracking Optimizer Eng-2612 | Persistence landscapes / Topological contours / Equity index | 2918 | 4951 | No |
| 12519 | Wasserstein Scholarly Index Tracking Optimizer Eng-2708 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12439 | 12339 | No |
| 12559 | Wasserstein Scholarly Index Tracking Optimizer Eng-2804 | Operator theory / Koopman spectral expansion / ETF allocation | 2934 | 9125 | No |
| 12636 | Wasserstein Scholarly Index Tracking Optimizer Eng-2996 | Koopman operator / Model predictive control / ETF rebalancing | 12205 | 13902 | No |
| 12673 | Wasserstein Scholarly Index Tracking Optimizer Eng-3092 | Persistence landscapes / Topological contours / Equity index | 2956 | 5044 | No |
| 12710 | Wasserstein Scholarly Index Tracking Optimizer Eng-3188 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12449 | 12362 | No |
| 12750 | Wasserstein Scholarly Index Tracking Optimizer Eng-3284 | Operator theory / Koopman spectral expansion / ETF allocation | 2972 | 9160 | No |
| 12827 | Wasserstein Scholarly Index Tracking Optimizer Eng-3476 | Koopman operator / Model predictive control / ETF rebalancing | 12211 | 13911 | No |
| 12864 | Wasserstein Scholarly Index Tracking Optimizer Eng-3572 | Persistence landscapes / Topological contours / Equity index | 2994 | 5137 | No |
| 12901 | Wasserstein Scholarly Index Tracking Optimizer Eng-3668 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12459 | 12385 | No |
| 12941 | Wasserstein Scholarly Index Tracking Optimizer Eng-3764 | Operator theory / Koopman spectral expansion / ETF allocation | 3010 | 9195 | No |
| 13018 | Wasserstein Scholarly Index Tracking Optimizer Eng-3956 | Koopman operator / Model predictive control / ETF rebalancing | 12217 | 13920 | No |
| 13055 | Wasserstein Scholarly Index Tracking Optimizer Eng-4052 | Persistence landscapes / Topological contours / Equity index | 3032 | 5230 | No |
| 13092 | Wasserstein Scholarly Index Tracking Optimizer Eng-4148 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12469 | 12408 | No |
| 13132 | Wasserstein Scholarly Index Tracking Optimizer Eng-4244 | Operator theory / Koopman spectral expansion / ETF allocation | 3048 | 9230 | No |
| 13209 | Wasserstein Scholarly Index Tracking Optimizer Eng-4436 | Koopman operator / Model predictive control / ETF rebalancing | 12223 | 13929 | No |
| 13246 | Wasserstein Scholarly Index Tracking Optimizer Eng-4532 | Persistence landscapes / Topological contours / Equity index | 3070 | 5323 | No |
| 13283 | Wasserstein Scholarly Index Tracking Optimizer Eng-4628 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12479 | 12431 | No |
| 13323 | Wasserstein Scholarly Index Tracking Optimizer Eng-4724 | Operator theory / Koopman spectral expansion / ETF allocation | 3086 | 9265 | No |
| 13400 | Wasserstein Scholarly Index Tracking Optimizer Eng-4916 | Koopman operator / Model predictive control / ETF rebalancing | 12229 | 13938 | No |
| 13437 | Wasserstein Scholarly Index Tracking Optimizer Eng-5012 | Persistence landscapes / Topological contours / Equity index | 3108 | 5416 | No |
| 13474 | Wasserstein Scholarly Index Tracking Optimizer Eng-5108 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12489 | 12454 | No |
| 13514 | Wasserstein Scholarly Index Tracking Optimizer Eng-5204 | Operator theory / Koopman spectral expansion / ETF allocation | 3124 | 9300 | No |
| 13591 | Wasserstein Scholarly Index Tracking Optimizer Eng-5396 | Koopman operator / Model predictive control / ETF rebalancing | 12235 | 13947 | No |
| 13628 | Wasserstein Scholarly Index Tracking Optimizer Eng-5492 | Persistence landscapes / Topological contours / Equity index | 3146 | 5509 | No |
| 13665 | Wasserstein Scholarly Index Tracking Optimizer Eng-5588 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12499 | 12477 | No |
| 13705 | Wasserstein Scholarly Index Tracking Optimizer Eng-5684 | Operator theory / Koopman spectral expansion / ETF allocation | 3162 | 9335 | No |
| 13782 | Wasserstein Scholarly Index Tracking Optimizer Eng-5876 | Koopman operator / Model predictive control / ETF rebalancing | 12241 | 13956 | No |
| 13819 | Wasserstein Scholarly Index Tracking Optimizer Eng-5972 | Persistence landscapes / Topological contours / Equity index | 3184 | 5602 | No |
