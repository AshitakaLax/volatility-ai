# Quantum/quantum-inspired approach to index/ETF constituent arbitrage

**Concept page** · shared by **138** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,670) ·
researched 2026-10-30

| | |
|---|---|
| Task | Index / ETF constituent arbitrage |
| Method | Quantum or quantum-inspired computing |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Constituent arbitrage needs creation/redemption access or a short leg against the basket; both are outside this book. |
| Implemented in volatility-ai | Creation/redemption arbitrage is research code in `excluded` (C-RJ6). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK24, C-RJ6 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Quantum Scholarly Index
Arbitrage Engine Alpha-100") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Estimate fair-value gaps between an index-linked instrument and its
constituent basket and trade the convergence after fees and slippage.
The quantum version encodes the problem for a quantum circuit or a
quantum-inspired classical solver. I found no study of this method on
this task.

## The CSV's description

Proposed quantum/quantum-inspired approach to index/ETF constituent
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
* No quantum advantage has been shown on a financial problem; at this
  size a classical solver is exact.

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
| 1670 | Quantum Scholarly Index Arbitrage Engine Alpha-100 | Fractional calculus / ETF trend filtering | 10564 | 12512 | No |
| 1683 | Quantum Scholarly Index Arbitrage Engine Alpha-200 | Fractional calculus / ETF trend filtering | 11090 | 13507 | No |
| 1696 | Quantum Scholarly Index Arbitrage Engine Alpha-300 | Fractional calculus / ETF trend filtering | 10040 | 11856 | No |
| 1709 | Quantum Scholarly Index Arbitrage Engine Alpha-400 | Fractional calculus / ETF trend filtering | 10566 | 12527 | No |
| 1722 | Quantum Scholarly Index Arbitrage Engine Alpha-500 | Fractional calculus / ETF trend filtering | 11092 | 13508 | No |
| 1777 | Quantum Scholarly Index Arbitrage Engine Ref-480 | Fractional order / Multi-scale ETF momentum | 10055 | 10674 | No |
| 1832 | Quantum Scholarly Index Arbitrage Engine Ref-960 | Fractional order / Multi-scale ETF momentum | 10065 | 10675 | No |
| 1886 | Quantum Scholarly Index Arbitrage Engine Sys-480 | Fractional order / Multi-scale ETF momentum | 10077 | 10676 | No |
| 1935 | Quantum Scholarly Index Arbitrage Engine Sys-960 | Fractional order / Multi-scale ETF momentum | 10088 | 10677 | No |
| 1984 | Quantum Scholarly Index Arbitrage Engine Sys-1440 | Fractional order / Multi-scale ETF momentum | 10099 | 10678 | No |
| 2033 | Quantum Scholarly Index Arbitrage Engine Sys-1920 | Fractional order / Multi-scale ETF momentum | 10110 | 10679 | No |
| 2094 | Quantum Scholarly Index Arbitrage Engine Mod-480 | Fractional order / Multi-scale ETF momentum | 10124 | 10680 | No |
| 2147 | Quantum Scholarly Index Arbitrage Engine Mod-960 | Fractional order / Multi-scale ETF momentum | 10136 | 10681 | No |
| 2200 | Quantum Scholarly Index Arbitrage Engine Mod-1440 | Fractional order / Multi-scale ETF momentum | 10148 | 10682 | No |
| 2253 | Quantum Scholarly Index Arbitrage Engine Mod-1920 | Fractional order / Multi-scale ETF momentum | 10160 | 10683 | No |
| 2306 | Quantum Scholarly Index Arbitrage Engine Mod-2400 | Fractional order / Multi-scale ETF momentum | 10172 | 10684 | No |
| 2359 | Quantum Scholarly Index Arbitrage Engine Mod-2880 | Fractional order / Multi-scale ETF momentum | 10184 | 10685 | No |
| 2412 | Quantum Scholarly Index Arbitrage Engine Mod-3360 | Fractional order / Multi-scale ETF momentum | 10196 | 10686 | No |
| 2465 | Quantum Scholarly Index Arbitrage Engine Mod-3840 | Fractional order / Multi-scale ETF momentum | 10208 | 10687 | No |
| 2534 | Quantum Scholarly Index Arbitrage Engine Eng-480 | Fractional order / Multi-scale ETF momentum | 10225 | 10688 | No |
| 2589 | Quantum Scholarly Index Arbitrage Engine Eng-960 | Fractional order / Multi-scale ETF momentum | 10238 | 10689 | No |
| 2644 | Quantum Scholarly Index Arbitrage Engine Eng-1440 | Fractional order / Multi-scale ETF momentum | 10251 | 10690 | No |
| 2699 | Quantum Scholarly Index Arbitrage Engine Eng-1920 | Fractional order / Multi-scale ETF momentum | 10264 | 10691 | No |
| 2754 | Quantum Scholarly Index Arbitrage Engine Eng-2400 | Fractional order / Multi-scale ETF momentum | 10277 | 10692 | No |
| 2809 | Quantum Scholarly Index Arbitrage Engine Eng-2880 | Fractional order / Multi-scale ETF momentum | 10290 | 10693 | No |
| 2864 | Quantum Scholarly Index Arbitrage Engine Eng-3360 | Fractional order / Multi-scale ETF momentum | 10303 | 10694 | No |
| 2919 | Quantum Scholarly Index Arbitrage Engine Eng-3840 | Fractional order / Multi-scale ETF momentum | 10316 | 10695 | No |
| 2974 | Quantum Scholarly Index Arbitrage Engine Eng-4320 | Fractional order / Multi-scale ETF momentum | 10329 | 10696 | No |
| 3029 | Quantum Scholarly Index Arbitrage Engine Eng-4800 | Fractional order / Multi-scale ETF momentum | 10342 | 10697 | No |
| 3084 | Quantum Scholarly Index Arbitrage Engine Eng-5280 | Fractional order / Multi-scale ETF momentum | 10355 | 10698 | No |
| 3139 | Quantum Scholarly Index Arbitrage Engine Eng-5760 | Fractional order / Multi-scale ETF momentum | 10368 | 10699 | No |
| 8713 | Quantum Scholarly Index Arbitrage Engine Ref-96 | Koopman operator / Model predictive control / ETF rebalancing | 11093 | 12536 | No |
| 8752 | Quantum Scholarly Index Arbitrage Engine Ref-192 | Persistence landscapes / Topological contours / Equity index | 7786 | 11303 | No |
| 8825 | Quantum Scholarly Index Arbitrage Engine Ref-384 | Operator theory / Koopman spectral expansion / ETF allocation | 10568 | 11312 | No |
| 8904 | Quantum Scholarly Index Arbitrage Engine Ref-576 | Koopman operator / Model predictive control / ETF rebalancing | 11095 | 12549 | No |
| 8943 | Quantum Scholarly Index Arbitrage Engine Ref-672 | Persistence landscapes / Topological contours / Equity index | 7803 | 11324 | No |
| 9016 | Quantum Scholarly Index Arbitrage Engine Ref-864 | Operator theory / Koopman spectral expansion / ETF allocation | 10570 | 11333 | No |
| 9112 | Quantum Scholarly Index Arbitrage Engine Sys-96 | Koopman operator / Model predictive control / ETF rebalancing | 11098 | 12562 | No |
| 9148 | Quantum Scholarly Index Arbitrage Engine Sys-192 | Persistence landscapes / Topological contours / Equity index | 7818 | 11343 | No |
| 9224 | Quantum Scholarly Index Arbitrage Engine Sys-384 | Operator theory / Koopman spectral expansion / ETF allocation | 10577 | 11347 | No |
| 9299 | Quantum Scholarly Index Arbitrage Engine Sys-576 | Koopman operator / Model predictive control / ETF rebalancing | 11102 | 12574 | No |
| 9335 | Quantum Scholarly Index Arbitrage Engine Sys-672 | Persistence landscapes / Topological contours / Equity index | 7823 | 11353 | No |
| 9411 | Quantum Scholarly Index Arbitrage Engine Sys-864 | Operator theory / Koopman spectral expansion / ETF allocation | 10585 | 11357 | No |
| 9486 | Quantum Scholarly Index Arbitrage Engine Sys-1056 | Koopman operator / Model predictive control / ETF rebalancing | 11106 | 12586 | No |
| 9522 | Quantum Scholarly Index Arbitrage Engine Sys-1152 | Persistence landscapes / Topological contours / Equity index | 7828 | 11363 | No |
| 9598 | Quantum Scholarly Index Arbitrage Engine Sys-1344 | Operator theory / Koopman spectral expansion / ETF allocation | 10593 | 11367 | No |
| 9673 | Quantum Scholarly Index Arbitrage Engine Sys-1536 | Koopman operator / Model predictive control / ETF rebalancing | 11110 | 12598 | No |
| 9709 | Quantum Scholarly Index Arbitrage Engine Sys-1632 | Persistence landscapes / Topological contours / Equity index | 7833 | 11373 | No |
| 9785 | Quantum Scholarly Index Arbitrage Engine Sys-1824 | Operator theory / Koopman spectral expansion / ETF allocation | 10601 | 11377 | No |
| 9891 | Quantum Scholarly Index Arbitrage Engine Mod-96 | Koopman operator / Model predictive control / ETF rebalancing | 11115 | 12611 | No |
| 9927 | Quantum Scholarly Index Arbitrage Engine Mod-192 | Persistence landscapes / Topological contours / Equity index | 7841 | 11385 | No |
| 10005 | Quantum Scholarly Index Arbitrage Engine Mod-384 | Operator theory / Koopman spectral expansion / ETF allocation | 10607 | 11391 | No |
| 10082 | Quantum Scholarly Index Arbitrage Engine Mod-576 | Koopman operator / Model predictive control / ETF rebalancing | 11121 | 12619 | No |
| 10118 | Quantum Scholarly Index Arbitrage Engine Mod-672 | Persistence landscapes / Topological contours / Equity index | 7855 | 11399 | No |
| 10196 | Quantum Scholarly Index Arbitrage Engine Mod-864 | Operator theory / Koopman spectral expansion / ETF allocation | 10613 | 11405 | No |
| 10273 | Quantum Scholarly Index Arbitrage Engine Mod-1056 | Koopman operator / Model predictive control / ETF rebalancing | 11127 | 12627 | No |
| 10309 | Quantum Scholarly Index Arbitrage Engine Mod-1152 | Persistence landscapes / Topological contours / Equity index | 7869 | 11413 | No |
| 10387 | Quantum Scholarly Index Arbitrage Engine Mod-1344 | Operator theory / Koopman spectral expansion / ETF allocation | 10619 | 11419 | No |
| 10464 | Quantum Scholarly Index Arbitrage Engine Mod-1536 | Koopman operator / Model predictive control / ETF rebalancing | 11133 | 12635 | No |
| 10500 | Quantum Scholarly Index Arbitrage Engine Mod-1632 | Persistence landscapes / Topological contours / Equity index | 7883 | 11427 | No |
| 10578 | Quantum Scholarly Index Arbitrage Engine Mod-1824 | Operator theory / Koopman spectral expansion / ETF allocation | 10625 | 11433 | No |
| 10655 | Quantum Scholarly Index Arbitrage Engine Mod-2016 | Koopman operator / Model predictive control / ETF rebalancing | 11139 | 12643 | No |
| 10691 | Quantum Scholarly Index Arbitrage Engine Mod-2112 | Persistence landscapes / Topological contours / Equity index | 7897 | 11441 | No |
| 10769 | Quantum Scholarly Index Arbitrage Engine Mod-2304 | Operator theory / Koopman spectral expansion / ETF allocation | 10631 | 11447 | No |
| 10846 | Quantum Scholarly Index Arbitrage Engine Mod-2496 | Koopman operator / Model predictive control / ETF rebalancing | 11145 | 12651 | No |
| 10882 | Quantum Scholarly Index Arbitrage Engine Mod-2592 | Persistence landscapes / Topological contours / Equity index | 7911 | 11455 | No |
| 10960 | Quantum Scholarly Index Arbitrage Engine Mod-2784 | Operator theory / Koopman spectral expansion / ETF allocation | 10637 | 11461 | No |
| 11037 | Quantum Scholarly Index Arbitrage Engine Mod-2976 | Koopman operator / Model predictive control / ETF rebalancing | 11151 | 12659 | No |
| 11073 | Quantum Scholarly Index Arbitrage Engine Mod-3072 | Persistence landscapes / Topological contours / Equity index | 7925 | 11469 | No |
| 11151 | Quantum Scholarly Index Arbitrage Engine Mod-3264 | Operator theory / Koopman spectral expansion / ETF allocation | 10643 | 11475 | No |
| 11228 | Quantum Scholarly Index Arbitrage Engine Mod-3456 | Koopman operator / Model predictive control / ETF rebalancing | 11157 | 12667 | No |
| 11264 | Quantum Scholarly Index Arbitrage Engine Mod-3552 | Persistence landscapes / Topological contours / Equity index | 7939 | 11483 | No |
| 11342 | Quantum Scholarly Index Arbitrage Engine Mod-3744 | Operator theory / Koopman spectral expansion / ETF allocation | 10649 | 11489 | No |
| 11419 | Quantum Scholarly Index Arbitrage Engine Mod-3936 | Koopman operator / Model predictive control / ETF rebalancing | 11163 | 12675 | No |
| 11482 | Quantum Scholarly Index Arbitrage Engine Eng-96 | Koopman operator / Model predictive control / ETF rebalancing | 11166 | 12680 | No |
| 11521 | Quantum Scholarly Index Arbitrage Engine Eng-192 | Persistence landscapes / Topological contours / Equity index | 7959 | 11500 | No |
| 11594 | Quantum Scholarly Index Arbitrage Engine Eng-384 | Operator theory / Koopman spectral expansion / ETF allocation | 10657 | 11506 | No |
| 11673 | Quantum Scholarly Index Arbitrage Engine Eng-576 | Koopman operator / Model predictive control / ETF rebalancing | 11173 | 12688 | No |
| 11712 | Quantum Scholarly Index Arbitrage Engine Eng-672 | Persistence landscapes / Topological contours / Equity index | 7976 | 11514 | No |
| 11785 | Quantum Scholarly Index Arbitrage Engine Eng-864 | Operator theory / Koopman spectral expansion / ETF allocation | 10663 | 11520 | No |
| 11864 | Quantum Scholarly Index Arbitrage Engine Eng-1056 | Koopman operator / Model predictive control / ETF rebalancing | 11180 | 12696 | No |
| 11903 | Quantum Scholarly Index Arbitrage Engine Eng-1152 | Persistence landscapes / Topological contours / Equity index | 7993 | 11528 | No |
| 11976 | Quantum Scholarly Index Arbitrage Engine Eng-1344 | Operator theory / Koopman spectral expansion / ETF allocation | 10669 | 11534 | No |
| 12055 | Quantum Scholarly Index Arbitrage Engine Eng-1536 | Koopman operator / Model predictive control / ETF rebalancing | 11187 | 12704 | No |
| 12094 | Quantum Scholarly Index Arbitrage Engine Eng-1632 | Persistence landscapes / Topological contours / Equity index | 8010 | 11542 | No |
| 12167 | Quantum Scholarly Index Arbitrage Engine Eng-1824 | Operator theory / Koopman spectral expansion / ETF allocation | 10675 | 11548 | No |
| 12246 | Quantum Scholarly Index Arbitrage Engine Eng-2016 | Koopman operator / Model predictive control / ETF rebalancing | 11194 | 12712 | No |
| 12285 | Quantum Scholarly Index Arbitrage Engine Eng-2112 | Persistence landscapes / Topological contours / Equity index | 8027 | 11556 | No |
| 12358 | Quantum Scholarly Index Arbitrage Engine Eng-2304 | Operator theory / Koopman spectral expansion / ETF allocation | 10681 | 11562 | No |
| 12437 | Quantum Scholarly Index Arbitrage Engine Eng-2496 | Koopman operator / Model predictive control / ETF rebalancing | 11201 | 12720 | No |
| 12476 | Quantum Scholarly Index Arbitrage Engine Eng-2592 | Persistence landscapes / Topological contours / Equity index | 8044 | 11570 | No |
| 12549 | Quantum Scholarly Index Arbitrage Engine Eng-2784 | Operator theory / Koopman spectral expansion / ETF allocation | 10687 | 11576 | No |
| 12628 | Quantum Scholarly Index Arbitrage Engine Eng-2976 | Koopman operator / Model predictive control / ETF rebalancing | 11208 | 12728 | No |
| 12667 | Quantum Scholarly Index Arbitrage Engine Eng-3072 | Persistence landscapes / Topological contours / Equity index | 8061 | 11584 | No |
| 12740 | Quantum Scholarly Index Arbitrage Engine Eng-3264 | Operator theory / Koopman spectral expansion / ETF allocation | 10693 | 11590 | No |
| 12819 | Quantum Scholarly Index Arbitrage Engine Eng-3456 | Koopman operator / Model predictive control / ETF rebalancing | 11215 | 12736 | No |
| 12858 | Quantum Scholarly Index Arbitrage Engine Eng-3552 | Persistence landscapes / Topological contours / Equity index | 8078 | 11598 | No |
| 12931 | Quantum Scholarly Index Arbitrage Engine Eng-3744 | Operator theory / Koopman spectral expansion / ETF allocation | 10699 | 11604 | No |
| 13010 | Quantum Scholarly Index Arbitrage Engine Eng-3936 | Koopman operator / Model predictive control / ETF rebalancing | 11222 | 12744 | No |
| 13049 | Quantum Scholarly Index Arbitrage Engine Eng-4032 | Persistence landscapes / Topological contours / Equity index | 8095 | 11612 | No |
| 13122 | Quantum Scholarly Index Arbitrage Engine Eng-4224 | Operator theory / Koopman spectral expansion / ETF allocation | 10705 | 11618 | No |
| 13201 | Quantum Scholarly Index Arbitrage Engine Eng-4416 | Koopman operator / Model predictive control / ETF rebalancing | 11229 | 12752 | No |
| 13240 | Quantum Scholarly Index Arbitrage Engine Eng-4512 | Persistence landscapes / Topological contours / Equity index | 8112 | 11626 | No |
| 13313 | Quantum Scholarly Index Arbitrage Engine Eng-4704 | Operator theory / Koopman spectral expansion / ETF allocation | 10711 | 11632 | No |
| 13392 | Quantum Scholarly Index Arbitrage Engine Eng-4896 | Koopman operator / Model predictive control / ETF rebalancing | 11236 | 12760 | No |
| 13431 | Quantum Scholarly Index Arbitrage Engine Eng-4992 | Persistence landscapes / Topological contours / Equity index | 8129 | 11640 | No |
| 13504 | Quantum Scholarly Index Arbitrage Engine Eng-5184 | Operator theory / Koopman spectral expansion / ETF allocation | 10717 | 11646 | No |
| 13583 | Quantum Scholarly Index Arbitrage Engine Eng-5376 | Koopman operator / Model predictive control / ETF rebalancing | 11243 | 12768 | No |
| 13622 | Quantum Scholarly Index Arbitrage Engine Eng-5472 | Persistence landscapes / Topological contours / Equity index | 8146 | 11654 | No |
| 13695 | Quantum Scholarly Index Arbitrage Engine Eng-5664 | Operator theory / Koopman spectral expansion / ETF allocation | 10723 | 11660 | No |
| 13774 | Quantum Scholarly Index Arbitrage Engine Eng-5856 | Koopman operator / Model predictive control / ETF rebalancing | 11250 | 12776 | No |
| 13813 | Quantum Scholarly Index Arbitrage Engine Eng-5952 | Persistence landscapes / Topological contours / Equity index | 8163 | 11668 | No |
| 13881 | Quantum Scholarly Index Arbitrage Engine Ref-288 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 9895 | 13114 | No |
| 13892 | Quantum Scholarly Index Arbitrage Engine Ref-768 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 9898 | 13115 | No |
| 13908 | Quantum Scholarly Index Arbitrage Engine Sys-288 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 9907 | 13116 | No |
| 13926 | Quantum Scholarly Index Arbitrage Engine Sys-768 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 9918 | 13117 | No |
| 13944 | Quantum Scholarly Index Arbitrage Engine Sys-1248 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 9929 | 13118 | No |
| 13962 | Quantum Scholarly Index Arbitrage Engine Sys-1728 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 9940 | 13119 | No |
| 13980 | Quantum Scholarly Index Arbitrage Engine Mod-288 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 9950 | 13120 | No |
| 13994 | Quantum Scholarly Index Arbitrage Engine Mod-768 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 9955 | 13121 | No |
| 14008 | Quantum Scholarly Index Arbitrage Engine Mod-1248 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 9960 | 13122 | No |
| 14022 | Quantum Scholarly Index Arbitrage Engine Mod-1728 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 9965 | 13123 | No |
| 14036 | Quantum Scholarly Index Arbitrage Engine Mod-2208 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 9970 | 13124 | No |
| 14050 | Quantum Scholarly Index Arbitrage Engine Mod-2688 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 9975 | 13125 | No |
| 14064 | Quantum Scholarly Index Arbitrage Engine Mod-3168 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 9980 | 13126 | No |
| 14078 | Quantum Scholarly Index Arbitrage Engine Mod-3648 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 9985 | 13127 | No |
| 14095 | Quantum Scholarly Index Arbitrage Engine Eng-288 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 9989 | 13128 | No |
| 14106 | Quantum Scholarly Index Arbitrage Engine Eng-768 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 9992 | 13129 | No |
| 14117 | Quantum Scholarly Index Arbitrage Engine Eng-1248 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 9995 | 13130 | No |
| 14128 | Quantum Scholarly Index Arbitrage Engine Eng-1728 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 9998 | 13131 | No |
| 14139 | Quantum Scholarly Index Arbitrage Engine Eng-2208 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10001 | 13132 | No |
| 14150 | Quantum Scholarly Index Arbitrage Engine Eng-2688 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10004 | 13133 | No |
| 14161 | Quantum Scholarly Index Arbitrage Engine Eng-3168 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10007 | 13134 | No |
| 14172 | Quantum Scholarly Index Arbitrage Engine Eng-3648 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10010 | 13135 | No |
| 14183 | Quantum Scholarly Index Arbitrage Engine Eng-4128 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10013 | 13136 | No |
| 14194 | Quantum Scholarly Index Arbitrage Engine Eng-4608 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10016 | 13137 | No |
| 14205 | Quantum Scholarly Index Arbitrage Engine Eng-5088 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10019 | 13138 | No |
| 14216 | Quantum Scholarly Index Arbitrage Engine Eng-5568 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10022 | 13139 | No |
