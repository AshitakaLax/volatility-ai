# Nonlinear approach to momentum/trend forecasting

**Concept page** · shared by **4** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(2 of them in ranks 426–700; best-ranked member #674) ·
researched 2026-10-29

| | |
|---|---|
| Task | Momentum / trend forecasting |
| Method | Nonlinear filtering / nonlinear models |
| Fit with this project | ⏳ via the trend-filter literature · ⛔ for ML variants |
| Implemented in volatility-ai | Time-series momentum weights exist as research code (`trend_following.tsmom_weights`, RK1); relative-strength rotation is built (X3). |
| Evidence | Evidence found (for the task; see the page for the method) |
| Related ledger entries | RK1, RK2, RK7, X3, RK292 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Non-Linear Scholarly
Trend-Following ETF System MK-35") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Forecast trends with nonlinear models or filters rather than moving
averages. The trend-filter review covers nonlinear estimators alongside
linear ones; the gains over linear filters in it are modest, and
machine-learning versions have not beaten simple momentum reliably (see
RK292).

## The CSV's description

Proposed nonlinear approach to momentum/trend forecasting: Estimate
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
* **Bruder, Dao, Richard & Roncalli (2011), "Trend Filtering Methods for
  Momentum Strategies" (Lyxor white paper; SSRN 2289097):** reviews
  linear and nonlinear trend estimators (moving averages, Kalman and L1
  filters), univariate and multivariate, calibrated by prediction error,
  applied to the S&P 500; Dao's L1 filter (arXiv 1403.4069) extracts
  piecewise-linear trends. Practitioner research. (Abstracts.)
* **Fischer & Krauss (2018):** an LSTM's stock picks were largely
  short-term reversal (see RK292).

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
| 674 | Non-Linear Scholarly Trend-Following ETF System MK-35 | Neural SDEs / Robust statistics / Stock options hedging | 10374 | 8381 | No |
| 676 | Non-Linear Scholarly Trend-Following ETF System MK-95 | Neural SDEs / Robust statistics / Stock options hedging | 10375 | 8384 | No |
| 1612 | Non-Linear Scholarly Trend-Following ETF System Ver-10 | Neural operators / Continuous normalizing flows / ETF rotation | 7620 | 2854 | No |
| 1636 | Non-Linear Scholarly Trend-Following ETF System Ver-110 | Neural operators / Continuous normalizing flows / ETF rotation | 9266 | 7567 | No |
