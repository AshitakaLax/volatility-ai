# Neural-network-based approach to momentum/trend forecasting

**Concept page** · shared by **5** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #851) ·
researched 2026-10-30

| | |
|---|---|
| Task | Momentum / trend forecasting |
| Method | Neural networks |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Neural trend forecasts have not reliably beaten simple momentum; the best-known LSTM study picked short-term reversal and faded after 2010. |
| Implemented in volatility-ai | Time-series momentum weights are research code (`trend_following.tsmom_weights`, RK1); the SMA leverage switch (V16) and the intraday momentum gate (X1) are built. |
| Evidence | Evidence found (for the task; see the page for the method) |
| Related ledger entries | RK1, RK2, RK3, V16, X1 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Neural Scholarly Stock
Momentum Predictor Alpha-54") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Forecast direction or relative strength from past prices and turn the
forecast into exposure or rankings. The neural-network version fits a
neural network to the task.

## The CSV's description

Proposed neural-network-based approach to momentum/trend forecasting:
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
  a 60/40 portfolio since 1880. (Abstract.)
* **Daniel & Moskowitz (2016), "Momentum crashes," *Journal of Financial
  Economics* 122(2), 221–247:** momentum crashes in rebounds after
  market declines and in high volatility. (Abstract.)
* **Fischer & Krauss (2018), *European Journal of Operational Research*
  270(2), 654–669:** an LSTM's S&P 500 stock picks were largely
  short-term reversal, and its edge faded after 2010 (see RK292).
  (Abstract.)

## Against, and failure modes

* Momentum crashes in rebounds after sell-offs, exactly when a long-only
  grid is buying (Daniel & Moskowitz).
* A trend forecast on one leveraged ETF is a timing rule with few
  independent episodes to test on; many members are stock predictors,
  which need a universe the project does not hold.
* Neural forecasts on one index have not reliably beaten simple rules;
  an LSTM's stock picks were largely short-term reversal (Fischer &
  Krauss 2018, RK292).

## Fit with volatility-ai

For this book a trend forecast can act only as a long-or-cash overlay on
TQQQ (RK1, V16) or as a rotation across ETFs (X3), since shorts are out.
The project's regime work points the other way: its strongest result is
a volatility regime (V17, N5), and direction signals used as regimes
have cost more than they saved.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Moskowitz, T. J., Ooi, Y. H., Pedersen, L. H. (2012). "Time series
  momentum." *Journal of Financial Economics* 104(2). Standard
  reference.
* Hurst, B., Ooi, Y. H., Pedersen, L. H. (2017). "A Century of Evidence
  on Trend-Following Investing." *Journal of Portfolio Management*.
  Abstract.
* Daniel, K., Moskowitz, T. J. (2016). "Momentum crashes." *Journal of
  Financial Economics* 122(2), 221–247. Abstract.
* Fischer, T., Krauss, C. (2018). *European Journal of Operational
  Research* 270(2), 654–669. Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 851 | Neural Scholarly Stock Momentum Predictor Alpha-54 | Vine copulas / Regularized trees / Multi-factor stock allocation | 1005 | 441 | No |
| 858 | Neural Scholarly Stock Momentum Predictor Alpha-154 | Vine copulas / Regularized trees / Multi-factor stock allocation | 2092 | 446 | No |
| 865 | Neural Scholarly Stock Momentum Predictor Alpha-254 | Vine copulas / Regularized trees / Multi-factor stock allocation | 1025 | 2784 | No |
| 872 | Neural Scholarly Stock Momentum Predictor Alpha-354 | Vine copulas / Regularized trees / Multi-factor stock allocation | 1034 | 455 | No |
| 879 | Neural Scholarly Stock Momentum Predictor Alpha-454 | Vine copulas / Regularized trees / Multi-factor stock allocation | 2122 | 460 | No |
