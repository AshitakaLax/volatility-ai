# Graph Attention Network Dynamic Cointegration Basket Selection

**Ledger ID RK136** · rank 136 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Graph neural networks / Cointegration / Statistical arbitrage |
| Potential effectiveness rank | 136 (1 = strongest) |
| AI implementability rank | 292 (1 = easiest) |
| Retail advantage rank | 305 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** A short-leg basket trade with no study of the graph-attention selector. |
| Implemented in volatility-ai | **Research code** `research.catalog.stat_arb`: `cointegrated_triplets`; `research.catalog.spd_covariance`: `GATShrinkage`. |
| Related ledger entries | RK36, RK100, RK232 |

## In one paragraph

Build a network of cointegration relations and let a graph attention
network weigh them to pick baskets. The closest published work selects
pairs by maximum-weight graph matching on a cointegration graph, without
a neural network, and reports lower portfolio variance than greedy
selection.

## Evidence

* **Qureshi & Zaman (2024, arXiv 2403.07998):** pairs chosen by maximum
  weighted matching on a cointegration-weighted graph have lower
  variance than a cointegration-only baseline. (Abstract.)
* **No GNN pair-selection study found.**

## Against, and failure modes

* Cointegration graphs re-estimated each window are noisy; attention
  adds parameters to a selection step that already over-fits.

## Fit with volatility-ai

A relative-value trade between assets: it needs a short leg and a
universe of related instruments, and the engine trades one leveraged ETF
long-only. Out of scope as a strategy.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Qureshi, F., Zaman, A. (2024). Pairs Trading Using a Novel Graphical
  Matching Approach. <https://arxiv.org/abs/2403.07998>. Abstract.
