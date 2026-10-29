# Quantum Neural Network (QNN) Volatility Surface Forecaster

**Ledger ID RK393** · rank 393 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Quantum machine learning / Derivatives forecasting |
| Potential effectiveness rank | 393 (1 = strongest) |
| AI implementability rank | 3,190 (1 = easiest) |
| Retail advantage rank | 10,700 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK375, RK387 |

## In one paragraph

Forecast implied-volatility surfaces with a parameterised quantum
circuit. Quantum kernels have been demonstrated on toy problems built to
suit them; a survey of quantum computing for finance finds speed-ups
possible in principle but far from practical, and I found no study of
this use. The CSV's reference, arXiv 2103.01234, is a black-hole physics
paper ("Hidden Symmetry of Vanishing Love"), unrelated to trading.

## Evidence

* **Havlíček et al. (2019), "Supervised learning with quantum-enhanced
  feature spaces," *Nature* 567, 209–212:** quantum kernel and
  variational classifiers on a superconducting processor, on a toy
  dataset built to suit them. (Standard reference.)
* **Herman et al. (2023), "Quantum computing for finance," *Nature
  Reviews Physics* 5, 450–465:** quantum Monte Carlo integration and
  gradient estimation offer up to a quadratic speed-up in principle, but
  the resources needed must fall a long way before any practical
  advantage; quantum machine learning carries its general strengths and
  difficulties over to finance. (Abstract and key points.)

## Against, and failure modes

* Noisy small devices; classical kernels match quantum kernels on real
  data so far.

## Fit with volatility-ai

Options are outside the owner's instrument rule (long-only stocks and
ETFs), and the engine has no options data or pricing.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Havlíček, V., et al. (2019). *Nature* 567, 209–212.
* Herman, D., et al. (2023). "Quantum computing for finance." *Nature
  Reviews Physics* 5, 450–465. doi:10.1038/s42254-023-00603-1.
  <https://arxiv.org/abs/2307.11230>. Abstract.
