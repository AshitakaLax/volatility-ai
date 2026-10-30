# Model for momentum/trend forecasting

**Concept page** · shared by **13** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #844) ·
researched 2026-10-30

| | |
|---|---|
| Task | Momentum / trend forecasting |
| Method | Unspecified model |
| Fit with this project | ⏳ worth testing · a concrete test is below |
| Useful for volatility-ai | **Worth testing.** Time-series momentum as a long-or-cash overlay on TQQQ (RK1) is the documented form; test it as a regime input against the NATR exit. |
| Implemented in volatility-ai | Time-series momentum weights are research code (`trend_following.tsmom_weights`, RK1); the SMA leverage switch (V16) and the intraday momentum gate (X1) are built. |
| Evidence | Evidence found (for the task; see the page for the method) |
| Related ledger entries | RK1, RK2, RK3, V16, X1 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Dynamic Scholarly Equities
Momentum Predictor MK-3") combine a method word, "Scholarly", a task and
a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Forecast direction or relative strength from past prices and turn the
forecast into exposure or rankings. The title names no method beyond
"model", so this page judges the task itself. Time-series momentum, a
security's own past return predicting its next, is one of the
best-documented effects in finance and has paid in most large equity
drawdowns.

## The CSV's description

Proposed model for momentum/trend forecasting: Estimate directional or
relative strength from historical prices, returns, or factor signals and
translate the forecast into rankings or portfolio exposure; the forecast
horizon and position rules are not specified. This is a concept-level
interpretation of the title, not a complete trading specification: the
exact model inputs/target, calibration, entry/exit or rebalance rules,
and position sizing are not fully defined here.

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

## Against, and failure modes

* Momentum crashes in rebounds after sell-offs, exactly when a long-only
  grid is buying (Daniel & Moskowitz).
* A trend forecast on one leveraged ETF is a timing rule with few
  independent episodes to test on; many members are stock predictors,
  which need a universe the project does not hold.

## Fit with volatility-ai

For this book a trend forecast can act only as a long-or-cash overlay on
TQQQ (RK1, V16) or as a rotation across ETFs (X3), since shorts are out.
The project's regime work points the other way: its strongest result is
a volatility regime (V17, N5), and direction signals used as regimes
have cost more than they saved.

## How to test it here

Gate the grid's buys (or trigger the regime exit) on QQQ's 12-month
return or its 200-day average, causally, and compare with N5 on the same
windows.

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

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 844 | Dynamic Scholarly Equities Momentum Predictor MK-3 | Topological data analysis / Clustering / Statistical arbitrage | 2039 | 1810 | No |
| 845 | Dynamic Scholarly Equities Momentum Predictor MK-63 | Topological data analysis / Clustering / Statistical arbitrage | 2047 | 1813 | No |
| 1190 | Transformer-Based Scholarly Equities Momentum Predictor Ver-19 | Riemannian manifold / Metric optimization / Stock portfolio | 8172 | 430 | No |
| 1194 | Transformer-Based Scholarly Equities Momentum Predictor Ver-119 | Riemannian manifold / Metric optimization / Stock portfolio | 6453 | 2771 | No |
| 1600 | Advanced Scholarly Trend-Following ETF System MK-20 | Fractional calculus / ETF trend following | 3815 | 2122 | No |
| 1602 | Cross-Sectional Scholarly Equities Momentum Predictor MK-48 | Point processes / Recurrent neural networks / Volatility | 5375 | 1812 | No |
| 1608 | Advanced Scholarly Trend-Following ETF System MK-80 | Fractional calculus / ETF trend following | 3818 | 2125 | No |
| 1620 | Advanced Scholarly Trend-Following ETF System Ver-50 | Neural operators / Continuous normalizing flows / ETF rotation | 9264 | 7564 | No |
| 1631 | Deep Scholarly Trend-Following ETF System Ver-90 | Neural operators / Continuous normalizing flows / ETF rotation | 5800 | 2130 | No |
| 1632 | Generative Scholarly Equities Momentum Predictor Ver-99 | Riemannian manifold / Metric optimization / Stock portfolio | 2064 | 434 | No |
| 1644 | Advanced Scholarly Trend-Following ETF System Ver-150 | Neural operators / Continuous normalizing flows / ETF rotation | 5802 | 2132 | No |
| 1655 | Deep Scholarly Trend-Following ETF System Ver-190 | Neural operators / Continuous normalizing flows / ETF rotation | 7626 | 2894 | No |
| 1656 | Generative Scholarly Equities Momentum Predictor Ver-199 | Riemannian manifold / Metric optimization / Stock portfolio | 3843 | 439 | No |
