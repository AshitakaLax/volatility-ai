# Cointegrated Triplet Basket Statistical Arbitrage

**Ledger ID RK93** · rank 93 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Statistical arbitrage / quantitative equity |
| Potential effectiveness rank | 93 (1 = strongest) |
| AI implementability rank | 158 (1 = easiest) |
| Retail advantage rank | 251 (1 = strongest) |
| Fit with this project | ⛔ (short legs) |
| Implemented in volatility-ai | **Research code** in `research.catalog.stat_arb`: `cointegrated_triplets`, `johansen_basket`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK36, RK37 |

## In one paragraph

RK36 with exactly three assets: find a stationary combination
A − αB − βC among three related stocks (the CSV's example is Chevron,
ExxonMobil and ConocoPhillips) with the Johansen test, and trade the
residual's mean reversion. A third asset can produce a stationary
spread where no pair is cointegrated. I found no study of equity
triplets as such: the nearest evidence is a three-contract crude-oil
basket and multi-asset cointegration in the Euro Stoxx 50.

## The rule

```
Johansen on log(A, B, C) over a formation window -> vector (1, -alpha, -beta)
spread = log A - alpha log B - beta log C; z-score it; trade the basket at |z| > 2, exit near 0
re-estimate on a rolling window; drop the triplet when the rank test fails
```

## Evidence

* **Three crude-oil futures (arXiv 2309.00875):** cointegrated as a
  triple when pairwise tests failed; profitable under conservative
  costs. (Summary.)
* **Euro Stoxx 50 (QFE 2025):** cointegration relationships beyond pairs,
  unstable over time; strategies beat the index. (Summary.)
* **Galenko, Popova & Popova (2012), "Trading in the presence of
  cointegration," *Journal of Alternative Investments* 15(1), 85–97:** a
  method for mean-reversion trading of three or more cointegrated
  assets (the basis of arbitragelab's multivariate cointegration
  module). Its results could not be read. (Bibliographic records.)
* **No equity-triplet study found.** The pairs record (RK37, RK72)
  applies.

## Against, and failure modes

* Fundamental shifts break the relationship and leave a permanent
  divergence (the CSV's caveat); more search across triplets means more
  false discoveries.

## Fit with volatility-ai

Out of scope.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* "A hidden Markov model for statistical arbitrage," arXiv 2309.00875.
  Summary.
* Euro Stoxx 50 multi-asset cointegration, *Quantitative Finance and
  Economics* 9(4), 2025. Summary.
* Johansen, S. (1991). *Econometrica* 59(6), 1551–1580.
* Galenko, A., Popova, E., Popova, I. (2012). "Trading in the presence of
  cointegration." *Journal of Alternative Investments* 15(1), 85–97.
  Records only.
