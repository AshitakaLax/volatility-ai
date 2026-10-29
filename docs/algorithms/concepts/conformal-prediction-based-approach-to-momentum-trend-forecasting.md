# Conformal-prediction-based approach to momentum/trend forecasting

**Concept page** · shared by **62** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(25 of them in ranks 426–700; best-ranked member #442) ·
researched 2026-10-29

| | |
|---|---|
| Task | Momentum / trend forecasting |
| Method | Conformal prediction intervals around the forecast |
| Fit with this project | 🧪 conformal sizing exists · ⏳ as an uncertainty wrapper |
| Implemented in volatility-ai | Split-conformal intervals and conformal long-only sizing are research code (`position_sizing.split_conformal_interval`, `conformal_long_size`; see RK99). |
| Evidence | Evidence found (for the task; see the page for the method) |
| Related ledger entries | RK99, V13, RK1 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Conformal Scholarly Stock
Momentum Predictor Sys-82") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Wrap a trend forecast in conformal prediction intervals, which have
distribution- free coverage, and trade only when the interval excludes
zero or size by its width. For time series, adaptive conformal inference
keeps coverage under distribution shift and has been tested on
stock-market volatility. It quantifies a forecast's uncertainty; it does
not create the forecast.

## The CSV's description

Proposed conformal-prediction-based approach to momentum/trend
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
* **Gibbs & Candès (2021, NeurIPS; 2024, *JMLR* 25):** adaptive
  conformal inference retunes interval width online; the 2024 paper is
  robust to real distribution shifts in stock-volatility and COVID-19
  forecasting. (Abstracts.)

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
* Gibbs, I., Candès, E. (2024). "Conformal Inference for Online
  Prediction with Arbitrary Distribution Shifts." *JMLR* 25.
  <https://arxiv.org/abs/2208.08401>. Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 442 | Conformal Scholarly Stock Momentum Predictor Sys-82 | Robust optimization / Distributionally robust CVaR / Index tracking | 8327 | 10557 | No |
| 447 | Conformal Scholarly Stock Momentum Predictor Sys-562 | Robust optimization / Distributionally robust CVaR / Index tracking | 8367 | 10561 | No |
| 452 | Conformal Scholarly Stock Momentum Predictor Sys-1042 | Robust optimization / Distributionally robust CVaR / Index tracking | 8407 | 10565 | No |
| 457 | Conformal Scholarly Stock Momentum Predictor Sys-1522 | Robust optimization / Distributionally robust CVaR / Index tracking | 8447 | 10569 | No |
| 464 | Conformal Scholarly Stock Momentum Predictor Mod-142 | Robust optimization / Distributionally robust CVaR / Index tracking | 8499 | 10574 | No |
| 470 | Conformal Scholarly Stock Momentum Predictor Mod-622 | Robust optimization / Distributionally robust CVaR / Index tracking | 8537 | 10578 | No |
| 476 | Conformal Scholarly Stock Momentum Predictor Mod-1102 | Robust optimization / Distributionally robust CVaR / Index tracking | 8575 | 10582 | No |
| 482 | Conformal Scholarly Stock Momentum Predictor Mod-1582 | Robust optimization / Distributionally robust CVaR / Index tracking | 8613 | 10586 | No |
| 488 | Conformal Scholarly Stock Momentum Predictor Mod-2062 | Robust optimization / Distributionally robust CVaR / Index tracking | 8651 | 10590 | No |
| 494 | Conformal Scholarly Stock Momentum Predictor Mod-2542 | Robust optimization / Distributionally robust CVaR / Index tracking | 8689 | 10594 | No |
| 500 | Conformal Scholarly Stock Momentum Predictor Mod-3022 | Robust optimization / Distributionally robust CVaR / Index tracking | 8727 | 10598 | No |
| 506 | Conformal Scholarly Stock Momentum Predictor Mod-3502 | Robust optimization / Distributionally robust CVaR / Index tracking | 8765 | 10602 | No |
| 512 | Conformal Scholarly Stock Momentum Predictor Mod-3982 | Robust optimization / Distributionally robust CVaR / Index tracking | 8803 | 10606 | No |
| 612 | Conformal Scholarly Stock Momentum Predictor Sys-274 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2218 | 495 | No |
| 614 | Conformal Scholarly Stock Momentum Predictor Sys-754 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2265 | 514 | No |
| 616 | Conformal Scholarly Stock Momentum Predictor Sys-1234 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2312 | 533 | No |
| 618 | Conformal Scholarly Stock Momentum Predictor Sys-1714 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2359 | 552 | No |
| 621 | Conformal Scholarly Stock Momentum Predictor Mod-334 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2416 | 576 | No |
| 623 | Conformal Scholarly Stock Momentum Predictor Mod-814 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2455 | 595 | No |
| 625 | Conformal Scholarly Stock Momentum Predictor Mod-1294 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2494 | 614 | No |
| 627 | Conformal Scholarly Stock Momentum Predictor Mod-1774 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2533 | 633 | No |
| 629 | Conformal Scholarly Stock Momentum Predictor Mod-2254 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2572 | 652 | No |
| 631 | Conformal Scholarly Stock Momentum Predictor Mod-2734 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2611 | 671 | No |
| 633 | Conformal Scholarly Stock Momentum Predictor Mod-3214 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2650 | 690 | No |
| 635 | Conformal Scholarly Stock Momentum Predictor Mod-3694 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2689 | 709 | No |
| 1226 | Conformal Scholarly Stock Momentum Predictor Sys-178 | Attention networks / Transformer encoders / Stock alpha generation | 3251 | 492 | No |
| 1243 | Conformal Scholarly Stock Momentum Predictor Sys-658 | Attention networks / Transformer encoders / Stock alpha generation | 3275 | 511 | No |
| 1260 | Conformal Scholarly Stock Momentum Predictor Sys-1138 | Attention networks / Transformer encoders / Stock alpha generation | 3299 | 530 | No |
| 1277 | Conformal Scholarly Stock Momentum Predictor Sys-1618 | Attention networks / Transformer encoders / Stock alpha generation | 3323 | 549 | No |
| 1297 | Conformal Scholarly Stock Momentum Predictor Mod-238 | Attention networks / Transformer encoders / Stock alpha generation | 3352 | 573 | No |
| 1310 | Conformal Scholarly Stock Momentum Predictor Mod-718 | Attention networks / Transformer encoders / Stock alpha generation | 3372 | 592 | No |
| 1323 | Conformal Scholarly Stock Momentum Predictor Mod-1198 | Attention networks / Transformer encoders / Stock alpha generation | 3392 | 611 | No |
| 1336 | Conformal Scholarly Stock Momentum Predictor Mod-1678 | Attention networks / Transformer encoders / Stock alpha generation | 3412 | 630 | No |
| 1349 | Conformal Scholarly Stock Momentum Predictor Mod-2158 | Attention networks / Transformer encoders / Stock alpha generation | 3432 | 649 | No |
| 1362 | Conformal Scholarly Stock Momentum Predictor Mod-2638 | Attention networks / Transformer encoders / Stock alpha generation | 3452 | 668 | No |
| 1375 | Conformal Scholarly Stock Momentum Predictor Mod-3118 | Attention networks / Transformer encoders / Stock alpha generation | 3472 | 687 | No |
| 1388 | Conformal Scholarly Stock Momentum Predictor Mod-3598 | Attention networks / Transformer encoders / Stock alpha generation | 3492 | 706 | No |
| 1876 | Conformal Scholarly Stock Momentum Predictor Sys-370 | Neural operators / Deep operator networks / ETF rotation | 3261 | 499 | No |
| 1884 | Conformal Scholarly Stock Momentum Predictor Sys-466 | Quantum machine learning / Variational circuits / Index prediction | 11362 | 1711 | No |
| 1925 | Conformal Scholarly Stock Momentum Predictor Sys-850 | Neural operators / Deep operator networks / ETF rotation | 3285 | 518 | No |
| 1933 | Conformal Scholarly Stock Momentum Predictor Sys-946 | Quantum machine learning / Variational circuits / Index prediction | 11388 | 1715 | No |
| 1974 | Conformal Scholarly Stock Momentum Predictor Sys-1330 | Neural operators / Deep operator networks / ETF rotation | 3309 | 537 | No |
| 1982 | Conformal Scholarly Stock Momentum Predictor Sys-1426 | Quantum machine learning / Variational circuits / Index prediction | 11414 | 1719 | No |
| 2023 | Conformal Scholarly Stock Momentum Predictor Sys-1810 | Neural operators / Deep operator networks / ETF rotation | 3333 | 556 | No |
| 2031 | Conformal Scholarly Stock Momentum Predictor Sys-1906 | Quantum machine learning / Variational circuits / Index prediction | 11440 | 1723 | No |
| 2046 | Conformal Scholarly Stock Momentum Predictor Mod-46 | Quantum machine learning / Variational circuits / Index prediction | 11449 | 1724 | No |
| 2086 | Conformal Scholarly Stock Momentum Predictor Mod-430 | Neural operators / Deep operator networks / ETF rotation | 3360 | 580 | No |
| 2099 | Conformal Scholarly Stock Momentum Predictor Mod-526 | Quantum machine learning / Variational circuits / Index prediction | 11476 | 1728 | No |
| 2139 | Conformal Scholarly Stock Momentum Predictor Mod-910 | Neural operators / Deep operator networks / ETF rotation | 3380 | 599 | No |
| 2152 | Conformal Scholarly Stock Momentum Predictor Mod-1006 | Quantum machine learning / Variational circuits / Index prediction | 11503 | 1732 | No |
| 2192 | Conformal Scholarly Stock Momentum Predictor Mod-1390 | Neural operators / Deep operator networks / ETF rotation | 3400 | 618 | No |
| 2205 | Conformal Scholarly Stock Momentum Predictor Mod-1486 | Quantum machine learning / Variational circuits / Index prediction | 11530 | 1736 | No |
| 2245 | Conformal Scholarly Stock Momentum Predictor Mod-1870 | Neural operators / Deep operator networks / ETF rotation | 3420 | 637 | No |
| 2258 | Conformal Scholarly Stock Momentum Predictor Mod-1966 | Quantum machine learning / Variational circuits / Index prediction | 11557 | 1740 | No |
| 2298 | Conformal Scholarly Stock Momentum Predictor Mod-2350 | Neural operators / Deep operator networks / ETF rotation | 3440 | 656 | No |
| 2311 | Conformal Scholarly Stock Momentum Predictor Mod-2446 | Quantum machine learning / Variational circuits / Index prediction | 11584 | 1744 | No |
| 2351 | Conformal Scholarly Stock Momentum Predictor Mod-2830 | Neural operators / Deep operator networks / ETF rotation | 3460 | 675 | No |
| 2364 | Conformal Scholarly Stock Momentum Predictor Mod-2926 | Quantum machine learning / Variational circuits / Index prediction | 11611 | 1748 | No |
| 2404 | Conformal Scholarly Stock Momentum Predictor Mod-3310 | Neural operators / Deep operator networks / ETF rotation | 3480 | 694 | No |
| 2417 | Conformal Scholarly Stock Momentum Predictor Mod-3406 | Quantum machine learning / Variational circuits / Index prediction | 11638 | 1752 | No |
| 2457 | Conformal Scholarly Stock Momentum Predictor Mod-3790 | Neural operators / Deep operator networks / ETF rotation | 3500 | 713 | No |
| 2470 | Conformal Scholarly Stock Momentum Predictor Mod-3886 | Quantum machine learning / Variational circuits / Index prediction | 11665 | 1756 | No |
