# Hawkes-Driven Optimal Execution with Transitory Price Impact

**Ledger ID RK367** · rank 367 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Market microstructure / Optimal execution |
| Potential effectiveness rank | 367 (1 = strongest) |
| AI implementability rank | 372 (1 = easiest) |
| Retail advantage rank | 10,331 (1 = strongest) |
| Fit with this project | ⛔ (large-order execution; event data) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK366, RK248, RK371 |

## In one paragraph

Extend optimal execution to a market where other traders' orders arrive
as a self-exciting Hawkes process and move the price with transient
impact. The optimum is explicit and reacts to the other traders' flow,
and the model clarifies when such markets admit price manipulation:
Poisson order arrivals do, while Hawkes parameters balancing
self-excitation against price resilience rule it out.

## Evidence

* **Alfonsi & Blanc (2016), "Dynamic optimal execution in a
  mixed-market-impact Hawkes price model," *Finance and Stochastics*
  20(1), 183–218 (arXiv 1404.0648):** with linear impact and other
  traders' orders arriving as a Hawkes process, the optimal execution
  strategy is explicit and reacts to their flow; Poisson arrivals admit
  price manipulation, and Hawkes parameters that balance self-excitation
  against resilience rule it out. (Abstract.)

## Against, and failure modes

* Calibration needs order-level data; transient-impact kernels are hard
  to estimate.

## Fit with volatility-ai

The grid's orders are small against TQQQ's daily volume, price-triggered
and single-venue; there is no parent order to schedule and no impact
worth modelling. The warehouse holds minute bars only; no historical
quotes, trades or depth.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Alfonsi, A., Blanc, P. (2016). *Finance and Stochastics* 20(1),
  183–218. <https://arxiv.org/abs/1404.0648>. Abstract.
