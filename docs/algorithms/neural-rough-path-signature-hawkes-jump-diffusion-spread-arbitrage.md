# Neural Rough Path Signature Hawkes Jump-Diffusion Spread Arbitrage

**Ledger ID RK190** · rank 190 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Rough path theory / Point processes / Statistical arbitrage |
| Potential effectiveness rank | 190 (1 = strongest) |
| AI implementability rank | 352 (1 = easiest) |
| Retail advantage rank | 6,480 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** A short-leg spread model stacking untested methods. |
| Implemented in volatility-ai | **Research code** `research.catalog.point_processes`: `signature_hawkes_forecast`. |
| Related ledger entries | RK342, RK328 |

## In one paragraph

Model a cointegrated spread with signature features and Hawkes-driven
jumps. Signature features have helped order-book forecasts and have a
mean-variance trading theory; I found no spread study combining them
with Hawkes jumps.

## Evidence

* **Futter, Horvath & Wiese (2023):** signature trading (RK328).
* **No study found** that tests this combination as a trading strategy.

## Against, and failure modes

* Jumps in spreads are rare events: too few to fit a self-exciting model
  per pair.

## Fit with volatility-ai

A relative-value trade between assets: it needs a short leg and a
universe of related instruments, and the engine trades one leveraged ETF
long-only. Out of scope as a strategy.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* See RK328 and RK342's references.
