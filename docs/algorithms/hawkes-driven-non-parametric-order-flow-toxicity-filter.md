# Hawkes-Driven Non-Parametric Order Flow Toxicity Filter

**Ledger ID RK259** · rank 259 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Point process / Market microstructure / Risk filter |
| Potential effectiveness rank | 259 (1 = strongest) |
| AI implementability rank | 378 (1 = easiest) |
| Retail advantage rank | 10,227 (1 = strongest) |
| Fit with this project | ⛔ (market-making halt; needs event data) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK247, RK248, RK277 |

## In one paragraph

Estimate Hawkes kernels non-parametrically on trade and cancellation
streams, turn them into a real-time toxicity score, and stop market
making when it is high. Non-parametric Hawkes estimation exists, and
VPIN is the best-known toxicity score; the VPIN dispute suggests such
scores may add little beyond volume and volatility. I found no study of
this combination, and the CSV's reference, arXiv 2002.09876, looks like
a placeholder ID (sequential digits, like the CSV's arXiv 1908.01234 on
RK97) and could not be identified.

## Evidence

* **Bacry, Mastromatteo & Muzy (2015), "Hawkes processes in finance,"
  *Market Microstructure and Liquidity* (arXiv 1502.04592):** review of
  Hawkes models in high-frequency finance: volatility estimation, market
  stability, contagion, optimal execution and order-book dynamics.
  (Abstract.)
* The VPIN dispute (RK247): toxicity scores may carry no information
  beyond volume and volatility.
* **No study found** of a non-parametric Hawkes toxicity filter.

## Against, and failure modes

* Kernels go stale without sliding-window re-estimation (the CSV's
  caveat).

## Fit with volatility-ai

Out of scope: a market-making halt on event-level data this project does
not have.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Bacry, E., Mastromatteo, I., Muzy, J.-F. (2015). "Hawkes processes in
  finance." *Market Microstructure and Liquidity*.
  <https://arxiv.org/abs/1502.04592>. Abstract.
* The CSV's references: hawkeslib; arXiv 2002.09876 (not identified).
