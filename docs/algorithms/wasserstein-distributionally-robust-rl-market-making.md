# Wasserstein Distributionally Robust RL Market Making

**Ledger ID RK335** · rank 335 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Reinforcement learning / Robust statistics / Market making |
| Potential effectiveness rank | 335 (1 = strongest) |
| AI implementability rank | 2,038 (1 = easiest) |
| Retail advantage rank | 10,229 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **Research code** in `research.catalog.market_making`: `train_rl_market_maker`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK234, RK313 |

## In one paragraph

Train a market-making agent against the worst order-flow model inside a
Wasserstein ball around the estimated one, so its quotes survive regime
shifts. Robust market making has closed-form relatives (ambiguity-averse
Avellaneda-Stoikov variants); I found no Wasserstein-robust RL market
maker, and the CSV's reference, arXiv 2110.09876, is a particle-physics
review ("Light Sterile Neutrinos"), unrelated to trading.

## Evidence

* **Spooner, Fearnley, Savani & Koukorinis (2018), "Market Making via
  Reinforcement Learning," AAMAS (arXiv 1804.04216):**
  temporal-difference learning with tile coding and an
  inventory-penalising reward in a high-fidelity order-book simulator;
  beats simple benchmarks and an online-learning method. Simulator
  results. (Abstract.)
* **No study found** of Wasserstein-robust RL market making.

## Against, and failure modes

* Results come from simulators whose other agents the authors designed.
* Two-sided quoting needs inventory to sell and a short-capable account.
* The ambiguity radius is arbitrary and drives the result.

## Fit with volatility-ai

The grid is the buy-side, long-only relative of market making: resting
buys below the price and a sale of each lot at its own target above
cost. It cannot quote an ask without inventory, and the no-loss guard
forbids skewing a sale below cost. Deep RL agents are rejected for now
in this project (ledger A1): far more free parameters than the
repository's multiple-comparison discipline can support, and few
correction episodes in the data to learn from.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Spooner, T., Fearnley, J., Savani, R., Koukorinis, A. (2018). "Market
  Making via Reinforcement Learning." AAMAS.
  <https://arxiv.org/abs/1804.04216>. Abstract.
