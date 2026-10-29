# Markov-state-based approach to momentum/trend forecasting

**Concept page** · shared by **74** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(30 of them in ranks 426–700; best-ranked member #433) ·
researched 2026-10-29

| | |
|---|---|
| Task | Momentum / trend forecasting |
| Method | Hidden Markov / regime-switching states |
| Fit with this project | 🧪 the regime models exist (C-R3) · ⏳ as a regime input |
| Implemented in volatility-ai | **Research code** in `research.catalog.concepts`: `hmm_trend`; tested on synthetic data, not wired into the engine. Related code already here: Causal HMM and Gaussian-mixture regimes are research code (`regime_models.GaussianHMM`, `causal_turbulence`, ledger C-R3); not wired as a trend forecast. |
| Evidence | Evidence found (for the task; see the page for the method) |
| Related ledger entries | C-R3, V17, N5, RK1 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Markovian Scholarly Stock
Momentum Predictor Ref-422") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Infer hidden market states (bull, bear, turbulent) with a hidden Markov
or Markov-switching model and forecast the trend from the current state.
Regime-based allocation with two-state Gaussian HMMs has been shown to
add value over static weights and to cut drawdowns, out of sample after
costs in a thesis version. This repository already has causal HMM and
Gaussian-mixture regimes as research code.

## The CSV's description

Proposed Markov-state-based approach to momentum/trend forecasting:
Estimate directional or relative strength from historical prices,
returns, or factor signals and translate the forecast into rankings or
portfolio exposure; the forecast horizon and position rules are not
specified. This is a concept-level interpretation of the title, not a
complete trading specification: the exact model inputs/target,
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
* **Nystrup, Hansson, Madsen & Lindström (2016), "Regime-Based versus
  Static Asset Allocation: Letting the Data Speak," *Journal of
  Portfolio Management* 42(1), 103–109:** regime-switching allocation
  can beat static weights even without forecasting skill; later work by
  the same group reports reduced drawdowns. (Abstract.)

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
* Nystrup, P., Hansson, B. W., Madsen, H., Lindström, E. (2016).
  *Journal of Portfolio Management* 42(1), 103–109. Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 433 | Markovian Scholarly Stock Momentum Predictor Ref-422 | Robust optimization / Distributionally robust CVaR / Index tracking | 4668 | 471 | No |
| 439 | Markovian Scholarly Stock Momentum Predictor Ref-902 | Robust optimization / Distributionally robust CVaR / Index tracking | 4695 | 482 | No |
| 514 | Markovian Scholarly Stock Momentum Predictor Eng-22 | Robust optimization / Distributionally robust CVaR / Index tracking | 8806 | 10607 | No |
| 520 | Markovian Scholarly Stock Momentum Predictor Eng-502 | Robust optimization / Distributionally robust CVaR / Index tracking | 8842 | 10611 | No |
| 526 | Markovian Scholarly Stock Momentum Predictor Eng-982 | Robust optimization / Distributionally robust CVaR / Index tracking | 8878 | 10615 | No |
| 532 | Markovian Scholarly Stock Momentum Predictor Eng-1462 | Robust optimization / Distributionally robust CVaR / Index tracking | 8914 | 10619 | No |
| 538 | Markovian Scholarly Stock Momentum Predictor Eng-1942 | Robust optimization / Distributionally robust CVaR / Index tracking | 8950 | 10623 | No |
| 544 | Markovian Scholarly Stock Momentum Predictor Eng-2422 | Robust optimization / Distributionally robust CVaR / Index tracking | 8986 | 10627 | No |
| 550 | Markovian Scholarly Stock Momentum Predictor Eng-2902 | Robust optimization / Distributionally robust CVaR / Index tracking | 9022 | 10631 | No |
| 556 | Markovian Scholarly Stock Momentum Predictor Eng-3382 | Robust optimization / Distributionally robust CVaR / Index tracking | 9058 | 10635 | No |
| 562 | Markovian Scholarly Stock Momentum Predictor Eng-3862 | Robust optimization / Distributionally robust CVaR / Index tracking | 9094 | 10639 | No |
| 568 | Markovian Scholarly Stock Momentum Predictor Eng-4342 | Robust optimization / Distributionally robust CVaR / Index tracking | 9130 | 10643 | No |
| 574 | Markovian Scholarly Stock Momentum Predictor Eng-4822 | Robust optimization / Distributionally robust CVaR / Index tracking | 9166 | 10647 | No |
| 580 | Markovian Scholarly Stock Momentum Predictor Eng-5302 | Robust optimization / Distributionally robust CVaR / Index tracking | 9202 | 10651 | No |
| 586 | Markovian Scholarly Stock Momentum Predictor Eng-5782 | Robust optimization / Distributionally robust CVaR / Index tracking | 9238 | 10655 | No |
| 606 | Markovian Scholarly Stock Momentum Predictor Ref-134 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1059 | 2794 | No |
| 609 | Markovian Scholarly Stock Momentum Predictor Ref-614 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1093 | 2798 | No |
| 637 | Markovian Scholarly Stock Momentum Predictor Eng-214 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2729 | 728 | No |
| 640 | Markovian Scholarly Stock Momentum Predictor Eng-694 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2767 | 747 | No |
| 643 | Markovian Scholarly Stock Momentum Predictor Eng-1174 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2805 | 766 | No |
| 646 | Markovian Scholarly Stock Momentum Predictor Eng-1654 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2843 | 785 | No |
| 649 | Markovian Scholarly Stock Momentum Predictor Eng-2134 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2881 | 804 | No |
| 652 | Markovian Scholarly Stock Momentum Predictor Eng-2614 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2919 | 823 | No |
| 655 | Markovian Scholarly Stock Momentum Predictor Eng-3094 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2957 | 842 | No |
| 658 | Markovian Scholarly Stock Momentum Predictor Eng-3574 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2995 | 861 | No |
| 661 | Markovian Scholarly Stock Momentum Predictor Eng-4054 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 3033 | 880 | No |
| 664 | Markovian Scholarly Stock Momentum Predictor Eng-4534 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 3071 | 899 | No |
| 667 | Markovian Scholarly Stock Momentum Predictor Eng-5014 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 3109 | 918 | No |
| 670 | Markovian Scholarly Stock Momentum Predictor Eng-5494 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 3147 | 937 | No |
| 673 | Markovian Scholarly Stock Momentum Predictor Eng-5974 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 3185 | 956 | No |
| 1198 | Markovian Scholarly Stock Momentum Predictor Ref-38 | Attention networks / Transformer encoders / Stock alpha generation | 11992 | 10733 | No |
| 1209 | Markovian Scholarly Stock Momentum Predictor Ref-518 | Attention networks / Transformer encoders / Stock alpha generation | 11996 | 10752 | No |
| 1220 | Markovian Scholarly Stock Momentum Predictor Ref-998 | Attention networks / Transformer encoders / Stock alpha generation | 12000 | 10771 | No |
| 1402 | Markovian Scholarly Stock Momentum Predictor Eng-118 | Attention networks / Transformer encoders / Stock alpha generation | 3513 | 726 | No |
| 1413 | Markovian Scholarly Stock Momentum Predictor Eng-598 | Attention networks / Transformer encoders / Stock alpha generation | 3533 | 745 | No |
| 1424 | Markovian Scholarly Stock Momentum Predictor Eng-1078 | Attention networks / Transformer encoders / Stock alpha generation | 3553 | 764 | No |
| 1435 | Markovian Scholarly Stock Momentum Predictor Eng-1558 | Attention networks / Transformer encoders / Stock alpha generation | 3573 | 783 | No |
| 1446 | Markovian Scholarly Stock Momentum Predictor Eng-2038 | Attention networks / Transformer encoders / Stock alpha generation | 3593 | 802 | No |
| 1457 | Markovian Scholarly Stock Momentum Predictor Eng-2518 | Attention networks / Transformer encoders / Stock alpha generation | 3613 | 821 | No |
| 1468 | Markovian Scholarly Stock Momentum Predictor Eng-2998 | Attention networks / Transformer encoders / Stock alpha generation | 3633 | 840 | No |
| 1479 | Markovian Scholarly Stock Momentum Predictor Eng-3478 | Attention networks / Transformer encoders / Stock alpha generation | 3653 | 859 | No |
| 1490 | Markovian Scholarly Stock Momentum Predictor Eng-3958 | Attention networks / Transformer encoders / Stock alpha generation | 3673 | 878 | No |
| 1501 | Markovian Scholarly Stock Momentum Predictor Eng-4438 | Attention networks / Transformer encoders / Stock alpha generation | 3693 | 897 | No |
| 1512 | Markovian Scholarly Stock Momentum Predictor Eng-4918 | Attention networks / Transformer encoders / Stock alpha generation | 3713 | 916 | No |
| 1523 | Markovian Scholarly Stock Momentum Predictor Eng-5398 | Attention networks / Transformer encoders / Stock alpha generation | 3733 | 935 | No |
| 1534 | Markovian Scholarly Stock Momentum Predictor Eng-5878 | Attention networks / Transformer encoders / Stock alpha generation | 3753 | 954 | No |
| 1750 | Markovian Scholarly Stock Momentum Predictor Ref-230 | Neural operators / Deep operator networks / ETF rotation | 4658 | 2160 | No |
| 1759 | Markovian Scholarly Stock Momentum Predictor Ref-326 | Quantum machine learning / Variational circuits / Index prediction | 13919 | 13511 | No |
| 1805 | Markovian Scholarly Stock Momentum Predictor Ref-710 | Neural operators / Deep operator networks / ETF rotation | 4685 | 2185 | No |
| 1814 | Markovian Scholarly Stock Momentum Predictor Ref-806 | Quantum machine learning / Variational circuits / Index prediction | 13927 | 13515 | No |
| 2514 | Markovian Scholarly Stock Momentum Predictor Eng-310 | Neural operators / Deep operator networks / ETF rotation | 3521 | 732 | No |
| 2526 | Markovian Scholarly Stock Momentum Predictor Eng-406 | Quantum machine learning / Variational circuits / Index prediction | 11693 | 1760 | No |
| 2569 | Markovian Scholarly Stock Momentum Predictor Eng-790 | Neural operators / Deep operator networks / ETF rotation | 3541 | 751 | No |
| 2581 | Markovian Scholarly Stock Momentum Predictor Eng-886 | Quantum machine learning / Variational circuits / Index prediction | 11718 | 1764 | No |
| 2624 | Markovian Scholarly Stock Momentum Predictor Eng-1270 | Neural operators / Deep operator networks / ETF rotation | 3561 | 770 | No |
| 2636 | Markovian Scholarly Stock Momentum Predictor Eng-1366 | Quantum machine learning / Variational circuits / Index prediction | 11743 | 1768 | No |
| 2679 | Markovian Scholarly Stock Momentum Predictor Eng-1750 | Neural operators / Deep operator networks / ETF rotation | 3581 | 789 | No |
| 2691 | Markovian Scholarly Stock Momentum Predictor Eng-1846 | Quantum machine learning / Variational circuits / Index prediction | 11768 | 1772 | No |
| 2734 | Markovian Scholarly Stock Momentum Predictor Eng-2230 | Neural operators / Deep operator networks / ETF rotation | 3601 | 808 | No |
| 2746 | Markovian Scholarly Stock Momentum Predictor Eng-2326 | Quantum machine learning / Variational circuits / Index prediction | 11793 | 1776 | No |
| 2789 | Markovian Scholarly Stock Momentum Predictor Eng-2710 | Neural operators / Deep operator networks / ETF rotation | 3621 | 827 | No |
| 2801 | Markovian Scholarly Stock Momentum Predictor Eng-2806 | Quantum machine learning / Variational circuits / Index prediction | 11818 | 1780 | No |
| 2844 | Markovian Scholarly Stock Momentum Predictor Eng-3190 | Neural operators / Deep operator networks / ETF rotation | 3641 | 846 | No |
| 2856 | Markovian Scholarly Stock Momentum Predictor Eng-3286 | Quantum machine learning / Variational circuits / Index prediction | 11843 | 1784 | No |
| 2899 | Markovian Scholarly Stock Momentum Predictor Eng-3670 | Neural operators / Deep operator networks / ETF rotation | 3661 | 865 | No |
| 2911 | Markovian Scholarly Stock Momentum Predictor Eng-3766 | Quantum machine learning / Variational circuits / Index prediction | 11868 | 1788 | No |
| 2954 | Markovian Scholarly Stock Momentum Predictor Eng-4150 | Neural operators / Deep operator networks / ETF rotation | 3681 | 884 | No |
| 2966 | Markovian Scholarly Stock Momentum Predictor Eng-4246 | Quantum machine learning / Variational circuits / Index prediction | 11893 | 1792 | No |
| 3009 | Markovian Scholarly Stock Momentum Predictor Eng-4630 | Neural operators / Deep operator networks / ETF rotation | 3701 | 903 | No |
| 3021 | Markovian Scholarly Stock Momentum Predictor Eng-4726 | Quantum machine learning / Variational circuits / Index prediction | 11918 | 1796 | No |
| 3064 | Markovian Scholarly Stock Momentum Predictor Eng-5110 | Neural operators / Deep operator networks / ETF rotation | 3721 | 922 | No |
| 3076 | Markovian Scholarly Stock Momentum Predictor Eng-5206 | Quantum machine learning / Variational circuits / Index prediction | 11943 | 1800 | No |
| 3119 | Markovian Scholarly Stock Momentum Predictor Eng-5590 | Neural operators / Deep operator networks / ETF rotation | 3741 | 941 | No |
| 3131 | Markovian Scholarly Stock Momentum Predictor Eng-5686 | Quantum machine learning / Variational circuits / Index prediction | 11968 | 1804 | No |
