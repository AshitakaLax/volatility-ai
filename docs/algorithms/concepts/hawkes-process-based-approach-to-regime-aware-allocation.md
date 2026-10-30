# Hawkes-process-based approach to regime-aware allocation

**Concept page** · shared by **136** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,746) ·
researched 2026-10-30

| | |
|---|---|
| Task | Regime-aware allocation |
| Method | Hawkes (self-exciting) point processes |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of Hawkes processes identifying market regimes better than a volatility threshold; the project's NATR regime (V17, N5) is the bar. |
| Implemented in volatility-ai | The NATR regime exit (V17, causal N5) runs through the Ultimate family's `lots_to_liquidate` and `allow_signal_exit`; HMM and Gaussian-mixture regimes are research code (C-R3). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | V17, N5, N6, C-R3, RK102, RK104 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Hawkes Scholarly Regime
Switching Allocator Ref-200") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Infer the market's state from prices, volatility or macro data and vary
exposure by regime. The Hawkes version models events (trades, jumps,
crashes) as self-exciting, each event raising the near-term chance of
another. I found no study of this method on this task.

## The CSV's description

Proposed Hawkes-process-based approach to regime-aware allocation: Infer
changing market states from available price, volatility, or
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
* Hawkes models describe intraday event clustering; daily bars hold too
  few events to fit them.

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
| 1746 | Hawkes Scholarly Regime Switching Allocator Ref-200 | Fractional order / Multi-scale ETF momentum | 5833 | 2158 | No |
| 1801 | Hawkes Scholarly Regime Switching Allocator Ref-680 | Fractional order / Multi-scale ETF momentum | 5858 | 2183 | No |
| 1841 | Hawkes Scholarly Regime Switching Allocator Sys-40 | Fractional order / Multi-scale ETF momentum | 4705 | 487 | No |
| 1890 | Hawkes Scholarly Regime Switching Allocator Sys-520 | Fractional order / Multi-scale ETF momentum | 4736 | 506 | No |
| 1939 | Hawkes Scholarly Regime Switching Allocator Sys-1000 | Fractional order / Multi-scale ETF momentum | 4767 | 525 | No |
| 1988 | Hawkes Scholarly Regime Switching Allocator Sys-1480 | Fractional order / Multi-scale ETF momentum | 4798 | 544 | No |
| 2037 | Hawkes Scholarly Regime Switching Allocator Sys-1960 | Fractional order / Multi-scale ETF momentum | 4829 | 563 | No |
| 2068 | Hawkes Scholarly Regime Switching Allocator Mod-280 | Fractional order / Multi-scale ETF momentum | 4848 | 574 | No |
| 2121 | Hawkes Scholarly Regime Switching Allocator Mod-760 | Fractional order / Multi-scale ETF momentum | 4875 | 593 | No |
| 2174 | Hawkes Scholarly Regime Switching Allocator Mod-1240 | Fractional order / Multi-scale ETF momentum | 4902 | 612 | No |
| 2227 | Hawkes Scholarly Regime Switching Allocator Mod-1720 | Fractional order / Multi-scale ETF momentum | 4929 | 631 | No |
| 2280 | Hawkes Scholarly Regime Switching Allocator Mod-2200 | Fractional order / Multi-scale ETF momentum | 4956 | 650 | No |
| 2333 | Hawkes Scholarly Regime Switching Allocator Mod-2680 | Fractional order / Multi-scale ETF momentum | 4983 | 669 | No |
| 2386 | Hawkes Scholarly Regime Switching Allocator Mod-3160 | Fractional order / Multi-scale ETF momentum | 5010 | 688 | No |
| 2439 | Hawkes Scholarly Regime Switching Allocator Mod-3640 | Fractional order / Multi-scale ETF momentum | 5037 | 707 | No |
| 2483 | Hawkes Scholarly Regime Switching Allocator Eng-40 | Fractional order / Multi-scale ETF momentum | 5059 | 722 | No |
| 2538 | Hawkes Scholarly Regime Switching Allocator Eng-520 | Fractional order / Multi-scale ETF momentum | 5084 | 741 | No |
| 2593 | Hawkes Scholarly Regime Switching Allocator Eng-1000 | Fractional order / Multi-scale ETF momentum | 5109 | 760 | No |
| 2648 | Hawkes Scholarly Regime Switching Allocator Eng-1480 | Fractional order / Multi-scale ETF momentum | 5134 | 779 | No |
| 2703 | Hawkes Scholarly Regime Switching Allocator Eng-1960 | Fractional order / Multi-scale ETF momentum | 5159 | 798 | No |
| 2758 | Hawkes Scholarly Regime Switching Allocator Eng-2440 | Fractional order / Multi-scale ETF momentum | 5184 | 817 | No |
| 2813 | Hawkes Scholarly Regime Switching Allocator Eng-2920 | Fractional order / Multi-scale ETF momentum | 5209 | 836 | No |
| 2868 | Hawkes Scholarly Regime Switching Allocator Eng-3400 | Fractional order / Multi-scale ETF momentum | 5234 | 855 | No |
| 2923 | Hawkes Scholarly Regime Switching Allocator Eng-3880 | Fractional order / Multi-scale ETF momentum | 5259 | 874 | No |
| 2978 | Hawkes Scholarly Regime Switching Allocator Eng-4360 | Fractional order / Multi-scale ETF momentum | 5284 | 893 | No |
| 3033 | Hawkes Scholarly Regime Switching Allocator Eng-4840 | Fractional order / Multi-scale ETF momentum | 5309 | 912 | No |
| 3088 | Hawkes Scholarly Regime Switching Allocator Eng-5320 | Fractional order / Multi-scale ETF momentum | 5334 | 931 | No |
| 3143 | Hawkes Scholarly Regime Switching Allocator Eng-5800 | Fractional order / Multi-scale ETF momentum | 5359 | 950 | No |
| 8679 | Hawkes Scholarly Regime Switching Allocator Ref-8 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12520 | 11874 | No |
| 8717 | Hawkes Scholarly Regime Switching Allocator Ref-104 | Operator theory / Koopman spectral expansion / ETF allocation | 9294 | 8429 | No |
| 8792 | Hawkes Scholarly Regime Switching Allocator Ref-296 | Koopman operator / Model predictive control / ETF rebalancing | 13616 | 13718 | No |
| 8831 | Hawkes Scholarly Regime Switching Allocator Ref-392 | Persistence landscapes / Topological contours / Equity index | 4666 | 3108 | No |
| 8870 | Hawkes Scholarly Regime Switching Allocator Ref-488 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12531 | 11897 | No |
| 8908 | Hawkes Scholarly Regime Switching Allocator Ref-584 | Operator theory / Koopman spectral expansion / ETF allocation | 9310 | 8449 | No |
| 8983 | Hawkes Scholarly Regime Switching Allocator Ref-776 | Koopman operator / Model predictive control / ETF rebalancing | 13624 | 13729 | No |
| 9022 | Hawkes Scholarly Regime Switching Allocator Ref-872 | Persistence landscapes / Topological contours / Equity index | 4693 | 3225 | No |
| 9061 | Hawkes Scholarly Regime Switching Allocator Ref-968 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 12542 | 11920 | No |
| 9125 | Hawkes Scholarly Regime Switching Allocator Sys-136 | Koopman operator / Model predictive control / ETF rebalancing | 5882 | 3281 | No |
| 9164 | Hawkes Scholarly Regime Switching Allocator Sys-232 | Persistence landscapes / Topological contours / Equity index | 8338 | 12567 | No |
| 9203 | Hawkes Scholarly Regime Switching Allocator Sys-328 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1138 | 3321 | No |
| 9239 | Hawkes Scholarly Regime Switching Allocator Sys-424 | Operator theory / Koopman spectral expansion / ETF allocation | 10074 | 3341 | No |
| 9312 | Hawkes Scholarly Regime Switching Allocator Sys-616 | Koopman operator / Model predictive control / ETF rebalancing | 5902 | 3376 | No |
| 9351 | Hawkes Scholarly Regime Switching Allocator Sys-712 | Persistence landscapes / Topological contours / Equity index | 8378 | 12579 | No |
| 9390 | Hawkes Scholarly Regime Switching Allocator Sys-808 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1168 | 3416 | No |
| 9426 | Hawkes Scholarly Regime Switching Allocator Sys-904 | Operator theory / Koopman spectral expansion / ETF allocation | 10085 | 3436 | No |
| 9499 | Hawkes Scholarly Regime Switching Allocator Sys-1096 | Koopman operator / Model predictive control / ETF rebalancing | 5922 | 3471 | No |
| 9538 | Hawkes Scholarly Regime Switching Allocator Sys-1192 | Persistence landscapes / Topological contours / Equity index | 8418 | 12591 | No |
| 9577 | Hawkes Scholarly Regime Switching Allocator Sys-1288 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1198 | 3511 | No |
| 9613 | Hawkes Scholarly Regime Switching Allocator Sys-1384 | Operator theory / Koopman spectral expansion / ETF allocation | 10096 | 3531 | No |
| 9686 | Hawkes Scholarly Regime Switching Allocator Sys-1576 | Koopman operator / Model predictive control / ETF rebalancing | 5942 | 3566 | No |
| 9725 | Hawkes Scholarly Regime Switching Allocator Sys-1672 | Persistence landscapes / Topological contours / Equity index | 8458 | 12603 | No |
| 9764 | Hawkes Scholarly Regime Switching Allocator Sys-1768 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1228 | 3606 | No |
| 9800 | Hawkes Scholarly Regime Switching Allocator Sys-1864 | Operator theory / Koopman spectral expansion / ETF allocation | 10107 | 3626 | No |
| 9887 | Hawkes Scholarly Regime Switching Allocator Mod-88 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1248 | 3668 | No |
| 9923 | Hawkes Scholarly Regime Switching Allocator Mod-184 | Operator theory / Koopman spectral expansion / ETF allocation | 10117 | 3687 | No |
| 10003 | Hawkes Scholarly Regime Switching Allocator Mod-376 | Koopman operator / Model predictive control / ETF rebalancing | 5978 | 3727 | No |
| 10041 | Hawkes Scholarly Regime Switching Allocator Mod-472 | Persistence landscapes / Topological contours / Equity index | 8524 | 12617 | No |
| 10078 | Hawkes Scholarly Regime Switching Allocator Mod-568 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1279 | 3763 | No |
| 10114 | Hawkes Scholarly Regime Switching Allocator Mod-664 | Operator theory / Koopman spectral expansion / ETF allocation | 10129 | 3782 | No |
| 10194 | Hawkes Scholarly Regime Switching Allocator Mod-856 | Koopman operator / Model predictive control / ETF rebalancing | 6002 | 3822 | No |
| 10232 | Hawkes Scholarly Regime Switching Allocator Mod-952 | Persistence landscapes / Topological contours / Equity index | 8562 | 12625 | No |
| 10269 | Hawkes Scholarly Regime Switching Allocator Mod-1048 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1310 | 3858 | No |
| 10305 | Hawkes Scholarly Regime Switching Allocator Mod-1144 | Operator theory / Koopman spectral expansion / ETF allocation | 10141 | 3877 | No |
| 10385 | Hawkes Scholarly Regime Switching Allocator Mod-1336 | Koopman operator / Model predictive control / ETF rebalancing | 6026 | 3917 | No |
| 10423 | Hawkes Scholarly Regime Switching Allocator Mod-1432 | Persistence landscapes / Topological contours / Equity index | 8600 | 12633 | No |
| 10460 | Hawkes Scholarly Regime Switching Allocator Mod-1528 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1341 | 3953 | No |
| 10496 | Hawkes Scholarly Regime Switching Allocator Mod-1624 | Operator theory / Koopman spectral expansion / ETF allocation | 10153 | 3972 | No |
| 10576 | Hawkes Scholarly Regime Switching Allocator Mod-1816 | Koopman operator / Model predictive control / ETF rebalancing | 6050 | 4012 | No |
| 10614 | Hawkes Scholarly Regime Switching Allocator Mod-1912 | Persistence landscapes / Topological contours / Equity index | 8638 | 12641 | No |
| 10651 | Hawkes Scholarly Regime Switching Allocator Mod-2008 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1372 | 4048 | No |
| 10687 | Hawkes Scholarly Regime Switching Allocator Mod-2104 | Operator theory / Koopman spectral expansion / ETF allocation | 10165 | 4067 | No |
| 10767 | Hawkes Scholarly Regime Switching Allocator Mod-2296 | Koopman operator / Model predictive control / ETF rebalancing | 6074 | 4107 | No |
| 10805 | Hawkes Scholarly Regime Switching Allocator Mod-2392 | Persistence landscapes / Topological contours / Equity index | 8676 | 12649 | No |
| 10842 | Hawkes Scholarly Regime Switching Allocator Mod-2488 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1403 | 4143 | No |
| 10878 | Hawkes Scholarly Regime Switching Allocator Mod-2584 | Operator theory / Koopman spectral expansion / ETF allocation | 10177 | 4162 | No |
| 10958 | Hawkes Scholarly Regime Switching Allocator Mod-2776 | Koopman operator / Model predictive control / ETF rebalancing | 6098 | 4202 | No |
| 10996 | Hawkes Scholarly Regime Switching Allocator Mod-2872 | Persistence landscapes / Topological contours / Equity index | 8714 | 12657 | No |
| 11033 | Hawkes Scholarly Regime Switching Allocator Mod-2968 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1434 | 4238 | No |
| 11069 | Hawkes Scholarly Regime Switching Allocator Mod-3064 | Operator theory / Koopman spectral expansion / ETF allocation | 10189 | 4257 | No |
| 11149 | Hawkes Scholarly Regime Switching Allocator Mod-3256 | Koopman operator / Model predictive control / ETF rebalancing | 6122 | 4297 | No |
| 11187 | Hawkes Scholarly Regime Switching Allocator Mod-3352 | Persistence landscapes / Topological contours / Equity index | 8752 | 12665 | No |
| 11224 | Hawkes Scholarly Regime Switching Allocator Mod-3448 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1465 | 4333 | No |
| 11260 | Hawkes Scholarly Regime Switching Allocator Mod-3544 | Operator theory / Koopman spectral expansion / ETF allocation | 10201 | 4352 | No |
| 11340 | Hawkes Scholarly Regime Switching Allocator Mod-3736 | Koopman operator / Model predictive control / ETF rebalancing | 6146 | 4392 | No |
| 11378 | Hawkes Scholarly Regime Switching Allocator Mod-3832 | Persistence landscapes / Topological contours / Equity index | 8790 | 12673 | No |
| 11415 | Hawkes Scholarly Regime Switching Allocator Mod-3928 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1496 | 4428 | No |
| 11499 | Hawkes Scholarly Regime Switching Allocator Eng-136 | Koopman operator / Model predictive control / ETF rebalancing | 6165 | 4468 | No |
| 11535 | Hawkes Scholarly Regime Switching Allocator Eng-232 | Persistence landscapes / Topological contours / Equity index | 8823 | 12683 | No |
| 11571 | Hawkes Scholarly Regime Switching Allocator Eng-328 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1519 | 4508 | No |
| 11613 | Hawkes Scholarly Regime Switching Allocator Eng-424 | Operator theory / Koopman spectral expansion / ETF allocation | 10222 | 4529 | No |
| 11690 | Hawkes Scholarly Regime Switching Allocator Eng-616 | Koopman operator / Model predictive control / ETF rebalancing | 6187 | 4561 | No |
| 11726 | Hawkes Scholarly Regime Switching Allocator Eng-712 | Persistence landscapes / Topological contours / Equity index | 8859 | 12691 | No |
| 11762 | Hawkes Scholarly Regime Switching Allocator Eng-808 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1549 | 4601 | No |
| 11804 | Hawkes Scholarly Regime Switching Allocator Eng-904 | Operator theory / Koopman spectral expansion / ETF allocation | 10235 | 4622 | No |
| 11881 | Hawkes Scholarly Regime Switching Allocator Eng-1096 | Koopman operator / Model predictive control / ETF rebalancing | 6209 | 4654 | No |
| 11917 | Hawkes Scholarly Regime Switching Allocator Eng-1192 | Persistence landscapes / Topological contours / Equity index | 8895 | 12699 | No |
| 11953 | Hawkes Scholarly Regime Switching Allocator Eng-1288 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1579 | 4694 | No |
| 11995 | Hawkes Scholarly Regime Switching Allocator Eng-1384 | Operator theory / Koopman spectral expansion / ETF allocation | 10248 | 4715 | No |
| 12072 | Hawkes Scholarly Regime Switching Allocator Eng-1576 | Koopman operator / Model predictive control / ETF rebalancing | 6231 | 4747 | No |
| 12108 | Hawkes Scholarly Regime Switching Allocator Eng-1672 | Persistence landscapes / Topological contours / Equity index | 8931 | 12707 | No |
| 12144 | Hawkes Scholarly Regime Switching Allocator Eng-1768 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1609 | 4787 | No |
| 12186 | Hawkes Scholarly Regime Switching Allocator Eng-1864 | Operator theory / Koopman spectral expansion / ETF allocation | 10261 | 4808 | No |
| 12263 | Hawkes Scholarly Regime Switching Allocator Eng-2056 | Koopman operator / Model predictive control / ETF rebalancing | 6253 | 4840 | No |
| 12299 | Hawkes Scholarly Regime Switching Allocator Eng-2152 | Persistence landscapes / Topological contours / Equity index | 8967 | 12715 | No |
| 12335 | Hawkes Scholarly Regime Switching Allocator Eng-2248 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1639 | 4880 | No |
| 12377 | Hawkes Scholarly Regime Switching Allocator Eng-2344 | Operator theory / Koopman spectral expansion / ETF allocation | 10274 | 4901 | No |
| 12454 | Hawkes Scholarly Regime Switching Allocator Eng-2536 | Koopman operator / Model predictive control / ETF rebalancing | 6275 | 4933 | No |
| 12490 | Hawkes Scholarly Regime Switching Allocator Eng-2632 | Persistence landscapes / Topological contours / Equity index | 9003 | 12723 | No |
| 12526 | Hawkes Scholarly Regime Switching Allocator Eng-2728 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1669 | 4973 | No |
| 12568 | Hawkes Scholarly Regime Switching Allocator Eng-2824 | Operator theory / Koopman spectral expansion / ETF allocation | 10287 | 4994 | No |
| 12645 | Hawkes Scholarly Regime Switching Allocator Eng-3016 | Koopman operator / Model predictive control / ETF rebalancing | 6297 | 5026 | No |
| 12681 | Hawkes Scholarly Regime Switching Allocator Eng-3112 | Persistence landscapes / Topological contours / Equity index | 9039 | 12731 | No |
| 12717 | Hawkes Scholarly Regime Switching Allocator Eng-3208 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1699 | 5066 | No |
| 12759 | Hawkes Scholarly Regime Switching Allocator Eng-3304 | Operator theory / Koopman spectral expansion / ETF allocation | 10300 | 5087 | No |
| 12836 | Hawkes Scholarly Regime Switching Allocator Eng-3496 | Koopman operator / Model predictive control / ETF rebalancing | 6319 | 5119 | No |
| 12872 | Hawkes Scholarly Regime Switching Allocator Eng-3592 | Persistence landscapes / Topological contours / Equity index | 9075 | 12739 | No |
| 12908 | Hawkes Scholarly Regime Switching Allocator Eng-3688 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1729 | 5159 | No |
| 12950 | Hawkes Scholarly Regime Switching Allocator Eng-3784 | Operator theory / Koopman spectral expansion / ETF allocation | 10313 | 5180 | No |
| 13027 | Hawkes Scholarly Regime Switching Allocator Eng-3976 | Koopman operator / Model predictive control / ETF rebalancing | 6341 | 5212 | No |
| 13063 | Hawkes Scholarly Regime Switching Allocator Eng-4072 | Persistence landscapes / Topological contours / Equity index | 9111 | 12747 | No |
| 13099 | Hawkes Scholarly Regime Switching Allocator Eng-4168 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1759 | 5252 | No |
| 13141 | Hawkes Scholarly Regime Switching Allocator Eng-4264 | Operator theory / Koopman spectral expansion / ETF allocation | 10326 | 5273 | No |
| 13218 | Hawkes Scholarly Regime Switching Allocator Eng-4456 | Koopman operator / Model predictive control / ETF rebalancing | 6363 | 5305 | No |
| 13254 | Hawkes Scholarly Regime Switching Allocator Eng-4552 | Persistence landscapes / Topological contours / Equity index | 9147 | 12755 | No |
| 13290 | Hawkes Scholarly Regime Switching Allocator Eng-4648 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1789 | 5345 | No |
| 13332 | Hawkes Scholarly Regime Switching Allocator Eng-4744 | Operator theory / Koopman spectral expansion / ETF allocation | 10339 | 5366 | No |
| 13409 | Hawkes Scholarly Regime Switching Allocator Eng-4936 | Koopman operator / Model predictive control / ETF rebalancing | 6385 | 5398 | No |
| 13445 | Hawkes Scholarly Regime Switching Allocator Eng-5032 | Persistence landscapes / Topological contours / Equity index | 9183 | 12763 | No |
| 13481 | Hawkes Scholarly Regime Switching Allocator Eng-5128 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1819 | 5438 | No |
| 13523 | Hawkes Scholarly Regime Switching Allocator Eng-5224 | Operator theory / Koopman spectral expansion / ETF allocation | 10352 | 5459 | No |
| 13600 | Hawkes Scholarly Regime Switching Allocator Eng-5416 | Koopman operator / Model predictive control / ETF rebalancing | 6407 | 5491 | No |
| 13636 | Hawkes Scholarly Regime Switching Allocator Eng-5512 | Persistence landscapes / Topological contours / Equity index | 9219 | 12771 | No |
| 13672 | Hawkes Scholarly Regime Switching Allocator Eng-5608 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1849 | 5531 | No |
| 13714 | Hawkes Scholarly Regime Switching Allocator Eng-5704 | Operator theory / Koopman spectral expansion / ETF allocation | 10365 | 5552 | No |
| 13791 | Hawkes Scholarly Regime Switching Allocator Eng-5896 | Koopman operator / Model predictive control / ETF rebalancing | 6429 | 5584 | No |
| 13827 | Hawkes Scholarly Regime Switching Allocator Eng-5992 | Persistence landscapes / Topological contours / Equity index | 9255 | 12779 | No |
