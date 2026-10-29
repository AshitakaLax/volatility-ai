# Physics-Informed Neural Operator (FNO) Yield Curve Dynamics

**Ledger ID RK323** · rank 323 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Physics-informed ML / Fourier Neural Operators / Fixed income |
| Potential effectiveness rank | 323 (1 = strongest) |
| AI implementability rank | 280 (1 = easiest) |
| Retail advantage rank | 188 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK226, RK287 |

## In one paragraph

Learn yield-curve dynamics with a Fourier neural operator constrained by
a term-structure PDE. The CSV's reference is the Fourier neural operator
paper itself (arXiv 2010.08895). I found no application of neural
operators here.

## Evidence

* **Li et al. (2021), Fourier Neural Operator (arXiv 2010.08895, the
  CSV's reference):** learns maps between function spaces for PDEs.
  (Standard reference.)
* **No finance study found.**

## Against, and failure modes

* A PDE-learning tool for low-dimensional, data-poor problems.

## Fit with volatility-ai

Rates and hedging have no use for this book.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Li, Z., et al. (2021). "Fourier Neural Operator for Parametric Partial
  Differential Equations." ICLR. <https://arxiv.org/abs/2010.08895>.
