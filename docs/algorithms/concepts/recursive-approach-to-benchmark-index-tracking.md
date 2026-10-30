# Recursive approach to benchmark index tracking

**Concept page** · shared by **135** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,732) ·
researched 2026-10-30

| | |
|---|---|
| Task | Benchmark index tracking |
| Method | Recursive (online) estimation |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** The project buys the index as an ETF; replicating it from constituents adds cost and tracking error for nothing. |
| Implemented in volatility-ai | Nothing. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK60 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Recursive Scholarly Index
Tracking Optimizer Ref-100") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Choose weights to track a target index while controlling tracking error,
turnover and costs; an allocation objective, not a return edge. The
recursive version updates its estimates one observation at a time
(recursive least squares, Kalman-style updates). I found no study of
this method on this task.

## The CSV's description

Proposed recursive approach to benchmark index tracking: Choose
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
* A recursive estimate needs a forgetting rate: too slow lags, too fast
  is noise.

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
| 1732 | Recursive Scholarly Index Tracking Optimizer Ref-100 | Fractional order / Multi-scale ETF momentum | 2133 | 464 | No |
| 1787 | Recursive Scholarly Index Tracking Optimizer Ref-580 | Fractional order / Multi-scale ETF momentum | 2165 | 475 | No |
| 1865 | Recursive Scholarly Index Tracking Optimizer Sys-260 | Fractional order / Multi-scale ETF momentum | 3934 | 2210 | No |
| 1914 | Recursive Scholarly Index Tracking Optimizer Sys-740 | Fractional order / Multi-scale ETF momentum | 3963 | 2229 | No |
| 1963 | Recursive Scholarly Index Tracking Optimizer Sys-1220 | Fractional order / Multi-scale ETF momentum | 3992 | 2248 | No |
| 2012 | Recursive Scholarly Index Tracking Optimizer Sys-1700 | Fractional order / Multi-scale ETF momentum | 4021 | 2267 | No |
| 2081 | Recursive Scholarly Index Tracking Optimizer Mod-380 | Fractional order / Multi-scale ETF momentum | 4059 | 2296 | No |
| 2134 | Recursive Scholarly Index Tracking Optimizer Mod-860 | Fractional order / Multi-scale ETF momentum | 4085 | 2319 | No |
| 2187 | Recursive Scholarly Index Tracking Optimizer Mod-1340 | Fractional order / Multi-scale ETF momentum | 4111 | 2342 | No |
| 2240 | Recursive Scholarly Index Tracking Optimizer Mod-1820 | Fractional order / Multi-scale ETF momentum | 4137 | 2365 | No |
| 2293 | Recursive Scholarly Index Tracking Optimizer Mod-2300 | Fractional order / Multi-scale ETF momentum | 4163 | 2388 | No |
| 2346 | Recursive Scholarly Index Tracking Optimizer Mod-2780 | Fractional order / Multi-scale ETF momentum | 4189 | 2411 | No |
| 2399 | Recursive Scholarly Index Tracking Optimizer Mod-3260 | Fractional order / Multi-scale ETF momentum | 4215 | 2434 | No |
| 2452 | Recursive Scholarly Index Tracking Optimizer Mod-3740 | Fractional order / Multi-scale ETF momentum | 4241 | 2457 | No |
| 2508 | Recursive Scholarly Index Tracking Optimizer Eng-260 | Fractional order / Multi-scale ETF momentum | 4272 | 2483 | No |
| 2563 | Recursive Scholarly Index Tracking Optimizer Eng-740 | Fractional order / Multi-scale ETF momentum | 4298 | 2506 | No |
| 2618 | Recursive Scholarly Index Tracking Optimizer Eng-1220 | Fractional order / Multi-scale ETF momentum | 4324 | 2529 | No |
| 2673 | Recursive Scholarly Index Tracking Optimizer Eng-1700 | Fractional order / Multi-scale ETF momentum | 4350 | 2552 | No |
| 2728 | Recursive Scholarly Index Tracking Optimizer Eng-2180 | Fractional order / Multi-scale ETF momentum | 4376 | 2575 | No |
| 2783 | Recursive Scholarly Index Tracking Optimizer Eng-2660 | Fractional order / Multi-scale ETF momentum | 4402 | 2598 | No |
| 2838 | Recursive Scholarly Index Tracking Optimizer Eng-3140 | Fractional order / Multi-scale ETF momentum | 4428 | 2621 | No |
| 2893 | Recursive Scholarly Index Tracking Optimizer Eng-3620 | Fractional order / Multi-scale ETF momentum | 4454 | 2644 | No |
| 2948 | Recursive Scholarly Index Tracking Optimizer Eng-4100 | Fractional order / Multi-scale ETF momentum | 4480 | 2667 | No |
| 3003 | Recursive Scholarly Index Tracking Optimizer Eng-4580 | Fractional order / Multi-scale ETF momentum | 4506 | 2690 | No |
| 3058 | Recursive Scholarly Index Tracking Optimizer Eng-5060 | Fractional order / Multi-scale ETF momentum | 4532 | 2713 | No |
| 3113 | Recursive Scholarly Index Tracking Optimizer Eng-5540 | Fractional order / Multi-scale ETF momentum | 4558 | 2736 | No |
| 8676 | Recursive Scholarly Index Tracking Optimizer Ref-4 | Operator theory / Koopman spectral expansion / ETF allocation | 3860 | 1007 | No |
| 8753 | Recursive Scholarly Index Tracking Optimizer Ref-196 | Koopman operator / Model predictive control / ETF rebalancing | 3871 | 3059 | No |
| 8791 | Recursive Scholarly Index Tracking Optimizer Ref-292 | Persistence landscapes / Topological contours / Equity index | 5838 | 11308 | No |
| 8828 | Recursive Scholarly Index Tracking Optimizer Ref-388 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1076 | 3106 | No |
| 8867 | Recursive Scholarly Index Tracking Optimizer Ref-484 | Operator theory / Koopman spectral expansion / ETF allocation | 3887 | 1042 | No |
| 8944 | Recursive Scholarly Index Tracking Optimizer Ref-676 | Koopman operator / Model predictive control / ETF rebalancing | 3898 | 3176 | No |
| 8982 | Recursive Scholarly Index Tracking Optimizer Ref-772 | Persistence landscapes / Topological contours / Equity index | 5863 | 11329 | No |
| 9019 | Recursive Scholarly Index Tracking Optimizer Ref-868 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1110 | 3223 | No |
| 9058 | Recursive Scholarly Index Tracking Optimizer Ref-964 | Operator theory / Koopman spectral expansion / ETF allocation | 3914 | 1077 | No |
| 9099 | Recursive Scholarly Index Tracking Optimizer Sys-68 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10744 | 11925 | No |
| 9136 | Recursive Scholarly Index Tracking Optimizer Sys-164 | Operator theory / Koopman spectral expansion / ETF allocation | 2210 | 3290 | No |
| 9214 | Recursive Scholarly Index Tracking Optimizer Sys-356 | Koopman operator / Model predictive control / ETF rebalancing | 12078 | 13740 | No |
| 9251 | Recursive Scholarly Index Tracking Optimizer Sys-452 | Persistence landscapes / Topological contours / Equity index | 2236 | 3345 | No |
| 9286 | Recursive Scholarly Index Tracking Optimizer Sys-548 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10752 | 11948 | No |
| 9323 | Recursive Scholarly Index Tracking Optimizer Sys-644 | Operator theory / Koopman spectral expansion / ETF allocation | 2257 | 3385 | No |
| 9401 | Recursive Scholarly Index Tracking Optimizer Sys-836 | Koopman operator / Model predictive control / ETF rebalancing | 12088 | 13749 | No |
| 9438 | Recursive Scholarly Index Tracking Optimizer Sys-932 | Persistence landscapes / Topological contours / Equity index | 2283 | 3440 | No |
| 9473 | Recursive Scholarly Index Tracking Optimizer Sys-1028 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10760 | 11971 | No |
| 9510 | Recursive Scholarly Index Tracking Optimizer Sys-1124 | Operator theory / Koopman spectral expansion / ETF allocation | 2304 | 3480 | No |
| 9588 | Recursive Scholarly Index Tracking Optimizer Sys-1316 | Koopman operator / Model predictive control / ETF rebalancing | 12098 | 13758 | No |
| 9625 | Recursive Scholarly Index Tracking Optimizer Sys-1412 | Persistence landscapes / Topological contours / Equity index | 2330 | 3535 | No |
| 9660 | Recursive Scholarly Index Tracking Optimizer Sys-1508 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10768 | 11994 | No |
| 9697 | Recursive Scholarly Index Tracking Optimizer Sys-1604 | Operator theory / Koopman spectral expansion / ETF allocation | 2351 | 3575 | No |
| 9775 | Recursive Scholarly Index Tracking Optimizer Sys-1796 | Koopman operator / Model predictive control / ETF rebalancing | 12108 | 13767 | No |
| 9812 | Recursive Scholarly Index Tracking Optimizer Sys-1892 | Persistence landscapes / Topological contours / Equity index | 2377 | 3630 | No |
| 9847 | Recursive Scholarly Index Tracking Optimizer Sys-1988 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10776 | 12017 | No |
| 9889 | Recursive Scholarly Index Tracking Optimizer Mod-92 | Persistence landscapes / Topological contours / Equity index | 2395 | 3669 | No |
| 9925 | Recursive Scholarly Index Tracking Optimizer Mod-188 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10778 | 12026 | No |
| 9965 | Recursive Scholarly Index Tracking Optimizer Mod-284 | Operator theory / Koopman spectral expansion / ETF allocation | 2410 | 3707 | No |
| 10042 | Recursive Scholarly Index Tracking Optimizer Mod-476 | Koopman operator / Model predictive control / ETF rebalancing | 12117 | 13780 | No |
| 10080 | Recursive Scholarly Index Tracking Optimizer Mod-572 | Persistence landscapes / Topological contours / Equity index | 2434 | 3764 | No |
| 10116 | Recursive Scholarly Index Tracking Optimizer Mod-668 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10781 | 12049 | No |
| 10156 | Recursive Scholarly Index Tracking Optimizer Mod-764 | Operator theory / Koopman spectral expansion / ETF allocation | 2449 | 3802 | No |
| 10233 | Recursive Scholarly Index Tracking Optimizer Mod-956 | Koopman operator / Model predictive control / ETF rebalancing | 12124 | 13789 | No |
| 10271 | Recursive Scholarly Index Tracking Optimizer Mod-1052 | Persistence landscapes / Topological contours / Equity index | 2473 | 3859 | No |
| 10307 | Recursive Scholarly Index Tracking Optimizer Mod-1148 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10784 | 12072 | No |
| 10347 | Recursive Scholarly Index Tracking Optimizer Mod-1244 | Operator theory / Koopman spectral expansion / ETF allocation | 2488 | 3897 | No |
| 10424 | Recursive Scholarly Index Tracking Optimizer Mod-1436 | Koopman operator / Model predictive control / ETF rebalancing | 12131 | 13798 | No |
| 10462 | Recursive Scholarly Index Tracking Optimizer Mod-1532 | Persistence landscapes / Topological contours / Equity index | 2512 | 3954 | No |
| 10498 | Recursive Scholarly Index Tracking Optimizer Mod-1628 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10787 | 12095 | No |
| 10538 | Recursive Scholarly Index Tracking Optimizer Mod-1724 | Operator theory / Koopman spectral expansion / ETF allocation | 2527 | 3992 | No |
| 10615 | Recursive Scholarly Index Tracking Optimizer Mod-1916 | Koopman operator / Model predictive control / ETF rebalancing | 12138 | 13807 | No |
| 10653 | Recursive Scholarly Index Tracking Optimizer Mod-2012 | Persistence landscapes / Topological contours / Equity index | 2551 | 4049 | No |
| 10689 | Recursive Scholarly Index Tracking Optimizer Mod-2108 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10790 | 12118 | No |
| 10729 | Recursive Scholarly Index Tracking Optimizer Mod-2204 | Operator theory / Koopman spectral expansion / ETF allocation | 2566 | 4087 | No |
| 10806 | Recursive Scholarly Index Tracking Optimizer Mod-2396 | Koopman operator / Model predictive control / ETF rebalancing | 12145 | 13816 | No |
| 10844 | Recursive Scholarly Index Tracking Optimizer Mod-2492 | Persistence landscapes / Topological contours / Equity index | 2590 | 4144 | No |
| 10880 | Recursive Scholarly Index Tracking Optimizer Mod-2588 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10793 | 12141 | No |
| 10920 | Recursive Scholarly Index Tracking Optimizer Mod-2684 | Operator theory / Koopman spectral expansion / ETF allocation | 2605 | 4182 | No |
| 10997 | Recursive Scholarly Index Tracking Optimizer Mod-2876 | Koopman operator / Model predictive control / ETF rebalancing | 12152 | 13825 | No |
| 11035 | Recursive Scholarly Index Tracking Optimizer Mod-2972 | Persistence landscapes / Topological contours / Equity index | 2629 | 4239 | No |
| 11071 | Recursive Scholarly Index Tracking Optimizer Mod-3068 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10796 | 12164 | No |
| 11111 | Recursive Scholarly Index Tracking Optimizer Mod-3164 | Operator theory / Koopman spectral expansion / ETF allocation | 2644 | 4277 | No |
| 11188 | Recursive Scholarly Index Tracking Optimizer Mod-3356 | Koopman operator / Model predictive control / ETF rebalancing | 12159 | 13834 | No |
| 11226 | Recursive Scholarly Index Tracking Optimizer Mod-3452 | Persistence landscapes / Topological contours / Equity index | 2668 | 4334 | No |
| 11262 | Recursive Scholarly Index Tracking Optimizer Mod-3548 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10799 | 12187 | No |
| 11302 | Recursive Scholarly Index Tracking Optimizer Mod-3644 | Operator theory / Koopman spectral expansion / ETF allocation | 2683 | 4372 | No |
| 11379 | Recursive Scholarly Index Tracking Optimizer Mod-3836 | Koopman operator / Model predictive control / ETF rebalancing | 12166 | 13843 | No |
| 11417 | Recursive Scholarly Index Tracking Optimizer Mod-3932 | Persistence landscapes / Topological contours / Equity index | 2707 | 4429 | No |
| 11470 | Recursive Scholarly Index Tracking Optimizer Eng-68 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10802 | 12213 | No |
| 11510 | Recursive Scholarly Index Tracking Optimizer Eng-164 | Operator theory / Koopman spectral expansion / ETF allocation | 2725 | 4477 | No |
| 11582 | Recursive Scholarly Index Tracking Optimizer Eng-356 | Koopman operator / Model predictive control / ETF rebalancing | 12173 | 13854 | No |
| 11621 | Recursive Scholarly Index Tracking Optimizer Eng-452 | Persistence landscapes / Topological contours / Equity index | 2747 | 4533 | No |
| 11661 | Recursive Scholarly Index Tracking Optimizer Eng-548 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10806 | 12236 | No |
| 11701 | Recursive Scholarly Index Tracking Optimizer Eng-644 | Operator theory / Koopman spectral expansion / ETF allocation | 2763 | 4570 | No |
| 11773 | Recursive Scholarly Index Tracking Optimizer Eng-836 | Koopman operator / Model predictive control / ETF rebalancing | 12179 | 13863 | No |
| 11812 | Recursive Scholarly Index Tracking Optimizer Eng-932 | Persistence landscapes / Topological contours / Equity index | 2785 | 4626 | No |
| 11852 | Recursive Scholarly Index Tracking Optimizer Eng-1028 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10810 | 12259 | No |
| 11892 | Recursive Scholarly Index Tracking Optimizer Eng-1124 | Operator theory / Koopman spectral expansion / ETF allocation | 2801 | 4663 | No |
| 11964 | Recursive Scholarly Index Tracking Optimizer Eng-1316 | Koopman operator / Model predictive control / ETF rebalancing | 12185 | 13872 | No |
| 12003 | Recursive Scholarly Index Tracking Optimizer Eng-1412 | Persistence landscapes / Topological contours / Equity index | 2823 | 4719 | No |
| 12043 | Recursive Scholarly Index Tracking Optimizer Eng-1508 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10814 | 12282 | No |
| 12083 | Recursive Scholarly Index Tracking Optimizer Eng-1604 | Operator theory / Koopman spectral expansion / ETF allocation | 2839 | 4756 | No |
| 12155 | Recursive Scholarly Index Tracking Optimizer Eng-1796 | Koopman operator / Model predictive control / ETF rebalancing | 12191 | 13881 | No |
| 12194 | Recursive Scholarly Index Tracking Optimizer Eng-1892 | Persistence landscapes / Topological contours / Equity index | 2861 | 4812 | No |
| 12234 | Recursive Scholarly Index Tracking Optimizer Eng-1988 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10818 | 12305 | No |
| 12274 | Recursive Scholarly Index Tracking Optimizer Eng-2084 | Operator theory / Koopman spectral expansion / ETF allocation | 2877 | 4849 | No |
| 12346 | Recursive Scholarly Index Tracking Optimizer Eng-2276 | Koopman operator / Model predictive control / ETF rebalancing | 12197 | 13890 | No |
| 12385 | Recursive Scholarly Index Tracking Optimizer Eng-2372 | Persistence landscapes / Topological contours / Equity index | 2899 | 4905 | No |
| 12425 | Recursive Scholarly Index Tracking Optimizer Eng-2468 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10822 | 12328 | No |
| 12465 | Recursive Scholarly Index Tracking Optimizer Eng-2564 | Operator theory / Koopman spectral expansion / ETF allocation | 2915 | 4942 | No |
| 12537 | Recursive Scholarly Index Tracking Optimizer Eng-2756 | Koopman operator / Model predictive control / ETF rebalancing | 12203 | 13899 | No |
| 12576 | Recursive Scholarly Index Tracking Optimizer Eng-2852 | Persistence landscapes / Topological contours / Equity index | 2937 | 4998 | No |
| 12616 | Recursive Scholarly Index Tracking Optimizer Eng-2948 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10826 | 12351 | No |
| 12656 | Recursive Scholarly Index Tracking Optimizer Eng-3044 | Operator theory / Koopman spectral expansion / ETF allocation | 2953 | 5035 | No |
| 12728 | Recursive Scholarly Index Tracking Optimizer Eng-3236 | Koopman operator / Model predictive control / ETF rebalancing | 12209 | 13908 | No |
| 12767 | Recursive Scholarly Index Tracking Optimizer Eng-3332 | Persistence landscapes / Topological contours / Equity index | 2975 | 5091 | No |
| 12807 | Recursive Scholarly Index Tracking Optimizer Eng-3428 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10830 | 12374 | No |
| 12847 | Recursive Scholarly Index Tracking Optimizer Eng-3524 | Operator theory / Koopman spectral expansion / ETF allocation | 2991 | 5128 | No |
| 12919 | Recursive Scholarly Index Tracking Optimizer Eng-3716 | Koopman operator / Model predictive control / ETF rebalancing | 12215 | 13917 | No |
| 12958 | Recursive Scholarly Index Tracking Optimizer Eng-3812 | Persistence landscapes / Topological contours / Equity index | 3013 | 5184 | No |
| 12998 | Recursive Scholarly Index Tracking Optimizer Eng-3908 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10834 | 12397 | No |
| 13038 | Recursive Scholarly Index Tracking Optimizer Eng-4004 | Operator theory / Koopman spectral expansion / ETF allocation | 3029 | 5221 | No |
| 13110 | Recursive Scholarly Index Tracking Optimizer Eng-4196 | Koopman operator / Model predictive control / ETF rebalancing | 12221 | 13926 | No |
| 13149 | Recursive Scholarly Index Tracking Optimizer Eng-4292 | Persistence landscapes / Topological contours / Equity index | 3051 | 5277 | No |
| 13189 | Recursive Scholarly Index Tracking Optimizer Eng-4388 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10838 | 12420 | No |
| 13229 | Recursive Scholarly Index Tracking Optimizer Eng-4484 | Operator theory / Koopman spectral expansion / ETF allocation | 3067 | 5314 | No |
| 13301 | Recursive Scholarly Index Tracking Optimizer Eng-4676 | Koopman operator / Model predictive control / ETF rebalancing | 12227 | 13935 | No |
| 13340 | Recursive Scholarly Index Tracking Optimizer Eng-4772 | Persistence landscapes / Topological contours / Equity index | 3089 | 5370 | No |
| 13380 | Recursive Scholarly Index Tracking Optimizer Eng-4868 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10842 | 12443 | No |
| 13420 | Recursive Scholarly Index Tracking Optimizer Eng-4964 | Operator theory / Koopman spectral expansion / ETF allocation | 3105 | 5407 | No |
| 13492 | Recursive Scholarly Index Tracking Optimizer Eng-5156 | Koopman operator / Model predictive control / ETF rebalancing | 12233 | 13944 | No |
| 13531 | Recursive Scholarly Index Tracking Optimizer Eng-5252 | Persistence landscapes / Topological contours / Equity index | 3127 | 5463 | No |
| 13571 | Recursive Scholarly Index Tracking Optimizer Eng-5348 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10846 | 12466 | No |
| 13611 | Recursive Scholarly Index Tracking Optimizer Eng-5444 | Operator theory / Koopman spectral expansion / ETF allocation | 3143 | 5500 | No |
| 13683 | Recursive Scholarly Index Tracking Optimizer Eng-5636 | Koopman operator / Model predictive control / ETF rebalancing | 12239 | 13953 | No |
| 13722 | Recursive Scholarly Index Tracking Optimizer Eng-5732 | Persistence landscapes / Topological contours / Equity index | 3165 | 5556 | No |
| 13762 | Recursive Scholarly Index Tracking Optimizer Eng-5828 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10850 | 12489 | No |
| 13802 | Recursive Scholarly Index Tracking Optimizer Eng-5924 | Operator theory / Koopman spectral expansion / ETF allocation | 3181 | 5593 | No |
