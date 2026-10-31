# Inverse-Volatility Allocation

**Ledger ID RK129** · rank 129 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Portfolio construction / risk scaling |
| Potential effectiveness rank | 129 (1 = strongest) |
| AI implementability rank | 146 (1 = easiest) |
| Retail advantage rank | 41 (1 = strongest) |
| Fit with this project | ✅ in use |
| Useful for volatility-ai | **In use.** For one instrument it is volatility targeting, which the grid already applies (S4 vol_target). |
| Implemented in volatility-ai | **Yes, as a backtest book.** `research/strategies/allocators.py` `inverse_volatility`, run by the portfolio book (`python -m tools.portfolio_book --allocator inverse_volatility`), which routes every sale through the no-loss guard. Trading it live needs a multi-asset deployment ([engine/roadmap.md](../../engine/roadmap.md) item 1). Unmeasured. Before this change: **Partly.** `research.strategies.hrp`: `hrp_weights`. |
| Related ledger entries | S4, A5, RK2, RK117 |

## In one paragraph

Weight assets inversely to their volatility so each carries similar
risk. Across assets it is the simplest risk-parity rule; for a single
asset it is volatility targeting, which has good evidence for equities
(RK2) and is wired on the grid.

## Evidence

* **Risk-based equity strategies** (Leote de Carvalho, Lu & Moulin
  2012): equal-risk weighting tilts toward small caps; the defensive
  strategies toward low beta. (Secondary summary.)
* **This repository:** `hrp.hrp_weights` (A5) uses inverse-variance
  weights inside clusters; the grid's S4 volatility target scales
  exposure by realised volatility.

## Against, and failure modes

* Ignores correlations across assets; volatility estimates lag regime
  changes.

## Fit with volatility-ai

Already in use in its single-asset form (S4 vol_target). Across a future
multi-ETF book it is the natural first allocator after 1/N.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Leote de Carvalho, R., Lu, X., Moulin, P. (2012). Demystifying Equity
  Risk-Based Strategies. *Journal of Portfolio Management* 38(3).
  Secondary summary.
