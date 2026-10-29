# Adaptive approach to momentum/trend forecasting

**Concept page** · shared by **73** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(30 of them in ranks 426–700; best-ranked member #431) ·
researched 2026-10-29

| | |
|---|---|
| Task | Momentum / trend forecasting |
| Method | Adaptive lookback / speed selection |
| Fit with this project | ⏳ as a long-or-cash overlay (as RK1) · ⛔ for stock members |
| Implemented in volatility-ai | Time-series momentum weights exist as research code (`trend_following.tsmom_weights`, RK1); relative-strength rotation is built (X3). |
| Evidence | Evidence found (for the task; see the page for the method) |
| Related ledger entries | RK1, RK2, RK7, X3 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Adaptive Scholarly Stock
Momentum Predictor Ref-302") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Adapt the trend signal's speed to the market instead of fixing one
lookback. The evidence is direct: slow time-series momentum reacts late
at turning points and fast momentum gives false alarms, and blending the
two by market cycle beat either out of sample. Adaptive moving averages
(Kaufman's efficiency ratio) are the practitioner version.

## The CSV's description

Proposed adaptive approach to momentum/trend forecasting: Estimate
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
* **Goulding, Harvey & Mazzoleni (2023), "Momentum turning points,"
  *Journal of Financial Economics* 149(3), 378–406:** slow and fast
  time-series momentum disagree at turning points; slow signals react
  late, fast ones give false alarms, and blending them by the market
  cycle (bull, correction, bear, rebound) improves on either, out of
  sample across markets. (Abstract and working paper.)

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
* Goulding, C. L., Harvey, C. R., Mazzoleni, M. G. (2023). "Momentum
  turning points." *Journal of Financial Economics* 149(3), 378–406.
  Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 431 | Adaptive Scholarly Stock Momentum Predictor Ref-302 | Robust optimization / Distributionally robust CVaR / Index tracking | 4663 | 468 | No |
| 437 | Adaptive Scholarly Stock Momentum Predictor Ref-782 | Robust optimization / Distributionally robust CVaR / Index tracking | 4690 | 479 | No |
| 518 | Adaptive Scholarly Stock Momentum Predictor Eng-382 | Robust optimization / Distributionally robust CVaR / Index tracking | 8833 | 10610 | No |
| 524 | Adaptive Scholarly Stock Momentum Predictor Eng-862 | Robust optimization / Distributionally robust CVaR / Index tracking | 8869 | 10614 | No |
| 530 | Adaptive Scholarly Stock Momentum Predictor Eng-1342 | Robust optimization / Distributionally robust CVaR / Index tracking | 8905 | 10618 | No |
| 536 | Adaptive Scholarly Stock Momentum Predictor Eng-1822 | Robust optimization / Distributionally robust CVaR / Index tracking | 8941 | 10622 | No |
| 542 | Adaptive Scholarly Stock Momentum Predictor Eng-2302 | Robust optimization / Distributionally robust CVaR / Index tracking | 8977 | 10626 | No |
| 548 | Adaptive Scholarly Stock Momentum Predictor Eng-2782 | Robust optimization / Distributionally robust CVaR / Index tracking | 9013 | 10630 | No |
| 554 | Adaptive Scholarly Stock Momentum Predictor Eng-3262 | Robust optimization / Distributionally robust CVaR / Index tracking | 9049 | 10634 | No |
| 560 | Adaptive Scholarly Stock Momentum Predictor Eng-3742 | Robust optimization / Distributionally robust CVaR / Index tracking | 9085 | 10638 | No |
| 566 | Adaptive Scholarly Stock Momentum Predictor Eng-4222 | Robust optimization / Distributionally robust CVaR / Index tracking | 9121 | 10642 | No |
| 572 | Adaptive Scholarly Stock Momentum Predictor Eng-4702 | Robust optimization / Distributionally robust CVaR / Index tracking | 9157 | 10646 | No |
| 578 | Adaptive Scholarly Stock Momentum Predictor Eng-5182 | Robust optimization / Distributionally robust CVaR / Index tracking | 9193 | 10650 | No |
| 584 | Adaptive Scholarly Stock Momentum Predictor Eng-5662 | Robust optimization / Distributionally robust CVaR / Index tracking | 9229 | 10654 | No |
| 605 | Adaptive Scholarly Stock Momentum Predictor Ref-14 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1049 | 2793 | No |
| 608 | Adaptive Scholarly Stock Momentum Predictor Ref-494 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1083 | 2797 | No |
| 611 | Adaptive Scholarly Stock Momentum Predictor Ref-974 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1117 | 2801 | No |
| 636 | Adaptive Scholarly Stock Momentum Predictor Eng-94 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2720 | 724 | No |
| 639 | Adaptive Scholarly Stock Momentum Predictor Eng-574 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2758 | 743 | No |
| 642 | Adaptive Scholarly Stock Momentum Predictor Eng-1054 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2796 | 762 | No |
| 645 | Adaptive Scholarly Stock Momentum Predictor Eng-1534 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2834 | 781 | No |
| 648 | Adaptive Scholarly Stock Momentum Predictor Eng-2014 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2872 | 800 | No |
| 651 | Adaptive Scholarly Stock Momentum Predictor Eng-2494 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2910 | 819 | No |
| 654 | Adaptive Scholarly Stock Momentum Predictor Eng-2974 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2948 | 838 | No |
| 657 | Adaptive Scholarly Stock Momentum Predictor Eng-3454 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2986 | 857 | No |
| 660 | Adaptive Scholarly Stock Momentum Predictor Eng-3934 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 3024 | 876 | No |
| 663 | Adaptive Scholarly Stock Momentum Predictor Eng-4414 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 3062 | 895 | No |
| 666 | Adaptive Scholarly Stock Momentum Predictor Eng-4894 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 3100 | 914 | No |
| 669 | Adaptive Scholarly Stock Momentum Predictor Eng-5374 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 3138 | 933 | No |
| 672 | Adaptive Scholarly Stock Momentum Predictor Eng-5854 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 3176 | 952 | No |
| 1206 | Adaptive Scholarly Stock Momentum Predictor Ref-398 | Attention networks / Transformer encoders / Stock alpha generation | 11995 | 10747 | No |
| 1217 | Adaptive Scholarly Stock Momentum Predictor Ref-878 | Attention networks / Transformer encoders / Stock alpha generation | 11999 | 10766 | No |
| 1409 | Adaptive Scholarly Stock Momentum Predictor Eng-478 | Attention networks / Transformer encoders / Stock alpha generation | 3528 | 740 | No |
| 1420 | Adaptive Scholarly Stock Momentum Predictor Eng-958 | Attention networks / Transformer encoders / Stock alpha generation | 3548 | 759 | No |
| 1431 | Adaptive Scholarly Stock Momentum Predictor Eng-1438 | Attention networks / Transformer encoders / Stock alpha generation | 3568 | 778 | No |
| 1442 | Adaptive Scholarly Stock Momentum Predictor Eng-1918 | Attention networks / Transformer encoders / Stock alpha generation | 3588 | 797 | No |
| 1453 | Adaptive Scholarly Stock Momentum Predictor Eng-2398 | Attention networks / Transformer encoders / Stock alpha generation | 3608 | 816 | No |
| 1464 | Adaptive Scholarly Stock Momentum Predictor Eng-2878 | Attention networks / Transformer encoders / Stock alpha generation | 3628 | 835 | No |
| 1475 | Adaptive Scholarly Stock Momentum Predictor Eng-3358 | Attention networks / Transformer encoders / Stock alpha generation | 3648 | 854 | No |
| 1486 | Adaptive Scholarly Stock Momentum Predictor Eng-3838 | Attention networks / Transformer encoders / Stock alpha generation | 3668 | 873 | No |
| 1497 | Adaptive Scholarly Stock Momentum Predictor Eng-4318 | Attention networks / Transformer encoders / Stock alpha generation | 3688 | 892 | No |
| 1508 | Adaptive Scholarly Stock Momentum Predictor Eng-4798 | Attention networks / Transformer encoders / Stock alpha generation | 3708 | 911 | No |
| 1519 | Adaptive Scholarly Stock Momentum Predictor Eng-5278 | Attention networks / Transformer encoders / Stock alpha generation | 3728 | 930 | No |
| 1530 | Adaptive Scholarly Stock Momentum Predictor Eng-5758 | Attention networks / Transformer encoders / Stock alpha generation | 3748 | 949 | No |
| 1735 | Adaptive Scholarly Stock Momentum Predictor Ref-110 | Neural operators / Deep operator networks / ETF rotation | 4651 | 2153 | No |
| 1747 | Adaptive Scholarly Stock Momentum Predictor Ref-206 | Quantum machine learning / Variational circuits / Index prediction | 13917 | 13510 | No |
| 1790 | Adaptive Scholarly Stock Momentum Predictor Ref-590 | Neural operators / Deep operator networks / ETF rotation | 4678 | 2178 | No |
| 1802 | Adaptive Scholarly Stock Momentum Predictor Ref-686 | Quantum machine learning / Variational circuits / Index prediction | 13925 | 13514 | No |
| 2500 | Adaptive Scholarly Stock Momentum Predictor Eng-190 | Neural operators / Deep operator networks / ETF rotation | 3516 | 727 | No |
| 2512 | Adaptive Scholarly Stock Momentum Predictor Eng-286 | Quantum machine learning / Variational circuits / Index prediction | 11688 | 1759 | No |
| 2555 | Adaptive Scholarly Stock Momentum Predictor Eng-670 | Neural operators / Deep operator networks / ETF rotation | 3536 | 746 | No |
| 2567 | Adaptive Scholarly Stock Momentum Predictor Eng-766 | Quantum machine learning / Variational circuits / Index prediction | 11713 | 1763 | No |
| 2610 | Adaptive Scholarly Stock Momentum Predictor Eng-1150 | Neural operators / Deep operator networks / ETF rotation | 3556 | 765 | No |
| 2622 | Adaptive Scholarly Stock Momentum Predictor Eng-1246 | Quantum machine learning / Variational circuits / Index prediction | 11738 | 1767 | No |
| 2665 | Adaptive Scholarly Stock Momentum Predictor Eng-1630 | Neural operators / Deep operator networks / ETF rotation | 3576 | 784 | No |
| 2677 | Adaptive Scholarly Stock Momentum Predictor Eng-1726 | Quantum machine learning / Variational circuits / Index prediction | 11763 | 1771 | No |
| 2720 | Adaptive Scholarly Stock Momentum Predictor Eng-2110 | Neural operators / Deep operator networks / ETF rotation | 3596 | 803 | No |
| 2732 | Adaptive Scholarly Stock Momentum Predictor Eng-2206 | Quantum machine learning / Variational circuits / Index prediction | 11788 | 1775 | No |
| 2775 | Adaptive Scholarly Stock Momentum Predictor Eng-2590 | Neural operators / Deep operator networks / ETF rotation | 3616 | 822 | No |
| 2787 | Adaptive Scholarly Stock Momentum Predictor Eng-2686 | Quantum machine learning / Variational circuits / Index prediction | 11813 | 1779 | No |
| 2830 | Adaptive Scholarly Stock Momentum Predictor Eng-3070 | Neural operators / Deep operator networks / ETF rotation | 3636 | 841 | No |
| 2842 | Adaptive Scholarly Stock Momentum Predictor Eng-3166 | Quantum machine learning / Variational circuits / Index prediction | 11838 | 1783 | No |
| 2885 | Adaptive Scholarly Stock Momentum Predictor Eng-3550 | Neural operators / Deep operator networks / ETF rotation | 3656 | 860 | No |
| 2897 | Adaptive Scholarly Stock Momentum Predictor Eng-3646 | Quantum machine learning / Variational circuits / Index prediction | 11863 | 1787 | No |
| 2940 | Adaptive Scholarly Stock Momentum Predictor Eng-4030 | Neural operators / Deep operator networks / ETF rotation | 3676 | 879 | No |
| 2952 | Adaptive Scholarly Stock Momentum Predictor Eng-4126 | Quantum machine learning / Variational circuits / Index prediction | 11888 | 1791 | No |
| 2995 | Adaptive Scholarly Stock Momentum Predictor Eng-4510 | Neural operators / Deep operator networks / ETF rotation | 3696 | 898 | No |
| 3007 | Adaptive Scholarly Stock Momentum Predictor Eng-4606 | Quantum machine learning / Variational circuits / Index prediction | 11913 | 1795 | No |
| 3050 | Adaptive Scholarly Stock Momentum Predictor Eng-4990 | Neural operators / Deep operator networks / ETF rotation | 3716 | 917 | No |
| 3062 | Adaptive Scholarly Stock Momentum Predictor Eng-5086 | Quantum machine learning / Variational circuits / Index prediction | 11938 | 1799 | No |
| 3105 | Adaptive Scholarly Stock Momentum Predictor Eng-5470 | Neural operators / Deep operator networks / ETF rotation | 3736 | 936 | No |
| 3117 | Adaptive Scholarly Stock Momentum Predictor Eng-5566 | Quantum machine learning / Variational circuits / Index prediction | 11963 | 1803 | No |
| 3160 | Adaptive Scholarly Stock Momentum Predictor Eng-5950 | Neural operators / Deep operator networks / ETF rotation | 3756 | 955 | No |
