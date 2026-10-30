# Neural Operator Delay-Differential Stochastic Control Portfolio Optimization

**Ledger ID RK156** · rank 156 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Neural operators / Stochastic control / Portfolio optimization |
| Potential effectiveness rank | 156 (1 = strongest) |
| AI implementability rank | 318 (1 = easiest) |
| Retail advantage rank | 276 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** A multi-period allocator with no study and nothing to allocate across here. |
| Implemented in volatility-ai | **Research code** `research.catalog.carry_rates`: `NeuralDelayCurve`. |
| Related ledger entries | RK287, RK330 |

## In one paragraph

Solve multi-period portfolio control with memory lags using neural delay
differential equations and Fourier neural operators. I found no study of
it; the CSV's reference, arXiv 2106.09876, is a general graph
anomaly-detection paper ("Anomaly Detection in Dynamic Graphs via
Transformer"), not a finance one.

## Evidence

* **No study found** that tests this combination as a trading strategy.

## Against, and failure modes

* Delay terms and operator networks for a few assets over-parameterise a
  problem with little data.

## Fit with volatility-ai

A portfolio-construction rule for a multi-asset book. The engine trades
one symbol and the multi-asset allocator in ledger §11 is not built; it
becomes relevant only if a multi-ETF book is added (as X2/X3 explore).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* The CSV's reference, arXiv 2106.09876 (graph anomaly detection; not
  finance).
