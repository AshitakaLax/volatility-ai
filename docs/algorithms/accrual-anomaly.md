# Accrual Anomaly

**Ledger ID RK50** · rank 50 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Factor / systematic equity |
| Potential effectiveness rank | 50 (1 = strongest) |
| AI implementability rank | 135 (1 = easiest) |
| Retail advantage rank | 180 (1 = strongest) |
| Fit with this project | ⏳ long-only (avoid high-accrual stocks) · ⛔ long/short; evidence says the edge is gone |
| Implemented in volatility-ai | **Yes, as a backtest book.** Selectable as `--allocator low_accruals` in the portfolio book (`python -m tools.portfolio_book` --data fundamentals=FILE; `research/strategies/allocator_library.py`), which routes every sale through the no-loss guard. Trading it live needs a multi-asset deployment ([engine/roadmap.md](../../engine/roadmap.md) item 1). Unmeasured. Before this change: **Research code** in `research.catalog.factors`: `accruals`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK11, RK51 |

## In one paragraph

Earnings made of accruals (non-cash accounting adjustments) persist less
than earnings backed by cash, and investors did not price the
difference: firms with the lowest accruals outperformed those with the
highest (Sloan 1996). It is the classic forensic-accounting anomaly, and
also the classic case of an anomaly that disappeared once it was
published and hedge funds traded it.

## The rule

```
accruals = (change in non-cash current assets - change in current liabilities
            excluding short-term debt and taxes payable - depreciation) / average total assets
            (cash-flow-statement version: net income - cash flow from operations)
annually, after statements: long the lowest-accrual decile, short the highest
```

## Evidence

* **Sloan (1996), *The Accounting Review* 71(3), 289–315:** a strategy
  long the most negative accruals and short the most positive earns
  abnormal returns; investors misjudge the persistence of the accrual
  and cash components of earnings. (As described in reviews.)

## Against, and failure modes

* **Green, Hand & Soliman (2011), *Management Science* 57(5), 797–816:**
  the hedge returns have decayed in US markets and are no longer reliably
  positive, much of it explained by growing hedge-fund capital trading
  extreme-accrual firms. (Abstract.) Other work dates the disappearance
  to about 2002.
* Accounting schema changes and publication lags (the CSV's caveat).

## Fit with volatility-ai

Long-only "avoid high accruals" fits the instrument rule but needs
statements for a stock universe; with the evidence that the premium has
been arbitraged away, it is a reference entry. Its value here is as an
example of post-publication decay, the risk every entry in this list
carries.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Sloan, R. G. (1996). "Do Stock Prices Fully Reflect Information in
  Accruals and Cash Flows about Future Earnings?" *The Accounting Review*
  71(3), 289–315. Described in reviews; not opened. The formula above is
  the standard balance-sheet definition, as I recall it.
* Green, J., Hand, J. R. M., Soliman, M. T. (2011). "Going, Going, Gone?
  The Apparent Demise of the Accruals Anomaly." *Management Science*
  57(5), 797–816. <https://doi.org/10.1287/mnsc.1110.1320>. Abstract.
