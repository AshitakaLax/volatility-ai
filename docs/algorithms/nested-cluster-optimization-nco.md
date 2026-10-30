# Nested Cluster Optimization (NCO)

**Ledger ID RK120** · rank 120 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Portfolio optimization / clustering |
| Potential effectiveness rank | 120 (1 = strongest) |
| AI implementability rank | 147 (1 = easiest) |
| Retail advantage rank | 45 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** A multi-asset optimiser whose gains are simulated by its author and not confirmed independently. |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | A5, RK119 |

## In one paragraph

Cluster assets, optimise within each cluster, then optimise across the
cluster portfolios, to contain the instability of mean-variance
optimisation. López de Prado reports up to 90% lower estimation error in
Monte Carlo experiments; a later empirical thesis did not confirm
general gains from hierarchical clustering.

## Evidence

* **López de Prado (2019), "A Robust Estimator of the Efficient
  Frontier" (SSRN 3469961):** NCO and the MCOS Monte Carlo test; up to
  90% less estimation error than standard optimisers, per the author.
  (Abstract.)
* **CBS master's thesis (2022):** no conclusive support for general
  gains from hierarchical clustering; early positive NCO effects not
  confirmed. (Abstract.)

## Against, and failure modes

* The gains are measured on simulated covariances, not on live
  portfolios.

## Fit with volatility-ai

A portfolio-construction rule for a multi-asset book. The engine trades
one symbol and the multi-asset allocator in ledger §11 is not built; it
becomes relevant only if a multi-ETF book is added (as X2/X3 explore).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* López de Prado, M. (2019). A Robust Estimator of the Efficient
  Frontier. SSRN 3469961. Abstract.
* Copenhagen Business School master's thesis on hierarchical risk parity
  (2022). Abstract.
