# Arrival-Price Adaptive Limit-vs-Market Execution

**Ledger ID RK250** · rank 250 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Execution / transaction-cost optimization |
| Potential effectiveness rank | 250 (1 = strongest) |
| AI implementability rank | 154 (1 = easiest) |
| Retail advantage rank | 302 (1 = strongest) |
| Fit with this project | 🧪 purpose-based limit pricing (built) · ⏳ an implementation-shortfall check on live fills |
| Implemented in volatility-ai | **Partial.** `engine/execution/limit_pricing.py` prices an order by its purpose: a grid buy rests at its trigger price (skipped while the spread is too wide), a must-fill order crosses to the far quote within a premium cap; regular-hours buys are notional market orders. No arrival-price or urgency model. Deferred: adaptive execution is [engine/roadmap.md](../../engine/roadmap.md) item 2. |
| Related ledger entries | RK244, RK249 |

## In one paragraph

Decide between a resting limit and a marketable order using how far the
price has moved since the order arrived, urgency, volatility and the
quantity left, and judge the result by implementation shortfall: the gap
between the paper portfolio at the decision price and what was actually
filled. Limits risk not filling and adverse selection; market orders pay
the spread and impact.

## Evidence

* **Perold (1988), "The Implementation Shortfall: Paper versus Reality,"
  *Journal of Portfolio Management* 14(3):** the benchmark. (Standard
  reference; not re-checked here.)
* **Almgren & Chriss (2001):** the impact-versus-risk schedule. (See
  RK244.)
* The CSV's reference (*Quantitative Finance*, doi
  10.1080/14697688.2015.1032543) could not be identified.

## Against, and failure modes

* Benchmark every fill model against realised implementation shortfall
  (the CSV's caveat).

## Fit with volatility-ai

The grid buy that rests at its trigger is the order the backtest
measured (intrabar fill at the level), so the live engine already places
it that way outside regular hours. The useful addition is measurement:
compare journaled live fills with each trigger price to get this book's
actual shortfall.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Perold, A. F. (1988). *Journal of Portfolio Management* 14(3). Not
  re-checked.
* This repository: `engine/execution/limit_pricing.py`,
  `engine/brokers/alpaca_broker.py` (notional market orders in regular
  hours, limit orders outside).
