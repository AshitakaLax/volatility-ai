# Recursive approach to tail-risk hedging and allocation

**Concept page** · shared by **139** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(3 of them in ranks 426–700; best-ranked member #683) ·
researched 2026-10-29

| | |
|---|---|
| Task | Tail-risk hedging and allocation |
| Method | Recursive quantile models (CAViaR) |
| Fit with this project | ⏳ as an alternative exit trigger · test against N5 |
| Implemented in volatility-ai | The tail-risk response is the regime exit (V17, N5) and drawdown throttle (V11); no hedge allocation. |
| Evidence | Evidence found (for the task; see the page for the method) |
| Related ledger entries | V17, N5, V11, X5, X8, RK23 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Recursive Scholarly
Tail-Risk Hedge Allocator Ref-420") combine a method word, "Scholarly",
a task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Update a value-at-risk estimate recursively from its own past and recent
returns, as CAViaR does, and de-risk when it rises. Recursive quantile
models are an established way to forecast tail risk; as a trigger they
compete with the volatility regime the project already uses.

## The CSV's description

Proposed recursive approach to tail-risk hedging and allocation:
Estimate stress or extreme-loss risk and allocate defensive assets or
hedges to reduce portfolio downside exposure. This is a concept-level
interpretation of the title, not a complete trading specification: the
exact model inputs/target, calibration, entry/exit or rebalance rules,
and position sizing are not fully defined here.

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
* **Engle & Manganelli (2004), "CAViaR: Conditional Autoregressive Value
  at Risk by Regression Quantiles," *Journal of Business & Economic
  Statistics* 22(4):** recursive quantile models of VaR. (Standard
  reference; not re-checked here.)

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
* Engle, R. F., Manganelli, S. (2004). *Journal of Business & Economic
  Statistics* 22(4). Not re-checked.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 683 | Recursive Scholarly Tail-Risk Hedge Allocator Ref-420 | Fractional order / Multi-scale ETF momentum | 1905 | 319 | No |
| 689 | Recursive Scholarly Tail-Risk Hedge Allocator Ref-900 | Fractional order / Multi-scale ETF momentum | 1910 | 323 | No |
| 695 | Recursive Scholarly Tail-Risk Hedge Allocator Sys-420 | Fractional order / Multi-scale ETF momentum | 1915 | 327 | No |
| 702 | Recursive Scholarly Tail-Risk Hedge Allocator Sys-900 | Fractional order / Multi-scale ETF momentum | 1920 | 331 | No |
| 709 | Recursive Scholarly Tail-Risk Hedge Allocator Sys-1380 | Fractional order / Multi-scale ETF momentum | 1925 | 335 | No |
| 716 | Recursive Scholarly Tail-Risk Hedge Allocator Sys-1860 | Fractional order / Multi-scale ETF momentum | 1930 | 339 | No |
| 719 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-60 | Fractional order / Multi-scale ETF momentum | 1932 | 341 | No |
| 725 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-540 | Fractional order / Multi-scale ETF momentum | 1937 | 345 | No |
| 731 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-1020 | Fractional order / Multi-scale ETF momentum | 1942 | 349 | No |
| 737 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-1500 | Fractional order / Multi-scale ETF momentum | 1947 | 353 | No |
| 743 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-1980 | Fractional order / Multi-scale ETF momentum | 1952 | 357 | No |
| 749 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-2460 | Fractional order / Multi-scale ETF momentum | 1957 | 361 | No |
| 755 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-2940 | Fractional order / Multi-scale ETF momentum | 1962 | 365 | No |
| 761 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-3420 | Fractional order / Multi-scale ETF momentum | 1967 | 369 | No |
| 767 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-3900 | Fractional order / Multi-scale ETF momentum | 1972 | 373 | No |
| 773 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-420 | Fractional order / Multi-scale ETF momentum | 1977 | 377 | No |
| 779 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-900 | Fractional order / Multi-scale ETF momentum | 1982 | 381 | No |
| 785 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-1380 | Fractional order / Multi-scale ETF momentum | 1987 | 385 | No |
| 791 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-1860 | Fractional order / Multi-scale ETF momentum | 1992 | 389 | No |
| 797 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-2340 | Fractional order / Multi-scale ETF momentum | 1997 | 393 | No |
| 803 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-2820 | Fractional order / Multi-scale ETF momentum | 2002 | 397 | No |
| 809 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-3300 | Fractional order / Multi-scale ETF momentum | 2007 | 401 | No |
| 815 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-3780 | Fractional order / Multi-scale ETF momentum | 2012 | 405 | No |
| 821 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-4260 | Fractional order / Multi-scale ETF momentum | 2017 | 409 | No |
| 827 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-4740 | Fractional order / Multi-scale ETF momentum | 2022 | 413 | No |
| 833 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-5220 | Fractional order / Multi-scale ETF momentum | 2027 | 417 | No |
| 839 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-5700 | Fractional order / Multi-scale ETF momentum | 2032 | 421 | No |
| 1599 | Recursive Scholarly Tail-Risk Hedge Allocator MK-19 | Riemannian manifold / Metric optimization / Stock portfolio | 3814 | 2835 | No |
| 1607 | Recursive Scholarly Tail-Risk Hedge Allocator MK-79 | Riemannian manifold / Metric optimization / Stock portfolio | 3817 | 2847 | No |
| 3777 | Recursive Scholarly Tail-Risk Hedge Allocator Ref-36 | Koopman operator / Model predictive control / ETF rebalancing | 3863 | 3020 | No |
| 3793 | Recursive Scholarly Tail-Risk Hedge Allocator Ref-132 | Persistence landscapes / Topological contours / Equity index | 400 | 1016 | No |
| 3810 | Recursive Scholarly Tail-Risk Hedge Allocator Ref-228 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1065 | 6541 | No |
| 3829 | Recursive Scholarly Tail-Risk Hedge Allocator Ref-324 | Operator theory / Koopman spectral expansion / ETF allocation | 2147 | 1030 | No |
| 3863 | Recursive Scholarly Tail-Risk Hedge Allocator Ref-516 | Koopman operator / Model predictive control / ETF rebalancing | 3890 | 3137 | No |
| 3879 | Recursive Scholarly Tail-Risk Hedge Allocator Ref-612 | Persistence landscapes / Topological contours / Equity index | 412 | 1051 | No |
| 3896 | Recursive Scholarly Tail-Risk Hedge Allocator Ref-708 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1099 | 6567 | No |
| 3915 | Recursive Scholarly Tail-Risk Hedge Allocator Ref-804 | Operator theory / Koopman spectral expansion / ETF allocation | 2179 | 1065 | No |
| 3949 | Recursive Scholarly Tail-Risk Hedge Allocator Ref-996 | Koopman operator / Model predictive control / ETF rebalancing | 3917 | 3254 | No |
| 3958 | Recursive Scholarly Tail-Risk Hedge Allocator Sys-36 | Koopman operator / Model predictive control / ETF rebalancing | 3921 | 3262 | No |
| 3974 | Recursive Scholarly Tail-Risk Hedge Allocator Sys-132 | Persistence landscapes / Topological contours / Equity index | 424 | 1086 | No |
| 3993 | Recursive Scholarly Tail-Risk Hedge Allocator Sys-228 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1133 | 6601 | No |
| 4011 | Recursive Scholarly Tail-Risk Hedge Allocator Sys-324 | Operator theory / Koopman spectral expansion / ETF allocation | 2223 | 1095 | No |
| 4044 | Recursive Scholarly Tail-Risk Hedge Allocator Sys-516 | Koopman operator / Model predictive control / ETF rebalancing | 3950 | 3357 | No |
| 4060 | Recursive Scholarly Tail-Risk Hedge Allocator Sys-612 | Persistence landscapes / Topological contours / Equity index | 432 | 1110 | No |
| 4079 | Recursive Scholarly Tail-Risk Hedge Allocator Sys-708 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1163 | 6637 | No |
| 4097 | Recursive Scholarly Tail-Risk Hedge Allocator Sys-804 | Operator theory / Koopman spectral expansion / ETF allocation | 2270 | 1119 | No |
| 4130 | Recursive Scholarly Tail-Risk Hedge Allocator Sys-996 | Koopman operator / Model predictive control / ETF rebalancing | 3979 | 3452 | No |
| 4146 | Recursive Scholarly Tail-Risk Hedge Allocator Sys-1092 | Persistence landscapes / Topological contours / Equity index | 440 | 1134 | No |
| 4165 | Recursive Scholarly Tail-Risk Hedge Allocator Sys-1188 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1193 | 6673 | No |
| 4183 | Recursive Scholarly Tail-Risk Hedge Allocator Sys-1284 | Operator theory / Koopman spectral expansion / ETF allocation | 2317 | 1143 | No |
| 4216 | Recursive Scholarly Tail-Risk Hedge Allocator Sys-1476 | Koopman operator / Model predictive control / ETF rebalancing | 4008 | 3547 | No |
| 4232 | Recursive Scholarly Tail-Risk Hedge Allocator Sys-1572 | Persistence landscapes / Topological contours / Equity index | 448 | 1158 | No |
| 4251 | Recursive Scholarly Tail-Risk Hedge Allocator Sys-1668 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1223 | 6709 | No |
| 4269 | Recursive Scholarly Tail-Risk Hedge Allocator Sys-1764 | Operator theory / Koopman spectral expansion / ETF allocation | 2364 | 1167 | No |
| 4302 | Recursive Scholarly Tail-Risk Hedge Allocator Sys-1956 | Koopman operator / Model predictive control / ETF rebalancing | 4037 | 3642 | No |
| 4343 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-156 | Koopman operator / Model predictive control / ETF rebalancing | 4048 | 3681 | No |
| 4359 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-252 | Persistence landscapes / Topological contours / Equity index | 462 | 1192 | No |
| 4372 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-348 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1264 | 6759 | No |
| 4389 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-444 | Operator theory / Koopman spectral expansion / ETF allocation | 2423 | 1202 | No |
| 4428 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-636 | Koopman operator / Model predictive control / ETF rebalancing | 4074 | 3776 | No |
| 4444 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-732 | Persistence landscapes / Topological contours / Equity index | 472 | 1216 | No |
| 4457 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-828 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1295 | 6793 | No |
| 4474 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-924 | Operator theory / Koopman spectral expansion / ETF allocation | 2462 | 1226 | No |
| 4513 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-1116 | Koopman operator / Model predictive control / ETF rebalancing | 4100 | 3871 | No |
| 4529 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-1212 | Persistence landscapes / Topological contours / Equity index | 482 | 1240 | No |
| 4542 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-1308 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1326 | 6827 | No |
| 4559 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-1404 | Operator theory / Koopman spectral expansion / ETF allocation | 2501 | 1250 | No |
| 4598 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-1596 | Koopman operator / Model predictive control / ETF rebalancing | 4126 | 3966 | No |
| 4614 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-1692 | Persistence landscapes / Topological contours / Equity index | 492 | 1264 | No |
| 4627 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-1788 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1357 | 6861 | No |
| 4644 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-1884 | Operator theory / Koopman spectral expansion / ETF allocation | 2540 | 1274 | No |
| 4683 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-2076 | Koopman operator / Model predictive control / ETF rebalancing | 4152 | 4061 | No |
| 4699 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-2172 | Persistence landscapes / Topological contours / Equity index | 502 | 1288 | No |
| 4712 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-2268 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1388 | 6895 | No |
| 4729 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-2364 | Operator theory / Koopman spectral expansion / ETF allocation | 2579 | 1298 | No |
| 4768 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-2556 | Koopman operator / Model predictive control / ETF rebalancing | 4178 | 4156 | No |
| 4784 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-2652 | Persistence landscapes / Topological contours / Equity index | 512 | 1312 | No |
| 4797 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-2748 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1419 | 6929 | No |
| 4814 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-2844 | Operator theory / Koopman spectral expansion / ETF allocation | 2618 | 1322 | No |
| 4853 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-3036 | Koopman operator / Model predictive control / ETF rebalancing | 4204 | 4251 | No |
| 4869 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-3132 | Persistence landscapes / Topological contours / Equity index | 522 | 1336 | No |
| 4882 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-3228 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1450 | 6963 | No |
| 4899 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-3324 | Operator theory / Koopman spectral expansion / ETF allocation | 2657 | 1346 | No |
| 4938 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-3516 | Koopman operator / Model predictive control / ETF rebalancing | 4230 | 4346 | No |
| 4954 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-3612 | Persistence landscapes / Topological contours / Equity index | 532 | 1360 | No |
| 4967 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-3708 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1481 | 6997 | No |
| 4984 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-3804 | Operator theory / Koopman spectral expansion / ETF allocation | 2696 | 1370 | No |
| 5023 | Recursive Scholarly Tail-Risk Hedge Allocator Mod-3996 | Koopman operator / Model predictive control / ETF rebalancing | 4256 | 4441 | No |
| 5030 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-36 | Koopman operator / Model predictive control / ETF rebalancing | 4260 | 4450 | No |
| 5046 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-132 | Persistence landscapes / Topological contours / Equity index | 543 | 1389 | No |
| 5063 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-228 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1514 | 7034 | No |
| 5081 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-324 | Operator theory / Koopman spectral expansion / ETF allocation | 2736 | 1399 | No |
| 5116 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-516 | Koopman operator / Model predictive control / ETF rebalancing | 4286 | 4543 | No |
| 5132 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-612 | Persistence landscapes / Topological contours / Equity index | 555 | 1415 | No |
| 5149 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-708 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1544 | 7066 | No |
| 5167 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-804 | Operator theory / Koopman spectral expansion / ETF allocation | 2774 | 1425 | No |
| 5202 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-996 | Koopman operator / Model predictive control / ETF rebalancing | 4312 | 4636 | No |
| 5218 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-1092 | Persistence landscapes / Topological contours / Equity index | 567 | 1441 | No |
| 5235 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-1188 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1574 | 7098 | No |
| 5253 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-1284 | Operator theory / Koopman spectral expansion / ETF allocation | 2812 | 1451 | No |
| 5288 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-1476 | Koopman operator / Model predictive control / ETF rebalancing | 4338 | 4729 | No |
| 5304 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-1572 | Persistence landscapes / Topological contours / Equity index | 579 | 1467 | No |
| 5321 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-1668 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1604 | 7130 | No |
| 5339 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-1764 | Operator theory / Koopman spectral expansion / ETF allocation | 2850 | 1477 | No |
| 5374 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-1956 | Koopman operator / Model predictive control / ETF rebalancing | 4364 | 4822 | No |
| 5390 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-2052 | Persistence landscapes / Topological contours / Equity index | 591 | 1493 | No |
| 5407 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-2148 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1634 | 7162 | No |
| 5425 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-2244 | Operator theory / Koopman spectral expansion / ETF allocation | 2888 | 1503 | No |
| 5460 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-2436 | Koopman operator / Model predictive control / ETF rebalancing | 4390 | 4915 | No |
| 5476 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-2532 | Persistence landscapes / Topological contours / Equity index | 603 | 1519 | No |
| 5493 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-2628 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1664 | 7194 | No |
| 5511 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-2724 | Operator theory / Koopman spectral expansion / ETF allocation | 2926 | 1529 | No |
| 5546 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-2916 | Koopman operator / Model predictive control / ETF rebalancing | 4416 | 5008 | No |
| 5562 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-3012 | Persistence landscapes / Topological contours / Equity index | 615 | 1545 | No |
| 5579 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-3108 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1694 | 7226 | No |
| 5597 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-3204 | Operator theory / Koopman spectral expansion / ETF allocation | 2964 | 1555 | No |
| 5632 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-3396 | Koopman operator / Model predictive control / ETF rebalancing | 4442 | 5101 | No |
| 5648 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-3492 | Persistence landscapes / Topological contours / Equity index | 627 | 1571 | No |
| 5665 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-3588 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1724 | 7258 | No |
| 5683 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-3684 | Operator theory / Koopman spectral expansion / ETF allocation | 3002 | 1581 | No |
| 5718 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-3876 | Koopman operator / Model predictive control / ETF rebalancing | 4468 | 5194 | No |
| 5734 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-3972 | Persistence landscapes / Topological contours / Equity index | 639 | 1597 | No |
| 5751 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-4068 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1754 | 7290 | No |
| 5769 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-4164 | Operator theory / Koopman spectral expansion / ETF allocation | 3040 | 1607 | No |
| 5804 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-4356 | Koopman operator / Model predictive control / ETF rebalancing | 4494 | 5287 | No |
| 5820 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-4452 | Persistence landscapes / Topological contours / Equity index | 651 | 1623 | No |
| 5837 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-4548 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1784 | 7322 | No |
| 5855 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-4644 | Operator theory / Koopman spectral expansion / ETF allocation | 3078 | 1633 | No |
| 5890 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-4836 | Koopman operator / Model predictive control / ETF rebalancing | 4520 | 5380 | No |
| 5906 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-4932 | Persistence landscapes / Topological contours / Equity index | 663 | 1649 | No |
| 5923 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-5028 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1814 | 7354 | No |
| 5941 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-5124 | Operator theory / Koopman spectral expansion / ETF allocation | 3116 | 1659 | No |
| 5976 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-5316 | Koopman operator / Model predictive control / ETF rebalancing | 4546 | 5473 | No |
| 5992 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-5412 | Persistence landscapes / Topological contours / Equity index | 675 | 1675 | No |
| 6009 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-5508 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1844 | 7386 | No |
| 6027 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-5604 | Operator theory / Koopman spectral expansion / ETF allocation | 3154 | 1685 | No |
| 6062 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-5796 | Koopman operator / Model predictive control / ETF rebalancing | 4572 | 5566 | No |
| 6078 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-5892 | Persistence landscapes / Topological contours / Equity index | 687 | 1701 | No |
| 6095 | Recursive Scholarly Tail-Risk Hedge Allocator Eng-5988 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1874 | 7418 | No |
