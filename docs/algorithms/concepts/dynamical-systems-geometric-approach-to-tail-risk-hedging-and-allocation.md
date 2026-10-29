# Dynamical-systems/geometric approach to tail-risk hedging and allocation

**Concept page** · shared by **136** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(4 of them in ranks 426–700; best-ranked member #682) ·
researched 2026-10-29

| | |
|---|---|
| Task | Tail-risk hedging and allocation |
| Method | Dynamical-systems / geometric methods |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | The tail-risk response is the regime exit (V17, N5) and drawdown throttle (V11); no hedge allocation. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | V17, N5, V11, X5, X8, RK23 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Symplectic Scholarly
Tail-Risk Hedge Allocator Ref-300") combine a method word, "Scholarly",
a task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Model stress with dynamical-systems or geometric methods and allocate
hedges. I found no study of this.

## The CSV's description

Proposed dynamical-systems/geometric approach to tail-risk hedging and
allocation: Estimate stress or extreme-loss risk and allocate defensive
assets or hedges to reduce portfolio downside exposure. This is a
concept-level interpretation of the title, not a complete trading
specification: the exact model inputs/target, calibration, entry/exit or
rebalance rules, and position sizing are not fully defined here.

## Evidence

* **Israelov (2019), "Pathetic Protection: The Elusive Benefits of
  Protective Puts," *Journal of Alternative Investments*:**
  put-protected portfolios had worse peak-to-trough drawdowns per unit
  of expected return than portfolios that simply held less equity; puts
  help only when drawdowns line up with expiries. (Summaries.)
* **Hurst, Ooi & Pedersen (2017), "A Century of Evidence on
  Trend-Following Investing," *Journal of Portfolio Management*:**
  time-series momentum was positive in 8 of the 10 largest drawdowns of
  a 60/40 portfolio since 1880, with low correlation to stocks and
  bonds. (Abstract.)

## Against, and failure modes

* Hedges cost carry in calm markets; a de-risking trigger whipsaws.
* Fast crashes outrun daily triggers (V17's one-day lookahead caveat).

## Fit with volatility-ai

This project's tail-risk answer is to step out rather than hedge: the
regime exit (V17, causal N5) and the drawdown throttle (V11). Hedging
assets were weighed and set aside: Treasuries as the hedge (X5, ❌) and a
long-volatility sleeve (X8, excluded by the owner); options are outside
the instrument rule. A tail-risk model would earn a place only as a
better trigger for the existing exit.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Israelov, R. (2019). "Pathetic Protection." *Journal of Alternative
  Investments*.
  <https://www.aqr.com/insights/research/white-papers/pathetic-protection-the-elusive-benefits-of-protective-puts>.
  Summaries.
* Hurst, B., Ooi, Y. H., Pedersen, L. H. (2017). "A Century of Evidence
  on Trend-Following Investing." *Journal of Portfolio Management*.
  <https://www.aqr.com/Insights/Research/Journal-Article/A-Century-of-Evidence-on-Trend-Following-Investing>.
  Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 682 | Symplectic Scholarly Tail-Risk Hedge Allocator Ref-300 | Fractional order / Multi-scale ETF momentum | 1904 | 318 | No |
| 688 | Symplectic Scholarly Tail-Risk Hedge Allocator Ref-780 | Fractional order / Multi-scale ETF momentum | 1909 | 322 | No |
| 692 | Symplectic Scholarly Tail-Risk Hedge Allocator Sys-300 | Fractional order / Multi-scale ETF momentum | 1914 | 326 | No |
| 699 | Symplectic Scholarly Tail-Risk Hedge Allocator Sys-780 | Fractional order / Multi-scale ETF momentum | 1919 | 330 | No |
| 706 | Symplectic Scholarly Tail-Risk Hedge Allocator Sys-1260 | Fractional order / Multi-scale ETF momentum | 1924 | 334 | No |
| 713 | Symplectic Scholarly Tail-Risk Hedge Allocator Sys-1740 | Fractional order / Multi-scale ETF momentum | 1929 | 338 | No |
| 720 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-180 | Fractional order / Multi-scale ETF momentum | 1933 | 342 | No |
| 726 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-660 | Fractional order / Multi-scale ETF momentum | 1938 | 346 | No |
| 732 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-1140 | Fractional order / Multi-scale ETF momentum | 1943 | 350 | No |
| 738 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-1620 | Fractional order / Multi-scale ETF momentum | 1948 | 354 | No |
| 744 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-2100 | Fractional order / Multi-scale ETF momentum | 1953 | 358 | No |
| 750 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-2580 | Fractional order / Multi-scale ETF momentum | 1958 | 362 | No |
| 756 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-3060 | Fractional order / Multi-scale ETF momentum | 1963 | 366 | No |
| 762 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-3540 | Fractional order / Multi-scale ETF momentum | 1968 | 370 | No |
| 772 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-300 | Fractional order / Multi-scale ETF momentum | 1976 | 376 | No |
| 778 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-780 | Fractional order / Multi-scale ETF momentum | 1981 | 380 | No |
| 784 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-1260 | Fractional order / Multi-scale ETF momentum | 1986 | 384 | No |
| 790 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-1740 | Fractional order / Multi-scale ETF momentum | 1991 | 388 | No |
| 796 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-2220 | Fractional order / Multi-scale ETF momentum | 1996 | 392 | No |
| 802 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-2700 | Fractional order / Multi-scale ETF momentum | 2001 | 396 | No |
| 808 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-3180 | Fractional order / Multi-scale ETF momentum | 2006 | 400 | No |
| 814 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-3660 | Fractional order / Multi-scale ETF momentum | 2011 | 404 | No |
| 820 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-4140 | Fractional order / Multi-scale ETF momentum | 2016 | 408 | No |
| 826 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-4620 | Fractional order / Multi-scale ETF momentum | 2021 | 412 | No |
| 832 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-5100 | Fractional order / Multi-scale ETF momentum | 2026 | 416 | No |
| 838 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-5580 | Fractional order / Multi-scale ETF momentum | 2031 | 420 | No |
| 3773 | Symplectic Scholarly Tail-Risk Hedge Allocator Ref-12 | Persistence landscapes / Topological contours / Equity index | 397 | 1008 | No |
| 3789 | Symplectic Scholarly Tail-Risk Hedge Allocator Ref-108 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1057 | 6535 | No |
| 3806 | Symplectic Scholarly Tail-Risk Hedge Allocator Ref-204 | Operator theory / Koopman spectral expansion / ETF allocation | 2139 | 1021 | No |
| 3843 | Symplectic Scholarly Tail-Risk Hedge Allocator Ref-396 | Koopman operator / Model predictive control / ETF rebalancing | 3883 | 3110 | No |
| 3859 | Symplectic Scholarly Tail-Risk Hedge Allocator Ref-492 | Persistence landscapes / Topological contours / Equity index | 409 | 1043 | No |
| 3875 | Symplectic Scholarly Tail-Risk Hedge Allocator Ref-588 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1091 | 6561 | No |
| 3892 | Symplectic Scholarly Tail-Risk Hedge Allocator Ref-684 | Operator theory / Koopman spectral expansion / ETF allocation | 2171 | 1056 | No |
| 3929 | Symplectic Scholarly Tail-Risk Hedge Allocator Ref-876 | Koopman operator / Model predictive control / ETF rebalancing | 3910 | 3227 | No |
| 3945 | Symplectic Scholarly Tail-Risk Hedge Allocator Ref-972 | Persistence landscapes / Topological contours / Equity index | 421 | 1078 | No |
| 3953 | Symplectic Scholarly Tail-Risk Hedge Allocator Sys-12 | Persistence landscapes / Topological contours / Equity index | 422 | 1081 | No |
| 3970 | Symplectic Scholarly Tail-Risk Hedge Allocator Sys-108 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1126 | 6592 | No |
| 3990 | Symplectic Scholarly Tail-Risk Hedge Allocator Sys-204 | Operator theory / Koopman spectral expansion / ETF allocation | 2213 | 1090 | No |
| 4022 | Symplectic Scholarly Tail-Risk Hedge Allocator Sys-396 | Koopman operator / Model predictive control / ETF rebalancing | 3942 | 3336 | No |
| 4039 | Symplectic Scholarly Tail-Risk Hedge Allocator Sys-492 | Persistence landscapes / Topological contours / Equity index | 430 | 1105 | No |
| 4056 | Symplectic Scholarly Tail-Risk Hedge Allocator Sys-588 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1156 | 6628 | No |
| 4076 | Symplectic Scholarly Tail-Risk Hedge Allocator Sys-684 | Operator theory / Koopman spectral expansion / ETF allocation | 2260 | 1114 | No |
| 4108 | Symplectic Scholarly Tail-Risk Hedge Allocator Sys-876 | Koopman operator / Model predictive control / ETF rebalancing | 3971 | 3431 | No |
| 4125 | Symplectic Scholarly Tail-Risk Hedge Allocator Sys-972 | Persistence landscapes / Topological contours / Equity index | 438 | 1129 | No |
| 4142 | Symplectic Scholarly Tail-Risk Hedge Allocator Sys-1068 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1186 | 6664 | No |
| 4162 | Symplectic Scholarly Tail-Risk Hedge Allocator Sys-1164 | Operator theory / Koopman spectral expansion / ETF allocation | 2307 | 1138 | No |
| 4194 | Symplectic Scholarly Tail-Risk Hedge Allocator Sys-1356 | Koopman operator / Model predictive control / ETF rebalancing | 4000 | 3526 | No |
| 4211 | Symplectic Scholarly Tail-Risk Hedge Allocator Sys-1452 | Persistence landscapes / Topological contours / Equity index | 446 | 1153 | No |
| 4228 | Symplectic Scholarly Tail-Risk Hedge Allocator Sys-1548 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1216 | 6700 | No |
| 4248 | Symplectic Scholarly Tail-Risk Hedge Allocator Sys-1644 | Operator theory / Koopman spectral expansion / ETF allocation | 2354 | 1162 | No |
| 4280 | Symplectic Scholarly Tail-Risk Hedge Allocator Sys-1836 | Koopman operator / Model predictive control / ETF rebalancing | 4029 | 3621 | No |
| 4297 | Symplectic Scholarly Tail-Risk Hedge Allocator Sys-1932 | Persistence landscapes / Topological contours / Equity index | 454 | 1177 | No |
| 4327 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-84 | Operator theory / Koopman spectral expansion / ETF allocation | 2394 | 1184 | No |
| 4363 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-276 | Koopman operator / Model predictive control / ETF rebalancing | 4055 | 3706 | No |
| 4378 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-372 | Persistence landscapes / Topological contours / Equity index | 464 | 1197 | No |
| 4393 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-468 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1273 | 6768 | No |
| 4412 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-564 | Operator theory / Koopman spectral expansion / ETF allocation | 2433 | 1208 | No |
| 4448 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-756 | Koopman operator / Model predictive control / ETF rebalancing | 4081 | 3801 | No |
| 4463 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-852 | Persistence landscapes / Topological contours / Equity index | 474 | 1221 | No |
| 4478 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-948 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1304 | 6802 | No |
| 4497 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-1044 | Operator theory / Koopman spectral expansion / ETF allocation | 2472 | 1232 | No |
| 4533 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-1236 | Koopman operator / Model predictive control / ETF rebalancing | 4107 | 3896 | No |
| 4548 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-1332 | Persistence landscapes / Topological contours / Equity index | 484 | 1245 | No |
| 4563 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-1428 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1335 | 6836 | No |
| 4582 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-1524 | Operator theory / Koopman spectral expansion / ETF allocation | 2511 | 1256 | No |
| 4618 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-1716 | Koopman operator / Model predictive control / ETF rebalancing | 4133 | 3991 | No |
| 4633 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-1812 | Persistence landscapes / Topological contours / Equity index | 494 | 1269 | No |
| 4648 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-1908 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1366 | 6870 | No |
| 4667 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-2004 | Operator theory / Koopman spectral expansion / ETF allocation | 2550 | 1280 | No |
| 4703 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-2196 | Koopman operator / Model predictive control / ETF rebalancing | 4159 | 4086 | No |
| 4718 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-2292 | Persistence landscapes / Topological contours / Equity index | 504 | 1293 | No |
| 4733 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-2388 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1397 | 6904 | No |
| 4752 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-2484 | Operator theory / Koopman spectral expansion / ETF allocation | 2589 | 1304 | No |
| 4788 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-2676 | Koopman operator / Model predictive control / ETF rebalancing | 4185 | 4181 | No |
| 4803 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-2772 | Persistence landscapes / Topological contours / Equity index | 514 | 1317 | No |
| 4818 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-2868 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1428 | 6938 | No |
| 4837 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-2964 | Operator theory / Koopman spectral expansion / ETF allocation | 2628 | 1328 | No |
| 4873 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-3156 | Koopman operator / Model predictive control / ETF rebalancing | 4211 | 4276 | No |
| 4888 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-3252 | Persistence landscapes / Topological contours / Equity index | 524 | 1341 | No |
| 4903 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-3348 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1459 | 6972 | No |
| 4922 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-3444 | Operator theory / Koopman spectral expansion / ETF allocation | 2667 | 1352 | No |
| 4958 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-3636 | Koopman operator / Model predictive control / ETF rebalancing | 4237 | 4371 | No |
| 4973 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-3732 | Persistence landscapes / Topological contours / Equity index | 534 | 1365 | No |
| 4988 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-3828 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1490 | 7006 | No |
| 5007 | Symplectic Scholarly Tail-Risk Hedge Allocator Mod-3924 | Operator theory / Koopman spectral expansion / ETF allocation | 2706 | 1376 | No |
| 5026 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-12 | Persistence landscapes / Topological contours / Equity index | 540 | 1383 | No |
| 5041 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-108 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1507 | 7026 | No |
| 5058 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-204 | Operator theory / Koopman spectral expansion / ETF allocation | 2727 | 1393 | No |
| 5094 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-396 | Koopman operator / Model predictive control / ETF rebalancing | 4279 | 4522 | No |
| 5112 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-492 | Persistence landscapes / Topological contours / Equity index | 552 | 1409 | No |
| 5127 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-588 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1537 | 7058 | No |
| 5144 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-684 | Operator theory / Koopman spectral expansion / ETF allocation | 2765 | 1419 | No |
| 5180 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-876 | Koopman operator / Model predictive control / ETF rebalancing | 4305 | 4615 | No |
| 5198 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-972 | Persistence landscapes / Topological contours / Equity index | 564 | 1435 | No |
| 5213 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-1068 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1567 | 7090 | No |
| 5230 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-1164 | Operator theory / Koopman spectral expansion / ETF allocation | 2803 | 1445 | No |
| 5266 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-1356 | Koopman operator / Model predictive control / ETF rebalancing | 4331 | 4708 | No |
| 5284 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-1452 | Persistence landscapes / Topological contours / Equity index | 576 | 1461 | No |
| 5299 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-1548 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1597 | 7122 | No |
| 5316 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-1644 | Operator theory / Koopman spectral expansion / ETF allocation | 2841 | 1471 | No |
| 5352 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-1836 | Koopman operator / Model predictive control / ETF rebalancing | 4357 | 4801 | No |
| 5370 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-1932 | Persistence landscapes / Topological contours / Equity index | 588 | 1487 | No |
| 5385 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-2028 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1627 | 7154 | No |
| 5402 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-2124 | Operator theory / Koopman spectral expansion / ETF allocation | 2879 | 1497 | No |
| 5438 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-2316 | Koopman operator / Model predictive control / ETF rebalancing | 4383 | 4894 | No |
| 5456 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-2412 | Persistence landscapes / Topological contours / Equity index | 600 | 1513 | No |
| 5471 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-2508 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1657 | 7186 | No |
| 5488 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-2604 | Operator theory / Koopman spectral expansion / ETF allocation | 2917 | 1523 | No |
| 5524 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-2796 | Koopman operator / Model predictive control / ETF rebalancing | 4409 | 4987 | No |
| 5542 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-2892 | Persistence landscapes / Topological contours / Equity index | 612 | 1539 | No |
| 5557 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-2988 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1687 | 7218 | No |
| 5574 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-3084 | Operator theory / Koopman spectral expansion / ETF allocation | 2955 | 1549 | No |
| 5610 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-3276 | Koopman operator / Model predictive control / ETF rebalancing | 4435 | 5080 | No |
| 5628 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-3372 | Persistence landscapes / Topological contours / Equity index | 624 | 1565 | No |
| 5643 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-3468 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1717 | 7250 | No |
| 5660 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-3564 | Operator theory / Koopman spectral expansion / ETF allocation | 2993 | 1575 | No |
| 5696 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-3756 | Koopman operator / Model predictive control / ETF rebalancing | 4461 | 5173 | No |
| 5714 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-3852 | Persistence landscapes / Topological contours / Equity index | 636 | 1591 | No |
| 5729 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-3948 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1747 | 7282 | No |
| 5746 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-4044 | Operator theory / Koopman spectral expansion / ETF allocation | 3031 | 1601 | No |
| 5782 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-4236 | Koopman operator / Model predictive control / ETF rebalancing | 4487 | 5266 | No |
| 5800 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-4332 | Persistence landscapes / Topological contours / Equity index | 648 | 1617 | No |
| 5815 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-4428 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1777 | 7314 | No |
| 5832 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-4524 | Operator theory / Koopman spectral expansion / ETF allocation | 3069 | 1627 | No |
| 5868 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-4716 | Koopman operator / Model predictive control / ETF rebalancing | 4513 | 5359 | No |
| 5886 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-4812 | Persistence landscapes / Topological contours / Equity index | 660 | 1643 | No |
| 5901 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-4908 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1807 | 7346 | No |
| 5918 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-5004 | Operator theory / Koopman spectral expansion / ETF allocation | 3107 | 1653 | No |
| 5954 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-5196 | Koopman operator / Model predictive control / ETF rebalancing | 4539 | 5452 | No |
| 5972 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-5292 | Persistence landscapes / Topological contours / Equity index | 672 | 1669 | No |
| 5987 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-5388 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1837 | 7378 | No |
| 6004 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-5484 | Operator theory / Koopman spectral expansion / ETF allocation | 3145 | 1679 | No |
| 6040 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-5676 | Koopman operator / Model predictive control / ETF rebalancing | 4565 | 5545 | No |
| 6058 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-5772 | Persistence landscapes / Topological contours / Equity index | 684 | 1695 | No |
| 6073 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-5868 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1867 | 7410 | No |
| 6090 | Symplectic Scholarly Tail-Risk Hedge Allocator Eng-5964 | Operator theory / Koopman spectral expansion / ETF allocation | 3183 | 1705 | No |
