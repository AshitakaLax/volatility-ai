# Quantum/quantum-inspired approach to dependence-aware cointegration / relative-value analysis

**Concept page** · shared by **136** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #885) ·
researched 2026-10-30

| | |
|---|---|
| Task | Dependence-aware cointegration / relative-value analysis |
| Method | Quantum or quantum-inspired computing |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Relative-value positions need a short leg, which the owner's rules exclude; modelling the dependence better does not change that. |
| Implemented in volatility-ai | Pairs rules are research code (`stat_arb`, RK72–RK74). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK74, RK94, RK37 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Quantum Scholarly Copula
Cointegration System Ref-160") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Model joint and tail dependence among assets and test for a stable
long-run spread before taking relative-value positions. The quantum
version encodes the problem for a quantum circuit or a quantum-inspired
classical solver. I found no study of this method on this task.

## The CSV's description

Proposed quantum/quantum-inspired approach to dependence-aware
cointegration / relative-value analysis: Model joint and tail dependence
among assets and assess whether a stable long-run spread exists before
considering relative-value positions. This is a concept-level
interpretation of the title, not a complete trading specification: the
exact model inputs/target, calibration, entry/exit or rebalance rules,
and position sizing are not fully defined here.

## Evidence

* **Gatev, Goetzmann & Rouwenhorst (2006), "Pairs Trading," *Review of
  Financial Studies* 19(3), 797–827:** matched pairs earned up to 11% a
  year in excess returns over 1962–2002, with lower raw profits in the
  later years (see RK72). (Abstract and summaries.)

## Against, and failure modes

* Pairs profits have fallen since the 1980s and relationships break down
  without warning.
* No quantum advantage has been shown on a financial problem; at this
  size a classical solver is exact.

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
| 885 | Quantum Scholarly Copula Cointegration System Ref-160 | Fractional order / Multi-scale ETF momentum | 11293 | 5618 | No |
| 895 | Quantum Scholarly Copula Cointegration System Ref-640 | Fractional order / Multi-scale ETF momentum | 11318 | 5629 | No |
| 911 | Quantum Scholarly Copula Cointegration System Sys-320 | Fractional order / Multi-scale ETF momentum | 12077 | 8490 | No |
| 923 | Quantum Scholarly Copula Cointegration System Sys-800 | Fractional order / Multi-scale ETF momentum | 12087 | 8525 | No |
| 935 | Quantum Scholarly Copula Cointegration System Sys-1280 | Fractional order / Multi-scale ETF momentum | 12097 | 8560 | No |
| 947 | Quantum Scholarly Copula Cointegration System Sys-1760 | Fractional order / Multi-scale ETF momentum | 12107 | 8595 | No |
| 963 | Quantum Scholarly Copula Cointegration System Mod-320 | Fractional order / Multi-scale ETF momentum | 12115 | 8636 | No |
| 976 | Quantum Scholarly Copula Cointegration System Mod-800 | Fractional order / Multi-scale ETF momentum | 12122 | 8673 | No |
| 989 | Quantum Scholarly Copula Cointegration System Mod-1280 | Fractional order / Multi-scale ETF momentum | 12129 | 8710 | No |
| 1002 | Quantum Scholarly Copula Cointegration System Mod-1760 | Fractional order / Multi-scale ETF momentum | 12136 | 8747 | No |
| 1015 | Quantum Scholarly Copula Cointegration System Mod-2240 | Fractional order / Multi-scale ETF momentum | 12143 | 8784 | No |
| 1028 | Quantum Scholarly Copula Cointegration System Mod-2720 | Fractional order / Multi-scale ETF momentum | 12150 | 8821 | No |
| 1041 | Quantum Scholarly Copula Cointegration System Mod-3200 | Fractional order / Multi-scale ETF momentum | 12157 | 8858 | No |
| 1054 | Quantum Scholarly Copula Cointegration System Mod-3680 | Fractional order / Multi-scale ETF momentum | 12164 | 8895 | No |
| 1068 | Quantum Scholarly Copula Cointegration System Eng-320 | Fractional order / Multi-scale ETF momentum | 12172 | 8942 | No |
| 1078 | Quantum Scholarly Copula Cointegration System Eng-800 | Fractional order / Multi-scale ETF momentum | 12178 | 8977 | No |
| 1088 | Quantum Scholarly Copula Cointegration System Eng-1280 | Fractional order / Multi-scale ETF momentum | 12184 | 9012 | No |
| 1098 | Quantum Scholarly Copula Cointegration System Eng-1760 | Fractional order / Multi-scale ETF momentum | 12190 | 9047 | No |
| 1108 | Quantum Scholarly Copula Cointegration System Eng-2240 | Fractional order / Multi-scale ETF momentum | 12196 | 9082 | No |
| 1118 | Quantum Scholarly Copula Cointegration System Eng-2720 | Fractional order / Multi-scale ETF momentum | 12202 | 9117 | No |
| 1128 | Quantum Scholarly Copula Cointegration System Eng-3200 | Fractional order / Multi-scale ETF momentum | 12208 | 9152 | No |
| 1138 | Quantum Scholarly Copula Cointegration System Eng-3680 | Fractional order / Multi-scale ETF momentum | 12214 | 9187 | No |
| 1148 | Quantum Scholarly Copula Cointegration System Eng-4160 | Fractional order / Multi-scale ETF momentum | 12220 | 9222 | No |
| 1158 | Quantum Scholarly Copula Cointegration System Eng-4640 | Fractional order / Multi-scale ETF momentum | 12226 | 9257 | No |
| 1168 | Quantum Scholarly Copula Cointegration System Eng-5120 | Fractional order / Multi-scale ETF momentum | 12232 | 9292 | No |
| 1178 | Quantum Scholarly Copula Cointegration System Eng-5600 | Fractional order / Multi-scale ETF momentum | 12238 | 9327 | No |
| 6191 | Quantum Scholarly Copula Cointegration System Ref-64 | Operator theory / Koopman spectral expansion / ETF allocation | 13174 | 9819 | No |
| 6211 | Quantum Scholarly Copula Cointegration System Ref-256 | Koopman operator / Model predictive control / ETF rebalancing | 12064 | 9821 | No |
| 6221 | Quantum Scholarly Copula Cointegration System Ref-352 | Persistence landscapes / Topological contours / Equity index | 12647 | 13646 | No |
| 6237 | Quantum Scholarly Copula Cointegration System Ref-544 | Operator theory / Koopman spectral expansion / ETF allocation | 13181 | 9824 | No |
| 6257 | Quantum Scholarly Copula Cointegration System Ref-736 | Koopman operator / Model predictive control / ETF rebalancing | 12067 | 9826 | No |
| 6267 | Quantum Scholarly Copula Cointegration System Ref-832 | Persistence landscapes / Topological contours / Equity index | 12652 | 13647 | No |
| 6286 | Quantum Scholarly Copula Cointegration System Sys-32 | Persistence landscapes / Topological contours / Equity index | 11339 | 9829 | No |
| 6298 | Quantum Scholarly Copula Cointegration System Sys-224 | Operator theory / Koopman spectral expansion / ETF allocation | 12777 | 10458 | No |
| 6318 | Quantum Scholarly Copula Cointegration System Sys-416 | Koopman operator / Model predictive control / ETF rebalancing | 14200 | 14202 | No |
| 6327 | Quantum Scholarly Copula Cointegration System Sys-512 | Persistence landscapes / Topological contours / Equity index | 11365 | 9846 | No |
| 6339 | Quantum Scholarly Copula Cointegration System Sys-704 | Operator theory / Koopman spectral expansion / ETF allocation | 12778 | 10459 | No |
| 6359 | Quantum Scholarly Copula Cointegration System Sys-896 | Koopman operator / Model predictive control / ETF rebalancing | 14201 | 14203 | No |
| 6368 | Quantum Scholarly Copula Cointegration System Sys-992 | Persistence landscapes / Topological contours / Equity index | 11391 | 9863 | No |
| 6380 | Quantum Scholarly Copula Cointegration System Sys-1184 | Operator theory / Koopman spectral expansion / ETF allocation | 12779 | 10460 | No |
| 6400 | Quantum Scholarly Copula Cointegration System Sys-1376 | Koopman operator / Model predictive control / ETF rebalancing | 14202 | 14204 | No |
| 6409 | Quantum Scholarly Copula Cointegration System Sys-1472 | Persistence landscapes / Topological contours / Equity index | 11417 | 9880 | No |
| 6421 | Quantum Scholarly Copula Cointegration System Sys-1664 | Operator theory / Koopman spectral expansion / ETF allocation | 12780 | 10461 | No |
| 6441 | Quantum Scholarly Copula Cointegration System Sys-1856 | Koopman operator / Model predictive control / ETF rebalancing | 14203 | 14205 | No |
| 6450 | Quantum Scholarly Copula Cointegration System Sys-1952 | Persistence landscapes / Topological contours / Equity index | 11443 | 9897 | No |
| 6456 | Quantum Scholarly Copula Cointegration System Mod-32 | Persistence landscapes / Topological contours / Equity index | 11448 | 9902 | No |
| 6474 | Quantum Scholarly Copula Cointegration System Mod-224 | Operator theory / Koopman spectral expansion / ETF allocation | 12781 | 10462 | No |
| 6492 | Quantum Scholarly Copula Cointegration System Mod-416 | Koopman operator / Model predictive control / ETF rebalancing | 14204 | 14206 | No |
| 6501 | Quantum Scholarly Copula Cointegration System Mod-512 | Persistence landscapes / Topological contours / Equity index | 11475 | 9917 | No |
| 6519 | Quantum Scholarly Copula Cointegration System Mod-704 | Operator theory / Koopman spectral expansion / ETF allocation | 12783 | 10463 | No |
| 6537 | Quantum Scholarly Copula Cointegration System Mod-896 | Koopman operator / Model predictive control / ETF rebalancing | 14205 | 14207 | No |
| 6546 | Quantum Scholarly Copula Cointegration System Mod-992 | Persistence landscapes / Topological contours / Equity index | 11502 | 9932 | No |
| 6564 | Quantum Scholarly Copula Cointegration System Mod-1184 | Operator theory / Koopman spectral expansion / ETF allocation | 12785 | 10464 | No |
| 6582 | Quantum Scholarly Copula Cointegration System Mod-1376 | Koopman operator / Model predictive control / ETF rebalancing | 14206 | 14208 | No |
| 6591 | Quantum Scholarly Copula Cointegration System Mod-1472 | Persistence landscapes / Topological contours / Equity index | 11529 | 9947 | No |
| 6609 | Quantum Scholarly Copula Cointegration System Mod-1664 | Operator theory / Koopman spectral expansion / ETF allocation | 12787 | 10465 | No |
| 6627 | Quantum Scholarly Copula Cointegration System Mod-1856 | Koopman operator / Model predictive control / ETF rebalancing | 14207 | 14209 | No |
| 6636 | Quantum Scholarly Copula Cointegration System Mod-1952 | Persistence landscapes / Topological contours / Equity index | 11556 | 9962 | No |
| 6654 | Quantum Scholarly Copula Cointegration System Mod-2144 | Operator theory / Koopman spectral expansion / ETF allocation | 12789 | 10466 | No |
| 6672 | Quantum Scholarly Copula Cointegration System Mod-2336 | Koopman operator / Model predictive control / ETF rebalancing | 14208 | 14210 | No |
| 6681 | Quantum Scholarly Copula Cointegration System Mod-2432 | Persistence landscapes / Topological contours / Equity index | 11583 | 9977 | No |
| 6699 | Quantum Scholarly Copula Cointegration System Mod-2624 | Operator theory / Koopman spectral expansion / ETF allocation | 12791 | 10467 | No |
| 6717 | Quantum Scholarly Copula Cointegration System Mod-2816 | Koopman operator / Model predictive control / ETF rebalancing | 14209 | 14211 | No |
| 6726 | Quantum Scholarly Copula Cointegration System Mod-2912 | Persistence landscapes / Topological contours / Equity index | 11610 | 9992 | No |
| 6744 | Quantum Scholarly Copula Cointegration System Mod-3104 | Operator theory / Koopman spectral expansion / ETF allocation | 12793 | 10468 | No |
| 6762 | Quantum Scholarly Copula Cointegration System Mod-3296 | Koopman operator / Model predictive control / ETF rebalancing | 14210 | 14212 | No |
| 6771 | Quantum Scholarly Copula Cointegration System Mod-3392 | Persistence landscapes / Topological contours / Equity index | 11637 | 10007 | No |
| 6789 | Quantum Scholarly Copula Cointegration System Mod-3584 | Operator theory / Koopman spectral expansion / ETF allocation | 12795 | 10469 | No |
| 6807 | Quantum Scholarly Copula Cointegration System Mod-3776 | Koopman operator / Model predictive control / ETF rebalancing | 14211 | 14213 | No |
| 6816 | Quantum Scholarly Copula Cointegration System Mod-3872 | Persistence landscapes / Topological contours / Equity index | 11664 | 10022 | No |
| 6831 | Quantum Scholarly Copula Cointegration System Eng-32 | Persistence landscapes / Topological contours / Equity index | 11674 | 10026 | No |
| 6851 | Quantum Scholarly Copula Cointegration System Eng-224 | Operator theory / Koopman spectral expansion / ETF allocation | 12797 | 10470 | No |
| 6867 | Quantum Scholarly Copula Cointegration System Eng-416 | Koopman operator / Model predictive control / ETF rebalancing | 14212 | 14214 | No |
| 6877 | Quantum Scholarly Copula Cointegration System Eng-512 | Persistence landscapes / Topological contours / Equity index | 11699 | 10037 | No |
| 6897 | Quantum Scholarly Copula Cointegration System Eng-704 | Operator theory / Koopman spectral expansion / ETF allocation | 12798 | 10471 | No |
| 6913 | Quantum Scholarly Copula Cointegration System Eng-896 | Koopman operator / Model predictive control / ETF rebalancing | 14213 | 14215 | No |
| 6923 | Quantum Scholarly Copula Cointegration System Eng-992 | Persistence landscapes / Topological contours / Equity index | 11724 | 10048 | No |
| 6943 | Quantum Scholarly Copula Cointegration System Eng-1184 | Operator theory / Koopman spectral expansion / ETF allocation | 12799 | 10472 | No |
| 6959 | Quantum Scholarly Copula Cointegration System Eng-1376 | Koopman operator / Model predictive control / ETF rebalancing | 14214 | 14216 | No |
| 6969 | Quantum Scholarly Copula Cointegration System Eng-1472 | Persistence landscapes / Topological contours / Equity index | 11749 | 10059 | No |
| 6989 | Quantum Scholarly Copula Cointegration System Eng-1664 | Operator theory / Koopman spectral expansion / ETF allocation | 12800 | 10473 | No |
| 7005 | Quantum Scholarly Copula Cointegration System Eng-1856 | Koopman operator / Model predictive control / ETF rebalancing | 14215 | 14217 | No |
| 7015 | Quantum Scholarly Copula Cointegration System Eng-1952 | Persistence landscapes / Topological contours / Equity index | 11774 | 10070 | No |
| 7035 | Quantum Scholarly Copula Cointegration System Eng-2144 | Operator theory / Koopman spectral expansion / ETF allocation | 12801 | 10474 | No |
| 7051 | Quantum Scholarly Copula Cointegration System Eng-2336 | Koopman operator / Model predictive control / ETF rebalancing | 14216 | 14218 | No |
| 7061 | Quantum Scholarly Copula Cointegration System Eng-2432 | Persistence landscapes / Topological contours / Equity index | 11799 | 10081 | No |
| 7081 | Quantum Scholarly Copula Cointegration System Eng-2624 | Operator theory / Koopman spectral expansion / ETF allocation | 12802 | 10475 | No |
| 7097 | Quantum Scholarly Copula Cointegration System Eng-2816 | Koopman operator / Model predictive control / ETF rebalancing | 14217 | 14219 | No |
| 7107 | Quantum Scholarly Copula Cointegration System Eng-2912 | Persistence landscapes / Topological contours / Equity index | 11824 | 10092 | No |
| 7127 | Quantum Scholarly Copula Cointegration System Eng-3104 | Operator theory / Koopman spectral expansion / ETF allocation | 12803 | 10476 | No |
| 7143 | Quantum Scholarly Copula Cointegration System Eng-3296 | Koopman operator / Model predictive control / ETF rebalancing | 14218 | 14220 | No |
| 7153 | Quantum Scholarly Copula Cointegration System Eng-3392 | Persistence landscapes / Topological contours / Equity index | 11849 | 10103 | No |
| 7173 | Quantum Scholarly Copula Cointegration System Eng-3584 | Operator theory / Koopman spectral expansion / ETF allocation | 12804 | 10477 | No |
| 7189 | Quantum Scholarly Copula Cointegration System Eng-3776 | Koopman operator / Model predictive control / ETF rebalancing | 14219 | 14221 | No |
| 7199 | Quantum Scholarly Copula Cointegration System Eng-3872 | Persistence landscapes / Topological contours / Equity index | 11874 | 10114 | No |
| 7219 | Quantum Scholarly Copula Cointegration System Eng-4064 | Operator theory / Koopman spectral expansion / ETF allocation | 12805 | 10478 | No |
| 7235 | Quantum Scholarly Copula Cointegration System Eng-4256 | Koopman operator / Model predictive control / ETF rebalancing | 14220 | 14222 | No |
| 7245 | Quantum Scholarly Copula Cointegration System Eng-4352 | Persistence landscapes / Topological contours / Equity index | 11899 | 10125 | No |
| 7265 | Quantum Scholarly Copula Cointegration System Eng-4544 | Operator theory / Koopman spectral expansion / ETF allocation | 12806 | 10479 | No |
| 7281 | Quantum Scholarly Copula Cointegration System Eng-4736 | Koopman operator / Model predictive control / ETF rebalancing | 14221 | 14223 | No |
| 7291 | Quantum Scholarly Copula Cointegration System Eng-4832 | Persistence landscapes / Topological contours / Equity index | 11924 | 10136 | No |
| 7311 | Quantum Scholarly Copula Cointegration System Eng-5024 | Operator theory / Koopman spectral expansion / ETF allocation | 12807 | 10480 | No |
| 7327 | Quantum Scholarly Copula Cointegration System Eng-5216 | Koopman operator / Model predictive control / ETF rebalancing | 14222 | 14224 | No |
| 7337 | Quantum Scholarly Copula Cointegration System Eng-5312 | Persistence landscapes / Topological contours / Equity index | 11949 | 10147 | No |
| 7357 | Quantum Scholarly Copula Cointegration System Eng-5504 | Operator theory / Koopman spectral expansion / ETF allocation | 12808 | 10481 | No |
| 7373 | Quantum Scholarly Copula Cointegration System Eng-5696 | Koopman operator / Model predictive control / ETF rebalancing | 14223 | 14225 | No |
| 7383 | Quantum Scholarly Copula Cointegration System Eng-5792 | Persistence landscapes / Topological contours / Equity index | 11974 | 10158 | No |
| 7403 | Quantum Scholarly Copula Cointegration System Eng-5984 | Operator theory / Koopman spectral expansion / ETF allocation | 12809 | 10482 | No |
| 8346 | Quantum Scholarly Copula Cointegration System Ref-448 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 9896 | 9822 | No |
| 8348 | Quantum Scholarly Copula Cointegration System Ref-928 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 9899 | 9827 | No |
| 8349 | Quantum Scholarly Copula Cointegration System Sys-128 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 13935 | 13519 | No |
| 8350 | Quantum Scholarly Copula Cointegration System Sys-608 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 13938 | 13520 | No |
| 8351 | Quantum Scholarly Copula Cointegration System Sys-1088 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 13941 | 13521 | No |
| 8352 | Quantum Scholarly Copula Cointegration System Sys-1568 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 13944 | 13522 | No |
| 8353 | Quantum Scholarly Copula Cointegration System Mod-128 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 13946 | 13524 | No |
| 8354 | Quantum Scholarly Copula Cointegration System Mod-608 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 13947 | 13531 | No |
| 8355 | Quantum Scholarly Copula Cointegration System Mod-1088 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 13948 | 13538 | No |
| 8356 | Quantum Scholarly Copula Cointegration System Mod-1568 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 13949 | 13545 | No |
| 8357 | Quantum Scholarly Copula Cointegration System Mod-2048 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 13950 | 13552 | No |
| 8358 | Quantum Scholarly Copula Cointegration System Mod-2528 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 13951 | 13559 | No |
| 8359 | Quantum Scholarly Copula Cointegration System Mod-3008 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 13952 | 13566 | No |
| 8360 | Quantum Scholarly Copula Cointegration System Mod-3488 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 13953 | 13573 | No |
| 8361 | Quantum Scholarly Copula Cointegration System Mod-3968 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 13954 | 13580 | No |
| 8362 | Quantum Scholarly Copula Cointegration System Eng-128 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 13955 | 13583 | No |
| 8364 | Quantum Scholarly Copula Cointegration System Eng-608 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 13956 | 13588 | No |
| 8366 | Quantum Scholarly Copula Cointegration System Eng-1088 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 13957 | 13593 | No |
| 8368 | Quantum Scholarly Copula Cointegration System Eng-1568 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 13958 | 13598 | No |
| 8370 | Quantum Scholarly Copula Cointegration System Eng-2048 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 13959 | 13603 | No |
| 8372 | Quantum Scholarly Copula Cointegration System Eng-2528 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 13960 | 13608 | No |
| 8374 | Quantum Scholarly Copula Cointegration System Eng-3008 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 13961 | 13613 | No |
| 8376 | Quantum Scholarly Copula Cointegration System Eng-3488 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 13962 | 13618 | No |
| 8378 | Quantum Scholarly Copula Cointegration System Eng-3968 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 13963 | 13623 | No |
| 8380 | Quantum Scholarly Copula Cointegration System Eng-4448 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 13964 | 13628 | No |
| 8382 | Quantum Scholarly Copula Cointegration System Eng-4928 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 13965 | 13633 | No |
| 8384 | Quantum Scholarly Copula Cointegration System Eng-5408 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 13966 | 13638 | No |
| 8386 | Quantum Scholarly Copula Cointegration System Eng-5888 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 13967 | 13643 | No |
