# Net Stock Issuance Anomaly

**Ledger ID RK35** · rank 35 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Equity factor / corporate actions |
| Potential effectiveness rank | 35 (1 = strongest) |
| AI implementability rank | 22 (1 = easiest) |
| Retail advantage rank | 68 (1 = strongest) |
| Fit with this project | ⏳ long-only stock basket (needs share-count history) · ⛔ long/short |
| Implemented in volatility-ai | **Yes, as a backtest book.** Selectable as `--allocator net_issuance` in the portfolio book (`python -m tools.portfolio_book` --data fundamentals=FILE; `research/strategies/allocator_library.py`), which routes every sale through the no-loss guard. Trading it live needs a multi-asset deployment ([engine/roadmap.md](../../engine/roadmap.md) item 1). Unmeasured. Before this change: **Research code** in `research.catalog.factors`: `net_issuance`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK27, RK51 |

## In one paragraph

Firms that issue shares go on to underperform and firms that shrink
their share count outperform. Measure each firm's change in split-
adjusted shares outstanding over a year or more and tilt toward low (or
negative) issuers. After 1970 this signal predicts returns more
significantly than size, value or momentum individually, and it holds
in 41 countries. The CSV added it with references and no backtest; the
data cleaning (splits, mergers, spin-offs) is most of the work.

## The rule

```
NSI = log(split-adjusted shares_t / split-adjusted shares_{t-12 months})        # or a multi-year window
annually or monthly: rank; long the lowest-issuance group (diversified, long-only)
test incremental value against shareholder yield (RK27) and value (RK48)
```

## Evidence

* **Pontiff & Woodgate (2008), *Journal of Finance* 63(2), 921–945:**
  post-1970, share issuance predicts cross-sectional returns more
  significantly than size, book-to-market or momentum; pre-1970 the
  relation is mostly insignificant. (Abstract.)
* **McLean, Pontiff & Watanabe (2009), *Journal of Financial Economics*
  94(1), 1–17:** the effect holds in 41 non-US countries. (Abstract.)
* **Fama & French (2008), "Dissecting Anomalies"** (the CSV's reference)
  finds net-stock-issue returns pervasive across size groups. (Cited in
  search results; not opened.)

## Against, and failure modes

* Corporate actions are messy: acquisitions paid in stock, ADRs,
  spin-offs, missing share counts (the CSV's caveat).
* The pre-1970 absence is a warning that the effect may be period-specific.
* Overlaps heavily with buyback/shareholder yield and asset growth.

## Fit with volatility-ai

Long-only stock basket; share-count histories are not in the warehouse.
Reference entry.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Pontiff, J., Woodgate, A. (2008). "Share Issuance and Cross-sectional
  Returns." *Journal of Finance* 63(2), 921–945.
  <https://ideas.repec.org/a/bla/jfinan/v63y2008i2p921-945.html>. Abstract.
* McLean, R. D., Pontiff, J., Watanabe, A. (2009). "Share Issuance and
  Cross-sectional Returns: International Evidence." *Journal of
  Financial Economics* 94(1), 1–17. Abstract.
* Fama, E. F., French, K. R. (2008). "Dissecting Anomalies." *Journal of
  Finance* 63(4).
  <https://onlinelibrary.wiley.com/doi/full/10.1111/j.1540-6261.2008.01371.x>
  (the CSV's reference). Not opened.
