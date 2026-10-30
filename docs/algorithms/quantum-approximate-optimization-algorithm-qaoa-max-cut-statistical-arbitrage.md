# Quantum Approximate Optimization Algorithm (QAOA) Max-Cut Statistical Arbitrage

**Ledger ID RK184** · rank 184 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Quantum computing / Max-Cut / Statistical arbitrage |
| Potential effectiveness rank | 184 (1 = strongest) |
| AI implementability rank | 327 (1 = easiest) |
| Retail advantage rank | 1,707 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** A short-leg stock-universe trade on hardware with no demonstrated advantage. |
| Implemented in volatility-ai | **Research code** `research.catalog.quantum`: `qaoa`. |
| Related ledger entries | RK175, RK270, RK305 |

## In one paragraph

Split a cointegration graph into market-neutral clusters by Max-Cut,
solved with QAOA (Farhi et al., the CSV's reference). The combinatorial
step (partitioning, cuts, independent sets) is solved just as well by
classical heuristics at these sizes, and the strategy needs a stock
universe and short legs.

## Evidence

* **No quantum advantage for portfolio problems** has been shown: QAOA
  benchmarks (Brandhofer et al. 2023, *Quantum Information Processing*)
  study circuit choices and noise on toy portfolios. (Abstract.)
* **No study found** that tests this combination as a trading strategy.

## Against, and failure modes

* Today's quantum devices solve toy instances; classical annealing
  matches them.

## Fit with volatility-ai

A relative-value trade between assets: it needs a short leg and a
universe of related instruments, and the engine trades one leveraged ETF
long-only. Out of scope as a strategy.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Brandhofer, S. et al. (2023). Benchmarking the performance of
  portfolio optimization with QAOA. *Quantum Information Processing* 22.
  <https://arxiv.org/abs/2207.10555>. Abstract.
