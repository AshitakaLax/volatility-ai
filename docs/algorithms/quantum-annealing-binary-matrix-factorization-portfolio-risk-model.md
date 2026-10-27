# Quantum Annealing Binary Matrix Factorization Portfolio Risk Model

**Ledger ID RK270** · rank 270 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Quantum computing / Matrix factorization / Risk management |
| Potential effectiveness rank | 270 (1 = strongest) |
| AI implementability rank | 261 (1 = easiest) |
| Retail advantage rank | 243 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK260, RK229 |

## In one paragraph

Factorise a risk-factor covariance into binary matrices by posing it as
a quadratic binary problem for a quantum annealer, to isolate latent
crash drivers. Binary matrix factorisation on annealers has been
explored in machine learning; I found no finance study. The CSV's
reference, arXiv 2103.01234, looks like a placeholder ID (like arXiv
1908.01234 on RK97) and could not be identified.

## Evidence

* **No finance study found** of annealer-based binary matrix
  factorisation for risk models.
* **Mugel et al. (2022), "Dynamic portfolio optimization with real
  datasets using quantum processors and quantum-inspired tensor
  networks," *Physical Review Research* 4(1), 013006:** 52 assets, eight
  years of daily prices; classical solvers, D-Wave hybrid annealing, two
  VQE variants on IBM hardware and a tensor-network optimiser compared
  on Sharpe ratio, profit and time; the hybrid annealer and tensor
  networks handled the largest instances (up to 1,272 fully connected
  qubits as a demonstration). (Abstract.)

## Against, and failure modes

* Binary factors are a strong restriction for continuous risk exposures.

## Fit with volatility-ai

This book trades one instrument; it has no combinatorial portfolio
problem for a quantum solver, and none of these studies shows an
advantage over classical optimisation at a useful scale.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Mugel, S., et al. (2022). *Physical Review Research* 4(1), 013006.
  <https://arxiv.org/abs/2007.00017>. Abstract.
