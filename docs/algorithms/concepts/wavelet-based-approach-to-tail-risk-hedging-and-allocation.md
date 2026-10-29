# Wavelet-based approach to tail-risk hedging and allocation

**Concept page** · shared by **135** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(4 of them in ranks 426–700; best-ranked member #678) ·
researched 2026-10-29

| | |
|---|---|
| Task | Tail-risk hedging and allocation |
| Method | Wavelet multiscale decomposition |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **Research code** in `research.catalog.concepts`: `wavelet_tail_risk`; tested on synthetic data, not wired into the engine. Related code already here: The tail-risk response is the regime exit (V17, N5) and drawdown throttle (V11); no hedge allocation. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | V17, N5, V11, X5, X8, RK23 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Wavelet Scholarly Tail-Risk
Hedge Allocator Ref-60") combine a method word, "Scholarly", a task and
a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Decompose returns by time scale with wavelets and measure tail risk
scale by scale to time hedges. Wavelets are used to study risk across
horizons; I found no study of a wavelet tail-hedging rule.

## The CSV's description

Proposed wavelet-based approach to tail-risk hedging and allocation:
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
| 678 | Wavelet Scholarly Tail-Risk Hedge Allocator Ref-60 | Fractional order / Multi-scale ETF momentum | 1901 | 316 | No |
| 684 | Wavelet Scholarly Tail-Risk Hedge Allocator Ref-540 | Fractional order / Multi-scale ETF momentum | 1906 | 320 | No |
| 690 | Wavelet Scholarly Tail-Risk Hedge Allocator Sys-60 | Fractional order / Multi-scale ETF momentum | 1911 | 324 | No |
| 697 | Wavelet Scholarly Tail-Risk Hedge Allocator Sys-540 | Fractional order / Multi-scale ETF momentum | 1916 | 328 | No |
| 704 | Wavelet Scholarly Tail-Risk Hedge Allocator Sys-1020 | Fractional order / Multi-scale ETF momentum | 1921 | 332 | No |
| 711 | Wavelet Scholarly Tail-Risk Hedge Allocator Sys-1500 | Fractional order / Multi-scale ETF momentum | 1926 | 336 | No |
| 718 | Wavelet Scholarly Tail-Risk Hedge Allocator Sys-1980 | Fractional order / Multi-scale ETF momentum | 1931 | 340 | No |
| 724 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-420 | Fractional order / Multi-scale ETF momentum | 1936 | 344 | No |
| 730 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-900 | Fractional order / Multi-scale ETF momentum | 1941 | 348 | No |
| 736 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-1380 | Fractional order / Multi-scale ETF momentum | 1946 | 352 | No |
| 742 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-1860 | Fractional order / Multi-scale ETF momentum | 1951 | 356 | No |
| 748 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-2340 | Fractional order / Multi-scale ETF momentum | 1956 | 360 | No |
| 754 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-2820 | Fractional order / Multi-scale ETF momentum | 1961 | 364 | No |
| 760 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-3300 | Fractional order / Multi-scale ETF momentum | 1966 | 368 | No |
| 766 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-3780 | Fractional order / Multi-scale ETF momentum | 1971 | 372 | No |
| 768 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-60 | Fractional order / Multi-scale ETF momentum | 1973 | 374 | No |
| 774 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-540 | Fractional order / Multi-scale ETF momentum | 1978 | 378 | No |
| 780 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-1020 | Fractional order / Multi-scale ETF momentum | 1983 | 382 | No |
| 786 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-1500 | Fractional order / Multi-scale ETF momentum | 1988 | 386 | No |
| 792 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-1980 | Fractional order / Multi-scale ETF momentum | 1993 | 390 | No |
| 798 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-2460 | Fractional order / Multi-scale ETF momentum | 1998 | 394 | No |
| 804 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-2940 | Fractional order / Multi-scale ETF momentum | 2003 | 398 | No |
| 810 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-3420 | Fractional order / Multi-scale ETF momentum | 2008 | 402 | No |
| 816 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-3900 | Fractional order / Multi-scale ETF momentum | 2013 | 406 | No |
| 822 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-4380 | Fractional order / Multi-scale ETF momentum | 2018 | 410 | No |
| 828 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-4860 | Fractional order / Multi-scale ETF momentum | 2023 | 414 | No |
| 834 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-5340 | Fractional order / Multi-scale ETF momentum | 2028 | 418 | No |
| 840 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-5820 | Fractional order / Multi-scale ETF momentum | 2033 | 422 | No |
| 3797 | Wavelet Scholarly Tail-Risk Hedge Allocator Ref-156 | Koopman operator / Model predictive control / ETF rebalancing | 3870 | 3049 | No |
| 3816 | Wavelet Scholarly Tail-Risk Hedge Allocator Ref-252 | Persistence landscapes / Topological contours / Equity index | 403 | 1025 | No |
| 3832 | Wavelet Scholarly Tail-Risk Hedge Allocator Ref-348 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1073 | 6547 | No |
| 3852 | Wavelet Scholarly Tail-Risk Hedge Allocator Ref-444 | Operator theory / Koopman spectral expansion / ETF allocation | 2155 | 1038 | No |
| 3883 | Wavelet Scholarly Tail-Risk Hedge Allocator Ref-636 | Koopman operator / Model predictive control / ETF rebalancing | 3897 | 3166 | No |
| 3902 | Wavelet Scholarly Tail-Risk Hedge Allocator Ref-732 | Persistence landscapes / Topological contours / Equity index | 415 | 1060 | No |
| 3918 | Wavelet Scholarly Tail-Risk Hedge Allocator Ref-828 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1107 | 6573 | No |
| 3938 | Wavelet Scholarly Tail-Risk Hedge Allocator Ref-924 | Operator theory / Koopman spectral expansion / ETF allocation | 2187 | 1073 | No |
| 3980 | Wavelet Scholarly Tail-Risk Hedge Allocator Sys-156 | Koopman operator / Model predictive control / ETF rebalancing | 3927 | 3287 | No |
| 3996 | Wavelet Scholarly Tail-Risk Hedge Allocator Sys-252 | Persistence landscapes / Topological contours / Equity index | 426 | 1092 | No |
| 4014 | Wavelet Scholarly Tail-Risk Hedge Allocator Sys-348 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1140 | 6610 | No |
| 4031 | Wavelet Scholarly Tail-Risk Hedge Allocator Sys-444 | Operator theory / Koopman spectral expansion / ETF allocation | 2235 | 1101 | No |
| 4066 | Wavelet Scholarly Tail-Risk Hedge Allocator Sys-636 | Koopman operator / Model predictive control / ETF rebalancing | 3956 | 3382 | No |
| 4082 | Wavelet Scholarly Tail-Risk Hedge Allocator Sys-732 | Persistence landscapes / Topological contours / Equity index | 434 | 1116 | No |
| 4100 | Wavelet Scholarly Tail-Risk Hedge Allocator Sys-828 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1170 | 6646 | No |
| 4117 | Wavelet Scholarly Tail-Risk Hedge Allocator Sys-924 | Operator theory / Koopman spectral expansion / ETF allocation | 2282 | 1125 | No |
| 4152 | Wavelet Scholarly Tail-Risk Hedge Allocator Sys-1116 | Koopman operator / Model predictive control / ETF rebalancing | 3985 | 3477 | No |
| 4168 | Wavelet Scholarly Tail-Risk Hedge Allocator Sys-1212 | Persistence landscapes / Topological contours / Equity index | 442 | 1140 | No |
| 4186 | Wavelet Scholarly Tail-Risk Hedge Allocator Sys-1308 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1200 | 6682 | No |
| 4203 | Wavelet Scholarly Tail-Risk Hedge Allocator Sys-1404 | Operator theory / Koopman spectral expansion / ETF allocation | 2329 | 1149 | No |
| 4238 | Wavelet Scholarly Tail-Risk Hedge Allocator Sys-1596 | Koopman operator / Model predictive control / ETF rebalancing | 4014 | 3572 | No |
| 4254 | Wavelet Scholarly Tail-Risk Hedge Allocator Sys-1692 | Persistence landscapes / Topological contours / Equity index | 450 | 1164 | No |
| 4272 | Wavelet Scholarly Tail-Risk Hedge Allocator Sys-1788 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1230 | 6718 | No |
| 4289 | Wavelet Scholarly Tail-Risk Hedge Allocator Sys-1884 | Operator theory / Koopman spectral expansion / ETF allocation | 2376 | 1173 | No |
| 4319 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-36 | Koopman operator / Model predictive control / ETF rebalancing | 4042 | 3659 | No |
| 4338 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-132 | Persistence landscapes / Topological contours / Equity index | 459 | 1187 | No |
| 4353 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-228 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1257 | 6750 | No |
| 4368 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-324 | Operator theory / Koopman spectral expansion / ETF allocation | 2414 | 1195 | No |
| 4404 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-516 | Koopman operator / Model predictive control / ETF rebalancing | 4068 | 3754 | No |
| 4423 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-612 | Persistence landscapes / Topological contours / Equity index | 469 | 1211 | No |
| 4438 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-708 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1288 | 6784 | No |
| 4453 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-804 | Operator theory / Koopman spectral expansion / ETF allocation | 2453 | 1219 | No |
| 4489 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-996 | Koopman operator / Model predictive control / ETF rebalancing | 4094 | 3849 | No |
| 4508 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-1092 | Persistence landscapes / Topological contours / Equity index | 479 | 1235 | No |
| 4523 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-1188 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1319 | 6818 | No |
| 4538 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-1284 | Operator theory / Koopman spectral expansion / ETF allocation | 2492 | 1243 | No |
| 4574 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-1476 | Koopman operator / Model predictive control / ETF rebalancing | 4120 | 3944 | No |
| 4593 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-1572 | Persistence landscapes / Topological contours / Equity index | 489 | 1259 | No |
| 4608 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-1668 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1350 | 6852 | No |
| 4623 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-1764 | Operator theory / Koopman spectral expansion / ETF allocation | 2531 | 1267 | No |
| 4659 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-1956 | Koopman operator / Model predictive control / ETF rebalancing | 4146 | 4039 | No |
| 4678 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-2052 | Persistence landscapes / Topological contours / Equity index | 499 | 1283 | No |
| 4693 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-2148 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1381 | 6886 | No |
| 4708 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-2244 | Operator theory / Koopman spectral expansion / ETF allocation | 2570 | 1291 | No |
| 4744 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-2436 | Koopman operator / Model predictive control / ETF rebalancing | 4172 | 4134 | No |
| 4763 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-2532 | Persistence landscapes / Topological contours / Equity index | 509 | 1307 | No |
| 4778 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-2628 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1412 | 6920 | No |
| 4793 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-2724 | Operator theory / Koopman spectral expansion / ETF allocation | 2609 | 1315 | No |
| 4829 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-2916 | Koopman operator / Model predictive control / ETF rebalancing | 4198 | 4229 | No |
| 4848 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-3012 | Persistence landscapes / Topological contours / Equity index | 519 | 1331 | No |
| 4863 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-3108 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1443 | 6954 | No |
| 4878 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-3204 | Operator theory / Koopman spectral expansion / ETF allocation | 2648 | 1339 | No |
| 4914 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-3396 | Koopman operator / Model predictive control / ETF rebalancing | 4224 | 4324 | No |
| 4933 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-3492 | Persistence landscapes / Topological contours / Equity index | 529 | 1355 | No |
| 4948 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-3588 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1474 | 6988 | No |
| 4963 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-3684 | Operator theory / Koopman spectral expansion / ETF allocation | 2687 | 1363 | No |
| 4999 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-3876 | Koopman operator / Model predictive control / ETF rebalancing | 4250 | 4419 | No |
| 5018 | Wavelet Scholarly Tail-Risk Hedge Allocator Mod-3972 | Persistence landscapes / Topological contours / Equity index | 539 | 1379 | No |
| 5051 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-156 | Koopman operator / Model predictive control / ETF rebalancing | 4266 | 4474 | No |
| 5068 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-252 | Persistence landscapes / Topological contours / Equity index | 546 | 1396 | No |
| 5085 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-348 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1521 | 7042 | No |
| 5102 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-444 | Operator theory / Koopman spectral expansion / ETF allocation | 2746 | 1405 | No |
| 5137 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-636 | Koopman operator / Model predictive control / ETF rebalancing | 4292 | 4567 | No |
| 5154 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-732 | Persistence landscapes / Topological contours / Equity index | 558 | 1422 | No |
| 5171 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-828 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1551 | 7074 | No |
| 5188 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-924 | Operator theory / Koopman spectral expansion / ETF allocation | 2784 | 1431 | No |
| 5223 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-1116 | Koopman operator / Model predictive control / ETF rebalancing | 4318 | 4660 | No |
| 5240 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-1212 | Persistence landscapes / Topological contours / Equity index | 570 | 1448 | No |
| 5257 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-1308 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1581 | 7106 | No |
| 5274 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-1404 | Operator theory / Koopman spectral expansion / ETF allocation | 2822 | 1457 | No |
| 5309 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-1596 | Koopman operator / Model predictive control / ETF rebalancing | 4344 | 4753 | No |
| 5326 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-1692 | Persistence landscapes / Topological contours / Equity index | 582 | 1474 | No |
| 5343 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-1788 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1611 | 7138 | No |
| 5360 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-1884 | Operator theory / Koopman spectral expansion / ETF allocation | 2860 | 1483 | No |
| 5395 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-2076 | Koopman operator / Model predictive control / ETF rebalancing | 4370 | 4846 | No |
| 5412 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-2172 | Persistence landscapes / Topological contours / Equity index | 594 | 1500 | No |
| 5429 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-2268 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1641 | 7170 | No |
| 5446 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-2364 | Operator theory / Koopman spectral expansion / ETF allocation | 2898 | 1509 | No |
| 5481 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-2556 | Koopman operator / Model predictive control / ETF rebalancing | 4396 | 4939 | No |
| 5498 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-2652 | Persistence landscapes / Topological contours / Equity index | 606 | 1526 | No |
| 5515 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-2748 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1671 | 7202 | No |
| 5532 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-2844 | Operator theory / Koopman spectral expansion / ETF allocation | 2936 | 1535 | No |
| 5567 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-3036 | Koopman operator / Model predictive control / ETF rebalancing | 4422 | 5032 | No |
| 5584 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-3132 | Persistence landscapes / Topological contours / Equity index | 618 | 1552 | No |
| 5601 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-3228 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1701 | 7234 | No |
| 5618 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-3324 | Operator theory / Koopman spectral expansion / ETF allocation | 2974 | 1561 | No |
| 5653 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-3516 | Koopman operator / Model predictive control / ETF rebalancing | 4448 | 5125 | No |
| 5670 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-3612 | Persistence landscapes / Topological contours / Equity index | 630 | 1578 | No |
| 5687 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-3708 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1731 | 7266 | No |
| 5704 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-3804 | Operator theory / Koopman spectral expansion / ETF allocation | 3012 | 1587 | No |
| 5739 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-3996 | Koopman operator / Model predictive control / ETF rebalancing | 4474 | 5218 | No |
| 5756 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-4092 | Persistence landscapes / Topological contours / Equity index | 642 | 1604 | No |
| 5773 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-4188 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1761 | 7298 | No |
| 5790 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-4284 | Operator theory / Koopman spectral expansion / ETF allocation | 3050 | 1613 | No |
| 5825 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-4476 | Koopman operator / Model predictive control / ETF rebalancing | 4500 | 5311 | No |
| 5842 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-4572 | Persistence landscapes / Topological contours / Equity index | 654 | 1630 | No |
| 5859 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-4668 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1791 | 7330 | No |
| 5876 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-4764 | Operator theory / Koopman spectral expansion / ETF allocation | 3088 | 1639 | No |
| 5911 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-4956 | Koopman operator / Model predictive control / ETF rebalancing | 4526 | 5404 | No |
| 5928 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-5052 | Persistence landscapes / Topological contours / Equity index | 666 | 1656 | No |
| 5945 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-5148 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1821 | 7362 | No |
| 5962 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-5244 | Operator theory / Koopman spectral expansion / ETF allocation | 3126 | 1665 | No |
| 5997 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-5436 | Koopman operator / Model predictive control / ETF rebalancing | 4552 | 5497 | No |
| 6014 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-5532 | Persistence landscapes / Topological contours / Equity index | 678 | 1682 | No |
| 6031 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-5628 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 1851 | 7394 | No |
| 6048 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-5724 | Operator theory / Koopman spectral expansion / ETF allocation | 3164 | 1691 | No |
| 6083 | Wavelet Scholarly Tail-Risk Hedge Allocator Eng-5916 | Koopman operator / Model predictive control / ETF rebalancing | 4578 | 5590 | No |
