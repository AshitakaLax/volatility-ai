# Asset-Growth Anomaly

**Ledger ID RK51** · rank 51 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Factor / systematic equity |
| Potential effectiveness rank | 51 (1 = strongest) |
| AI implementability rank | 165 (1 = easiest) |
| Retail advantage rank | 159 (1 = strongest) |
| Fit with this project | ⏳ long-only stock basket (needs balance sheets) · ⛔ long/short |
| Implemented in volatility-ai | **Yes, as a backtest book.** Selectable as `--allocator asset_growth` in the portfolio book (`python -m tools.portfolio_book` --data fundamentals=FILE; `research/strategies/allocator_library.py`), which routes every sale through the no-loss guard. Trading it live needs a multi-asset deployment ([engine/roadmap.md](../../engine/roadmap.md) item 1). Unmeasured. Before this change: **Research code** in `research.catalog.factors`: `asset_growth`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK15, RK35, RK50 |

## In one paragraph

Firms that grow total assets fastest earn the lowest subsequent returns;
restrained growers earn the highest. Cooper, Gulen and Schill found the
annual asset growth rate predicts abnormal returns, including among
large stocks, beyond value, size, momentum and accruals, with a spread of
about 20% a year over four decades in the working paper. It became the
investment factor of the five-factor and q-factor models (RK15). Later
work questions whether growth itself matters or the financing behind it.

## The rule

```
asset growth = total assets_t / total assets_{t-1} - 1       # fiscal year, lagged to June
June each year: long the lowest-growth decile, short the highest; hold 12 months
```

## Evidence

* **Cooper, Gulen & Schill (2008), *Journal of Finance* 63(4),
  1609–1651:** asset growth is a strong predictor of abnormal returns,
  holds among large caps, and survives book-to-market, size, prior
  returns and accruals. The working paper reports a ~20% annual premium
  for low over high growth, non-financial US stocks 1968–2007.
  (Abstract and working paper.)

## Against, and failure modes

* A critique finds the poor returns of high-growth firms concentrated
  among firms that raised large amounts of debt or equity; controlling
  for delisting bias and external financing, no independent asset-growth
  effect remains. (Search-result summary; authors not identified.)
* Cooper, Gulen & Ion (2024): the information sits mostly in inventory
  and receivables growth. (Abstract.)
* Effects vary over time and overlap other factors (the CSV's caveat).

## Fit with volatility-ai

Long-only stock basket; balance sheets and a stock universe are not in
the repository. Reference entry, best read together with RK15 and RK35.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Cooper, M. J., Gulen, H., Schill, M. J. (2008). "Asset Growth and the
  Cross-Section of Stock Returns." *Journal of Finance* 63(4),
  1609–1651. <https://econpapers.repec.org/RePEc:bla:jfinan:v:63:y:2008:i:4:p:1609-1651>.
  Abstract and working-paper summary.
* Cooper, M., Gulen, H., Ion, M. (2024). "The Use of Asset Growth in
  Empirical Asset Pricing Models." *Journal of Financial Economics*.
  Abstract.
