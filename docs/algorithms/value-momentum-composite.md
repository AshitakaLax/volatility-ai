# Value-Momentum Composite

**Ledger ID RK5** · rank 5 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Equity factor / multi-factor |
| Potential effectiveness rank | 5 (1 = strongest) |
| AI implementability rank | 57 (1 = easiest) |
| Retail advantage rank | 8 (1 = strongest) |
| Fit with this project | ⏳ long-only (a stock basket, or value and momentum ETFs) · ⛔ long/short |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK6, RK48, RK65, X3, A5 |

## In one paragraph

Rank stocks on a blend of a value score (cheapness) and a momentum score
(trailing return) and hold the best combined names. The reason to blend
is the strongest result in the factor literature for combining:
value and momentum are each rewarded, in every market and asset class
Asness, Moskowitz and Pedersen studied, and they are *negatively*
correlated with each other, so the combination is far steadier than
either. For this project it is a stock-selection book; its cheap,
testable form is a two-ETF allocation (a value fund and a momentum fund).

## The rule

```
for each stock, monthly:
    value_z    = z-score of book/price (or a composite: E/P, CF/P, B/P)
    momentum_z = z-score of the return over t-12..t-2
    score      = 0.5 value_z + 0.5 momentum_z           # weights fixed in advance
long the top group (equal or cap weight); academic form also shorts the bottom group
```

The CSV's caveat is the key design rule: fix the weights before testing.

## Evidence

* **Asness, Moskowitz & Pedersen (2013):** consistent value and momentum
  premia across eight markets and asset classes; value and momentum are
  negatively correlated within and across asset classes, and more
  correlated across asset classes than passive exposures are; a
  three-factor global model captures common risk, partly funding
  liquidity. (Abstract.)
* Ken French's library and AQR publish value and momentum factor returns
  (the CSV's references) for testing the combination without stock data.

## Against, and failure modes

* **Both legs can be out of favour for years.** Value's 2017–2020
  drawdown was about −55%, the largest since 1963 in one study and the
  worst on record since the 1920s in another (Arnott et al. 2021;
  BlackRock).
* **The negative correlation is what pays**, and it is a long/short
  property; long-only value and momentum portfolios share market beta
  and are much more correlated.
* Point-in-time fundamentals are required for the value score.

## Fit with volatility-ai

A long-only stock basket fits the instrument rule but the warehouse has
no stock universe or fundamentals. A value ETF and a momentum ETF held
together (fixed 50/50, or HRP, A5) is buildable with the rotation
harness, but it is an allocation book unrelated to the TQQQ grid.

## How to test it here

Research-only first: on Ken French's monthly value (HML) and momentum
factors, confirm the negative correlation and the combination's
drawdown over 1963–present. Then, if worth it, a fixed two-ETF book via
`tools/rotation.py --mode hrp --universe <value ETF> <momentum ETF>`.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Asness, C., Moskowitz, T., Pedersen, L. H. (2013). "Value and Momentum
  Everywhere." *Journal of Finance* 68(3), 929–985.
  <https://econpapers.repec.org/RePEc:bla:jfinan:v:68:y:2013:i:3:p:929-985>.
  Abstract.
* Arnott, R., Harvey, C. R., Kalesnik, V., Linnainmaa, J. (2021).
  "Reports of Value's Death May Be Greatly Exaggerated." *Financial
  Analysts Journal* 77(1).
  <https://www.researchaffiliates.com/insights/journal-papers/reports-of-values-death-may-be-greatly-exaggerated>.
  Summary (the −55% drawdown).
* BlackRock, "The Sleeping Giant: Value's Dormant not Dead". Summary
  (worst value drawdown on record, January 2017–June 2020).
* The CSV's own references: Ken French data library; AQR research.
