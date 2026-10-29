# Physics-Informed Deep Learning Schrödinger Volatility Solver

**Ledger ID RK350** · rank 350 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Physics-informed neural networks (PINN) / Derivatives pricing |
| Potential effectiveness rank | 350 (1 = strongest) |
| AI implementability rank | 697 (1 = easiest) |
| Retail advantage rank | 10,223 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK302, RK374 |

## In one paragraph

Model volatility as the solution of the Schrödinger equation and fit it
with a physics-informed network trained on the equation's residual.
PINNs are established, and the Schrödinger equation is one of their
textbook examples; I found no reason or study for volatility to follow
it.

## Evidence

* **Raissi, Perdikaris & Karniadakis (2019), physics-informed neural
  networks, *Journal of Computational Physics* 378 (arXiv 1711.10561,
  the CSV's reference for RK374):** networks trained to satisfy a PDE's
  residual; the Burgers and Schrödinger equations are among the paper's
  own examples. (Standard reference.)
* **No volatility study found.**

## Against, and failure modes

* No economic mechanism makes volatility obey the Schrödinger equation.

## Fit with volatility-ai

No mechanism and no evidence. Not a candidate.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Raissi, M., Perdikaris, P., Karniadakis, G. E. (2019). *Journal of
  Computational Physics* 378. <https://arxiv.org/abs/1711.10561>.
