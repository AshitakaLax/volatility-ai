# Diffusion-model-based approach to momentum/trend forecasting

**Concept page** · shared by **62** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(2 of them in ranks 426–700; best-ranked member #693) ·
researched 2026-10-29

| | |
|---|---|
| Task | Momentum / trend forecasting |
| Method | Generative diffusion models |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **Research code** in `research.catalog.concepts`: `diffusion_trend`; tested on synthetic data, not wired into the engine. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK200, RK395 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Diffusion Scholarly Stock
Momentum Predictor Sys-322") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Forecast trends by sampling future paths from a score-based diffusion
model. Diffusion models generate realistic synthetic series (RK200); I
found no study using them to forecast trends for trading.

## The CSV's description

Proposed diffusion-model-based approach to momentum/trend forecasting:
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
* **Takahashi & Mizuno (2024, arXiv 2410.18897):** diffusion-generated
  series reproduce stylized facts (see RK200).

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
| 693 | Diffusion Scholarly Stock Momentum Predictor Sys-322 | Robust optimization / Distributionally robust CVaR / Index tracking | 8348 | 10559 | No |
| 700 | Diffusion Scholarly Stock Momentum Predictor Sys-802 | Robust optimization / Distributionally robust CVaR / Index tracking | 8388 | 10563 | No |
| 707 | Diffusion Scholarly Stock Momentum Predictor Sys-1282 | Robust optimization / Distributionally robust CVaR / Index tracking | 8428 | 10567 | No |
| 714 | Diffusion Scholarly Stock Momentum Predictor Sys-1762 | Robust optimization / Distributionally robust CVaR / Index tracking | 8468 | 10571 | No |
| 723 | Diffusion Scholarly Stock Momentum Predictor Mod-382 | Robust optimization / Distributionally robust CVaR / Index tracking | 8518 | 10576 | No |
| 729 | Diffusion Scholarly Stock Momentum Predictor Mod-862 | Robust optimization / Distributionally robust CVaR / Index tracking | 8556 | 10580 | No |
| 735 | Diffusion Scholarly Stock Momentum Predictor Mod-1342 | Robust optimization / Distributionally robust CVaR / Index tracking | 8594 | 10584 | No |
| 741 | Diffusion Scholarly Stock Momentum Predictor Mod-1822 | Robust optimization / Distributionally robust CVaR / Index tracking | 8632 | 10588 | No |
| 747 | Diffusion Scholarly Stock Momentum Predictor Mod-2302 | Robust optimization / Distributionally robust CVaR / Index tracking | 8670 | 10592 | No |
| 753 | Diffusion Scholarly Stock Momentum Predictor Mod-2782 | Robust optimization / Distributionally robust CVaR / Index tracking | 8708 | 10596 | No |
| 759 | Diffusion Scholarly Stock Momentum Predictor Mod-3262 | Robust optimization / Distributionally robust CVaR / Index tracking | 8746 | 10600 | No |
| 765 | Diffusion Scholarly Stock Momentum Predictor Mod-3742 | Robust optimization / Distributionally robust CVaR / Index tracking | 8784 | 10604 | No |
| 904 | Diffusion Scholarly Stock Momentum Predictor Sys-34 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2195 | 486 | No |
| 916 | Diffusion Scholarly Stock Momentum Predictor Sys-514 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2242 | 505 | No |
| 928 | Diffusion Scholarly Stock Momentum Predictor Sys-994 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2289 | 524 | No |
| 940 | Diffusion Scholarly Stock Momentum Predictor Sys-1474 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2336 | 543 | No |
| 952 | Diffusion Scholarly Stock Momentum Predictor Sys-1954 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2383 | 562 | No |
| 957 | Diffusion Scholarly Stock Momentum Predictor Mod-94 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2396 | 567 | No |
| 970 | Diffusion Scholarly Stock Momentum Predictor Mod-574 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2435 | 586 | No |
| 983 | Diffusion Scholarly Stock Momentum Predictor Mod-1054 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2474 | 605 | No |
| 996 | Diffusion Scholarly Stock Momentum Predictor Mod-1534 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2513 | 624 | No |
| 1009 | Diffusion Scholarly Stock Momentum Predictor Mod-2014 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2552 | 643 | No |
| 1022 | Diffusion Scholarly Stock Momentum Predictor Mod-2494 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2591 | 662 | No |
| 1035 | Diffusion Scholarly Stock Momentum Predictor Mod-2974 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2630 | 681 | No |
| 1048 | Diffusion Scholarly Stock Momentum Predictor Mod-3454 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2669 | 700 | No |
| 1061 | Diffusion Scholarly Stock Momentum Predictor Mod-3934 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2708 | 719 | No |
| 1851 | Diffusion Scholarly Stock Momentum Predictor Sys-130 | Neural operators / Deep operator networks / ETF rotation | 3249 | 490 | No |
| 1859 | Diffusion Scholarly Stock Momentum Predictor Sys-226 | Quantum machine learning / Variational circuits / Index prediction | 11349 | 1709 | No |
| 1882 | Diffusion Scholarly Stock Momentum Predictor Sys-418 | Attention networks / Transformer encoders / Stock alpha generation | 3263 | 502 | No |
| 1900 | Diffusion Scholarly Stock Momentum Predictor Sys-610 | Neural operators / Deep operator networks / ETF rotation | 3273 | 509 | No |
| 1908 | Diffusion Scholarly Stock Momentum Predictor Sys-706 | Quantum machine learning / Variational circuits / Index prediction | 11375 | 1713 | No |
| 1931 | Diffusion Scholarly Stock Momentum Predictor Sys-898 | Attention networks / Transformer encoders / Stock alpha generation | 3287 | 521 | No |
| 1949 | Diffusion Scholarly Stock Momentum Predictor Sys-1090 | Neural operators / Deep operator networks / ETF rotation | 3297 | 528 | No |
| 1957 | Diffusion Scholarly Stock Momentum Predictor Sys-1186 | Quantum machine learning / Variational circuits / Index prediction | 11401 | 1717 | No |
| 1980 | Diffusion Scholarly Stock Momentum Predictor Sys-1378 | Attention networks / Transformer encoders / Stock alpha generation | 3311 | 540 | No |
| 1998 | Diffusion Scholarly Stock Momentum Predictor Sys-1570 | Neural operators / Deep operator networks / ETF rotation | 3321 | 547 | No |
| 2006 | Diffusion Scholarly Stock Momentum Predictor Sys-1666 | Quantum machine learning / Variational circuits / Index prediction | 11427 | 1721 | No |
| 2029 | Diffusion Scholarly Stock Momentum Predictor Sys-1858 | Attention networks / Transformer encoders / Stock alpha generation | 3335 | 559 | No |
| 2059 | Diffusion Scholarly Stock Momentum Predictor Mod-190 | Neural operators / Deep operator networks / ETF rotation | 3350 | 570 | No |
| 2070 | Diffusion Scholarly Stock Momentum Predictor Mod-286 | Quantum machine learning / Variational circuits / Index prediction | 11463 | 1726 | No |
| 2093 | Diffusion Scholarly Stock Momentum Predictor Mod-478 | Attention networks / Transformer encoders / Stock alpha generation | 3362 | 583 | No |
| 2112 | Diffusion Scholarly Stock Momentum Predictor Mod-670 | Neural operators / Deep operator networks / ETF rotation | 3370 | 589 | No |
| 2123 | Diffusion Scholarly Stock Momentum Predictor Mod-766 | Quantum machine learning / Variational circuits / Index prediction | 11490 | 1730 | No |
| 2146 | Diffusion Scholarly Stock Momentum Predictor Mod-958 | Attention networks / Transformer encoders / Stock alpha generation | 3382 | 602 | No |
| 2165 | Diffusion Scholarly Stock Momentum Predictor Mod-1150 | Neural operators / Deep operator networks / ETF rotation | 3390 | 608 | No |
| 2176 | Diffusion Scholarly Stock Momentum Predictor Mod-1246 | Quantum machine learning / Variational circuits / Index prediction | 11517 | 1734 | No |
| 2199 | Diffusion Scholarly Stock Momentum Predictor Mod-1438 | Attention networks / Transformer encoders / Stock alpha generation | 3402 | 621 | No |
| 2218 | Diffusion Scholarly Stock Momentum Predictor Mod-1630 | Neural operators / Deep operator networks / ETF rotation | 3410 | 627 | No |
| 2229 | Diffusion Scholarly Stock Momentum Predictor Mod-1726 | Quantum machine learning / Variational circuits / Index prediction | 11544 | 1738 | No |
| 2252 | Diffusion Scholarly Stock Momentum Predictor Mod-1918 | Attention networks / Transformer encoders / Stock alpha generation | 3422 | 640 | No |
| 2271 | Diffusion Scholarly Stock Momentum Predictor Mod-2110 | Neural operators / Deep operator networks / ETF rotation | 3430 | 646 | No |
| 2282 | Diffusion Scholarly Stock Momentum Predictor Mod-2206 | Quantum machine learning / Variational circuits / Index prediction | 11571 | 1742 | No |
| 2305 | Diffusion Scholarly Stock Momentum Predictor Mod-2398 | Attention networks / Transformer encoders / Stock alpha generation | 3442 | 659 | No |
| 2324 | Diffusion Scholarly Stock Momentum Predictor Mod-2590 | Neural operators / Deep operator networks / ETF rotation | 3450 | 665 | No |
| 2335 | Diffusion Scholarly Stock Momentum Predictor Mod-2686 | Quantum machine learning / Variational circuits / Index prediction | 11598 | 1746 | No |
| 2358 | Diffusion Scholarly Stock Momentum Predictor Mod-2878 | Attention networks / Transformer encoders / Stock alpha generation | 3462 | 678 | No |
| 2377 | Diffusion Scholarly Stock Momentum Predictor Mod-3070 | Neural operators / Deep operator networks / ETF rotation | 3470 | 684 | No |
| 2388 | Diffusion Scholarly Stock Momentum Predictor Mod-3166 | Quantum machine learning / Variational circuits / Index prediction | 11625 | 1750 | No |
| 2411 | Diffusion Scholarly Stock Momentum Predictor Mod-3358 | Attention networks / Transformer encoders / Stock alpha generation | 3482 | 697 | No |
| 2430 | Diffusion Scholarly Stock Momentum Predictor Mod-3550 | Neural operators / Deep operator networks / ETF rotation | 3490 | 703 | No |
| 2441 | Diffusion Scholarly Stock Momentum Predictor Mod-3646 | Quantum machine learning / Variational circuits / Index prediction | 11652 | 1754 | No |
| 2464 | Diffusion Scholarly Stock Momentum Predictor Mod-3838 | Attention networks / Transformer encoders / Stock alpha generation | 3502 | 716 | No |
