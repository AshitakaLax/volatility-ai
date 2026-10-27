# Causal Discovery Directed Acyclic Graph (DAG) Pair Selection

**Ledger ID RK100** · rank 100 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Causal inference / statistical arbitrage |
| Potential effectiveness rank | 100 (1 = strongest) |
| AI implementability rank | 324 (1 = easiest) |
| Retail advantage rank | 6,478 (1 = strongest) |
| Fit with this project | ⛔ (pairs need a short leg) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK37, RK72 |

## In one paragraph

Run a causal-discovery algorithm (PC, NOTEARS, PCMCI) over stock returns
to infer a directed graph, then choose pairs, or leader→follower trades,
from direct causal links rather than correlation, which breaks in
shocks. I found no study that uses the PC algorithm or NOTEARS to select
pairs. The nearest published work is a lead-lag method on minute-level
S&P 500 data (Stübinger 2019) and a small PCMCI study on nine stocks over
three months.

## The rule

```
returns (with lags) -> PC / PCMCI / NOTEARS -> DAG of directed edges
candidate pairs = assets joined by a direct edge (not a common cause); trade the follower on the leader's move, or trade the pair's spread
```

## Evidence

* **Stübinger (2019), "Statistical arbitrage with optimal causal paths on
  high-frequency data of the S&P 500," *Quantitative Finance* 19(6),
  921–935:** lead-lag paths between stocks on minute data, trading the
  follower on the leader. Strong backtests reported by the author.
  (Summary.)
* **Letteri (arXiv 2507.09347):** Granger causality, PCMCI and transfer
  entropy on nine stocks, June–August 2023. (Summary.)
* **No PC- or NOTEARS-based pair-selection study found.** The
  algorithms themselves: Spirtes, Glymour & Scheines (2000), *Causation,
  Prediction, and Search* (PC), and Zheng et al. (2018), "DAGs with NO
  TEARS," NeurIPS (NOTEARS).

## Against, and failure modes

* Unobserved confounders and the sampling frequency change the graph (the
  CSV's caveat); causal discovery on returns has low power.

## Fit with volatility-ai

Out of scope.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Stübinger, J. (2019). *Quantitative Finance* 19(6), 921–935.
  <https://ideas.repec.org/a/taf/quantf/v19y2019i6p921-935.html>.
  Summary.
* Letteri, I. arXiv 2507.09347. Summary.
* The CSV's references: DoWhy; Tetrad.
