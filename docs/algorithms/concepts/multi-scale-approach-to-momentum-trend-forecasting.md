# Multi-scale approach to momentum/trend forecasting

**Concept page** · shared by **2** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,188) ·
researched 2026-10-30

| | |
|---|---|
| Task | Momentum / trend forecasting |
| Method | Multi-scale (several horizons combined) |
| Fit with this project | ⏳ worth testing · a concrete test is below |
| Useful for volatility-ai | **Worth testing.** Blending lookbacks (as Goulding et al. and Keller's 13612W momentum do) is the documented fix for single-lookback lag, and cheap to test. |
| Implemented in volatility-ai | Time-series momentum weights are research code (`trend_following.tsmom_weights`, RK1); the SMA leverage switch (V16) and the intraday momentum gate (X1) are built. |
| Evidence | Evidence found (for the task; see the page for the method) |
| Related ledger entries | RK1, RK2, RK3, V16, X1 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Multi-Scale Scholarly
Equities Momentum Predictor MK-18") combine a method word, "Scholarly",
a task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Forecast direction or relative strength from past prices and turn the
forecast into exposure or rankings. The multi-scale version combines
signals or estimates measured over several horizons. Blending horizons
has direct evidence: combining slow and fast momentum by market cycle
beat either alone out of sample, and practitioner rotation rules average
1-, 3-, 6- and 12-month returns.

## The CSV's description

Proposed multi-scale approach to momentum/trend forecasting: Estimate
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
* **Goulding, Harvey & Mazzoleni (2023), "Momentum turning points,"
  *Journal of Financial Economics* 149(3), 378–406:** slow momentum
  reacts late at turning points and fast momentum gives false alarms;
  blending the two by market cycle beat either out of sample.
  (Abstract.)
* **Keller & Keuning, Protective Asset Allocation (2016, SSRN 2759734)
  and Vigilant Asset Allocation (2017, SSRN 3002624):** ETF rotation
  with crash protection; VAA's "13612W" momentum averages the 1-, 3-, 6-
  and 12-month returns, weighting the recent ones most. Practitioner
  research. (Summaries; the SSRN texts were not opened.)

## Against, and failure modes

* Momentum crashes in rebounds after sell-offs, exactly when a long-only
  grid is buying (Daniel & Moskowitz).
* A trend forecast on one leveraged ETF is a timing rule with few
  independent episodes to test on; many members are stock predictors,
  which need a universe the project does not hold.
* More horizons mean more weights to choose, and the blend can be
  overfitted.

## Fit with volatility-ai

For this book a trend forecast can act only as a long-or-cash overlay on
TQQQ (RK1, V16) or as a rotation across ETFs (X3), since shorts are out.
The project's regime work points the other way: its strongest result is
a volatility regime (V17, N5), and direction signals used as regimes
have cost more than they saved.

## How to test it here

Replace the single lookback in the RK1 overlay with the 13612W average
and compare whipsaw count, drawdown and Calmar against the single
lookback.

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
* Goulding, C. L., Harvey, C. R., Mazzoleni, M. G. (2023). "Momentum
  turning points." *Journal of Financial Economics* 149(3), 378–406.
  Abstract.
* Keller, W. J., Keuning, J. W. (2016, 2017). "Protective Asset
  Allocation" (SSRN 2759734); "Vigilant Asset Allocation" (SSRN
  3002624). Summaries.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 1188 | Multi-Scale Scholarly Equities Momentum Predictor MK-18 | Attention networks / Hawkes point processes / Stock alpha | 5373 | 1811 | No |
| 1189 | Multi-Scale Scholarly Equities Momentum Predictor MK-78 | Attention networks / Hawkes point processes / Stock alpha | 5377 | 1814 | No |
