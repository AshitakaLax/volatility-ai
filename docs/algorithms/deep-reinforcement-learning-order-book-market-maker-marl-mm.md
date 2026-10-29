# Deep Reinforcement Learning Order Book Market Maker (Marl-MM)

**Ledger ID RK361** · rank 361 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Multi-agent reinforcement learning / Market making |
| Potential effectiveness rank | 361 (1 = strongest) |
| AI implementability rank | 381 (1 = easiest) |
| Retail advantage rank | 10,226 (1 = strongest) |
| Fit with this project | ⛔ (two-sided quoting; simulator-only evidence) |
| Implemented in volatility-ai | **Research code** in `research.catalog.market_making`: `train_competing_dqn_makers`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK313, RK339 |

## In one paragraph

A deep RL market maker trained against other learning agents in a
simulated order book. The multi-agent dealer study is the clearest
example: the agent learned to model a competitor's pricing and skew its
quotes.

## Evidence

* **Ganesh et al. (2019), "Reinforcement Learning for Market Making in a
  Multi-agent Dealer Market" (JPMorgan, arXiv 1911.05892):** in a
  simulated OTC dealer market the agent learns to read a competitor's
  pricing, skews quotes to manage inventory and leans with the price
  drift; risk-averse reward formulations tested. Simulator results.
  (Abstract.)
* **Spooner, Fearnley, Savani & Koukorinis (2018), "Market Making via
  Reinforcement Learning," AAMAS (arXiv 1804.04216):**
  temporal-difference learning with tile coding and an
  inventory-penalising reward in a high-fidelity order-book simulator;
  beats simple benchmarks and an online-learning method. Simulator
  results. (Abstract.)

## Against, and failure modes

* Results come from simulators whose other agents the authors designed.
* Two-sided quoting needs inventory to sell and a short-capable account.

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

* Ganesh, S., Vadori, N., Xu, M., Zheng, H., Reddy, P., Veloso, M.
  (2019). <https://arxiv.org/abs/1911.05892>. Abstract.
* Spooner, T., Fearnley, J., Savani, R., Koukorinis, A. (2018). "Market
  Making via Reinforcement Learning." AAMAS.
  <https://arxiv.org/abs/1804.04216>. Abstract.
