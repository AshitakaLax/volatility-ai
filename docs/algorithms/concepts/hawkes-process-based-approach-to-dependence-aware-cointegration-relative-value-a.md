# Hawkes-process-based approach to dependence-aware cointegration / relative-value analysis

**Concept page** · shared by **142** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #883) ·
researched 2026-10-30

| | |
|---|---|
| Task | Dependence-aware cointegration / relative-value analysis |
| Method | Hawkes (self-exciting) point processes |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Relative-value positions need a short leg, which the owner's rules exclude; modelling the dependence better does not change that. |
| Implemented in volatility-ai | Pairs rules are research code (`stat_arb`, RK72–RK74). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK74, RK94, RK37 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Hawkes Scholarly Copula
Cointegration System Ref-40") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Model joint and tail dependence among assets and test for a stable
long-run spread before taking relative-value positions. The Hawkes
version models events (trades, jumps, crashes) as self-exciting, each
event raising the near-term chance of another. I found no study of this
method on this task.

## The CSV's description

Proposed Hawkes-process-based approach to dependence-aware cointegration
/ relative-value analysis: Model joint and tail dependence among assets
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
* Hawkes models describe intraday event clustering; daily bars hold too
  few events to fit them.

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
| 883 | Hawkes Scholarly Copula Cointegration System Ref-40 | Fractional order / Multi-scale ETF momentum | 4647 | 462 | No |
| 893 | Hawkes Scholarly Copula Cointegration System Ref-520 | Fractional order / Multi-scale ETF momentum | 4674 | 473 | No |
| 903 | Hawkes Scholarly Copula Cointegration System Ref-1000 | Fractional order / Multi-scale ETF momentum | 4701 | 484 | No |
| 908 | Hawkes Scholarly Copula Cointegration System Sys-200 | Fractional order / Multi-scale ETF momentum | 5885 | 2207 | No |
| 920 | Hawkes Scholarly Copula Cointegration System Sys-680 | Fractional order / Multi-scale ETF momentum | 5905 | 2226 | No |
| 932 | Hawkes Scholarly Copula Cointegration System Sys-1160 | Fractional order / Multi-scale ETF momentum | 5925 | 2245 | No |
| 944 | Hawkes Scholarly Copula Cointegration System Sys-1640 | Fractional order / Multi-scale ETF momentum | 5945 | 2264 | No |
| 965 | Hawkes Scholarly Copula Cointegration System Mod-440 | Fractional order / Multi-scale ETF momentum | 5981 | 2299 | No |
| 978 | Hawkes Scholarly Copula Cointegration System Mod-920 | Fractional order / Multi-scale ETF momentum | 6005 | 2322 | No |
| 991 | Hawkes Scholarly Copula Cointegration System Mod-1400 | Fractional order / Multi-scale ETF momentum | 6029 | 2345 | No |
| 1004 | Hawkes Scholarly Copula Cointegration System Mod-1880 | Fractional order / Multi-scale ETF momentum | 6053 | 2368 | No |
| 1017 | Hawkes Scholarly Copula Cointegration System Mod-2360 | Fractional order / Multi-scale ETF momentum | 6077 | 2391 | No |
| 1030 | Hawkes Scholarly Copula Cointegration System Mod-2840 | Fractional order / Multi-scale ETF momentum | 6101 | 2414 | No |
| 1043 | Hawkes Scholarly Copula Cointegration System Mod-3320 | Fractional order / Multi-scale ETF momentum | 6125 | 2437 | No |
| 1056 | Hawkes Scholarly Copula Cointegration System Mod-3800 | Fractional order / Multi-scale ETF momentum | 6149 | 2460 | No |
| 1067 | Hawkes Scholarly Copula Cointegration System Eng-200 | Fractional order / Multi-scale ETF momentum | 6169 | 2481 | No |
| 1077 | Hawkes Scholarly Copula Cointegration System Eng-680 | Fractional order / Multi-scale ETF momentum | 6191 | 2504 | No |
| 1087 | Hawkes Scholarly Copula Cointegration System Eng-1160 | Fractional order / Multi-scale ETF momentum | 6213 | 2527 | No |
| 1097 | Hawkes Scholarly Copula Cointegration System Eng-1640 | Fractional order / Multi-scale ETF momentum | 6235 | 2550 | No |
| 1107 | Hawkes Scholarly Copula Cointegration System Eng-2120 | Fractional order / Multi-scale ETF momentum | 6257 | 2573 | No |
| 1117 | Hawkes Scholarly Copula Cointegration System Eng-2600 | Fractional order / Multi-scale ETF momentum | 6279 | 2596 | No |
| 1127 | Hawkes Scholarly Copula Cointegration System Eng-3080 | Fractional order / Multi-scale ETF momentum | 6301 | 2619 | No |
| 1137 | Hawkes Scholarly Copula Cointegration System Eng-3560 | Fractional order / Multi-scale ETF momentum | 6323 | 2642 | No |
| 1147 | Hawkes Scholarly Copula Cointegration System Eng-4040 | Fractional order / Multi-scale ETF momentum | 6345 | 2665 | No |
| 1157 | Hawkes Scholarly Copula Cointegration System Eng-4520 | Fractional order / Multi-scale ETF momentum | 6367 | 2688 | No |
| 1167 | Hawkes Scholarly Copula Cointegration System Eng-5000 | Fractional order / Multi-scale ETF momentum | 6389 | 2711 | No |
| 1177 | Hawkes Scholarly Copula Cointegration System Eng-5480 | Fractional order / Multi-scale ETF momentum | 6411 | 2734 | No |
| 1187 | Hawkes Scholarly Copula Cointegration System Eng-5960 | Fractional order / Multi-scale ETF momentum | 6433 | 2757 | No |
| 6138 | Hawkes Scholarly Copula Cointegration System Alpha-32 | Persistence landscapes / Topological contours / Equity index | 4603 | 2905 | No |
| 6148 | Hawkes Scholarly Copula Cointegration System Alpha-132 | Persistence landscapes / Topological contours / Equity index | 1013 | 2927 | No |
| 6158 | Hawkes Scholarly Copula Cointegration System Alpha-232 | Persistence landscapes / Topological contours / Equity index | 8206 | 12518 | No |
| 6168 | Hawkes Scholarly Copula Cointegration System Alpha-332 | Persistence landscapes / Topological contours / Equity index | 4631 | 2973 | No |
| 6178 | Hawkes Scholarly Copula Cointegration System Alpha-432 | Persistence landscapes / Topological contours / Equity index | 1042 | 2995 | No |
| 6200 | Hawkes Scholarly Copula Cointegration System Ref-136 | Koopman operator / Model predictive control / ETF rebalancing | 5830 | 3043 | No |
| 6210 | Hawkes Scholarly Copula Cointegration System Ref-232 | Persistence landscapes / Topological contours / Equity index | 8254 | 12540 | No |
| 6219 | Hawkes Scholarly Copula Cointegration System Ref-328 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1071 | 3091 | No |
| 6227 | Hawkes Scholarly Copula Cointegration System Ref-424 | Operator theory / Koopman spectral expansion / ETF allocation | 10054 | 3116 | No |
| 6246 | Hawkes Scholarly Copula Cointegration System Ref-616 | Koopman operator / Model predictive control / ETF rebalancing | 5855 | 3160 | No |
| 6256 | Hawkes Scholarly Copula Cointegration System Ref-712 | Persistence landscapes / Topological contours / Equity index | 8295 | 12553 | No |
| 6265 | Hawkes Scholarly Copula Cointegration System Ref-808 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1105 | 3208 | No |
| 6273 | Hawkes Scholarly Copula Cointegration System Ref-904 | Operator theory / Koopman spectral expansion / ETF allocation | 10064 | 3233 | No |
| 6283 | Hawkes Scholarly Copula Cointegration System Sys-8 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12543 | 11922 | No |
| 6290 | Hawkes Scholarly Copula Cointegration System Sys-104 | Operator theory / Koopman spectral expansion / ETF allocation | 9326 | 8475 | No |
| 6306 | Hawkes Scholarly Copula Cointegration System Sys-296 | Koopman operator / Model predictive control / ETF rebalancing | 13629 | 13739 | No |
| 6316 | Hawkes Scholarly Copula Cointegration System Sys-392 | Persistence landscapes / Topological contours / Equity index | 4727 | 3335 | No |
| 6324 | Hawkes Scholarly Copula Cointegration System Sys-488 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12550 | 11945 | No |
| 6331 | Hawkes Scholarly Copula Cointegration System Sys-584 | Operator theory / Koopman spectral expansion / ETF allocation | 9342 | 8510 | No |
| 6347 | Hawkes Scholarly Copula Cointegration System Sys-776 | Koopman operator / Model predictive control / ETF rebalancing | 13632 | 13748 | No |
| 6357 | Hawkes Scholarly Copula Cointegration System Sys-872 | Persistence landscapes / Topological contours / Equity index | 4758 | 3430 | No |
| 6365 | Hawkes Scholarly Copula Cointegration System Sys-968 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12557 | 11968 | No |
| 6372 | Hawkes Scholarly Copula Cointegration System Sys-1064 | Operator theory / Koopman spectral expansion / ETF allocation | 9358 | 8545 | No |
| 6388 | Hawkes Scholarly Copula Cointegration System Sys-1256 | Koopman operator / Model predictive control / ETF rebalancing | 13635 | 13757 | No |
| 6398 | Hawkes Scholarly Copula Cointegration System Sys-1352 | Persistence landscapes / Topological contours / Equity index | 4789 | 3525 | No |
| 6406 | Hawkes Scholarly Copula Cointegration System Sys-1448 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12564 | 11991 | No |
| 6413 | Hawkes Scholarly Copula Cointegration System Sys-1544 | Operator theory / Koopman spectral expansion / ETF allocation | 9374 | 8580 | No |
| 6429 | Hawkes Scholarly Copula Cointegration System Sys-1736 | Koopman operator / Model predictive control / ETF rebalancing | 13638 | 13766 | No |
| 6439 | Hawkes Scholarly Copula Cointegration System Sys-1832 | Persistence landscapes / Topological contours / Equity index | 4820 | 3620 | No |
| 6447 | Hawkes Scholarly Copula Cointegration System Sys-1928 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12571 | 12014 | No |
| 6458 | Hawkes Scholarly Copula Cointegration System Mod-56 | Koopman operator / Model predictive control / ETF rebalancing | 13640 | 13773 | No |
| 6466 | Hawkes Scholarly Copula Cointegration System Mod-152 | Persistence landscapes / Topological contours / Equity index | 4840 | 3679 | No |
| 6475 | Hawkes Scholarly Copula Cointegration System Mod-248 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12574 | 12029 | No |
| 6487 | Hawkes Scholarly Copula Cointegration System Mod-344 | Operator theory / Koopman spectral expansion / ETF allocation | 9399 | 8639 | No |
| 6503 | Hawkes Scholarly Copula Cointegration System Mod-536 | Koopman operator / Model predictive control / ETF rebalancing | 13644 | 13782 | No |
| 6511 | Hawkes Scholarly Copula Cointegration System Mod-632 | Persistence landscapes / Topological contours / Equity index | 4867 | 3774 | No |
| 6520 | Hawkes Scholarly Copula Cointegration System Mod-728 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12577 | 12052 | No |
| 6532 | Hawkes Scholarly Copula Cointegration System Mod-824 | Operator theory / Koopman spectral expansion / ETF allocation | 9416 | 8676 | No |
| 6548 | Hawkes Scholarly Copula Cointegration System Mod-1016 | Koopman operator / Model predictive control / ETF rebalancing | 13648 | 13791 | No |
| 6556 | Hawkes Scholarly Copula Cointegration System Mod-1112 | Persistence landscapes / Topological contours / Equity index | 4894 | 3869 | No |
| 6565 | Hawkes Scholarly Copula Cointegration System Mod-1208 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12580 | 12075 | No |
| 6577 | Hawkes Scholarly Copula Cointegration System Mod-1304 | Operator theory / Koopman spectral expansion / ETF allocation | 9433 | 8713 | No |
| 6593 | Hawkes Scholarly Copula Cointegration System Mod-1496 | Koopman operator / Model predictive control / ETF rebalancing | 13652 | 13800 | No |
| 6601 | Hawkes Scholarly Copula Cointegration System Mod-1592 | Persistence landscapes / Topological contours / Equity index | 4921 | 3964 | No |
| 6610 | Hawkes Scholarly Copula Cointegration System Mod-1688 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12583 | 12098 | No |
| 6622 | Hawkes Scholarly Copula Cointegration System Mod-1784 | Operator theory / Koopman spectral expansion / ETF allocation | 9450 | 8750 | No |
| 6638 | Hawkes Scholarly Copula Cointegration System Mod-1976 | Koopman operator / Model predictive control / ETF rebalancing | 13656 | 13809 | No |
| 6646 | Hawkes Scholarly Copula Cointegration System Mod-2072 | Persistence landscapes / Topological contours / Equity index | 4948 | 4059 | No |
| 6655 | Hawkes Scholarly Copula Cointegration System Mod-2168 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12586 | 12121 | No |
| 6667 | Hawkes Scholarly Copula Cointegration System Mod-2264 | Operator theory / Koopman spectral expansion / ETF allocation | 9467 | 8787 | No |
| 6683 | Hawkes Scholarly Copula Cointegration System Mod-2456 | Koopman operator / Model predictive control / ETF rebalancing | 13660 | 13818 | No |
| 6691 | Hawkes Scholarly Copula Cointegration System Mod-2552 | Persistence landscapes / Topological contours / Equity index | 4975 | 4154 | No |
| 6700 | Hawkes Scholarly Copula Cointegration System Mod-2648 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12589 | 12144 | No |
| 6712 | Hawkes Scholarly Copula Cointegration System Mod-2744 | Operator theory / Koopman spectral expansion / ETF allocation | 9484 | 8824 | No |
| 6728 | Hawkes Scholarly Copula Cointegration System Mod-2936 | Koopman operator / Model predictive control / ETF rebalancing | 13664 | 13827 | No |
| 6736 | Hawkes Scholarly Copula Cointegration System Mod-3032 | Persistence landscapes / Topological contours / Equity index | 5002 | 4249 | No |
| 6745 | Hawkes Scholarly Copula Cointegration System Mod-3128 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12592 | 12167 | No |
| 6757 | Hawkes Scholarly Copula Cointegration System Mod-3224 | Operator theory / Koopman spectral expansion / ETF allocation | 9501 | 8861 | No |
| 6773 | Hawkes Scholarly Copula Cointegration System Mod-3416 | Koopman operator / Model predictive control / ETF rebalancing | 13668 | 13836 | No |
| 6781 | Hawkes Scholarly Copula Cointegration System Mod-3512 | Persistence landscapes / Topological contours / Equity index | 5029 | 4344 | No |
| 6790 | Hawkes Scholarly Copula Cointegration System Mod-3608 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12595 | 12190 | No |
| 6802 | Hawkes Scholarly Copula Cointegration System Mod-3704 | Operator theory / Koopman spectral expansion / ETF allocation | 9518 | 8898 | No |
| 6818 | Hawkes Scholarly Copula Cointegration System Mod-3896 | Koopman operator / Model predictive control / ETF rebalancing | 13672 | 13845 | No |
| 6826 | Hawkes Scholarly Copula Cointegration System Mod-3992 | Persistence landscapes / Topological contours / Equity index | 5056 | 4439 | No |
| 6828 | Hawkes Scholarly Copula Cointegration System Eng-8 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12598 | 12210 | No |
| 6839 | Hawkes Scholarly Copula Cointegration System Eng-104 | Operator theory / Koopman spectral expansion / ETF allocation | 9533 | 8928 | No |
| 6857 | Hawkes Scholarly Copula Cointegration System Eng-296 | Koopman operator / Model predictive control / ETF rebalancing | 13677 | 13852 | No |
| 6865 | Hawkes Scholarly Copula Cointegration System Eng-392 | Persistence landscapes / Topological contours / Equity index | 5077 | 4520 | No |
| 6874 | Hawkes Scholarly Copula Cointegration System Eng-488 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12601 | 12233 | No |
| 6885 | Hawkes Scholarly Copula Cointegration System Eng-584 | Operator theory / Koopman spectral expansion / ETF allocation | 9549 | 8963 | No |
| 6903 | Hawkes Scholarly Copula Cointegration System Eng-776 | Koopman operator / Model predictive control / ETF rebalancing | 13681 | 13861 | No |
| 6911 | Hawkes Scholarly Copula Cointegration System Eng-872 | Persistence landscapes / Topological contours / Equity index | 5102 | 4613 | No |
| 6920 | Hawkes Scholarly Copula Cointegration System Eng-968 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12604 | 12256 | No |
| 6931 | Hawkes Scholarly Copula Cointegration System Eng-1064 | Operator theory / Koopman spectral expansion / ETF allocation | 9565 | 8998 | No |
| 6949 | Hawkes Scholarly Copula Cointegration System Eng-1256 | Koopman operator / Model predictive control / ETF rebalancing | 13685 | 13870 | No |
| 6957 | Hawkes Scholarly Copula Cointegration System Eng-1352 | Persistence landscapes / Topological contours / Equity index | 5127 | 4706 | No |
| 6966 | Hawkes Scholarly Copula Cointegration System Eng-1448 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12607 | 12279 | No |
| 6977 | Hawkes Scholarly Copula Cointegration System Eng-1544 | Operator theory / Koopman spectral expansion / ETF allocation | 9581 | 9033 | No |
| 6995 | Hawkes Scholarly Copula Cointegration System Eng-1736 | Koopman operator / Model predictive control / ETF rebalancing | 13689 | 13879 | No |
| 7003 | Hawkes Scholarly Copula Cointegration System Eng-1832 | Persistence landscapes / Topological contours / Equity index | 5152 | 4799 | No |
| 7012 | Hawkes Scholarly Copula Cointegration System Eng-1928 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12610 | 12302 | No |
| 7023 | Hawkes Scholarly Copula Cointegration System Eng-2024 | Operator theory / Koopman spectral expansion / ETF allocation | 9597 | 9068 | No |
| 7041 | Hawkes Scholarly Copula Cointegration System Eng-2216 | Koopman operator / Model predictive control / ETF rebalancing | 13693 | 13888 | No |
| 7049 | Hawkes Scholarly Copula Cointegration System Eng-2312 | Persistence landscapes / Topological contours / Equity index | 5177 | 4892 | No |
| 7058 | Hawkes Scholarly Copula Cointegration System Eng-2408 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12613 | 12325 | No |
| 7069 | Hawkes Scholarly Copula Cointegration System Eng-2504 | Operator theory / Koopman spectral expansion / ETF allocation | 9613 | 9103 | No |
| 7087 | Hawkes Scholarly Copula Cointegration System Eng-2696 | Koopman operator / Model predictive control / ETF rebalancing | 13697 | 13897 | No |
| 7095 | Hawkes Scholarly Copula Cointegration System Eng-2792 | Persistence landscapes / Topological contours / Equity index | 5202 | 4985 | No |
| 7104 | Hawkes Scholarly Copula Cointegration System Eng-2888 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12616 | 12348 | No |
| 7115 | Hawkes Scholarly Copula Cointegration System Eng-2984 | Operator theory / Koopman spectral expansion / ETF allocation | 9629 | 9138 | No |
| 7133 | Hawkes Scholarly Copula Cointegration System Eng-3176 | Koopman operator / Model predictive control / ETF rebalancing | 13701 | 13906 | No |
| 7141 | Hawkes Scholarly Copula Cointegration System Eng-3272 | Persistence landscapes / Topological contours / Equity index | 5227 | 5078 | No |
| 7150 | Hawkes Scholarly Copula Cointegration System Eng-3368 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12619 | 12371 | No |
| 7161 | Hawkes Scholarly Copula Cointegration System Eng-3464 | Operator theory / Koopman spectral expansion / ETF allocation | 9645 | 9173 | No |
| 7179 | Hawkes Scholarly Copula Cointegration System Eng-3656 | Koopman operator / Model predictive control / ETF rebalancing | 13705 | 13915 | No |
| 7187 | Hawkes Scholarly Copula Cointegration System Eng-3752 | Persistence landscapes / Topological contours / Equity index | 5252 | 5171 | No |
| 7196 | Hawkes Scholarly Copula Cointegration System Eng-3848 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12622 | 12394 | No |
| 7207 | Hawkes Scholarly Copula Cointegration System Eng-3944 | Operator theory / Koopman spectral expansion / ETF allocation | 9661 | 9208 | No |
| 7225 | Hawkes Scholarly Copula Cointegration System Eng-4136 | Koopman operator / Model predictive control / ETF rebalancing | 13709 | 13924 | No |
| 7233 | Hawkes Scholarly Copula Cointegration System Eng-4232 | Persistence landscapes / Topological contours / Equity index | 5277 | 5264 | No |
| 7242 | Hawkes Scholarly Copula Cointegration System Eng-4328 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12625 | 12417 | No |
| 7253 | Hawkes Scholarly Copula Cointegration System Eng-4424 | Operator theory / Koopman spectral expansion / ETF allocation | 9677 | 9243 | No |
| 7271 | Hawkes Scholarly Copula Cointegration System Eng-4616 | Koopman operator / Model predictive control / ETF rebalancing | 13713 | 13933 | No |
| 7279 | Hawkes Scholarly Copula Cointegration System Eng-4712 | Persistence landscapes / Topological contours / Equity index | 5302 | 5357 | No |
| 7288 | Hawkes Scholarly Copula Cointegration System Eng-4808 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12628 | 12440 | No |
| 7299 | Hawkes Scholarly Copula Cointegration System Eng-4904 | Operator theory / Koopman spectral expansion / ETF allocation | 9693 | 9278 | No |
| 7317 | Hawkes Scholarly Copula Cointegration System Eng-5096 | Koopman operator / Model predictive control / ETF rebalancing | 13717 | 13942 | No |
| 7325 | Hawkes Scholarly Copula Cointegration System Eng-5192 | Persistence landscapes / Topological contours / Equity index | 5327 | 5450 | No |
| 7334 | Hawkes Scholarly Copula Cointegration System Eng-5288 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12631 | 12463 | No |
| 7345 | Hawkes Scholarly Copula Cointegration System Eng-5384 | Operator theory / Koopman spectral expansion / ETF allocation | 9709 | 9313 | No |
| 7363 | Hawkes Scholarly Copula Cointegration System Eng-5576 | Koopman operator / Model predictive control / ETF rebalancing | 13721 | 13951 | No |
| 7371 | Hawkes Scholarly Copula Cointegration System Eng-5672 | Persistence landscapes / Topological contours / Equity index | 5352 | 5543 | No |
| 7380 | Hawkes Scholarly Copula Cointegration System Eng-5768 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12634 | 12486 | No |
| 7391 | Hawkes Scholarly Copula Cointegration System Eng-5864 | Operator theory / Koopman spectral expansion / ETF allocation | 9725 | 9348 | No |
