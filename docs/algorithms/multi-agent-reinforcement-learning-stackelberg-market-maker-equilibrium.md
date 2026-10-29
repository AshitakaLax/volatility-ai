# Multi-Agent Reinforcement Learning Stackelberg Market Maker Equilibrium

**Ledger ID RK344** · rank 344 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Multi-agent reinforcement learning / Game theory / Market making |
| Potential effectiveness rank | 344 (1 = strongest) |
| AI implementability rank | 991 (1 = easiest) |
| Retail advantage rank | 10,341 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK341, RK345, RK339 |

## In one paragraph

Solve for the Stackelberg equilibrium between a leading market maker and
following traders with multi-agent RL, as a model of how quotes should
be set. RL methods for Stackelberg equilibria exist, and one paper uses
a price-skewing market maker as a test environment; I found no
market-making performance study.

## Evidence

* **Stackelberg learning:** RL methods for leader-follower equilibria
  exist (Brero et al., arXiv 2210.03852; Zhong et al., arXiv
  2112.13521), and a Stackelberg mean-field-game paper uses a market
  maker skewing prices to steer traders as one test environment (arXiv
  2509.15392). None is a market-making performance study. (Abstracts.)
* **Ganesh et al. (2019), "Reinforcement Learning for Market Making in a
  Multi-agent Dealer Market" (JPMorgan, arXiv 1911.05892):** in a
  simulated OTC dealer market the agent learns to read a competitor's
  pricing, skews quotes to manage inventory and leans with the price
  drift; risk-averse reward formulations tested. Simulator results.
  (Abstract.)

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

* Brero, G., et al. <https://arxiv.org/abs/2210.03852>; Zhong, H., et
  al. <https://arxiv.org/abs/2112.13521>; Stackelberg MFG
  <https://arxiv.org/abs/2509.15392>. Abstracts.
* Ganesh, S., Vadori, N., Xu, M., Zheng, H., Reddy, P., Veloso, M.
  (2019). <https://arxiv.org/abs/1911.05892>. Abstract.
