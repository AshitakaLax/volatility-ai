# 52-Week High Momentum

**Ledger ID RK14** · rank 14 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Cross-sectional momentum (anchoring) |
| Potential effectiveness rank | 14 (1 = strongest) |
| AI implementability rank | 15 (1 = easiest) |
| Retail advantage rank | 5 (1 = strongest) |
| Fit with this project | ⏳ long-only stock basket (needs a stock universe) · ⛔ long/short · its nearness measure already gates the Ultimate strategy |
| Implemented in volatility-ai | **No** as a ranking. The same quantity, distance from the trailing one-year high, is the Ultimate strategy's bear filter (`bear_dd`, `bear_window=250`). |
| Related ledger entries | RK6, RK7; Ultimate lesson L12 |

## In one paragraph

Rank stocks by how close the current price is to its own 52-week high
and buy the closest (short the farthest in the academic form). George &
Hwang found this nearness predicts returns better than past returns do,
explains much of ordinary momentum, and, unlike ordinary momentum, does
not reverse later. The usual explanation is anchoring: investors treat
the high as a reference and under-react to news that pushes price near
it. As a stock-picking rule it needs a stock universe; as a single-asset
condition it is already in this repository.

## The rule

```
nearness_i(t) = P_i(t) / max(P_i over the past 52 weeks)       # in (0, 1]
monthly: long the top 30% by nearness, short the bottom 30% (academic form)
hold 6 months in overlapping portfolios (the paper's construction)
```

## Evidence

* **George & Hwang (2004)**, US stocks 1963–2001: nearness to the 52-week
  high dominates and improves on past returns (individual and industry)
  as a forecaster, and its predictions do not reverse in the long run,
  which separates short-term momentum from long-term reversal.
  (Abstract.)
* International follow-up work reports profits in 18 of 20 markets,
  significant in 10. (Search-result summary.)

## Against, and failure modes

* **Crowding near highs** in late bull markets; like all momentum it is
  exposed to sharp reversals after panics (Daniel & Moskowitz 2016).
* **Sample sensitivity**, the CSV's own caveat; overlapping 6-month
  holdings make the realised turnover and costs hard to read from the
  headline numbers.

## Fit with volatility-ai

* As a stock ranking: long-only fits, but needs a survivorship-free stock
  universe the warehouse does not hold.
* As a **single-asset condition** it is already researched here: the
  Ultimate strategy allows calm re-entry only while price is within 50%
  of its 250-session high (L12), which lifted Calmar from 1.30 to
  1.63–1.75 in its experiment, mostly through 2022.

## How to test it here

* The useful question for this book is not the cross-section but the
  threshold: run the Ultimate bear filter at `bear_dd` 0.2 / 0.3 / 0.5 on
  TQQQ (and on QQQ's price, per lesson L15) and check that the benefit is
  not only 2022.
* For the stock version, start research-only from published 52-week-high
  portfolio returns before building a universe.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* George, T. J., Hwang, C.-Y. (2004). "The 52-Week High and Momentum
  Investing." *Journal of Finance* 59(5), 2145–2176.
  <https://onlinelibrary.wiley.com/doi/full/10.1111/j.1540-6261.2004.00695.x>.
  Abstract (the CSV's own reference).
* Daniel, K., Moskowitz, T. (2016). "Momentum Crashes." *Journal of
  Financial Economics* 122(2), 221–247. Abstract.
* `docs/research/ultimate-algorithm.md`, lesson L12 and experiment 5 (this
  repository).
