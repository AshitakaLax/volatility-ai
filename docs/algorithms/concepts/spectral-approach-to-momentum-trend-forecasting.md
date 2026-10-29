# Spectral approach to momentum/trend forecasting

**Concept page** · shared by **66** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(25 of them in ranks 426–700; best-ranked member #444) ·
researched 2026-10-29

| | |
|---|---|
| Task | Momentum / trend forecasting |
| Method | Spectral (frequency-domain) decomposition |
| Fit with this project | ⛔ (no evidence over plain momentum) |
| Implemented in volatility-ai | **Research code** in `research.catalog.concepts`: `spectral_trend_positions`; tested on synthetic data, not wired into the engine. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK1, RK315 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Spectral Scholarly Stock
Momentum Predictor Sys-202") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Decompose prices into frequency components and forecast the trend from
the low-frequency part. Spectral methods are established for measuring
risk across horizons (spectral betas), but I found no study testing a
spectral trend forecast against plain time-series momentum.

## The CSV's description

Proposed spectral approach to momentum/trend forecasting: Estimate
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
* **Bandi, Chaudhuri, Lo & Tamoni (2021), "Spectral factor models,"
  *Journal of Financial Economics* 142(1), 214–238:** factor exposures
  that differ by cycle length (spectral betas); a risk-measurement
  result, not a trend forecast. (Abstract.)

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
* Bandi, F. M., Chaudhuri, S. E., Lo, A. W., Tamoni, A. (2021).
  "Spectral factor models." *Journal of Financial Economics* 142(1),
  214–238. Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 444 | Spectral Scholarly Stock Momentum Predictor Sys-202 | Robust optimization / Distributionally robust CVaR / Index tracking | 8337 | 10558 | No |
| 449 | Spectral Scholarly Stock Momentum Predictor Sys-682 | Robust optimization / Distributionally robust CVaR / Index tracking | 8377 | 10562 | No |
| 454 | Spectral Scholarly Stock Momentum Predictor Sys-1162 | Robust optimization / Distributionally robust CVaR / Index tracking | 8417 | 10566 | No |
| 459 | Spectral Scholarly Stock Momentum Predictor Sys-1642 | Robust optimization / Distributionally robust CVaR / Index tracking | 8457 | 10570 | No |
| 462 | Spectral Scholarly Stock Momentum Predictor Mod-22 | Robust optimization / Distributionally robust CVaR / Index tracking | 8490 | 10573 | No |
| 468 | Spectral Scholarly Stock Momentum Predictor Mod-502 | Robust optimization / Distributionally robust CVaR / Index tracking | 8528 | 10577 | No |
| 474 | Spectral Scholarly Stock Momentum Predictor Mod-982 | Robust optimization / Distributionally robust CVaR / Index tracking | 8566 | 10581 | No |
| 480 | Spectral Scholarly Stock Momentum Predictor Mod-1462 | Robust optimization / Distributionally robust CVaR / Index tracking | 8604 | 10585 | No |
| 486 | Spectral Scholarly Stock Momentum Predictor Mod-1942 | Robust optimization / Distributionally robust CVaR / Index tracking | 8642 | 10589 | No |
| 492 | Spectral Scholarly Stock Momentum Predictor Mod-2422 | Robust optimization / Distributionally robust CVaR / Index tracking | 8680 | 10593 | No |
| 498 | Spectral Scholarly Stock Momentum Predictor Mod-2902 | Robust optimization / Distributionally robust CVaR / Index tracking | 8718 | 10597 | No |
| 504 | Spectral Scholarly Stock Momentum Predictor Mod-3382 | Robust optimization / Distributionally robust CVaR / Index tracking | 8756 | 10601 | No |
| 510 | Spectral Scholarly Stock Momentum Predictor Mod-3862 | Robust optimization / Distributionally robust CVaR / Index tracking | 8794 | 10605 | No |
| 613 | Spectral Scholarly Stock Momentum Predictor Sys-394 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2230 | 500 | No |
| 615 | Spectral Scholarly Stock Momentum Predictor Sys-874 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2277 | 519 | No |
| 617 | Spectral Scholarly Stock Momentum Predictor Sys-1354 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2324 | 538 | No |
| 619 | Spectral Scholarly Stock Momentum Predictor Sys-1834 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2371 | 557 | No |
| 620 | Spectral Scholarly Stock Momentum Predictor Mod-214 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2405 | 571 | No |
| 622 | Spectral Scholarly Stock Momentum Predictor Mod-694 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2444 | 590 | No |
| 624 | Spectral Scholarly Stock Momentum Predictor Mod-1174 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2483 | 609 | No |
| 626 | Spectral Scholarly Stock Momentum Predictor Mod-1654 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2522 | 628 | No |
| 628 | Spectral Scholarly Stock Momentum Predictor Mod-2134 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2561 | 647 | No |
| 630 | Spectral Scholarly Stock Momentum Predictor Mod-2614 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2600 | 666 | No |
| 632 | Spectral Scholarly Stock Momentum Predictor Mod-3094 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2639 | 685 | No |
| 634 | Spectral Scholarly Stock Momentum Predictor Mod-3574 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 2678 | 704 | No |
| 1230 | Spectral Scholarly Stock Momentum Predictor Sys-298 | Attention networks / Transformer encoders / Stock alpha generation | 3257 | 497 | No |
| 1247 | Spectral Scholarly Stock Momentum Predictor Sys-778 | Attention networks / Transformer encoders / Stock alpha generation | 3281 | 516 | No |
| 1264 | Spectral Scholarly Stock Momentum Predictor Sys-1258 | Attention networks / Transformer encoders / Stock alpha generation | 3305 | 535 | No |
| 1281 | Spectral Scholarly Stock Momentum Predictor Sys-1738 | Attention networks / Transformer encoders / Stock alpha generation | 3329 | 554 | No |
| 1293 | Spectral Scholarly Stock Momentum Predictor Mod-118 | Attention networks / Transformer encoders / Stock alpha generation | 3347 | 569 | No |
| 1306 | Spectral Scholarly Stock Momentum Predictor Mod-598 | Attention networks / Transformer encoders / Stock alpha generation | 3367 | 588 | No |
| 1319 | Spectral Scholarly Stock Momentum Predictor Mod-1078 | Attention networks / Transformer encoders / Stock alpha generation | 3387 | 607 | No |
| 1332 | Spectral Scholarly Stock Momentum Predictor Mod-1558 | Attention networks / Transformer encoders / Stock alpha generation | 3407 | 626 | No |
| 1345 | Spectral Scholarly Stock Momentum Predictor Mod-2038 | Attention networks / Transformer encoders / Stock alpha generation | 3427 | 645 | No |
| 1358 | Spectral Scholarly Stock Momentum Predictor Mod-2518 | Attention networks / Transformer encoders / Stock alpha generation | 3447 | 664 | No |
| 1371 | Spectral Scholarly Stock Momentum Predictor Mod-2998 | Attention networks / Transformer encoders / Stock alpha generation | 3467 | 683 | No |
| 1384 | Spectral Scholarly Stock Momentum Predictor Mod-3478 | Attention networks / Transformer encoders / Stock alpha generation | 3487 | 702 | No |
| 1397 | Spectral Scholarly Stock Momentum Predictor Mod-3958 | Attention networks / Transformer encoders / Stock alpha generation | 3507 | 721 | No |
| 1603 | Spectral Scholarly Trend-Following ETF System MK-50 | Neural operators / Continuous normalizing flows / ETF rotation | 9259 | 7561 | No |
| 1626 | Spectral Scholarly Trend-Following ETF System Ver-70 | Neural operators / Continuous normalizing flows / ETF rotation | 7622 | 2865 | No |
| 1650 | Spectral Scholarly Trend-Following ETF System Ver-170 | Neural operators / Continuous normalizing flows / ETF rotation | 9268 | 7570 | No |
| 1838 | Spectral Scholarly Stock Momentum Predictor Sys-10 | Neural operators / Deep operator networks / ETF rotation | 3243 | 485 | No |
| 1847 | Spectral Scholarly Stock Momentum Predictor Sys-106 | Quantum machine learning / Variational circuits / Index prediction | 11343 | 1708 | No |
| 1887 | Spectral Scholarly Stock Momentum Predictor Sys-490 | Neural operators / Deep operator networks / ETF rotation | 3267 | 504 | No |
| 1896 | Spectral Scholarly Stock Momentum Predictor Sys-586 | Quantum machine learning / Variational circuits / Index prediction | 11369 | 1712 | No |
| 1936 | Spectral Scholarly Stock Momentum Predictor Sys-970 | Neural operators / Deep operator networks / ETF rotation | 3291 | 523 | No |
| 1945 | Spectral Scholarly Stock Momentum Predictor Sys-1066 | Quantum machine learning / Variational circuits / Index prediction | 11395 | 1716 | No |
| 1985 | Spectral Scholarly Stock Momentum Predictor Sys-1450 | Neural operators / Deep operator networks / ETF rotation | 3315 | 542 | No |
| 1994 | Spectral Scholarly Stock Momentum Predictor Sys-1546 | Quantum machine learning / Variational circuits / Index prediction | 11421 | 1720 | No |
| 2034 | Spectral Scholarly Stock Momentum Predictor Sys-1930 | Neural operators / Deep operator networks / ETF rotation | 3339 | 561 | No |
| 2072 | Spectral Scholarly Stock Momentum Predictor Mod-310 | Neural operators / Deep operator networks / ETF rotation | 3355 | 575 | No |
| 2085 | Spectral Scholarly Stock Momentum Predictor Mod-406 | Quantum machine learning / Variational circuits / Index prediction | 11469 | 1727 | No |
| 2125 | Spectral Scholarly Stock Momentum Predictor Mod-790 | Neural operators / Deep operator networks / ETF rotation | 3375 | 594 | No |
| 2138 | Spectral Scholarly Stock Momentum Predictor Mod-886 | Quantum machine learning / Variational circuits / Index prediction | 11496 | 1731 | No |
| 2178 | Spectral Scholarly Stock Momentum Predictor Mod-1270 | Neural operators / Deep operator networks / ETF rotation | 3395 | 613 | No |
| 2191 | Spectral Scholarly Stock Momentum Predictor Mod-1366 | Quantum machine learning / Variational circuits / Index prediction | 11523 | 1735 | No |
| 2231 | Spectral Scholarly Stock Momentum Predictor Mod-1750 | Neural operators / Deep operator networks / ETF rotation | 3415 | 632 | No |
| 2244 | Spectral Scholarly Stock Momentum Predictor Mod-1846 | Quantum machine learning / Variational circuits / Index prediction | 11550 | 1739 | No |
| 2284 | Spectral Scholarly Stock Momentum Predictor Mod-2230 | Neural operators / Deep operator networks / ETF rotation | 3435 | 651 | No |
| 2297 | Spectral Scholarly Stock Momentum Predictor Mod-2326 | Quantum machine learning / Variational circuits / Index prediction | 11577 | 1743 | No |
| 2337 | Spectral Scholarly Stock Momentum Predictor Mod-2710 | Neural operators / Deep operator networks / ETF rotation | 3455 | 670 | No |
| 2350 | Spectral Scholarly Stock Momentum Predictor Mod-2806 | Quantum machine learning / Variational circuits / Index prediction | 11604 | 1747 | No |
| 2390 | Spectral Scholarly Stock Momentum Predictor Mod-3190 | Neural operators / Deep operator networks / ETF rotation | 3475 | 689 | No |
| 2403 | Spectral Scholarly Stock Momentum Predictor Mod-3286 | Quantum machine learning / Variational circuits / Index prediction | 11631 | 1751 | No |
| 2443 | Spectral Scholarly Stock Momentum Predictor Mod-3670 | Neural operators / Deep operator networks / ETF rotation | 3495 | 708 | No |
| 2456 | Spectral Scholarly Stock Momentum Predictor Mod-3766 | Quantum machine learning / Variational circuits / Index prediction | 11658 | 1755 | No |
