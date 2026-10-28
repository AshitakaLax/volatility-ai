# Sparse Bayesian Learning Dynamic Factor Model

**Ledger ID RK218** · rank 218 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Bayesian statistics / Systematic equity |
| Potential effectiveness rank | 218 (1 = strongest) |
| AI implementability rank | 76 (1 = easiest) |
| Retail advantage rank | 109 (1 = strongest) |
| Fit with this project | ⏳ as a factor-selection method for a stock book |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK9, RK205 |

## In one paragraph

Put sparsity priors (automatic relevance determination) on a dynamic
factor model so that irrelevant factors shrink to zero and only active
ones remain. The strongest related evidence is Bayesian: averaging over
2.25 quadrillion candidate factor models produced a stochastic discount
factor that beat existing models in and out of sample, and showed which
factors are weakly identified.

## Evidence

* **Bryzgalova, Huang & Julliard (2023), "Bayesian Solutions for the
  Factor Zoo," *Journal of Finance* 78(1), 487–557:** Bayesian model
  averaging over 2.25 quadrillion linear factor models; flags weakly
  identified factors; the averaged SDF outperforms existing models in
  and out of sample. (Abstract.)
* **Tipping (2001), *Journal of Machine Learning Research*:** sparse
  Bayesian learning and ARD. (Standard reference; not re-checked here.)

## Against, and failure modes

* Factor selection is for cross-sectional stock books; priors and
  dynamics add tuning.

## Fit with volatility-ai

A stock-selection tool; this project has no stock universe. Reference
entry.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Bryzgalova, S., Huang, J., Julliard, C. (2023). *Journal of Finance*
  78(1), 487–557. Abstract.
* Tipping, M. E. (2001). "Sparse Bayesian Learning and the Relevance
  Vector Machine." *JMLR* 1. Not re-checked.
