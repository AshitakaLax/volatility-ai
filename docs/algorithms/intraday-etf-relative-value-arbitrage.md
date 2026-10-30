# Intraday ETF Relative-Value Arbitrage

**Ledger ID RK108** · rank 108 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Statistical arbitrage / intraday |
| Potential effectiveness rank | 108 (1 = strongest) |
| AI implementability rank | 195 (1 = easiest) |
| Retail advantage rank | 279 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** A seconds-to-minutes short-leg trade between twin ETFs; needs quotes, shorting and speed. |
| Implemented in volatility-ai | **Research code** `research.catalog.excluded`: `ib_hft_signals`, `ib_pairs_long_only`. |
| Related ledger entries | A6, RK24 |

## In one paragraph

Trade brief divergences between ETFs on the same index (SPY against IVV)
or an ETF and its benchmark. Marshall, Nguyen and Visaltanachoti found
divergences that close within minutes, profitable before broker fees;
the trade is a speed and cost game.

## Evidence

* **Marshall, Nguyen & Visaltanachoti (2013), *Journal of Banking &
  Finance* 37(9):** SPY/IVV quote divergences close quickly (median
  trade about 23 minutes); gross profits of 6.7% a year for SPY-IVV
  before broker fees, 2001–2010. (Secondary summary.)

## Against, and failure modes

* Profits are gross of fees and assume 15-second execution; the
  opportunity shrinks as it is traded.

## Fit with volatility-ai

A high-frequency relative-value trade with a short leg: it needs tick
data (the warehouse holds minute bars), a second instrument and
shorting. Out of scope.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Marshall, B. R., Nguyen, N. H., Visaltanachoti, N. (2013). ETF
  arbitrage: Intraday evidence. *Journal of Banking & Finance* 37(9),
  3486–3498. Secondary summary (CXO Advisory).
