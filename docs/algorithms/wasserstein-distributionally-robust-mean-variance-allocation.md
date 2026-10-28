# Wasserstein Distributionally Robust Mean-Variance Allocation

**Ledger ID RK225** · rank 225 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Robust statistics / Mean-variance optimization |
| Potential effectiveness rank | 225 (1 = strongest) |
| AI implementability rank | 78 (1 = easiest) |
| Retail advantage rank | 147 (1 = strongest) |
| Fit with this project | ⏳ for a multi-ETF book (long-only weights) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK88, RK233, RK61 |

## In one paragraph

Choose weights that minimise variance under the worst return
distribution within a Wasserstein ball around the empirical one.
Blanchet, Chen and Zhou show this is empirical variance minimisation
plus a regularisation term, with the ball's radius chosen from data;
their S&P 500 back-tests compare it with Fama-French and Black-Litterman
benchmarks. The CSV's reference, arXiv 1805.08765, looks like a
placeholder ID (like arXiv 1908.01234 on RK97) and could not be
identified.

## The rule

```text
min_w max_(Q: W(Q, P_hat) <= delta) Var_Q(w'R)  s.t. min_(Q) E_Q[w'R] >= alpha, 1'w = 1, w >= 0
equivalent: min_w sqrt(w' Sigma_hat w) + sqrt(delta) ||w||_2 (a regularised empirical problem)
```

## Evidence

* **Blanchet, Chen & Zhou (2022), "Distributionally Robust Mean-Variance
  Portfolio Selection with Wasserstein Distances," *Management Science*
  68(9), 6382–6410:** the robust problem reduces to empirical variance
  minimisation plus a regularisation term, with the ambiguity radius and
  robust target return chosen from data; S&P 500 back-tests against
  Fama-French and Black-Litterman benchmarks. (Abstract.)
* **Mohajerin Esfahani & Kuhn (2018):** the general Wasserstein DRO
  framework (see RK88).

## Against, and failure modes

* The radius drives everything; regularised variance minimisation
  behaves much like shrinkage.

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
