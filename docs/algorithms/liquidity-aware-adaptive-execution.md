# Liquidity-Aware Adaptive Execution

**Ledger ID RK244** · rank 244 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Execution / market microstructure |
| Potential effectiveness rank | 244 (1 = strongest) |
| AI implementability rank | 362 (1 = easiest) |
| Retail advantage rank | 9,357 (1 = strongest) |
| Fit with this project | 🧪 the spread gate on live buys · ⛔ child-order slicing (orders are small) |
| Implemented in volatility-ai | **Partial.** Live grid buys are skipped while the quote's spread exceeds `live.orders.max_spread`, and must-fill orders cap their premium over the bar (`engine/execution/limit_pricing.py`); no order slicing or adaptive aggressiveness. |
| Related ledger entries | RK250, RK251, RK249 |

## In one paragraph

Execution algorithms that adjust aggressiveness and child-order timing
to live spreads, depth, volume, volatility and the deadline, trading off
market impact against the risk of the price moving before the order
completes (Almgren and Chriss's framework). A 2020 BIS study found such
algorithms improve FX market functioning but shift execution risk from
dealers to end users and raise the bar for data and tools.

## Evidence

* **Almgren & Chriss (2001), "Optimal execution of portfolio
  transactions," *Journal of Risk* 3(2):** the impact-versus-timing-risk
  frontier behind most schedules. (Standard reference; not re-checked
  here.)
* **BIS Markets Committee (2020), "FX execution algorithms and market
  functioning," Paper 13 (the CSV's reference):** survey of 70
  participants; algorithms improve market functioning, transfer
  execution risk to end users, change liquidity dynamics and raise the
  bar for data, skills and tools. (Report summary.)

## Against, and failure modes

* The objective must balance cost, completion risk and information
  leakage; vendor methods differ (the CSV's caveat).

## Fit with volatility-ai

This book's orders are small against TQQQ's volume, so impact is
negligible and slicing buys nothing. What matters is not paying a wide
spread in thin extended hours, which the live loop already handles by
skipping grid buys when the spread is too wide.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Almgren, R., Chriss, N. (2001). "Optimal execution of portfolio
  transactions." *Journal of Risk* 3(2). Not re-checked.
* BIS Markets Committee (2020). "FX execution algorithms and market
  functioning." Markets Committee Papers No 13.
  <https://www.bis.org/publ/mktc13.htm>. Summary.
* This repository: `engine/execution/limit_pricing.py`,
  `engine/trading/live_trading_loop.py`.
