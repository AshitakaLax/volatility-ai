# Multi-Agent Reinforcement Learning Evolutionary Market Making Equilibrium

**Ledger ID RK359** · rank 359 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Multi-agent reinforcement learning / Evolutionary algorithms / Market making |
| Potential effectiveness rank | 359 (1 = strongest) |
| AI implementability rank | 386 (1 = easiest) |
| Retail advantage rank | 10,236 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK354, RK339 |

## In one paragraph

Let an evolving population of market-making agents settle into an
evolutionarily stable quoting equilibrium. Evolutionary search and
multi-agent RL are each common; I found no market-making study combining
them with out-of-sample results.

## Evidence

* **Ganesh et al. (2019), "Reinforcement Learning for Market Making in a
  Multi-agent Dealer Market" (JPMorgan, arXiv 1911.05892):** in a
  simulated OTC dealer market the agent learns to read a competitor's
  pricing, skews quotes to manage inventory and leans with the price
  drift; risk-averse reward formulations tested. Simulator results.
  (Abstract.)
* **No study found** of evolutionary multi-agent market makers.

## Against, and failure modes

* Results come from simulators whose other agents the authors designed.
* Two-sided quoting needs inventory to sell and a short-capable account.
* Two search procedures stacked: maximal data-snooping risk (see RK227).

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
