# Cross-Exchange Market Making (XEMM)

**Ledger ID RK307** · rank 307 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Market microstructure / market making |
| Potential effectiveness rank | 307 (1 = strongest) |
| AI implementability rank | 226 (1 = easiest) |
| Retail advantage rank | 2,117 (1 = strongest) |
| Fit with this project | ⛔ (two venues, two-sided quoting, mostly crypto) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK245, RK279, A7 |

## In one paragraph

Quote limit orders on a less liquid venue, wider than the best price on
a more liquid one by a minimum profitability margin, and hedge each fill
immediately with a market order on the liquid venue. The spread between
the venues is the profit; the risk is the hedge leg slipping or failing.
It is a crypto market-making strategy, documented mainly by the
open-source Hummingbot bot.

## Evidence

* **Hummingbot documentation (the CSV's reference):** maker orders on
  one exchange, spread wider than the taker side by `min_profitability`,
  with an opposite hedge on the taker exchange whenever a maker order
  fills; centralised exchanges on the maker side, centralised or
  decentralised on the taker side. (Documentation.)
* **No performance study found.**

## Against, and failure modes

* Hedge-leg slippage, fees and failed fills; inventory and transfer
  between venues.

## Fit with volatility-ai

One broker, one venue, and the owner's rule excludes crypto. The grid is
the buy-side, long-only relative of market making: resting buys below
the price and a sale of each lot at its own target above cost. It cannot
quote an ask without inventory, and the no-loss guard forbids skewing a
sale below cost.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Hummingbot. "Cross Exchange Market Making."
  <https://hummingbot.org/strategies/v1-strategies/cross-exchange-market-making/>.
  Documentation.
