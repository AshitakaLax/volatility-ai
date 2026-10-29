# Hawkes-Process Order-Flow Forecast

**Ledger ID RK248** · rank 248 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Market microstructure / point process |
| Potential effectiveness rank | 248 (1 = strongest) |
| AI implementability rank | 332 (1 = easiest) |
| Retail advantage rank | 10,217 (1 = strongest) |
| Fit with this project | ⛔ (needs event-level order data) |
| Implemented in volatility-ai | **Research code** in `research.catalog.point_processes`: `order_flow_forecast`, `fit_multivariate_hawkes`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK277, RK259, RK289 |

## In one paragraph

Model order arrivals, cancellations and trades as Hawkes processes, in
which each event raises the short-term rate of further events of the
same and other types, and use the fitted intensities to forecast
near-term flow for quoting or direction. The models describe clustering
in order flow well and are widely used in microstructure research; I
found no evidence of their trading value at retail latency.

## The rule

```text
lambda_i(t) = mu_i + sum_j sum_(t_k^j < t) phi_ij(t - t_k^j)       # e.g. phi = alpha x exp(-beta x dt)
fit by maximum likelihood on event streams; forecast the next interval's buy/sell intensity
```

## Evidence

* **Bacry, Mastromatteo & Muzy (2015), "Hawkes processes in finance,"
  *Market Microstructure and Liquidity* (arXiv 1502.04592):** review of
  Hawkes models in high-frequency finance: volatility estimation, market
  stability, contagion, optimal execution and order-book dynamics.
  (Abstract.)
* The CSV's two references (Springer s42786-024-00049-8; PMC8871091)
  were not opened.

## Against, and failure modes

* Parameter instability, cost and non-stationary event rates (the CSV's
  caveat); needs event streams, not candles.

## Fit with volatility-ai

Out of scope: The warehouse holds minute bars only; no historical
quotes, trades or depth. Minute bars aggregate away the self-excitation
the model describes.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Bacry, E., Mastromatteo, I., Muzy, J.-F. (2015). "Hawkes processes in
  finance." *Market Microstructure and Liquidity*.
  <https://arxiv.org/abs/1502.04592>. Abstract.
