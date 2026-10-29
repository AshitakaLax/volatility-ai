# Hawkes Process Multi-Dimensional Order Flow Intensity Model

**Ledger ID RK277** · rank 277 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Point process / Market microstructure |
| Potential effectiveness rank | 277 (1 = strongest) |
| AI implementability rank | 364 (1 = easiest) |
| Retail advantage rank | 10,556 (1 = strongest) |
| Fit with this project | ⛔ (needs event-level order data) |
| Implemented in volatility-ai | **Research code** in `research.catalog.point_processes`: `fit_multivariate_hawkes`, `simulate_multivariate_hawkes`, `multivariate_intensity`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK248, RK259, RK289 |

## In one paragraph

A multivariate Hawkes model of buy and sell market orders, limit orders
and cancellations, in which each event type excites the others, used to
forecast bursts of activity seconds ahead. It is the general form of
RK248. Bacry and Muzy's model links market-order arrivals to price
changes; the review by Bacry, Mastromatteo and Muzy covers the
applications.

## Evidence

* **Bacry, Mastromatteo & Muzy (2015), "Hawkes processes in finance,"
  *Market Microstructure and Liquidity* (arXiv 1502.04592):** review of
  Hawkes models in high-frequency finance: volatility estimation, market
  stability, contagion, optimal execution and order-book dynamics.
  (Abstract.)
* **Bacry & Muzy (2014), "Hawkes model for price and trades
  high-frequency dynamics" (arXiv 1301.1135):** a multivariate Hawkes
  model linking market-order arrivals and price changes. (Abstract.)

## Against, and failure modes

* Low-latency implementation and maximum likelihood on dense event
  streams (the CSV's caveat).

## Fit with volatility-ai

Out of scope for the same reason as RK248: the warehouse holds minute
bars only; no historical quotes, trades or depth.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Bacry, E., Mastromatteo, I., Muzy, J.-F. (2015). "Hawkes processes in
  finance." *Market Microstructure and Liquidity*.
  <https://arxiv.org/abs/1502.04592>. Abstract.
* Bacry, E., Muzy, J.-F. (2014). "Hawkes model for price and trades
  high-frequency dynamics." <https://arxiv.org/abs/1301.1135>. Abstract.
