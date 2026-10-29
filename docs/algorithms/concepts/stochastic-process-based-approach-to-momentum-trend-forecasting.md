# Stochastic-process-based approach to momentum/trend forecasting

**Concept page** · shared by **72** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(28 of them in ranks 426–700; best-ranked member #430) ·
researched 2026-10-29

| | |
|---|---|
| Task | Momentum / trend forecasting |
| Method | Stochastic-process trend estimation (drift extraction with Kalman or L1 filters) |
| Fit with this project | ⏳ as a long-or-cash overlay (as RK1) · ⛔ for stock members |
| Implemented in volatility-ai | **Research code** in `research.catalog.concepts`: `kalman_trend`, `l1_trend_filter`, `l1_trend_positions`; tested on synthetic data, not wired into the engine. Related code already here: Time-series momentum weights exist as research code (`trend_following.tsmom_weights`, RK1); relative-strength rotation is built (X3). |
| Evidence | Evidence found (for the task; see the page for the method) |
| Related ledger entries | RK1, RK2, RK7, X3 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Stochastic Scholarly Stock
Momentum Predictor Ref-182") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Estimate the trend as the drift of a stochastic process, filtered out of
the noise with a Kalman or L1 trend filter, and trade its sign or
strength. This is how much of the industry's trend following is
formalised: a review of linear and nonlinear trend filters applied to
the S&P 500 calibrates them by prediction error, and an L1 filter
extracts piecewise-linear trends. The underlying effect, time-series
momentum, is one of the best documented in finance.

## The CSV's description

Proposed stochastic-process-based approach to momentum/trend
forecasting: Estimate directional or relative strength from historical
prices, returns, or factor signals and translate the forecast into
rankings or portfolio exposure; the forecast horizon and position rules
are not specified. This is a concept-level interpretation of the title,
not a complete trading specification: the exact model inputs/target,
calibration, entry/exit or rebalance rules, and position sizing are not
fully defined here.

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
* **Bruder, Dao, Richard & Roncalli (2011), "Trend Filtering Methods for
  Momentum Strategies" (Lyxor white paper; SSRN 2289097):** reviews
  linear and nonlinear trend estimators (moving averages, Kalman and L1
  filters), univariate and multivariate, calibrated by prediction error,
  applied to the S&P 500; Dao's L1 filter (arXiv 1403.4069) extracts
  piecewise-linear trends. Practitioner research. (Abstracts.)

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
* Bruder, B., Dao, T.-L., Richard, J.-C., Roncalli, T. (2011). "Trend
  Filtering Methods for Momentum Strategies." Lyxor. SSRN 2289097.
  Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 430 | Stochastic Scholarly Stock Momentum Predictor Ref-182 | Robust optimization / Distributionally robust CVaR / Index tracking | 4656 | 465 | No |
| 436 | Stochastic Scholarly Stock Momentum Predictor Ref-662 | Robust optimization / Distributionally robust CVaR / Index tracking | 4683 | 476 | No |
| 516 | Stochastic Scholarly Stock Momentum Predictor Eng-262 | Robust optimization / Distributionally robust CVaR / Index tracking | 8826 | 10609 | No |
| 522 | Stochastic Scholarly Stock Momentum Predictor Eng-742 | Robust optimization / Distributionally robust CVaR / Index tracking | 8862 | 10613 | No |
| 528 | Stochastic Scholarly Stock Momentum Predictor Eng-1222 | Robust optimization / Distributionally robust CVaR / Index tracking | 8898 | 10617 | No |
| 534 | Stochastic Scholarly Stock Momentum Predictor Eng-1702 | Robust optimization / Distributionally robust CVaR / Index tracking | 8934 | 10621 | No |
| 540 | Stochastic Scholarly Stock Momentum Predictor Eng-2182 | Robust optimization / Distributionally robust CVaR / Index tracking | 8970 | 10625 | No |
| 546 | Stochastic Scholarly Stock Momentum Predictor Eng-2662 | Robust optimization / Distributionally robust CVaR / Index tracking | 9006 | 10629 | No |
| 552 | Stochastic Scholarly Stock Momentum Predictor Eng-3142 | Robust optimization / Distributionally robust CVaR / Index tracking | 9042 | 10633 | No |
| 558 | Stochastic Scholarly Stock Momentum Predictor Eng-3622 | Robust optimization / Distributionally robust CVaR / Index tracking | 9078 | 10637 | No |
| 564 | Stochastic Scholarly Stock Momentum Predictor Eng-4102 | Robust optimization / Distributionally robust CVaR / Index tracking | 9114 | 10641 | No |
| 570 | Stochastic Scholarly Stock Momentum Predictor Eng-4582 | Robust optimization / Distributionally robust CVaR / Index tracking | 9150 | 10645 | No |
| 576 | Stochastic Scholarly Stock Momentum Predictor Eng-5062 | Robust optimization / Distributionally robust CVaR / Index tracking | 9186 | 10649 | No |
| 582 | Stochastic Scholarly Stock Momentum Predictor Eng-5542 | Robust optimization / Distributionally robust CVaR / Index tracking | 9222 | 10653 | No |
| 607 | Stochastic Scholarly Stock Momentum Predictor Ref-374 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1075 | 2796 | No |
| 610 | Stochastic Scholarly Stock Momentum Predictor Ref-854 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1109 | 2800 | No |
| 638 | Stochastic Scholarly Stock Momentum Predictor Eng-454 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2748 | 738 | No |
| 641 | Stochastic Scholarly Stock Momentum Predictor Eng-934 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2786 | 757 | No |
| 644 | Stochastic Scholarly Stock Momentum Predictor Eng-1414 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2824 | 776 | No |
| 647 | Stochastic Scholarly Stock Momentum Predictor Eng-1894 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2862 | 795 | No |
| 650 | Stochastic Scholarly Stock Momentum Predictor Eng-2374 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2900 | 814 | No |
| 653 | Stochastic Scholarly Stock Momentum Predictor Eng-2854 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2938 | 833 | No |
| 656 | Stochastic Scholarly Stock Momentum Predictor Eng-3334 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2976 | 852 | No |
| 659 | Stochastic Scholarly Stock Momentum Predictor Eng-3814 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 3014 | 871 | No |
| 662 | Stochastic Scholarly Stock Momentum Predictor Eng-4294 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 3052 | 890 | No |
| 665 | Stochastic Scholarly Stock Momentum Predictor Eng-4774 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 3090 | 909 | No |
| 668 | Stochastic Scholarly Stock Momentum Predictor Eng-5254 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 3128 | 928 | No |
| 671 | Stochastic Scholarly Stock Momentum Predictor Eng-5734 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 3166 | 947 | No |
| 1202 | Stochastic Scholarly Stock Momentum Predictor Ref-278 | Attention networks / Transformer encoders / Stock alpha generation | 11994 | 10743 | No |
| 1213 | Stochastic Scholarly Stock Momentum Predictor Ref-758 | Attention networks / Transformer encoders / Stock alpha generation | 11998 | 10762 | No |
| 1407 | Stochastic Scholarly Stock Momentum Predictor Eng-358 | Attention networks / Transformer encoders / Stock alpha generation | 3523 | 735 | No |
| 1418 | Stochastic Scholarly Stock Momentum Predictor Eng-838 | Attention networks / Transformer encoders / Stock alpha generation | 3543 | 754 | No |
| 1429 | Stochastic Scholarly Stock Momentum Predictor Eng-1318 | Attention networks / Transformer encoders / Stock alpha generation | 3563 | 773 | No |
| 1440 | Stochastic Scholarly Stock Momentum Predictor Eng-1798 | Attention networks / Transformer encoders / Stock alpha generation | 3583 | 792 | No |
| 1451 | Stochastic Scholarly Stock Momentum Predictor Eng-2278 | Attention networks / Transformer encoders / Stock alpha generation | 3603 | 811 | No |
| 1462 | Stochastic Scholarly Stock Momentum Predictor Eng-2758 | Attention networks / Transformer encoders / Stock alpha generation | 3623 | 830 | No |
| 1473 | Stochastic Scholarly Stock Momentum Predictor Eng-3238 | Attention networks / Transformer encoders / Stock alpha generation | 3643 | 849 | No |
| 1484 | Stochastic Scholarly Stock Momentum Predictor Eng-3718 | Attention networks / Transformer encoders / Stock alpha generation | 3663 | 868 | No |
| 1495 | Stochastic Scholarly Stock Momentum Predictor Eng-4198 | Attention networks / Transformer encoders / Stock alpha generation | 3683 | 887 | No |
| 1506 | Stochastic Scholarly Stock Momentum Predictor Eng-4678 | Attention networks / Transformer encoders / Stock alpha generation | 3703 | 906 | No |
| 1517 | Stochastic Scholarly Stock Momentum Predictor Eng-5158 | Attention networks / Transformer encoders / Stock alpha generation | 3723 | 925 | No |
| 1528 | Stochastic Scholarly Stock Momentum Predictor Eng-5638 | Attention networks / Transformer encoders / Stock alpha generation | 3743 | 944 | No |
| 1731 | Stochastic Scholarly Stock Momentum Predictor Ref-86 | Quantum machine learning / Variational circuits / Index prediction | 13915 | 13509 | No |
| 1775 | Stochastic Scholarly Stock Momentum Predictor Ref-470 | Neural operators / Deep operator networks / ETF rotation | 4671 | 2171 | No |
| 1786 | Stochastic Scholarly Stock Momentum Predictor Ref-566 | Quantum machine learning / Variational circuits / Index prediction | 13923 | 13513 | No |
| 1830 | Stochastic Scholarly Stock Momentum Predictor Ref-950 | Neural operators / Deep operator networks / ETF rotation | 4698 | 2196 | No |
| 2487 | Stochastic Scholarly Stock Momentum Predictor Eng-70 | Neural operators / Deep operator networks / ETF rotation | 3511 | 723 | No |
| 2498 | Stochastic Scholarly Stock Momentum Predictor Eng-166 | Quantum machine learning / Variational circuits / Index prediction | 11682 | 1758 | No |
| 2542 | Stochastic Scholarly Stock Momentum Predictor Eng-550 | Neural operators / Deep operator networks / ETF rotation | 3531 | 742 | No |
| 2553 | Stochastic Scholarly Stock Momentum Predictor Eng-646 | Quantum machine learning / Variational circuits / Index prediction | 11707 | 1762 | No |
| 2597 | Stochastic Scholarly Stock Momentum Predictor Eng-1030 | Neural operators / Deep operator networks / ETF rotation | 3551 | 761 | No |
| 2608 | Stochastic Scholarly Stock Momentum Predictor Eng-1126 | Quantum machine learning / Variational circuits / Index prediction | 11732 | 1766 | No |
| 2652 | Stochastic Scholarly Stock Momentum Predictor Eng-1510 | Neural operators / Deep operator networks / ETF rotation | 3571 | 780 | No |
| 2663 | Stochastic Scholarly Stock Momentum Predictor Eng-1606 | Quantum machine learning / Variational circuits / Index prediction | 11757 | 1770 | No |
| 2707 | Stochastic Scholarly Stock Momentum Predictor Eng-1990 | Neural operators / Deep operator networks / ETF rotation | 3591 | 799 | No |
| 2718 | Stochastic Scholarly Stock Momentum Predictor Eng-2086 | Quantum machine learning / Variational circuits / Index prediction | 11782 | 1774 | No |
| 2762 | Stochastic Scholarly Stock Momentum Predictor Eng-2470 | Neural operators / Deep operator networks / ETF rotation | 3611 | 818 | No |
| 2773 | Stochastic Scholarly Stock Momentum Predictor Eng-2566 | Quantum machine learning / Variational circuits / Index prediction | 11807 | 1778 | No |
| 2817 | Stochastic Scholarly Stock Momentum Predictor Eng-2950 | Neural operators / Deep operator networks / ETF rotation | 3631 | 837 | No |
| 2828 | Stochastic Scholarly Stock Momentum Predictor Eng-3046 | Quantum machine learning / Variational circuits / Index prediction | 11832 | 1782 | No |
| 2872 | Stochastic Scholarly Stock Momentum Predictor Eng-3430 | Neural operators / Deep operator networks / ETF rotation | 3651 | 856 | No |
| 2883 | Stochastic Scholarly Stock Momentum Predictor Eng-3526 | Quantum machine learning / Variational circuits / Index prediction | 11857 | 1786 | No |
| 2927 | Stochastic Scholarly Stock Momentum Predictor Eng-3910 | Neural operators / Deep operator networks / ETF rotation | 3671 | 875 | No |
| 2938 | Stochastic Scholarly Stock Momentum Predictor Eng-4006 | Quantum machine learning / Variational circuits / Index prediction | 11882 | 1790 | No |
| 2982 | Stochastic Scholarly Stock Momentum Predictor Eng-4390 | Neural operators / Deep operator networks / ETF rotation | 3691 | 894 | No |
| 2993 | Stochastic Scholarly Stock Momentum Predictor Eng-4486 | Quantum machine learning / Variational circuits / Index prediction | 11907 | 1794 | No |
| 3037 | Stochastic Scholarly Stock Momentum Predictor Eng-4870 | Neural operators / Deep operator networks / ETF rotation | 3711 | 913 | No |
| 3048 | Stochastic Scholarly Stock Momentum Predictor Eng-4966 | Quantum machine learning / Variational circuits / Index prediction | 11932 | 1798 | No |
| 3092 | Stochastic Scholarly Stock Momentum Predictor Eng-5350 | Neural operators / Deep operator networks / ETF rotation | 3731 | 932 | No |
| 3103 | Stochastic Scholarly Stock Momentum Predictor Eng-5446 | Quantum machine learning / Variational circuits / Index prediction | 11957 | 1802 | No |
| 3147 | Stochastic Scholarly Stock Momentum Predictor Eng-5830 | Neural operators / Deep operator networks / ETF rotation | 3751 | 951 | No |
| 3158 | Stochastic Scholarly Stock Momentum Predictor Eng-5926 | Quantum machine learning / Variational circuits / Index prediction | 11982 | 1806 | No |
