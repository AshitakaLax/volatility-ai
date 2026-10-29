# Topology-aware approach to momentum/trend forecasting

**Concept page** · shared by **62** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(1 of them in ranks 426–700; best-ranked member #696) ·
researched 2026-10-29

| | |
|---|---|
| Task | Momentum / trend forecasting |
| Method | Topological data analysis |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | Nothing. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK255, RK254 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Topological Scholarly Stock
Momentum Predictor Sys-442") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Forecast trends from topological features (persistent homology) of price
point clouds. Topological measures have been studied as crash warnings
(RK255), not as trend forecasts; I found no study of the latter.

## The CSV's description

Proposed topology-aware approach to momentum/trend forecasting: Estimate
directional or relative strength from historical prices, returns, or
factor signals and translate the forecast into rankings or portfolio
exposure; the forecast horizon and position rules are not specified.
This is a concept-level interpretation of the title, not a complete
trading specification: the exact model inputs/target, calibration,
entry/exit or rebalance rules, and position sizing are not fully defined
here.

## Evidence

* **Moskowitz, Ooi & Pedersen (2012), "Time series momentum," *Journal
  of Financial Economics* 104(2):** a security's own past 12-month
  return predicts its next month across 58 futures and forwards (see
  RK1). (Standard reference.)
* **Hurst, Ooi & Pedersen (2017), "A Century of Evidence on
  Trend-Following Investing," *Journal of Portfolio Management*:**
  time-series momentum was positive in 8 of the 10 largest drawdowns of
  a 60/40 portfolio since 1880, with low correlation to stocks and
  bonds. (Abstract.)
* **Daniel & Moskowitz (2016), "Momentum crashes," *Journal of Financial
  Economics* 122(2), 221–247:** momentum crashes after market declines,
  in high volatility, during rebounds; a dynamic strategy scaled by
  forecasts of momentum's mean and variance roughly doubles the static
  strategy's Sharpe ratio. (Abstract.)
* **Gidea & Katz (2018):** persistence-landscape norms rose before two
  crashes, in sample (see RK255).

## Against, and failure modes

* Momentum crashes in rebounds after selloffs, exactly when a long-only
  grid is buying (Daniel & Moskowitz).
* A trend forecast on one leveraged ETF is a timing rule with few
  independent episodes to test on.

## Fit with volatility-ai

For this book a trend forecast could only act as a long-or-cash overlay
on TQQQ (RK1, RK2), since shorts are out, or as a rotation across ETFs
(X3). The project's regime work points the other way: its strongest
result is a volatility regime (V17, N5), and direction signals used as
regimes have cost more than they saved. Many members are "stock momentum
predictors", which need a stock universe this project does not have.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Moskowitz, T. J., Ooi, Y. H., Pedersen, L. H. (2012). "Time series
  momentum." *Journal of Financial Economics* 104(2). Standard
  reference.
* Hurst, B., Ooi, Y. H., Pedersen, L. H. (2017). "A Century of Evidence
  on Trend-Following Investing." *Journal of Portfolio Management*.
  <https://www.aqr.com/Insights/Research/Journal-Article/A-Century-of-Evidence-on-Trend-Following-Investing>.
  Abstract.
* Daniel, K., Moskowitz, T. J. (2016). "Momentum crashes." *Journal of
  Financial Economics* 122(2), 221–247. Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 696 | Topological Scholarly Stock Momentum Predictor Sys-442 | Robust optimization / Distributionally robust CVaR / Index tracking | 8359 | 10560 | No |
| 703 | Topological Scholarly Stock Momentum Predictor Sys-922 | Robust optimization / Distributionally robust CVaR / Index tracking | 8399 | 10564 | No |
| 710 | Topological Scholarly Stock Momentum Predictor Sys-1402 | Robust optimization / Distributionally robust CVaR / Index tracking | 8439 | 10568 | No |
| 717 | Topological Scholarly Stock Momentum Predictor Sys-1882 | Robust optimization / Distributionally robust CVaR / Index tracking | 8479 | 10572 | No |
| 721 | Topological Scholarly Stock Momentum Predictor Mod-262 | Robust optimization / Distributionally robust CVaR / Index tracking | 8509 | 10575 | No |
| 727 | Topological Scholarly Stock Momentum Predictor Mod-742 | Robust optimization / Distributionally robust CVaR / Index tracking | 8547 | 10579 | No |
| 733 | Topological Scholarly Stock Momentum Predictor Mod-1222 | Robust optimization / Distributionally robust CVaR / Index tracking | 8585 | 10583 | No |
| 739 | Topological Scholarly Stock Momentum Predictor Mod-1702 | Robust optimization / Distributionally robust CVaR / Index tracking | 8623 | 10587 | No |
| 745 | Topological Scholarly Stock Momentum Predictor Mod-2182 | Robust optimization / Distributionally robust CVaR / Index tracking | 8661 | 10591 | No |
| 751 | Topological Scholarly Stock Momentum Predictor Mod-2662 | Robust optimization / Distributionally robust CVaR / Index tracking | 8699 | 10595 | No |
| 757 | Topological Scholarly Stock Momentum Predictor Mod-3142 | Robust optimization / Distributionally robust CVaR / Index tracking | 8737 | 10599 | No |
| 763 | Topological Scholarly Stock Momentum Predictor Mod-3622 | Robust optimization / Distributionally robust CVaR / Index tracking | 8775 | 10603 | No |
| 907 | Topological Scholarly Stock Momentum Predictor Sys-154 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2207 | 491 | No |
| 919 | Topological Scholarly Stock Momentum Predictor Sys-634 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2254 | 510 | No |
| 931 | Topological Scholarly Stock Momentum Predictor Sys-1114 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2301 | 529 | No |
| 943 | Topological Scholarly Stock Momentum Predictor Sys-1594 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2348 | 548 | No |
| 966 | Topological Scholarly Stock Momentum Predictor Mod-454 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2425 | 581 | No |
| 979 | Topological Scholarly Stock Momentum Predictor Mod-934 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2464 | 600 | No |
| 992 | Topological Scholarly Stock Momentum Predictor Mod-1414 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2503 | 619 | No |
| 1005 | Topological Scholarly Stock Momentum Predictor Mod-1894 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2542 | 638 | No |
| 1018 | Topological Scholarly Stock Momentum Predictor Mod-2374 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2581 | 657 | No |
| 1031 | Topological Scholarly Stock Momentum Predictor Mod-2854 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2620 | 676 | No |
| 1044 | Topological Scholarly Stock Momentum Predictor Mod-3334 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2659 | 695 | No |
| 1057 | Topological Scholarly Stock Momentum Predictor Mod-3814 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2698 | 714 | No |
| 1844 | Topological Scholarly Stock Momentum Predictor Sys-58 | Attention networks / Transformer encoders / Stock alpha generation | 3245 | 488 | No |
| 1864 | Topological Scholarly Stock Momentum Predictor Sys-250 | Neural operators / Deep operator networks / ETF rotation | 3255 | 494 | No |
| 1870 | Topological Scholarly Stock Momentum Predictor Sys-346 | Quantum machine learning / Variational circuits / Index prediction | 11355 | 1710 | No |
| 1893 | Topological Scholarly Stock Momentum Predictor Sys-538 | Attention networks / Transformer encoders / Stock alpha generation | 3269 | 507 | No |
| 1913 | Topological Scholarly Stock Momentum Predictor Sys-730 | Neural operators / Deep operator networks / ETF rotation | 3279 | 513 | No |
| 1919 | Topological Scholarly Stock Momentum Predictor Sys-826 | Quantum machine learning / Variational circuits / Index prediction | 11381 | 1714 | No |
| 1942 | Topological Scholarly Stock Momentum Predictor Sys-1018 | Attention networks / Transformer encoders / Stock alpha generation | 3293 | 526 | No |
| 1962 | Topological Scholarly Stock Momentum Predictor Sys-1210 | Neural operators / Deep operator networks / ETF rotation | 3303 | 532 | No |
| 1968 | Topological Scholarly Stock Momentum Predictor Sys-1306 | Quantum machine learning / Variational circuits / Index prediction | 11407 | 1718 | No |
| 1991 | Topological Scholarly Stock Momentum Predictor Sys-1498 | Attention networks / Transformer encoders / Stock alpha generation | 3317 | 545 | No |
| 2011 | Topological Scholarly Stock Momentum Predictor Sys-1690 | Neural operators / Deep operator networks / ETF rotation | 3327 | 551 | No |
| 2017 | Topological Scholarly Stock Momentum Predictor Sys-1786 | Quantum machine learning / Variational circuits / Index prediction | 11433 | 1722 | No |
| 2040 | Topological Scholarly Stock Momentum Predictor Sys-1978 | Attention networks / Transformer encoders / Stock alpha generation | 3341 | 564 | No |
| 2047 | Topological Scholarly Stock Momentum Predictor Mod-70 | Neural operators / Deep operator networks / ETF rotation | 3345 | 566 | No |
| 2057 | Topological Scholarly Stock Momentum Predictor Mod-166 | Quantum machine learning / Variational circuits / Index prediction | 11457 | 1725 | No |
| 2079 | Topological Scholarly Stock Momentum Predictor Mod-358 | Attention networks / Transformer encoders / Stock alpha generation | 3357 | 578 | No |
| 2100 | Topological Scholarly Stock Momentum Predictor Mod-550 | Neural operators / Deep operator networks / ETF rotation | 3365 | 585 | No |
| 2110 | Topological Scholarly Stock Momentum Predictor Mod-646 | Quantum machine learning / Variational circuits / Index prediction | 11484 | 1729 | No |
| 2132 | Topological Scholarly Stock Momentum Predictor Mod-838 | Attention networks / Transformer encoders / Stock alpha generation | 3377 | 597 | No |
| 2153 | Topological Scholarly Stock Momentum Predictor Mod-1030 | Neural operators / Deep operator networks / ETF rotation | 3385 | 604 | No |
| 2163 | Topological Scholarly Stock Momentum Predictor Mod-1126 | Quantum machine learning / Variational circuits / Index prediction | 11511 | 1733 | No |
| 2185 | Topological Scholarly Stock Momentum Predictor Mod-1318 | Attention networks / Transformer encoders / Stock alpha generation | 3397 | 616 | No |
| 2206 | Topological Scholarly Stock Momentum Predictor Mod-1510 | Neural operators / Deep operator networks / ETF rotation | 3405 | 623 | No |
| 2216 | Topological Scholarly Stock Momentum Predictor Mod-1606 | Quantum machine learning / Variational circuits / Index prediction | 11538 | 1737 | No |
| 2238 | Topological Scholarly Stock Momentum Predictor Mod-1798 | Attention networks / Transformer encoders / Stock alpha generation | 3417 | 635 | No |
| 2259 | Topological Scholarly Stock Momentum Predictor Mod-1990 | Neural operators / Deep operator networks / ETF rotation | 3425 | 642 | No |
| 2269 | Topological Scholarly Stock Momentum Predictor Mod-2086 | Quantum machine learning / Variational circuits / Index prediction | 11565 | 1741 | No |
| 2291 | Topological Scholarly Stock Momentum Predictor Mod-2278 | Attention networks / Transformer encoders / Stock alpha generation | 3437 | 654 | No |
| 2312 | Topological Scholarly Stock Momentum Predictor Mod-2470 | Neural operators / Deep operator networks / ETF rotation | 3445 | 661 | No |
| 2322 | Topological Scholarly Stock Momentum Predictor Mod-2566 | Quantum machine learning / Variational circuits / Index prediction | 11592 | 1745 | No |
| 2344 | Topological Scholarly Stock Momentum Predictor Mod-2758 | Attention networks / Transformer encoders / Stock alpha generation | 3457 | 673 | No |
| 2365 | Topological Scholarly Stock Momentum Predictor Mod-2950 | Neural operators / Deep operator networks / ETF rotation | 3465 | 680 | No |
| 2375 | Topological Scholarly Stock Momentum Predictor Mod-3046 | Quantum machine learning / Variational circuits / Index prediction | 11619 | 1749 | No |
| 2397 | Topological Scholarly Stock Momentum Predictor Mod-3238 | Attention networks / Transformer encoders / Stock alpha generation | 3477 | 692 | No |
| 2418 | Topological Scholarly Stock Momentum Predictor Mod-3430 | Neural operators / Deep operator networks / ETF rotation | 3485 | 699 | No |
| 2428 | Topological Scholarly Stock Momentum Predictor Mod-3526 | Quantum machine learning / Variational circuits / Index prediction | 11646 | 1753 | No |
| 2450 | Topological Scholarly Stock Momentum Predictor Mod-3718 | Attention networks / Transformer encoders / Stock alpha generation | 3497 | 711 | No |
| 2471 | Topological Scholarly Stock Momentum Predictor Mod-3910 | Neural operators / Deep operator networks / ETF rotation | 3505 | 718 | No |
