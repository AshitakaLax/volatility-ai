# Index Reconstitution / Rebalance Event Trading

**Ledger ID RK210** · rank 210 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Event-driven / flow prediction |
| Potential effectiveness rank | 210 (1 = strongest) |
| AI implementability rank | 97 (1 = easiest) |
| Retail advantage rank | 96 (1 = strongest) |
| Fit with this project | ⛔ (single-stock front-running) · note only |
| Implemented in volatility-ai | **Research code** in `research.catalog.factors`: `predict_index_changes`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK24, RK91 |

## In one paragraph

Buy stocks expected to join an index before the effective date and sell
to the index funds that must buy them. The S&P 500 inclusion effect fell
from an average 7.4% abnormal return in the 1990s to under 1% over the
last decade, and deletions from large losses to about 0.1%, mostly
because additions now migrate from the S&P MidCap 400, whose trackers
sell what S&P 500 trackers buy.

## The rule

```text
predict additions/deletions from the published methodology (size, liquidity, float, sector)
long predicted additions between announcement and effective date; exit into the close of the effective day
```

## Evidence

* **Greenwood & Sammon (2025), "The Disappearing Index Effect," *Journal
  of Finance* 80(2), 657–698:** inclusion abnormal return from 7.4% in
  the 1990s to under 1% in the past decade; deletions to about 0.1%
  (2010–2020); migrations from the MidCap index rose from about 50% to
  over 70% of additions, and direct additions still earned 5.4% against
  1.8% for migrations in the 2010s. (Abstract and summaries.)
* **Shleifer (1986), *Journal of Finance*:** the original evidence of
  S&P 500 inclusion price effects. (Standard reference; not re-checked
  here.)

## Against, and failure modes

* Crowding and anticipatory trading (the CSV's caveat); the effect has
  largely gone for the S&P 500.
* Single-stock positions, often with a short hedge.

## Fit with volatility-ai

Out of scope as a trade. For this book, index events matter only as flow
days: Nasdaq-100 reconstitutions and rebalances move QQQ-related volume,
and a leveraged ETF rebalances at every close regardless. Nothing to
build.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Greenwood, R., Sammon, M. (2025). "The Disappearing Index Effect."
  *Journal of Finance* 80(2), 657–698.
  <https://ideas.repec.org/a/bla/jfinan/v80y2025i2p657-698.html>.
  Abstract.
* Shleifer, A. (1986). "Do Demand Curves for Stocks Slope Down?"
  *Journal of Finance* 41(3). Not re-checked.
