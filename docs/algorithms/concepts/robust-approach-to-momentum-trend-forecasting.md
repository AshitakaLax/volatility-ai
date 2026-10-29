# Robust approach to momentum/trend forecasting

**Concept page** · shared by **7** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(5 of them in ranks 426–700; best-ranked member #591) ·
researched 2026-10-29

| | |
|---|---|
| Task | Momentum / trend forecasting |
| Method | Robust (outlier-resistant) estimation |
| Fit with this project | ⏳ in principle · no method-specific evidence |
| Implemented in volatility-ai | **Research code** in `research.catalog.concepts`: `robust_momentum`; tested on synthetic data, not wired into the engine. Related code already here: Time-series momentum weights exist as research code (`trend_following.tsmom_weights`, RK1); relative-strength rotation is built (X3). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK1, RK2, RK7, X3 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Robust Scholarly Stock
Momentum Predictor Alpha-34") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Estimate momentum with robust statistics (medians, Huber losses,
rank-based returns) so single outliers do not flip the signal. Sensible,
but I found no study comparing robust and plain momentum estimators out
of sample.

## The CSV's description

Proposed robust approach to momentum/trend forecasting: Estimate
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
| 591 | Robust Scholarly Stock Momentum Predictor Alpha-34 | Vine copulas / Regularized trees / Multi-factor stock allocation | 2081 | 440 | No |
| 594 | Robust Scholarly Stock Momentum Predictor Alpha-134 | Vine copulas / Regularized trees / Multi-factor stock allocation | 1014 | 2779 | No |
| 597 | Robust Scholarly Stock Momentum Predictor Alpha-234 | Vine copulas / Regularized trees / Multi-factor stock allocation | 1023 | 450 | No |
| 600 | Robust Scholarly Stock Momentum Predictor Alpha-334 | Vine copulas / Regularized trees / Multi-factor stock allocation | 2111 | 454 | No |
| 603 | Robust Scholarly Stock Momentum Predictor Alpha-434 | Vine copulas / Regularized trees / Multi-factor stock allocation | 1043 | 2789 | No |
| 1193 | Robust Scholarly Equities Momentum Predictor Ver-79 | Riemannian manifold / Metric optimization / Stock portfolio | 3829 | 433 | No |
| 1197 | Robust Scholarly Equities Momentum Predictor Ver-179 | Riemannian manifold / Metric optimization / Stock portfolio | 2075 | 2774 | No |
