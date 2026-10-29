# Multi-Agent Reinforcement Learning Nash Market Maker

**Ledger ID RK339** · rank 339 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Multi-agent reinforcement learning / Game theory / Market making |
| Potential effectiveness rank | 339 (1 = strongest) |
| AI implementability rank | 987 (1 = easiest) |
| Retail advantage rank | 10,336 (1 = strongest) |
| Fit with this project | ⛔ (two-sided quoting; no evidence) |
| Implemented in volatility-ai | **Research code** in `research.catalog.market_making`: `duopoly_payoffs`, `fictitious_play`, `nash_spread`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK361, RK341 |

## In one paragraph

Train several market-making agents together until their quoting policies
reach a Nash equilibrium, where none gains by changing its quotes alone.
Multi-agent market-making simulators exist (Ganesh et al.); I found no
study showing a Nash-equilibrium learner trading profitably.

## Evidence

* **Ganesh et al. (2019), "Reinforcement Learning for Market Making in a
  Multi-agent Dealer Market" (JPMorgan, arXiv 1911.05892):** in a
  simulated OTC dealer market the agent learns to read a competitor's
  pricing, skews quotes to manage inventory and leans with the price
  drift; risk-averse reward formulations tested. Simulator results.
  (Abstract.)
* **No Nash-equilibrium market-making performance study found.**

## Against, and failure modes

* Results come from simulators whose other agents the authors designed.
* Two-sided quoting needs inventory to sell and a short-capable account.
* Multi-agent learning need not converge, and a learned equilibrium
  depends on the simulated population.

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
