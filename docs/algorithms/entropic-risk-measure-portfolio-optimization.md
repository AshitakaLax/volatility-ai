# Entropic Risk Measure Portfolio Optimization

**Ledger ID RK126** · rank 126 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Risk-sensitive optimization / Portfolio construction |
| Potential effectiveness rank | 126 (1 = strongest) |
| AI implementability rank | 65 (1 = easiest) |
| Retail advantage rank | 79 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** A multi-asset objective; for one instrument it reduces to choosing exposure, which the regime exit already does. |
| Implemented in volatility-ai | **Research code** `research.catalog.spd_covariance`: `entropic_weights`. |
| Related ledger entries | RK266, RK53 |

## In one paragraph

Optimise weights for the entropic risk measure, (1/θ) log E[exp(−θX)],
which penalises the left tail more than variance does. It is
exponential-utility optimisation with a tail-sensitive parameter; the
CSV's reference, arXiv 1904.12345, could not be identified, and I found
no empirical portfolio study of it.

## Evidence

* **Föllmer & Schied (2004):** the entropic risk measure as a convex
  risk measure from exponential utility.
* **This repository:** `spd_covariance.entropic_weights` (RK266).
* **No study found** that tests this combination as a trading strategy.

## Against, and failure modes

* θ is a risk-aversion knob; tail estimates rest on few crashes.

## Fit with volatility-ai

A portfolio-construction rule for a multi-asset book. The engine trades
one symbol and the multi-asset allocator in ledger §11 is not built; it
becomes relevant only if a multi-ETF book is added (as X2/X3 explore).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Föllmer, H., Schied, A. (2004). *Stochastic Finance*. Standard
  reference.
* The CSV's reference, arXiv 1904.12345 (not identified).
