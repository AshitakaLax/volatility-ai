# Quantum Kernel-Based SVM Cross-Sectional Alpha Predictor

**Ledger ID RK387** · rank 387 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Quantum machine learning / Support vector machines / Alpha generation |
| Potential effectiveness rank | 387 (1 = strongest) |
| AI implementability rank | 367 (1 = easiest) |
| Retail advantage rank | 230 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **Research code** in `research.catalog.quantum`: `qsvm_predict`, `quantum_kernel`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK375, RK393 |

## In one paragraph

Classify stocks' next-period returns with a support vector machine on a
quantum kernel. Quantum kernels have been demonstrated on toy problems
built to suit them; a survey of quantum computing for finance finds
speed-ups possible in principle but far from practical, and I found no
study of this use.

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

A cross-sectional stock-selection model; this project trades one
leveraged index ETF and has no stock universe, fundamentals or relation
data.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Havlíček, V., et al. (2019). *Nature* 567, 209–212.
* Herman, D., et al. (2023). "Quantum computing for finance." *Nature
  Reviews Physics* 5, 450–465. doi:10.1038/s42254-023-00603-1.
  <https://arxiv.org/abs/2307.11230>. Abstract.
