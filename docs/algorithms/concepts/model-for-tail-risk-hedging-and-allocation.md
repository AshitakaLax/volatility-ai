# Model for tail-risk hedging and allocation

**Concept page** · shared by **142** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(6 of them in ranks 426–700; best-ranked member #426) ·
researched 2026-10-29

| | |
|---|---|
| Task | Tail-risk hedging and allocation |
| Method | Unspecified model |
| Fit with this project | 🔬 the project's equivalent is the regime exit (V17, N5) |
| Implemented in volatility-ai | The tail-risk response is the regime exit (V17, N5) and drawdown throttle (V11); no hedge allocation. |
| Evidence | Evidence found (for the task; see the page for the method) |
| Related ledger entries | V17, N5, V11, X5, X8, RK23 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Manifold-Valued Scholarly
Tail-Risk Hedge Allocator MK-34") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Estimate extreme-loss risk and shift into defensive assets or hedges to
cut downside. The evidence on how to hedge is sobering: protective puts
did worse per unit of return than just holding less equity, while trend
following has been positive in most of the largest 60/40 drawdowns of
the last century.

## The CSV's description

Proposed model for tail-risk hedging and allocation: Estimate stress or
extreme-loss risk and allocate defensive assets or hedges to reduce
portfolio downside exposure. This is a concept-level interpretation of
the title, not a complete trading specification: the exact model
inputs/target, calibration, entry/exit or rebalance rules, and position
sizing are not fully defined here.

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
| 426 | Manifold-Valued Scholarly Tail-Risk Hedge Allocator MK-34 | Vine copulas / Regularization / Multi-factor equity allocation | 10026 | 2762 | No |
| 427 | Manifold-Valued Scholarly Tail-Risk Hedge Allocator MK-94 | Vine copulas / Regularization / Multi-factor equity allocation | 10028 | 2765 | No |
| 680 | Wasserstein Scholarly Tail-Risk Hedge Allocator Ref-180 | Fractional order / Multi-scale ETF momentum | 1903 | 317 | No |
| 686 | Wasserstein Scholarly Tail-Risk Hedge Allocator Ref-660 | Fractional order / Multi-scale ETF momentum | 1908 | 321 | No |
| 691 | Wasserstein Scholarly Tail-Risk Hedge Allocator Sys-180 | Fractional order / Multi-scale ETF momentum | 1913 | 325 | No |
| 698 | Wasserstein Scholarly Tail-Risk Hedge Allocator Sys-660 | Fractional order / Multi-scale ETF momentum | 1918 | 329 | No |
| 705 | Wasserstein Scholarly Tail-Risk Hedge Allocator Sys-1140 | Fractional order / Multi-scale ETF momentum | 1923 | 333 | No |
| 712 | Wasserstein Scholarly Tail-Risk Hedge Allocator Sys-1620 | Fractional order / Multi-scale ETF momentum | 1928 | 337 | No |
| 722 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-300 | Fractional order / Multi-scale ETF momentum | 1934 | 343 | No |
| 728 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-780 | Fractional order / Multi-scale ETF momentum | 1939 | 347 | No |
| 734 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-1260 | Fractional order / Multi-scale ETF momentum | 1944 | 351 | No |
| 740 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-1740 | Fractional order / Multi-scale ETF momentum | 1949 | 355 | No |
| 746 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-2220 | Fractional order / Multi-scale ETF momentum | 1954 | 359 | No |
| 752 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-2700 | Fractional order / Multi-scale ETF momentum | 1959 | 363 | No |
| 758 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-3180 | Fractional order / Multi-scale ETF momentum | 1964 | 367 | No |
| 764 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-3660 | Fractional order / Multi-scale ETF momentum | 1969 | 371 | No |
| 771 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-180 | Fractional order / Multi-scale ETF momentum | 1975 | 375 | No |
| 777 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-660 | Fractional order / Multi-scale ETF momentum | 1980 | 379 | No |
| 783 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-1140 | Fractional order / Multi-scale ETF momentum | 1985 | 383 | No |
| 789 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-1620 | Fractional order / Multi-scale ETF momentum | 1990 | 387 | No |
| 795 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-2100 | Fractional order / Multi-scale ETF momentum | 1995 | 391 | No |
| 801 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-2580 | Fractional order / Multi-scale ETF momentum | 2000 | 395 | No |
| 807 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-3060 | Fractional order / Multi-scale ETF momentum | 2005 | 399 | No |
| 813 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-3540 | Fractional order / Multi-scale ETF momentum | 2010 | 403 | No |
| 819 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-4020 | Fractional order / Multi-scale ETF momentum | 2015 | 407 | No |
| 825 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-4500 | Fractional order / Multi-scale ETF momentum | 2020 | 411 | No |
| 831 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-4980 | Fractional order / Multi-scale ETF momentum | 2025 | 415 | No |
| 837 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-5460 | Fractional order / Multi-scale ETF momentum | 2030 | 419 | No |
| 843 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-5940 | Fractional order / Multi-scale ETF momentum | 2035 | 423 | No |
| 1610 | Dynamic Scholarly Tail-Risk Hedge Allocator Ver-2 | Robust statistics / Mean-variance / Index tracking | 2053 | 2852 | No |
| 1617 | Convolutional Scholarly Tail-Risk Hedge Allocator Ver-42 | Robust statistics / Mean-variance / Index tracking | 389 | 969 | No |
| 1627 | Cross-Sectional Scholarly Tail-Risk Hedge Allocator Ver-82 | Robust statistics / Mean-variance / Index tracking | 5799 | 11280 | No |
| 1634 | Dynamic Scholarly Tail-Risk Hedge Allocator Ver-102 | Robust statistics / Mean-variance / Index tracking | 390 | 971 | No |
| 1641 | Convolutional Scholarly Tail-Risk Hedge Allocator Ver-142 | Robust statistics / Mean-variance / Index tracking | 5801 | 11284 | No |
| 1651 | Cross-Sectional Scholarly Tail-Risk Hedge Allocator Ver-182 | Robust statistics / Mean-variance / Index tracking | 2076 | 2891 | No |
| 3786 | Wasserstein Scholarly Tail-Risk Hedge Allocator Ref-84 | Operator theory / Koopman spectral expansion / ETF allocation | 2131 | 3031 | No |
| 3820 | Wasserstein Scholarly Tail-Risk Hedge Allocator Ref-276 | Koopman operator / Model predictive control / ETF rebalancing | 3877 | 3078 | No |
| 3838 | Wasserstein Scholarly Tail-Risk Hedge Allocator Ref-372 | Persistence landscapes / Topological contours / Equity index | 2151 | 3102 | No |
| 3855 | Wasserstein Scholarly Tail-Risk Hedge Allocator Ref-468 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 4670 | 6554 | No |
| 3872 | Wasserstein Scholarly Tail-Risk Hedge Allocator Ref-564 | Operator theory / Koopman spectral expansion / ETF allocation | 2163 | 3148 | No |
| 3906 | Wasserstein Scholarly Tail-Risk Hedge Allocator Ref-756 | Koopman operator / Model predictive control / ETF rebalancing | 3904 | 3195 | No |
| 3924 | Wasserstein Scholarly Tail-Risk Hedge Allocator Ref-852 | Persistence landscapes / Topological contours / Equity index | 2183 | 3219 | No |
| 3941 | Wasserstein Scholarly Tail-Risk Hedge Allocator Ref-948 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 4697 | 6580 | No |
| 3967 | Wasserstein Scholarly Tail-Risk Hedge Allocator Sys-84 | Operator theory / Koopman spectral expansion / ETF allocation | 2201 | 3271 | No |
| 4001 | Wasserstein Scholarly Tail-Risk Hedge Allocator Sys-276 | Koopman operator / Model predictive control / ETF rebalancing | 3935 | 3311 | No |
| 4017 | Wasserstein Scholarly Tail-Risk Hedge Allocator Sys-372 | Persistence landscapes / Topological contours / Equity index | 2229 | 3329 | No |
| 4034 | Wasserstein Scholarly Tail-Risk Hedge Allocator Sys-468 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 4732 | 6619 | No |
| 4053 | Wasserstein Scholarly Tail-Risk Hedge Allocator Sys-564 | Operator theory / Koopman spectral expansion / ETF allocation | 2248 | 3366 | No |
| 4087 | Wasserstein Scholarly Tail-Risk Hedge Allocator Sys-756 | Koopman operator / Model predictive control / ETF rebalancing | 3964 | 3406 | No |
| 4103 | Wasserstein Scholarly Tail-Risk Hedge Allocator Sys-852 | Persistence landscapes / Topological contours / Equity index | 2276 | 3424 | No |
| 4120 | Wasserstein Scholarly Tail-Risk Hedge Allocator Sys-948 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 4763 | 6655 | No |
| 4139 | Wasserstein Scholarly Tail-Risk Hedge Allocator Sys-1044 | Operator theory / Koopman spectral expansion / ETF allocation | 2295 | 3461 | No |
| 4173 | Wasserstein Scholarly Tail-Risk Hedge Allocator Sys-1236 | Koopman operator / Model predictive control / ETF rebalancing | 3993 | 3501 | No |
| 4189 | Wasserstein Scholarly Tail-Risk Hedge Allocator Sys-1332 | Persistence landscapes / Topological contours / Equity index | 2323 | 3519 | No |
| 4206 | Wasserstein Scholarly Tail-Risk Hedge Allocator Sys-1428 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 4794 | 6691 | No |
| 4225 | Wasserstein Scholarly Tail-Risk Hedge Allocator Sys-1524 | Operator theory / Koopman spectral expansion / ETF allocation | 2342 | 3556 | No |
| 4259 | Wasserstein Scholarly Tail-Risk Hedge Allocator Sys-1716 | Koopman operator / Model predictive control / ETF rebalancing | 4022 | 3596 | No |
| 4275 | Wasserstein Scholarly Tail-Risk Hedge Allocator Sys-1812 | Persistence landscapes / Topological contours / Equity index | 2370 | 3614 | No |
| 4292 | Wasserstein Scholarly Tail-Risk Hedge Allocator Sys-1908 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 4825 | 6727 | No |
| 4314 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-12 | Persistence landscapes / Topological contours / Equity index | 2389 | 3654 | No |
| 4332 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-108 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 4837 | 6742 | No |
| 4348 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-204 | Operator theory / Koopman spectral expansion / ETF allocation | 2403 | 3692 | No |
| 4383 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-396 | Koopman operator / Model predictive control / ETF rebalancing | 4061 | 3732 | No |
| 4399 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-492 | Persistence landscapes / Topological contours / Equity index | 2428 | 3749 | No |
| 4417 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-588 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 4864 | 6776 | No |
| 4433 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-684 | Operator theory / Koopman spectral expansion / ETF allocation | 2442 | 3787 | No |
| 4468 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-876 | Koopman operator / Model predictive control / ETF rebalancing | 4087 | 3827 | No |
| 4484 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-972 | Persistence landscapes / Topological contours / Equity index | 2467 | 3844 | No |
| 4502 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-1068 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 4891 | 6810 | No |
| 4518 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-1164 | Operator theory / Koopman spectral expansion / ETF allocation | 2481 | 3882 | No |
| 4553 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-1356 | Koopman operator / Model predictive control / ETF rebalancing | 4113 | 3922 | No |
| 4569 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-1452 | Persistence landscapes / Topological contours / Equity index | 2506 | 3939 | No |
| 4587 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-1548 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 4918 | 6844 | No |
| 4603 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-1644 | Operator theory / Koopman spectral expansion / ETF allocation | 2520 | 3977 | No |
| 4638 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-1836 | Koopman operator / Model predictive control / ETF rebalancing | 4139 | 4017 | No |
| 4654 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-1932 | Persistence landscapes / Topological contours / Equity index | 2545 | 4034 | No |
| 4672 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-2028 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 4945 | 6878 | No |
| 4688 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-2124 | Operator theory / Koopman spectral expansion / ETF allocation | 2559 | 4072 | No |
| 4723 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-2316 | Koopman operator / Model predictive control / ETF rebalancing | 4165 | 4112 | No |
| 4739 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-2412 | Persistence landscapes / Topological contours / Equity index | 2584 | 4129 | No |
| 4757 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-2508 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 4972 | 6912 | No |
| 4773 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-2604 | Operator theory / Koopman spectral expansion / ETF allocation | 2598 | 4167 | No |
| 4808 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-2796 | Koopman operator / Model predictive control / ETF rebalancing | 4191 | 4207 | No |
| 4824 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-2892 | Persistence landscapes / Topological contours / Equity index | 2623 | 4224 | No |
| 4842 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-2988 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 4999 | 6946 | No |
| 4858 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-3084 | Operator theory / Koopman spectral expansion / ETF allocation | 2637 | 4262 | No |
| 4893 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-3276 | Koopman operator / Model predictive control / ETF rebalancing | 4217 | 4302 | No |
| 4909 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-3372 | Persistence landscapes / Topological contours / Equity index | 2662 | 4319 | No |
| 4927 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-3468 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 5026 | 6980 | No |
| 4943 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-3564 | Operator theory / Koopman spectral expansion / ETF allocation | 2676 | 4357 | No |
| 4978 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-3756 | Koopman operator / Model predictive control / ETF rebalancing | 4243 | 4397 | No |
| 4994 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-3852 | Persistence landscapes / Topological contours / Equity index | 2701 | 4414 | No |
| 5012 | Wasserstein Scholarly Tail-Risk Hedge Allocator Mod-3948 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 5053 | 7014 | No |
| 5037 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-84 | Operator theory / Koopman spectral expansion / ETF allocation | 2718 | 4460 | No |
| 5072 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-276 | Koopman operator / Model predictive control / ETF rebalancing | 4273 | 4497 | No |
| 5090 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-372 | Persistence landscapes / Topological contours / Equity index | 2742 | 4515 | No |
| 5107 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-468 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 5081 | 7050 | No |
| 5123 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-564 | Operator theory / Koopman spectral expansion / ETF allocation | 2756 | 4553 | No |
| 5158 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-756 | Koopman operator / Model predictive control / ETF rebalancing | 4299 | 4590 | No |
| 5176 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-852 | Persistence landscapes / Topological contours / Equity index | 2780 | 4608 | No |
| 5193 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-948 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 5106 | 7082 | No |
| 5209 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-1044 | Operator theory / Koopman spectral expansion / ETF allocation | 2794 | 4646 | No |
| 5244 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-1236 | Koopman operator / Model predictive control / ETF rebalancing | 4325 | 4683 | No |
| 5262 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-1332 | Persistence landscapes / Topological contours / Equity index | 2818 | 4701 | No |
| 5279 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-1428 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 5131 | 7114 | No |
| 5295 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-1524 | Operator theory / Koopman spectral expansion / ETF allocation | 2832 | 4739 | No |
| 5330 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-1716 | Koopman operator / Model predictive control / ETF rebalancing | 4351 | 4776 | No |
| 5348 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-1812 | Persistence landscapes / Topological contours / Equity index | 2856 | 4794 | No |
| 5365 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-1908 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 5156 | 7146 | No |
| 5381 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-2004 | Operator theory / Koopman spectral expansion / ETF allocation | 2870 | 4832 | No |
| 5416 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-2196 | Koopman operator / Model predictive control / ETF rebalancing | 4377 | 4869 | No |
| 5434 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-2292 | Persistence landscapes / Topological contours / Equity index | 2894 | 4887 | No |
| 5451 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-2388 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 5181 | 7178 | No |
| 5467 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-2484 | Operator theory / Koopman spectral expansion / ETF allocation | 2908 | 4925 | No |
| 5502 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-2676 | Koopman operator / Model predictive control / ETF rebalancing | 4403 | 4962 | No |
| 5520 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-2772 | Persistence landscapes / Topological contours / Equity index | 2932 | 4980 | No |
| 5537 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-2868 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 5206 | 7210 | No |
| 5553 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-2964 | Operator theory / Koopman spectral expansion / ETF allocation | 2946 | 5018 | No |
| 5588 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-3156 | Koopman operator / Model predictive control / ETF rebalancing | 4429 | 5055 | No |
| 5606 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-3252 | Persistence landscapes / Topological contours / Equity index | 2970 | 5073 | No |
| 5623 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-3348 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 5231 | 7242 | No |
| 5639 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-3444 | Operator theory / Koopman spectral expansion / ETF allocation | 2984 | 5111 | No |
| 5674 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-3636 | Koopman operator / Model predictive control / ETF rebalancing | 4455 | 5148 | No |
| 5692 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-3732 | Persistence landscapes / Topological contours / Equity index | 3008 | 5166 | No |
| 5709 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-3828 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 5256 | 7274 | No |
| 5725 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-3924 | Operator theory / Koopman spectral expansion / ETF allocation | 3022 | 5204 | No |
| 5760 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-4116 | Koopman operator / Model predictive control / ETF rebalancing | 4481 | 5241 | No |
| 5778 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-4212 | Persistence landscapes / Topological contours / Equity index | 3046 | 5259 | No |
| 5795 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-4308 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 5281 | 7306 | No |
| 5811 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-4404 | Operator theory / Koopman spectral expansion / ETF allocation | 3060 | 5297 | No |
| 5846 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-4596 | Koopman operator / Model predictive control / ETF rebalancing | 4507 | 5334 | No |
| 5864 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-4692 | Persistence landscapes / Topological contours / Equity index | 3084 | 5352 | No |
| 5881 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-4788 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 5306 | 7338 | No |
| 5897 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-4884 | Operator theory / Koopman spectral expansion / ETF allocation | 3098 | 5390 | No |
| 5932 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-5076 | Koopman operator / Model predictive control / ETF rebalancing | 4533 | 5427 | No |
| 5950 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-5172 | Persistence landscapes / Topological contours / Equity index | 3122 | 5445 | No |
| 5967 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-5268 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 5331 | 7370 | No |
| 5983 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-5364 | Operator theory / Koopman spectral expansion / ETF allocation | 3136 | 5483 | No |
| 6018 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-5556 | Koopman operator / Model predictive control / ETF rebalancing | 4559 | 5520 | No |
| 6036 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-5652 | Persistence landscapes / Topological contours / Equity index | 3160 | 5538 | No |
| 6053 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-5748 | Point processes / Multivariate Hawkes / Stock liquidity jumps | 5356 | 7402 | No |
| 6069 | Wasserstein Scholarly Tail-Risk Hedge Allocator Eng-5844 | Operator theory / Koopman spectral expansion / ETF allocation | 3174 | 5576 | No |
