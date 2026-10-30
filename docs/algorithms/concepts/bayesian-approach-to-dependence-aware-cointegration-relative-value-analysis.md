# Bayesian approach to dependence-aware cointegration / relative-value analysis

**Concept page** · shared by **135** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #892) ·
researched 2026-10-30

| | |
|---|---|
| Task | Dependence-aware cointegration / relative-value analysis |
| Method | Bayesian estimation |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Relative-value positions need a short leg, which the owner's rules exclude; modelling the dependence better does not change that. |
| Implemented in volatility-ai | Pairs rules are research code (`stat_arb`, RK72–RK74). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK74, RK94, RK37 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Bayesian Scholarly Copula
Cointegration System Ref-400") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Model joint and tail dependence among assets and test for a stable
long-run spread before taking relative-value positions. The Bayesian
version puts priors on the parameters and acts on the posterior. I found
no study of this method on this task.

## The CSV's description

Proposed Bayesian approach to dependence-aware cointegration /
relative-value analysis: Model joint and tail dependence among assets
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
* The prior decides a lot: a weak one returns the plain estimate, a
  strong one imposes the answer.

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
| 892 | Bayesian Scholarly Copula Cointegration System Ref-400 | Fractional order / Multi-scale ETF momentum | 4667 | 470 | No |
| 902 | Bayesian Scholarly Copula Cointegration System Ref-880 | Fractional order / Multi-scale ETF momentum | 4694 | 481 | No |
| 905 | Bayesian Scholarly Copula Cointegration System Sys-80 | Fractional order / Multi-scale ETF momentum | 5879 | 2202 | No |
| 917 | Bayesian Scholarly Copula Cointegration System Sys-560 | Fractional order / Multi-scale ETF momentum | 5899 | 2221 | No |
| 929 | Bayesian Scholarly Copula Cointegration System Sys-1040 | Fractional order / Multi-scale ETF momentum | 5919 | 2240 | No |
| 941 | Bayesian Scholarly Copula Cointegration System Sys-1520 | Fractional order / Multi-scale ETF momentum | 5939 | 2259 | No |
| 953 | Bayesian Scholarly Copula Cointegration System Sys-2000 | Fractional order / Multi-scale ETF momentum | 5959 | 2278 | No |
| 956 | Bayesian Scholarly Copula Cointegration System Mod-80 | Fractional order / Multi-scale ETF momentum | 5964 | 2282 | No |
| 969 | Bayesian Scholarly Copula Cointegration System Mod-560 | Fractional order / Multi-scale ETF momentum | 5988 | 2305 | No |
| 982 | Bayesian Scholarly Copula Cointegration System Mod-1040 | Fractional order / Multi-scale ETF momentum | 6012 | 2328 | No |
| 995 | Bayesian Scholarly Copula Cointegration System Mod-1520 | Fractional order / Multi-scale ETF momentum | 6036 | 2351 | No |
| 1008 | Bayesian Scholarly Copula Cointegration System Mod-2000 | Fractional order / Multi-scale ETF momentum | 6060 | 2374 | No |
| 1021 | Bayesian Scholarly Copula Cointegration System Mod-2480 | Fractional order / Multi-scale ETF momentum | 6084 | 2397 | No |
| 1034 | Bayesian Scholarly Copula Cointegration System Mod-2960 | Fractional order / Multi-scale ETF momentum | 6108 | 2420 | No |
| 1047 | Bayesian Scholarly Copula Cointegration System Mod-3440 | Fractional order / Multi-scale ETF momentum | 6132 | 2443 | No |
| 1060 | Bayesian Scholarly Copula Cointegration System Mod-3920 | Fractional order / Multi-scale ETF momentum | 6156 | 2466 | No |
| 1065 | Bayesian Scholarly Copula Cointegration System Eng-80 | Fractional order / Multi-scale ETF momentum | 6163 | 2475 | No |
| 1075 | Bayesian Scholarly Copula Cointegration System Eng-560 | Fractional order / Multi-scale ETF momentum | 6185 | 2498 | No |
| 1085 | Bayesian Scholarly Copula Cointegration System Eng-1040 | Fractional order / Multi-scale ETF momentum | 6207 | 2521 | No |
| 1095 | Bayesian Scholarly Copula Cointegration System Eng-1520 | Fractional order / Multi-scale ETF momentum | 6229 | 2544 | No |
| 1105 | Bayesian Scholarly Copula Cointegration System Eng-2000 | Fractional order / Multi-scale ETF momentum | 6251 | 2567 | No |
| 1115 | Bayesian Scholarly Copula Cointegration System Eng-2480 | Fractional order / Multi-scale ETF momentum | 6273 | 2590 | No |
| 1125 | Bayesian Scholarly Copula Cointegration System Eng-2960 | Fractional order / Multi-scale ETF momentum | 6295 | 2613 | No |
| 1135 | Bayesian Scholarly Copula Cointegration System Eng-3440 | Fractional order / Multi-scale ETF momentum | 6317 | 2636 | No |
| 1145 | Bayesian Scholarly Copula Cointegration System Eng-3920 | Fractional order / Multi-scale ETF momentum | 6339 | 2659 | No |
| 1155 | Bayesian Scholarly Copula Cointegration System Eng-4400 | Fractional order / Multi-scale ETF momentum | 6361 | 2682 | No |
| 1165 | Bayesian Scholarly Copula Cointegration System Eng-4880 | Fractional order / Multi-scale ETF momentum | 6383 | 2705 | No |
| 1175 | Bayesian Scholarly Copula Cointegration System Eng-5360 | Fractional order / Multi-scale ETF momentum | 6405 | 2728 | No |
| 1185 | Bayesian Scholarly Copula Cointegration System Eng-5840 | Fractional order / Multi-scale ETF momentum | 6427 | 2751 | No |
| 6186 | Bayesian Scholarly Copula Cointegration System Ref-16 | Koopman operator / Model predictive control / ETF rebalancing | 5825 | 3014 | No |
| 6198 | Bayesian Scholarly Copula Cointegration System Ref-112 | Persistence landscapes / Topological contours / Equity index | 8245 | 12537 | No |
| 6208 | Bayesian Scholarly Copula Cointegration System Ref-208 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1063 | 3062 | No |
| 6216 | Bayesian Scholarly Copula Cointegration System Ref-304 | Operator theory / Koopman spectral expansion / ETF allocation | 10052 | 3085 | No |
| 6232 | Bayesian Scholarly Copula Cointegration System Ref-496 | Koopman operator / Model predictive control / ETF rebalancing | 5850 | 3131 | No |
| 6244 | Bayesian Scholarly Copula Cointegration System Ref-592 | Persistence landscapes / Topological contours / Equity index | 8286 | 12550 | No |
| 6254 | Bayesian Scholarly Copula Cointegration System Ref-688 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1097 | 3179 | No |
| 6262 | Bayesian Scholarly Copula Cointegration System Ref-784 | Operator theory / Koopman spectral expansion / ETF allocation | 10062 | 3202 | No |
| 6278 | Bayesian Scholarly Copula Cointegration System Ref-976 | Koopman operator / Model predictive control / ETF rebalancing | 5875 | 3248 | No |
| 6296 | Bayesian Scholarly Copula Cointegration System Sys-176 | Koopman operator / Model predictive control / ETF rebalancing | 13628 | 13737 | No |
| 6305 | Bayesian Scholarly Copula Cointegration System Sys-272 | Persistence landscapes / Topological contours / Equity index | 4720 | 3310 | No |
| 6313 | Bayesian Scholarly Copula Cointegration System Sys-368 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12548 | 11939 | No |
| 6320 | Bayesian Scholarly Copula Cointegration System Sys-464 | Operator theory / Koopman spectral expansion / ETF allocation | 9338 | 8501 | No |
| 6337 | Bayesian Scholarly Copula Cointegration System Sys-656 | Koopman operator / Model predictive control / ETF rebalancing | 13631 | 13746 | No |
| 6346 | Bayesian Scholarly Copula Cointegration System Sys-752 | Persistence landscapes / Topological contours / Equity index | 4751 | 3405 | No |
| 6354 | Bayesian Scholarly Copula Cointegration System Sys-848 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12555 | 11962 | No |
| 6361 | Bayesian Scholarly Copula Cointegration System Sys-944 | Operator theory / Koopman spectral expansion / ETF allocation | 9354 | 8536 | No |
| 6378 | Bayesian Scholarly Copula Cointegration System Sys-1136 | Koopman operator / Model predictive control / ETF rebalancing | 13634 | 13755 | No |
| 6387 | Bayesian Scholarly Copula Cointegration System Sys-1232 | Persistence landscapes / Topological contours / Equity index | 4782 | 3500 | No |
| 6395 | Bayesian Scholarly Copula Cointegration System Sys-1328 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12562 | 11985 | No |
| 6402 | Bayesian Scholarly Copula Cointegration System Sys-1424 | Operator theory / Koopman spectral expansion / ETF allocation | 9370 | 8571 | No |
| 6419 | Bayesian Scholarly Copula Cointegration System Sys-1616 | Koopman operator / Model predictive control / ETF rebalancing | 13637 | 13764 | No |
| 6428 | Bayesian Scholarly Copula Cointegration System Sys-1712 | Persistence landscapes / Topological contours / Equity index | 4813 | 3595 | No |
| 6436 | Bayesian Scholarly Copula Cointegration System Sys-1808 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12569 | 12008 | No |
| 6443 | Bayesian Scholarly Copula Cointegration System Sys-1904 | Operator theory / Koopman spectral expansion / ETF allocation | 9386 | 8606 | No |
| 6468 | Bayesian Scholarly Copula Cointegration System Mod-176 | Koopman operator / Model predictive control / ETF rebalancing | 13642 | 13776 | No |
| 6477 | Bayesian Scholarly Copula Cointegration System Mod-272 | Persistence landscapes / Topological contours / Equity index | 4847 | 3704 | No |
| 6488 | Bayesian Scholarly Copula Cointegration System Mod-368 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12575 | 12035 | No |
| 6498 | Bayesian Scholarly Copula Cointegration System Mod-464 | Operator theory / Koopman spectral expansion / ETF allocation | 9404 | 8648 | No |
| 6513 | Bayesian Scholarly Copula Cointegration System Mod-656 | Koopman operator / Model predictive control / ETF rebalancing | 13646 | 13785 | No |
| 6522 | Bayesian Scholarly Copula Cointegration System Mod-752 | Persistence landscapes / Topological contours / Equity index | 4874 | 3799 | No |
| 6533 | Bayesian Scholarly Copula Cointegration System Mod-848 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12578 | 12058 | No |
| 6543 | Bayesian Scholarly Copula Cointegration System Mod-944 | Operator theory / Koopman spectral expansion / ETF allocation | 9421 | 8685 | No |
| 6558 | Bayesian Scholarly Copula Cointegration System Mod-1136 | Koopman operator / Model predictive control / ETF rebalancing | 13650 | 13794 | No |
| 6567 | Bayesian Scholarly Copula Cointegration System Mod-1232 | Persistence landscapes / Topological contours / Equity index | 4901 | 3894 | No |
| 6578 | Bayesian Scholarly Copula Cointegration System Mod-1328 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12581 | 12081 | No |
| 6588 | Bayesian Scholarly Copula Cointegration System Mod-1424 | Operator theory / Koopman spectral expansion / ETF allocation | 9438 | 8722 | No |
| 6603 | Bayesian Scholarly Copula Cointegration System Mod-1616 | Koopman operator / Model predictive control / ETF rebalancing | 13654 | 13803 | No |
| 6612 | Bayesian Scholarly Copula Cointegration System Mod-1712 | Persistence landscapes / Topological contours / Equity index | 4928 | 3989 | No |
| 6623 | Bayesian Scholarly Copula Cointegration System Mod-1808 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12584 | 12104 | No |
| 6633 | Bayesian Scholarly Copula Cointegration System Mod-1904 | Operator theory / Koopman spectral expansion / ETF allocation | 9455 | 8759 | No |
| 6648 | Bayesian Scholarly Copula Cointegration System Mod-2096 | Koopman operator / Model predictive control / ETF rebalancing | 13658 | 13812 | No |
| 6657 | Bayesian Scholarly Copula Cointegration System Mod-2192 | Persistence landscapes / Topological contours / Equity index | 4955 | 4084 | No |
| 6668 | Bayesian Scholarly Copula Cointegration System Mod-2288 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12587 | 12127 | No |
| 6678 | Bayesian Scholarly Copula Cointegration System Mod-2384 | Operator theory / Koopman spectral expansion / ETF allocation | 9472 | 8796 | No |
| 6693 | Bayesian Scholarly Copula Cointegration System Mod-2576 | Koopman operator / Model predictive control / ETF rebalancing | 13662 | 13821 | No |
| 6702 | Bayesian Scholarly Copula Cointegration System Mod-2672 | Persistence landscapes / Topological contours / Equity index | 4982 | 4179 | No |
| 6713 | Bayesian Scholarly Copula Cointegration System Mod-2768 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12590 | 12150 | No |
| 6723 | Bayesian Scholarly Copula Cointegration System Mod-2864 | Operator theory / Koopman spectral expansion / ETF allocation | 9489 | 8833 | No |
| 6738 | Bayesian Scholarly Copula Cointegration System Mod-3056 | Koopman operator / Model predictive control / ETF rebalancing | 13666 | 13830 | No |
| 6747 | Bayesian Scholarly Copula Cointegration System Mod-3152 | Persistence landscapes / Topological contours / Equity index | 5009 | 4274 | No |
| 6758 | Bayesian Scholarly Copula Cointegration System Mod-3248 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12593 | 12173 | No |
| 6768 | Bayesian Scholarly Copula Cointegration System Mod-3344 | Operator theory / Koopman spectral expansion / ETF allocation | 9506 | 8870 | No |
| 6783 | Bayesian Scholarly Copula Cointegration System Mod-3536 | Koopman operator / Model predictive control / ETF rebalancing | 13670 | 13839 | No |
| 6792 | Bayesian Scholarly Copula Cointegration System Mod-3632 | Persistence landscapes / Topological contours / Equity index | 5036 | 4369 | No |
| 6803 | Bayesian Scholarly Copula Cointegration System Mod-3728 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12596 | 12196 | No |
| 6813 | Bayesian Scholarly Copula Cointegration System Mod-3824 | Operator theory / Koopman spectral expansion / ETF allocation | 9523 | 8907 | No |
| 6845 | Bayesian Scholarly Copula Cointegration System Eng-176 | Koopman operator / Model predictive control / ETF rebalancing | 13675 | 13849 | No |
| 6855 | Bayesian Scholarly Copula Cointegration System Eng-272 | Persistence landscapes / Topological contours / Equity index | 5071 | 4495 | No |
| 6863 | Bayesian Scholarly Copula Cointegration System Eng-368 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12600 | 12227 | No |
| 6872 | Bayesian Scholarly Copula Cointegration System Eng-464 | Operator theory / Koopman spectral expansion / ETF allocation | 9544 | 8955 | No |
| 6891 | Bayesian Scholarly Copula Cointegration System Eng-656 | Koopman operator / Model predictive control / ETF rebalancing | 13679 | 13858 | No |
| 6901 | Bayesian Scholarly Copula Cointegration System Eng-752 | Persistence landscapes / Topological contours / Equity index | 5096 | 4588 | No |
| 6909 | Bayesian Scholarly Copula Cointegration System Eng-848 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12603 | 12250 | No |
| 6918 | Bayesian Scholarly Copula Cointegration System Eng-944 | Operator theory / Koopman spectral expansion / ETF allocation | 9560 | 8990 | No |
| 6937 | Bayesian Scholarly Copula Cointegration System Eng-1136 | Koopman operator / Model predictive control / ETF rebalancing | 13683 | 13867 | No |
| 6947 | Bayesian Scholarly Copula Cointegration System Eng-1232 | Persistence landscapes / Topological contours / Equity index | 5121 | 4681 | No |
| 6955 | Bayesian Scholarly Copula Cointegration System Eng-1328 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12606 | 12273 | No |
| 6964 | Bayesian Scholarly Copula Cointegration System Eng-1424 | Operator theory / Koopman spectral expansion / ETF allocation | 9576 | 9025 | No |
| 6983 | Bayesian Scholarly Copula Cointegration System Eng-1616 | Koopman operator / Model predictive control / ETF rebalancing | 13687 | 13876 | No |
| 6993 | Bayesian Scholarly Copula Cointegration System Eng-1712 | Persistence landscapes / Topological contours / Equity index | 5146 | 4774 | No |
| 7001 | Bayesian Scholarly Copula Cointegration System Eng-1808 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12609 | 12296 | No |
| 7010 | Bayesian Scholarly Copula Cointegration System Eng-1904 | Operator theory / Koopman spectral expansion / ETF allocation | 9592 | 9060 | No |
| 7029 | Bayesian Scholarly Copula Cointegration System Eng-2096 | Koopman operator / Model predictive control / ETF rebalancing | 13691 | 13885 | No |
| 7039 | Bayesian Scholarly Copula Cointegration System Eng-2192 | Persistence landscapes / Topological contours / Equity index | 5171 | 4867 | No |
| 7047 | Bayesian Scholarly Copula Cointegration System Eng-2288 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12612 | 12319 | No |
| 7056 | Bayesian Scholarly Copula Cointegration System Eng-2384 | Operator theory / Koopman spectral expansion / ETF allocation | 9608 | 9095 | No |
| 7075 | Bayesian Scholarly Copula Cointegration System Eng-2576 | Koopman operator / Model predictive control / ETF rebalancing | 13695 | 13894 | No |
| 7085 | Bayesian Scholarly Copula Cointegration System Eng-2672 | Persistence landscapes / Topological contours / Equity index | 5196 | 4960 | No |
| 7093 | Bayesian Scholarly Copula Cointegration System Eng-2768 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12615 | 12342 | No |
| 7102 | Bayesian Scholarly Copula Cointegration System Eng-2864 | Operator theory / Koopman spectral expansion / ETF allocation | 9624 | 9130 | No |
| 7121 | Bayesian Scholarly Copula Cointegration System Eng-3056 | Koopman operator / Model predictive control / ETF rebalancing | 13699 | 13903 | No |
| 7131 | Bayesian Scholarly Copula Cointegration System Eng-3152 | Persistence landscapes / Topological contours / Equity index | 5221 | 5053 | No |
| 7139 | Bayesian Scholarly Copula Cointegration System Eng-3248 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12618 | 12365 | No |
| 7148 | Bayesian Scholarly Copula Cointegration System Eng-3344 | Operator theory / Koopman spectral expansion / ETF allocation | 9640 | 9165 | No |
| 7167 | Bayesian Scholarly Copula Cointegration System Eng-3536 | Koopman operator / Model predictive control / ETF rebalancing | 13703 | 13912 | No |
| 7177 | Bayesian Scholarly Copula Cointegration System Eng-3632 | Persistence landscapes / Topological contours / Equity index | 5246 | 5146 | No |
| 7185 | Bayesian Scholarly Copula Cointegration System Eng-3728 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12621 | 12388 | No |
| 7194 | Bayesian Scholarly Copula Cointegration System Eng-3824 | Operator theory / Koopman spectral expansion / ETF allocation | 9656 | 9200 | No |
| 7213 | Bayesian Scholarly Copula Cointegration System Eng-4016 | Koopman operator / Model predictive control / ETF rebalancing | 13707 | 13921 | No |
| 7223 | Bayesian Scholarly Copula Cointegration System Eng-4112 | Persistence landscapes / Topological contours / Equity index | 5271 | 5239 | No |
| 7231 | Bayesian Scholarly Copula Cointegration System Eng-4208 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12624 | 12411 | No |
| 7240 | Bayesian Scholarly Copula Cointegration System Eng-4304 | Operator theory / Koopman spectral expansion / ETF allocation | 9672 | 9235 | No |
| 7259 | Bayesian Scholarly Copula Cointegration System Eng-4496 | Koopman operator / Model predictive control / ETF rebalancing | 13711 | 13930 | No |
| 7269 | Bayesian Scholarly Copula Cointegration System Eng-4592 | Persistence landscapes / Topological contours / Equity index | 5296 | 5332 | No |
| 7277 | Bayesian Scholarly Copula Cointegration System Eng-4688 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12627 | 12434 | No |
| 7286 | Bayesian Scholarly Copula Cointegration System Eng-4784 | Operator theory / Koopman spectral expansion / ETF allocation | 9688 | 9270 | No |
| 7305 | Bayesian Scholarly Copula Cointegration System Eng-4976 | Koopman operator / Model predictive control / ETF rebalancing | 13715 | 13939 | No |
| 7315 | Bayesian Scholarly Copula Cointegration System Eng-5072 | Persistence landscapes / Topological contours / Equity index | 5321 | 5425 | No |
| 7323 | Bayesian Scholarly Copula Cointegration System Eng-5168 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12630 | 12457 | No |
| 7332 | Bayesian Scholarly Copula Cointegration System Eng-5264 | Operator theory / Koopman spectral expansion / ETF allocation | 9704 | 9305 | No |
| 7351 | Bayesian Scholarly Copula Cointegration System Eng-5456 | Koopman operator / Model predictive control / ETF rebalancing | 13719 | 13948 | No |
| 7361 | Bayesian Scholarly Copula Cointegration System Eng-5552 | Persistence landscapes / Topological contours / Equity index | 5346 | 5518 | No |
| 7369 | Bayesian Scholarly Copula Cointegration System Eng-5648 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12633 | 12480 | No |
| 7378 | Bayesian Scholarly Copula Cointegration System Eng-5744 | Operator theory / Koopman spectral expansion / ETF allocation | 9720 | 9340 | No |
| 7397 | Bayesian Scholarly Copula Cointegration System Eng-5936 | Koopman operator / Model predictive control / ETF rebalancing | 13723 | 13957 | No |
