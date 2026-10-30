# Wasserstein Distributionally Robust Neural Operator Optimal Portfolio

**Ledger ID RK157** · rank 157 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Robust statistics / Neural operators / Portfolio optimization |
| Potential effectiveness rank | 157 (1 = strongest) |
| AI implementability rank | 337 (1 = easiest) |
| Retail advantage rank | 215 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** A multi-asset optimiser stacking two methods with no portfolio study. |
| Implemented in volatility-ai | **Research code** `research.catalog.allocation`: `wdro_mean_variance`; `research.catalog.execution`: `NeuralOperatorExecution`. |
| Related ledger entries | RK122, RK410 |

## In one paragraph

Optimise allocations over a Wasserstein ambiguity set of function-valued
return distributions represented by neural operators. The Wasserstein
half has theory (Mohajerin Esfahani and Kuhn); neural operators are PDE
solvers (Li et al., the CSV's reference); I found no portfolio study
combining them.

## Evidence

* **Mohajerin Esfahani & Kuhn (2018), *Mathematical Programming* 171:**
  worst-case optimisation over a Wasserstein ball around the empirical
  distribution has a finite-sample upper confidence bound on
  out-of-sample cost and, for mean-risk portfolios, reduces to convex
  (often linear) programmes. (Abstract.)
* **Li et al. (2021), Fourier Neural Operator (arXiv 2010.08895):** a
  PDE solver, not a finance method.
* **No study found** that tests this combination as a trading strategy.

## Against, and failure modes

* Infinite-dimensional ambiguity sets for a handful of assets add
  nothing but parameters.

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
* Li, Z. et al. (2021). Fourier Neural Operator for Parametric PDEs.
  ICLR. <https://arxiv.org/abs/2010.08895>. Abstract.
