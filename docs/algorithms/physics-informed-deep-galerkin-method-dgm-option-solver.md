# Physics-Informed Deep Galerkin Method (DGM) Option Solver

**Ledger ID RK302** · rank 302 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Physics-informed neural networks / Options pricing |
| Potential effectiveness rank | 302 (1 = strongest) |
| AI implementability rank | 281 (1 = easiest) |
| Retail advantage rank | 283 (1 = strongest) |
| Fit with this project | ⛔ (options pricing) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK350, RK374 |

## In one paragraph

Solve an option-pricing PDE with a deep network trained on randomly
sampled points to satisfy the differential operator and boundary
conditions, with no mesh (the Deep Galerkin Method). It scales to
American options in up to 200 dimensions, where grids fail. It is a
numerical method for pricing, not a trading strategy.

## Evidence

* **Sirignano & Spiliopoulos (2018), "DGM: A deep learning algorithm for
  solving partial differential equations," *Journal of Computational
  Physics* (arXiv 1708.07469, the CSV's reference):** American options
  in up to 200 dimensions (100 in v1), a high-dimensional HJB equation
  and Burgers' equation. (Abstract.)

## Against, and failure modes

* Accuracy is hard to certify; the network must be retrained for new
  parameters.

## Fit with volatility-ai

Options are outside the owner's instrument rule (long-only stocks and
ETFs), and the engine has no options data or pricing.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Sirignano, J., Spiliopoulos, K. (2018). *Journal of Computational
  Physics*. doi:10.1016/j.jcp.2018.08.029.
  <https://arxiv.org/abs/1708.07469>. Abstract.
