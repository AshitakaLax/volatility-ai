# Inflation-Regime Asset Rotation

**Ledger ID RK41** · rank 41 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Macro / tactical allocation |
| Potential effectiveness rank | 41 (1 = strongest) |
| AI implementability rank | 144 (1 = easiest) |
| Retail advantage rank | 37 (1 = strongest) |
| Fit with this project | ⏳ long-only ETF rotation with a causal macro regime |
| Implemented in volatility-ai | **Yes, as a backtest book.** Selectable as `--allocator inflation_rotation` in the portfolio book (`python -m tools.portfolio_book` --data macro=FILE; `research/strategies/allocator_library.py`), which routes every sale through the no-loss guard. Trading it live needs a multi-asset deployment ([engine/roadmap.md](../../engine/roadmap.md) item 1). Unmeasured. Before this change: **Research code** in `research.catalog.carry_rates`: `inflation_regimes`, `regime_rotation`; tested on synthetic data, not wired into the engine. The pieces exist: FRED fetchers (`research/ml/sources.py`), a lag-aware macro join in the warehouse, and the rotation harness (X2). |
| Related ledger entries | X2, X5, X9, RK1, RK32 |

## In one paragraph

Classify the economy by inflation (level, change, or surprise) and hold
the assets that have historically done well in that state: equities and
nominal bonds in disinflation, real assets and commodities in inflation
shocks. The best recent study, 95 years of data in three countries,
finds unexpected inflation hurts both stocks and bonds, commodities do
well but unevenly, and trend following is the most reliable dynamic
protection. For this project the 2022 bear market (TQQQ −79%) was an
inflation shock, so the question is live; the data and plumbing to test
it causally already exist.

## The rule

```
monthly, on data as published (with release lags):
    inflation state = YoY CPI above/below a threshold, and rising/falling
                      (or: CPI surprise vs consensus; or breakeven inflation trend)
    rising inflation  -> commodities / TIPS / cash; reduce long-duration growth equity
    falling inflation -> equities / nominal bonds
```

## Evidence

* **Neville, Draaisma, Funnell, Harvey & Van Hemert (2021), "The Best
  Strategies for Inflationary Times," *Journal of Portfolio Management*
  47(8):** 95 years, US, UK and Japan; unexpected inflation is bad for
  bonds and equities, worst for local inflation; commodities have
  positive returns in inflation surges with wide variation (energy best);
  trend following gives the most reliable protection among dynamic
  strategies; equity factor strategies help somewhat. (Abstract and
  summaries.)

## Against, and failure modes

* **Revisions and delays:** CPI is published with a lag and revised;
  using the final series as if known on its reference date is
  lookahead (the CSV's caveat). This repository's warehouse already
  shifts macro series by `lag_days` before the ASOF join for exactly this
  reason.
* Few inflation regimes in modern data (the 1970s, 2021–2023), so
  thresholds fit a handful of episodes.
* Asset sensitivities change with starting valuations.

## Fit with volatility-ai

Long-only ETFs (equities, TIPS, a commodity ETF, cash) fit the
constraints. As a regime for the TQQQ book it is a slow switch: the
inflation state changes a few times a decade, so few flips, but late.

## How to test it here

1. Fetch CPI (and 5-year breakevens) from FRED with publication lags
   (`research/ml/sources.fetch_fred`; the warehouse external-series
   manifest records `lag_days`).
2. Build a causal monthly "inflation rising" flag and run it as a
   `--regime` on `tools/leverage_stepdown.py` (TQQQ only while inflation
   is falling), with cash otherwise; then as X2's gate with a commodity
   ETF and TIPS among the defensives.
3. Score 2022 and 2016–2020 separately; the first is the reason to try
   it, the second is what it costs.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Neville, H., Draaisma, T., Funnell, B., Harvey, C. R., Van Hemert, O.
  (2021). "The Best Strategies for Inflationary Times." *Journal of
  Portfolio Management* 47(8), 8–37. <https://doi.org/10.3905/jpm.2021.1.274>.
  Abstract and summaries.
* FRED (the CSV's reference): <https://fred.stlouisfed.org/>.
* This repository: `research/ml/sources.py`, `engine/warehouse/queries.py`
  (lagged macro ASOF join).
