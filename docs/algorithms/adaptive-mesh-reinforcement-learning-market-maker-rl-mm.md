# Adaptive Mesh Reinforcement Learning Market Maker (RL-MM)

**Ledger ID RK313** · rank 313 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Reinforcement learning / Market making |
| Potential effectiveness rank | 313 (1 = strongest) |
| AI implementability rank | 5,368 (1 = easiest) |
| Retail advantage rank | 11,671 (1 = strongest) |
| Fit with this project | ⛔ (two-sided quoting; simulator-only evidence) |
| Implemented in volatility-ai | **No.** Avellaneda-Stoikov and GLFT quotes exist as research code (C-MM1, C-MM2). |
| Related ledger entries | RK274, RK361, A1 |

## In one paragraph

Learn a market maker's quoting policy with reinforcement learning on a
discretised (or adaptively refined) grid of spread and skew actions,
rewarding spread capture and penalising inventory. In a high-fidelity
order-book simulator such an agent beat simple benchmarks; in a
multi-agent dealer simulator one learned to skew against inventory, the
behaviour Avellaneda-Stoikov derives in closed form.

## Evidence

* **Spooner, Fearnley, Savani & Koukorinis (2018), "Market Making via
  Reinforcement Learning," AAMAS (arXiv 1804.04216):**
  temporal-difference learning with tile coding and an
  inventory-penalising reward in a high-fidelity order-book simulator;
  beats simple benchmarks and an online-learning method. Simulator
  results. (Abstract.)
* **Ganesh et al. (2019), "Reinforcement Learning for Market Making in a
  Multi-agent Dealer Market" (JPMorgan, arXiv 1911.05892):** in a
  simulated OTC dealer market the agent learns to read a competitor's
  pricing, skews quotes to manage inventory and leans with the price
  drift; risk-averse reward formulations tested. Simulator results.
  (Abstract.)
* **Hambly, Xu & Yang (2023), "Recent Advances in Reinforcement Learning
  in Finance," *Mathematical Finance* 33(3), 437–503:** survey of RL for
  execution, portfolios, hedging, market making and routing. (Abstract.)

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

* Spooner, T., Fearnley, J., Savani, R., Koukorinis, A. (2018). "Market
  Making via Reinforcement Learning." AAMAS.
  <https://arxiv.org/abs/1804.04216>. Abstract.
* Ganesh, S., Vadori, N., Xu, M., Zheng, H., Reddy, P., Veloso, M.
  (2019). <https://arxiv.org/abs/1911.05892>. Abstract.
* Hambly, B., Xu, R., Yang, H. (2023). *Mathematical Finance* 33(3),
  437–503. <https://arxiv.org/abs/2112.04553>. Abstract.
