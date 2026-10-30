# Wasserstein Distributionally Robust Mean-CVaR Dynamic Allocation

**Ledger ID RK181** · rank 181 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Robust statistics / Tail risk allocation |
| Potential effectiveness rank | 181 (1 = strongest) |
| AI implementability rank | 283 (1 = easiest) |
| Retail advantage rank | 169 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** A multi-asset allocator; the robust CVaR programme is built but there is nothing to allocate. |
| Implemented in volatility-ai | **Research code** `research.catalog.allocation`: `cvar_weights`. |
| Related ledger entries | RK88, RK53, RK122 |

## In one paragraph

Minimise the worst-case CVaR over a Wasserstein ball around historical
returns and re-solve as data arrive. Mohajerin Esfahani and Kuhn show
this is a linear programme with finite-sample guarantees (RK88); the
CSV's reference, arXiv 1908.01234, is a biomedical-engineering paper on
an electromagnetic bioreactor, unrelated to trading.

## Evidence

* **Mohajerin Esfahani & Kuhn (2018), *Mathematical Programming* 171:**
  worst-case optimisation over a Wasserstein ball around the empirical
  distribution has a finite-sample upper confidence bound on
  out-of-sample cost and, for mean-risk portfolios, reduces to convex
  (often linear) programmes. (Abstract.)
* **This repository:** `allocation.cvar_weights(radius=...)` (RK88).

## Against, and failure modes

* The radius drives the answer; CVaR estimates rest on few tail days.

## Fit with volatility-ai

A portfolio-construction rule for a multi-asset book. The engine trades
one symbol and the multi-asset allocator in ledger §11 is not built; it
becomes relevant only if a multi-ETF book is added (as X2/X3 explore).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Mohajerin Esfahani, P., Kuhn, D. (2018). Data-driven distributionally
  robust optimization using the Wasserstein metric. *Mathematical
  Programming* 171, 115–166. Abstract.
* The CSV's reference, arXiv 1908.01234 (bioreactor dosimetry;
  unrelated).
