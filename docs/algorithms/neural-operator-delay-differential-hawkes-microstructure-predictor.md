# Neural Operator Delay-Differential Hawkes Microstructure Predictor

**Ledger ID RK289** · rank 289 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Neural operators / Point processes / Microstructure |
| Potential effectiveness rank | 289 (1 = strongest) |
| AI implementability rank | 696 (1 = easiest) |
| Retail advantage rank | 10,285 (1 = strongest) |
| Fit with this project | ⛔ (event data; no evidence) |
| Implemented in volatility-ai | **Research code** in `research.catalog.point_processes`: `delay_hawkes_intensity`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK277, RK288, RK240 |

## In one paragraph

Combine Fourier neural operators with delay-differential Hawkes
intensities to model order arrivals and jumps under transmission lags.
Each part exists in its own literature (neural operators for PDEs;
Hawkes processes in microstructure); I found no study combining them for
market microstructure.

## Evidence

* **Li et al. (2021), "Fourier Neural Operator for Parametric Partial
  Differential Equations," ICLR:** the neural-operator class. (Standard
  reference; not re-checked here.)
* **Bacry, Mastromatteo & Muzy (2015), "Hawkes processes in finance,"
  *Market Microstructure and Liquidity* (arXiv 1502.04592):** review of
  Hawkes models in high-frequency finance: volatility estimation, market
  stability, contagion, optimal execution and order-book dynamics.
  (Abstract.)
* **No study found** combining them for microstructure.

## Against, and failure modes

* GPU mesh discretisation and kernel updates (the CSV's caveat); no
  evidence.

## Fit with volatility-ai

Out of scope: event-level data and no evidence.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Li, Z., et al. (2021). "Fourier Neural Operator for Parametric Partial
  Differential Equations." ICLR. Not re-checked.
* Bacry, E., Mastromatteo, I., Muzy, J.-F. (2015). "Hawkes processes in
  finance." *Market Microstructure and Liquidity*.
  <https://arxiv.org/abs/1502.04592>. Abstract.
