# Quantum/quantum-inspired approach to regime-aware allocation

**Concept page** · shared by **136** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,758) ·
researched 2026-10-30

| | |
|---|---|
| Task | Regime-aware allocation |
| Method | Quantum or quantum-inspired computing |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of quantum computing identifying market regimes better than a volatility threshold; the project's NATR regime (V17, N5) is the bar. |
| Implemented in volatility-ai | The NATR regime exit (V17, causal N5) runs through the Ultimate family's `lots_to_liquidate` and `allow_signal_exit`; HMM and Gaussian-mixture regimes are research code (C-R3). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | V17, N5, N6, C-R3, RK102, RK104 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Quantum Scholarly Regime
Switching Allocator Ref-320") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Infer the market's state from prices, volatility or macro data and vary
exposure by regime. The quantum version encodes the problem for a
quantum circuit or a quantum-inspired classical solver. I found no study
of this method on this task.

## The CSV's description

Proposed quantum/quantum-inspired approach to regime-aware allocation:
Infer changing market states from available price, volatility, or
macroeconomic signals and vary portfolio exposure by estimated regime;
regime labels and transition rules require specification. This is a
concept-level interpretation of the title, not a complete trading
specification: the exact model inputs/target, calibration, entry/exit or
rebalance rules, and position sizing are not fully defined here.

## Evidence

* **Nystrup, Hansson, Madsen & Lindström (2016), *Journal of Portfolio
  Management* 42(1), 103–109:** regime-based allocation can beat static
  weights; later work reports reduced drawdowns. (Abstract.)
* **Kritzman, Page & Turkington (2012), *Financial Analysts Journal*
  68(3):** Markov-switching regimes forecast out of sample and used to
  tilt a stock/bond/cash mix beat static allocation (see RK102).
  (Abstract.)
* **This repository (V17):** NATR(10) below its 100-day median,
  liquidating on the flip, gave 38.64% CAGR at 26.68% maximum drawdown
  against TQQQ's 39.15% at 81.68%, measured with a one-day lookahead;
  the causal version (N5) is the open measurement.

## Against, and failure modes

* Regime labels are clear only after the fact; a causal signal lags, and
  whipsaws cost.
* No quantum advantage has been shown on a financial problem; at this
  size a classical solver is exact.

## Fit with volatility-ai

The project's central line of work (V17, N5, N6, C-R3). A new regime
model earns a place only by beating the NATR regime on causal signals
(N5).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Nystrup, P., et al. (2016). *Journal of Portfolio Management* 42(1),
  103–109. Abstract.
* Kritzman, M., Page, S., Turkington, D. (2012). "Regime Shifts:
  Implications for Dynamic Strategies." *Financial Analysts Journal*
  68(3). Abstract.
* This repository: `plan.md`, ledger V17, N5.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 1758 | Quantum Scholarly Regime Switching Allocator Ref-320 | Fractional order / Multi-scale ETF momentum | 12065 | 8438 | No |
| 1813 | Quantum Scholarly Regime Switching Allocator Ref-800 | Fractional order / Multi-scale ETF momentum | 12068 | 8458 | No |
| 1853 | Quantum Scholarly Regime Switching Allocator Sys-160 | Fractional order / Multi-scale ETF momentum | 11345 | 5642 | No |
| 1902 | Quantum Scholarly Regime Switching Allocator Sys-640 | Fractional order / Multi-scale ETF momentum | 11371 | 5659 | No |
| 1951 | Quantum Scholarly Regime Switching Allocator Sys-1120 | Fractional order / Multi-scale ETF momentum | 11397 | 5676 | No |
| 2000 | Quantum Scholarly Regime Switching Allocator Sys-1600 | Fractional order / Multi-scale ETF momentum | 11423 | 5693 | No |
| 2055 | Quantum Scholarly Regime Switching Allocator Mod-160 | Fractional order / Multi-scale ETF momentum | 11455 | 5711 | No |
| 2108 | Quantum Scholarly Regime Switching Allocator Mod-640 | Fractional order / Multi-scale ETF momentum | 11482 | 5724 | No |
| 2161 | Quantum Scholarly Regime Switching Allocator Mod-1120 | Fractional order / Multi-scale ETF momentum | 11509 | 5737 | No |
| 2214 | Quantum Scholarly Regime Switching Allocator Mod-1600 | Fractional order / Multi-scale ETF momentum | 11536 | 5750 | No |
| 2267 | Quantum Scholarly Regime Switching Allocator Mod-2080 | Fractional order / Multi-scale ETF momentum | 11563 | 5763 | No |
| 2320 | Quantum Scholarly Regime Switching Allocator Mod-2560 | Fractional order / Multi-scale ETF momentum | 11590 | 5776 | No |
| 2373 | Quantum Scholarly Regime Switching Allocator Mod-3040 | Fractional order / Multi-scale ETF momentum | 11617 | 5789 | No |
| 2426 | Quantum Scholarly Regime Switching Allocator Mod-3520 | Fractional order / Multi-scale ETF momentum | 11644 | 5802 | No |
| 2479 | Quantum Scholarly Regime Switching Allocator Mod-4000 | Fractional order / Multi-scale ETF momentum | 11671 | 5815 | No |
| 2496 | Quantum Scholarly Regime Switching Allocator Eng-160 | Fractional order / Multi-scale ETF momentum | 11681 | 5817 | No |
| 2551 | Quantum Scholarly Regime Switching Allocator Eng-640 | Fractional order / Multi-scale ETF momentum | 11706 | 5826 | No |
| 2606 | Quantum Scholarly Regime Switching Allocator Eng-1120 | Fractional order / Multi-scale ETF momentum | 11731 | 5835 | No |
| 2661 | Quantum Scholarly Regime Switching Allocator Eng-1600 | Fractional order / Multi-scale ETF momentum | 11756 | 5844 | No |
| 2716 | Quantum Scholarly Regime Switching Allocator Eng-2080 | Fractional order / Multi-scale ETF momentum | 11781 | 5853 | No |
| 2771 | Quantum Scholarly Regime Switching Allocator Eng-2560 | Fractional order / Multi-scale ETF momentum | 11806 | 5862 | No |
| 2826 | Quantum Scholarly Regime Switching Allocator Eng-3040 | Fractional order / Multi-scale ETF momentum | 11831 | 5871 | No |
| 2881 | Quantum Scholarly Regime Switching Allocator Eng-3520 | Fractional order / Multi-scale ETF momentum | 11856 | 5880 | No |
| 2936 | Quantum Scholarly Regime Switching Allocator Eng-4000 | Fractional order / Multi-scale ETF momentum | 11881 | 5889 | No |
| 2991 | Quantum Scholarly Regime Switching Allocator Eng-4480 | Fractional order / Multi-scale ETF momentum | 11906 | 5898 | No |
| 3046 | Quantum Scholarly Regime Switching Allocator Eng-4960 | Fractional order / Multi-scale ETF momentum | 11931 | 5907 | No |
| 3101 | Quantum Scholarly Regime Switching Allocator Eng-5440 | Fractional order / Multi-scale ETF momentum | 11956 | 5916 | No |
| 3156 | Quantum Scholarly Regime Switching Allocator Eng-5920 | Fractional order / Multi-scale ETF momentum | 11981 | 5925 | No |
| 8690 | Quantum Scholarly Regime Switching Allocator Ref-32 | Persistence landscapes / Topological contours / Equity index | 11286 | 9818 | No |
| 8764 | Quantum Scholarly Regime Switching Allocator Ref-224 | Operator theory / Koopman spectral expansion / ETF allocation | 12775 | 9820 | No |
| 8840 | Quantum Scholarly Regime Switching Allocator Ref-416 | Koopman operator / Model predictive control / ETF rebalancing | 14198 | 14200 | No |
| 8881 | Quantum Scholarly Regime Switching Allocator Ref-512 | Persistence landscapes / Topological contours / Equity index | 11311 | 9823 | No |
| 8955 | Quantum Scholarly Regime Switching Allocator Ref-704 | Operator theory / Koopman spectral expansion / ETF allocation | 12776 | 9825 | No |
| 9031 | Quantum Scholarly Regime Switching Allocator Ref-896 | Koopman operator / Model predictive control / ETF rebalancing | 14199 | 14201 | No |
| 9072 | Quantum Scholarly Regime Switching Allocator Ref-992 | Persistence landscapes / Topological contours / Equity index | 11336 | 9828 | No |
| 9097 | Quantum Scholarly Regime Switching Allocator Sys-64 | Operator theory / Koopman spectral expansion / ETF allocation | 13189 | 6005 | No |
| 9173 | Quantum Scholarly Regime Switching Allocator Sys-256 | Koopman operator / Model predictive control / ETF rebalancing | 12074 | 9836 | No |
| 9212 | Quantum Scholarly Regime Switching Allocator Sys-352 | Persistence landscapes / Topological contours / Equity index | 12656 | 13012 | No |
| 9284 | Quantum Scholarly Regime Switching Allocator Sys-544 | Operator theory / Koopman spectral expansion / ETF allocation | 13195 | 6020 | No |
| 9360 | Quantum Scholarly Regime Switching Allocator Sys-736 | Koopman operator / Model predictive control / ETF rebalancing | 12084 | 9853 | No |
| 9399 | Quantum Scholarly Regime Switching Allocator Sys-832 | Persistence landscapes / Topological contours / Equity index | 12661 | 13013 | No |
| 9471 | Quantum Scholarly Regime Switching Allocator Sys-1024 | Operator theory / Koopman spectral expansion / ETF allocation | 13201 | 6035 | No |
| 9547 | Quantum Scholarly Regime Switching Allocator Sys-1216 | Koopman operator / Model predictive control / ETF rebalancing | 12094 | 9870 | No |
| 9586 | Quantum Scholarly Regime Switching Allocator Sys-1312 | Persistence landscapes / Topological contours / Equity index | 12666 | 13014 | No |
| 9658 | Quantum Scholarly Regime Switching Allocator Sys-1504 | Operator theory / Koopman spectral expansion / ETF allocation | 13207 | 6050 | No |
| 9734 | Quantum Scholarly Regime Switching Allocator Sys-1696 | Koopman operator / Model predictive control / ETF rebalancing | 12104 | 9887 | No |
| 9773 | Quantum Scholarly Regime Switching Allocator Sys-1792 | Persistence landscapes / Topological contours / Equity index | 12671 | 13015 | No |
| 9845 | Quantum Scholarly Regime Switching Allocator Sys-1984 | Operator theory / Koopman spectral expansion / ETF allocation | 13213 | 6065 | No |
| 9876 | Quantum Scholarly Regime Switching Allocator Mod-64 | Operator theory / Koopman spectral expansion / ETF allocation | 13216 | 6069 | No |
| 9955 | Quantum Scholarly Regime Switching Allocator Mod-256 | Koopman operator / Model predictive control / ETF rebalancing | 12114 | 9908 | No |
| 9995 | Quantum Scholarly Regime Switching Allocator Mod-352 | Persistence landscapes / Topological contours / Equity index | 12676 | 13018 | No |
| 10067 | Quantum Scholarly Regime Switching Allocator Mod-544 | Operator theory / Koopman spectral expansion / ETF allocation | 13228 | 6086 | No |
| 10146 | Quantum Scholarly Regime Switching Allocator Mod-736 | Koopman operator / Model predictive control / ETF rebalancing | 12121 | 9923 | No |
| 10186 | Quantum Scholarly Regime Switching Allocator Mod-832 | Persistence landscapes / Topological contours / Equity index | 12680 | 13021 | No |
| 10258 | Quantum Scholarly Regime Switching Allocator Mod-1024 | Operator theory / Koopman spectral expansion / ETF allocation | 13240 | 6103 | No |
| 10337 | Quantum Scholarly Regime Switching Allocator Mod-1216 | Koopman operator / Model predictive control / ETF rebalancing | 12128 | 9938 | No |
| 10377 | Quantum Scholarly Regime Switching Allocator Mod-1312 | Persistence landscapes / Topological contours / Equity index | 12684 | 13024 | No |
| 10449 | Quantum Scholarly Regime Switching Allocator Mod-1504 | Operator theory / Koopman spectral expansion / ETF allocation | 13252 | 6120 | No |
| 10528 | Quantum Scholarly Regime Switching Allocator Mod-1696 | Koopman operator / Model predictive control / ETF rebalancing | 12135 | 9953 | No |
| 10568 | Quantum Scholarly Regime Switching Allocator Mod-1792 | Persistence landscapes / Topological contours / Equity index | 12688 | 13027 | No |
| 10640 | Quantum Scholarly Regime Switching Allocator Mod-1984 | Operator theory / Koopman spectral expansion / ETF allocation | 13264 | 6137 | No |
| 10719 | Quantum Scholarly Regime Switching Allocator Mod-2176 | Koopman operator / Model predictive control / ETF rebalancing | 12142 | 9968 | No |
| 10759 | Quantum Scholarly Regime Switching Allocator Mod-2272 | Persistence landscapes / Topological contours / Equity index | 12692 | 13030 | No |
| 10831 | Quantum Scholarly Regime Switching Allocator Mod-2464 | Operator theory / Koopman spectral expansion / ETF allocation | 13276 | 6154 | No |
| 10910 | Quantum Scholarly Regime Switching Allocator Mod-2656 | Koopman operator / Model predictive control / ETF rebalancing | 12149 | 9983 | No |
| 10950 | Quantum Scholarly Regime Switching Allocator Mod-2752 | Persistence landscapes / Topological contours / Equity index | 12696 | 13033 | No |
| 11022 | Quantum Scholarly Regime Switching Allocator Mod-2944 | Operator theory / Koopman spectral expansion / ETF allocation | 13288 | 6171 | No |
| 11101 | Quantum Scholarly Regime Switching Allocator Mod-3136 | Koopman operator / Model predictive control / ETF rebalancing | 12156 | 9998 | No |
| 11141 | Quantum Scholarly Regime Switching Allocator Mod-3232 | Persistence landscapes / Topological contours / Equity index | 12700 | 13036 | No |
| 11213 | Quantum Scholarly Regime Switching Allocator Mod-3424 | Operator theory / Koopman spectral expansion / ETF allocation | 13300 | 6188 | No |
| 11292 | Quantum Scholarly Regime Switching Allocator Mod-3616 | Koopman operator / Model predictive control / ETF rebalancing | 12163 | 10013 | No |
| 11332 | Quantum Scholarly Regime Switching Allocator Mod-3712 | Persistence landscapes / Topological contours / Equity index | 12704 | 13039 | No |
| 11404 | Quantum Scholarly Regime Switching Allocator Mod-3904 | Operator theory / Koopman spectral expansion / ETF allocation | 13312 | 6205 | No |
| 11469 | Quantum Scholarly Regime Switching Allocator Eng-64 | Operator theory / Koopman spectral expansion / ETF allocation | 13317 | 6213 | No |
| 11545 | Quantum Scholarly Regime Switching Allocator Eng-256 | Koopman operator / Model predictive control / ETF rebalancing | 12171 | 10031 | No |
| 11580 | Quantum Scholarly Regime Switching Allocator Eng-352 | Persistence landscapes / Topological contours / Equity index | 12710 | 13043 | No |
| 11660 | Quantum Scholarly Regime Switching Allocator Eng-544 | Operator theory / Koopman spectral expansion / ETF allocation | 13329 | 6234 | No |
| 11736 | Quantum Scholarly Regime Switching Allocator Eng-736 | Koopman operator / Model predictive control / ETF rebalancing | 12177 | 10042 | No |
| 11771 | Quantum Scholarly Regime Switching Allocator Eng-832 | Persistence landscapes / Topological contours / Equity index | 12715 | 13048 | No |
| 11851 | Quantum Scholarly Regime Switching Allocator Eng-1024 | Operator theory / Koopman spectral expansion / ETF allocation | 13341 | 6255 | No |
| 11927 | Quantum Scholarly Regime Switching Allocator Eng-1216 | Koopman operator / Model predictive control / ETF rebalancing | 12183 | 10053 | No |
| 11962 | Quantum Scholarly Regime Switching Allocator Eng-1312 | Persistence landscapes / Topological contours / Equity index | 12720 | 13053 | No |
| 12042 | Quantum Scholarly Regime Switching Allocator Eng-1504 | Operator theory / Koopman spectral expansion / ETF allocation | 13353 | 6276 | No |
| 12118 | Quantum Scholarly Regime Switching Allocator Eng-1696 | Koopman operator / Model predictive control / ETF rebalancing | 12189 | 10064 | No |
| 12153 | Quantum Scholarly Regime Switching Allocator Eng-1792 | Persistence landscapes / Topological contours / Equity index | 12725 | 13058 | No |
| 12233 | Quantum Scholarly Regime Switching Allocator Eng-1984 | Operator theory / Koopman spectral expansion / ETF allocation | 13365 | 6297 | No |
| 12309 | Quantum Scholarly Regime Switching Allocator Eng-2176 | Koopman operator / Model predictive control / ETF rebalancing | 12195 | 10075 | No |
| 12344 | Quantum Scholarly Regime Switching Allocator Eng-2272 | Persistence landscapes / Topological contours / Equity index | 12730 | 13063 | No |
| 12424 | Quantum Scholarly Regime Switching Allocator Eng-2464 | Operator theory / Koopman spectral expansion / ETF allocation | 13377 | 6318 | No |
| 12500 | Quantum Scholarly Regime Switching Allocator Eng-2656 | Koopman operator / Model predictive control / ETF rebalancing | 12201 | 10086 | No |
| 12535 | Quantum Scholarly Regime Switching Allocator Eng-2752 | Persistence landscapes / Topological contours / Equity index | 12735 | 13068 | No |
| 12615 | Quantum Scholarly Regime Switching Allocator Eng-2944 | Operator theory / Koopman spectral expansion / ETF allocation | 13389 | 6339 | No |
| 12691 | Quantum Scholarly Regime Switching Allocator Eng-3136 | Koopman operator / Model predictive control / ETF rebalancing | 12207 | 10097 | No |
| 12726 | Quantum Scholarly Regime Switching Allocator Eng-3232 | Persistence landscapes / Topological contours / Equity index | 12740 | 13073 | No |
| 12806 | Quantum Scholarly Regime Switching Allocator Eng-3424 | Operator theory / Koopman spectral expansion / ETF allocation | 13401 | 6360 | No |
| 12882 | Quantum Scholarly Regime Switching Allocator Eng-3616 | Koopman operator / Model predictive control / ETF rebalancing | 12213 | 10108 | No |
| 12917 | Quantum Scholarly Regime Switching Allocator Eng-3712 | Persistence landscapes / Topological contours / Equity index | 12745 | 13078 | No |
| 12997 | Quantum Scholarly Regime Switching Allocator Eng-3904 | Operator theory / Koopman spectral expansion / ETF allocation | 13413 | 6381 | No |
| 13073 | Quantum Scholarly Regime Switching Allocator Eng-4096 | Koopman operator / Model predictive control / ETF rebalancing | 12219 | 10119 | No |
| 13108 | Quantum Scholarly Regime Switching Allocator Eng-4192 | Persistence landscapes / Topological contours / Equity index | 12750 | 13083 | No |
| 13188 | Quantum Scholarly Regime Switching Allocator Eng-4384 | Operator theory / Koopman spectral expansion / ETF allocation | 13425 | 6402 | No |
| 13264 | Quantum Scholarly Regime Switching Allocator Eng-4576 | Koopman operator / Model predictive control / ETF rebalancing | 12225 | 10130 | No |
| 13299 | Quantum Scholarly Regime Switching Allocator Eng-4672 | Persistence landscapes / Topological contours / Equity index | 12755 | 13088 | No |
| 13379 | Quantum Scholarly Regime Switching Allocator Eng-4864 | Operator theory / Koopman spectral expansion / ETF allocation | 13437 | 6423 | No |
| 13455 | Quantum Scholarly Regime Switching Allocator Eng-5056 | Koopman operator / Model predictive control / ETF rebalancing | 12231 | 10141 | No |
| 13490 | Quantum Scholarly Regime Switching Allocator Eng-5152 | Persistence landscapes / Topological contours / Equity index | 12760 | 13093 | No |
| 13570 | Quantum Scholarly Regime Switching Allocator Eng-5344 | Operator theory / Koopman spectral expansion / ETF allocation | 13449 | 6444 | No |
| 13646 | Quantum Scholarly Regime Switching Allocator Eng-5536 | Koopman operator / Model predictive control / ETF rebalancing | 12237 | 10152 | No |
| 13681 | Quantum Scholarly Regime Switching Allocator Eng-5632 | Persistence landscapes / Topological contours / Equity index | 12765 | 13098 | No |
| 13761 | Quantum Scholarly Regime Switching Allocator Eng-5824 | Operator theory / Koopman spectral expansion / ETF allocation | 13461 | 6465 | No |
| 13878 | Quantum Scholarly Regime Switching Allocator Ref-128 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 13932 | 13517 | No |
| 13889 | Quantum Scholarly Regime Switching Allocator Ref-608 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 13933 | 13518 | No |
| 13914 | Quantum Scholarly Regime Switching Allocator Sys-448 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 9910 | 9844 | No |
| 13932 | Quantum Scholarly Regime Switching Allocator Sys-928 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 9921 | 9861 | No |
| 13950 | Quantum Scholarly Regime Switching Allocator Sys-1408 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 9932 | 9878 | No |
| 13968 | Quantum Scholarly Regime Switching Allocator Sys-1888 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 9943 | 9895 | No |
| 13985 | Quantum Scholarly Regime Switching Allocator Mod-448 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 9951 | 9914 | No |
| 13999 | Quantum Scholarly Regime Switching Allocator Mod-928 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 9956 | 9929 | No |
| 14013 | Quantum Scholarly Regime Switching Allocator Mod-1408 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 9961 | 9944 | No |
| 14027 | Quantum Scholarly Regime Switching Allocator Mod-1888 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 9966 | 9959 | No |
| 14041 | Quantum Scholarly Regime Switching Allocator Mod-2368 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 9971 | 9974 | No |
| 14055 | Quantum Scholarly Regime Switching Allocator Mod-2848 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 9976 | 9989 | No |
| 14069 | Quantum Scholarly Regime Switching Allocator Mod-3328 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 9981 | 10004 | No |
| 14083 | Quantum Scholarly Regime Switching Allocator Mod-3808 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 9986 | 10019 | No |
| 14099 | Quantum Scholarly Regime Switching Allocator Eng-448 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 9990 | 10035 | No |
| 14110 | Quantum Scholarly Regime Switching Allocator Eng-928 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 9993 | 10046 | No |
| 14121 | Quantum Scholarly Regime Switching Allocator Eng-1408 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 9996 | 10057 | No |
| 14132 | Quantum Scholarly Regime Switching Allocator Eng-1888 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 9999 | 10068 | No |
| 14143 | Quantum Scholarly Regime Switching Allocator Eng-2368 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10002 | 10079 | No |
| 14154 | Quantum Scholarly Regime Switching Allocator Eng-2848 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10005 | 10090 | No |
| 14165 | Quantum Scholarly Regime Switching Allocator Eng-3328 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10008 | 10101 | No |
| 14176 | Quantum Scholarly Regime Switching Allocator Eng-3808 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10011 | 10112 | No |
| 14187 | Quantum Scholarly Regime Switching Allocator Eng-4288 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10014 | 10123 | No |
| 14198 | Quantum Scholarly Regime Switching Allocator Eng-4768 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10017 | 10134 | No |
| 14209 | Quantum Scholarly Regime Switching Allocator Eng-5248 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10020 | 10145 | No |
| 14220 | Quantum Scholarly Regime Switching Allocator Eng-5728 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 10023 | 10156 | No |
