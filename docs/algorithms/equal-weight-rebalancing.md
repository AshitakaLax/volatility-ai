# Equal-Weight Rebalancing

**Ledger ID RK117** · rank 117 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Portfolio construction |
| Potential effectiveness rank | 117 (1 = strongest) |
| AI implementability rank | 59 (1 = easiest) |
| Retail advantage rank | 22 (1 = strongest) |
| Fit with this project | 🧪 reference only |
| Useful for volatility-ai | **Reference only.** The right benchmark for any multi-ETF book this project might add; not a strategy for one instrument. |
| Implemented in volatility-ai | **Yes, as a backtest book.** `research/strategies/allocators.py` `equal_weight`, run by the portfolio book (`python -m tools.portfolio_book --allocator equal_weight`), which routes every sale through the no-loss guard. Trading it live needs a multi-asset deployment ([engine/roadmap.md](../../engine/roadmap.md) item 1). Unmeasured. Before this change: **Partly.** `research.catalog.excluded`: `rebalanced_mix`. |
| Related ledger entries | X5, RK116, RK129 |

## In one paragraph

Hold assets in equal weights and rebalance periodically. Because
estimation error ruins most optimisers, 1/N is the benchmark that more
sophisticated rules must beat (DeMiguel et al.), and periodic
rebalancing harvests some mean reversion between assets.

## Evidence

* **DeMiguel, Garlappi & Uppal (2009), *Review of Financial Studies*
  22(5):** across 14 models and seven datasets none consistently beat
  1/N out of sample on Sharpe ratio, certainty-equivalent return or
  turnover; sample mean-variance needs roughly 3,000 months of data to
  beat 1/N for 25 assets. (Abstract.)
* **This repository:** `excluded.rebalanced_mix` (X5) rebalances a
  stock/bond mix.

## Against, and failure modes

* Rebalancing into a falling asset is the 1/N version of averaging down;
  with leveraged ETFs, equal weights mean very unequal risk.

## Fit with volatility-ai

For a single-ETF book there is nothing to equal-weight. If a multi-ETF
sleeve is added, 1/N (or inverse volatility, RK129) is the baseline to
beat.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* DeMiguel, V., Garlappi, L., Uppal, R. (2009). Optimal Versus Naive
  Diversification. *Review of Financial Studies* 22(5), 1915–1953.
  Abstract.
