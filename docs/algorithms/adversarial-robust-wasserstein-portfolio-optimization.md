# Adversarial Robust Wasserstein Portfolio Optimization

**Ledger ID RK123** · rank 123 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Portfolio optimization / Robust statistics |
| Potential effectiveness rank | 123 (1 = strongest) |
| AI implementability rank | 115 (1 = easiest) |
| Retail advantage rank | 185 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** A multi-asset optimiser; the robust machinery is built but there is nothing to allocate across. |
| Implemented in volatility-ai | **Research code** `research.catalog.allocation`: `wdro_mean_variance`, `cvar_weights`. |
| Related ledger entries | RK225, RK88, RK181 |

## In one paragraph

Choose weights that do best under the worst return distribution within a
Wasserstein ball around the historical one. The theory is strong:
Mohajerin Esfahani and Kuhn give finite-sample guarantees and convex
reformulations, and Blanchet, Chen and Zhou show the mean-variance
version is regularised variance minimisation (RK225).

## Evidence

* **Mohajerin Esfahani & Kuhn (2018), *Mathematical Programming* 171:**
  worst-case optimisation over a Wasserstein ball around the empirical
  distribution has a finite-sample upper confidence bound on
  out-of-sample cost and, for mean-risk portfolios, reduces to convex
  (often linear) programmes. (Abstract.)
* **This repository:** `allocation.wdro_mean_variance` and
  `allocation.cvar_weights(radius=...)` implement the reformulations.

## Against, and failure modes

* The radius decides the answer; large radii push every book toward the
  least risky asset.

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
