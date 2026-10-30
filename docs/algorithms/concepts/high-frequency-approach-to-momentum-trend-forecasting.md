# High-frequency approach to momentum/trend forecasting

**Concept page** · shared by **4** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,598) ·
researched 2026-10-30

| | |
|---|---|
| Task | Momentum / trend forecasting |
| Method | High-frequency (intraday) data |
| Fit with this project | 🧪 worth testing · a concrete test is below |
| Useful for volatility-ai | **Worth testing.** The first half-hour return predicts the last half-hour on SPY (Gao et al. 2018); built here as an intraday gate (X1), not yet measured. |
| Implemented in volatility-ai | Time-series momentum weights are research code (`trend_following.tsmom_weights`, RK1); the SMA leverage switch (V16) and the intraday momentum gate (X1) are built. |
| Evidence | Evidence found (for the task; see the page for the method) |
| Related ledger entries | RK1, RK2, RK3, V16, X1 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "High-Frequency Scholarly
Trend-Following ETF System MK-5") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Forecast direction or relative strength from past prices and turn the
forecast into exposure or rankings. The high-frequency version estimates
its inputs from intraday data instead of daily closes. The
high-frequency effect with published out-of-sample evidence is market
intraday momentum: the first half-hour's return predicts the last
half-hour's.

## The CSV's description

Proposed high-frequency approach to momentum/trend forecasting: Estimate
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
  a 60/40 portfolio since 1880. (Abstract.)
* **Daniel & Moskowitz (2016), "Momentum crashes," *Journal of Financial
  Economics* 122(2), 221–247:** momentum crashes in rebounds after
  market declines and in high volatility. (Abstract.)
* **Gao, Han, Li & Zhou (2018), "Market intraday momentum," *Journal of
  Financial Economics* 129(2), 394–414:** on SPY, 1993–2013, the first
  half-hour return predicts the last half-hour return, with an
  out-of-sample R² of about 1.2%. (Abstract and summaries.)

## Against, and failure modes

* Momentum crashes in rebounds after sell-offs, exactly when a long-only
  grid is buying (Daniel & Moskowitz).
* A trend forecast on one leveraged ETF is a timing rule with few
  independent episodes to test on; many members are stock predictors,
  which need a universe the project does not hold.
* Intraday estimates bring microstructure noise and need minute data the
  warehouse holds only for some symbols.

## Fit with volatility-ai

For this book a trend forecast can act only as a long-or-cash overlay on
TQQQ (RK1, V16) or as a rotation across ETFs (X3), since shorts are out.
The project's regime work points the other way: its strongest result is
a volatility regime (V17, N5), and direction signals used as regimes
have cost more than they saved.

## How to test it here

Measure X1 on minute bars: allow the grid's late-day buys only after a
non-negative first half-hour and compare fills and harvests with the
ungated grid.

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
* Gao, L., Han, Y., Li, S. Z., Zhou, G. (2018). "Market intraday
  momentum." *Journal of Financial Economics* 129(2), 394–414. Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 1598 | High-Frequency Scholarly Trend-Following ETF System MK-5 | Rough path theory / Signature methods / Equity factors | 12243 | 11845 | No |
| 1606 | High-Frequency Scholarly Trend-Following ETF System MK-65 | Rough path theory / Signature methods / Equity factors | 12245 | 11846 | No |
| 3672 | High-Frequency Scholarly Trend-Following ETF System Ver-30 | Neural operators / Continuous normalizing flows / ETF rotation | 11257 | 10664 | No |
| 3681 | High-Frequency Scholarly Trend-Following ETF System Ver-130 | Neural operators / Continuous normalizing flows / ETF rotation | 12017 | 10707 | No |
