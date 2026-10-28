# Wasserstein Distributionally Robust Reinforcement Learning Portfolio Agent

**Ledger ID RK234** · rank 234 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Robust reinforcement learning / Portfolio allocation |
| Potential effectiveness rank | 234 (1 = strongest) |
| AI implementability rank | 349 (1 = easiest) |
| Retail advantage rank | 150 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK225, RK220, RK227 |

## In one paragraph

Train a deep reinforcement-learning portfolio agent against the worst
state-transition model in a Wasserstein ball, so its policy survives
regime shifts. Distributionally robust RL is an active research area; I
found no portfolio study with out-of-sample results. The CSV's
reference, arXiv 2110.09876, looks like a placeholder ID (like arXiv
1908.01234 on RK97) and could not be identified.

## Evidence

* **Blanchet, Chen & Zhou (2022), "Distributionally Robust Mean-Variance
  Portfolio Selection with Wasserstein Distances," *Management Science*
  68(9), 6382–6410:** the robust problem reduces to empirical variance
  minimisation plus a regularisation term, with the ambiguity radius and
  robust target return chosen from data; S&P 500 back-tests against
  Fama-French and Black-Litterman benchmarks. (Abstract.)
* **No portfolio study found** of Wasserstein-robust deep RL.

## Against, and failure modes

* Robust RL training is unstable and the ambiguity radius is arbitrary.

## Fit with volatility-ai

An allocator for a multi-asset book; the engine trades one symbol and
the allocator in ledger §11 is not built. Without published evidence, it
is not a candidate.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Blanchet, J., Chen, L., Zhou, X. Y. (2022). *Management Science*
  68(9), 6382–6410.
  <https://ideas.repec.org/a/inm/ormnsc/v68y2022i9p6382-6410.html>.
  Abstract.
