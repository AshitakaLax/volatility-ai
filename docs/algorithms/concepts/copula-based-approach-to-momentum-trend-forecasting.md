# Copula-based approach to momentum/trend forecasting

**Concept page** · shared by **7** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(5 of them in ranks 426–700; best-ranked member #592) ·
researched 2026-10-29

| | |
|---|---|
| Task | Momentum / trend forecasting |
| Method | Copula models of dependence |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | Nothing. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK1, RK94, RK296 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Copula Scholarly Stock
Momentum Predictor Alpha-94") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Model the dependence between assets' returns, or between momentum and
the market, with copulas, to anticipate joint crashes. Momentum's crash
risk is well documented and partly forecastable from market state and
volatility (Daniel and Moskowitz); I found no copula-based momentum
forecaster.

## The CSV's description

Proposed copula-based approach to momentum/trend forecasting: Estimate
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
| 592 | Copula Scholarly Stock Momentum Predictor Alpha-94 | Vine copulas / Regularized trees / Multi-factor stock allocation | 2087 | 443 | No |
| 595 | Copula Scholarly Stock Momentum Predictor Alpha-194 | Vine copulas / Regularized trees / Multi-factor stock allocation | 1019 | 2781 | No |
| 598 | Copula Scholarly Stock Momentum Predictor Alpha-294 | Vine copulas / Regularized trees / Multi-factor stock allocation | 1029 | 453 | No |
| 601 | Copula Scholarly Stock Momentum Predictor Alpha-394 | Vine copulas / Regularized trees / Multi-factor stock allocation | 2117 | 457 | No |
| 604 | Copula Scholarly Stock Momentum Predictor Alpha-494 | Vine copulas / Regularized trees / Multi-factor stock allocation | 1048 | 2791 | No |
| 1192 | Copula-Based Scholarly Equities Momentum Predictor Ver-59 | Riemannian manifold / Metric optimization / Stock portfolio | 4589 | 2768 | No |
| 1196 | Copula-Based Scholarly Equities Momentum Predictor Ver-159 | Riemannian manifold / Metric optimization / Stock portfolio | 4596 | 437 | No |
