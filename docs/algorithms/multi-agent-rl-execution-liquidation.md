# Multi-Agent RL Execution / Liquidation

**Ledger ID RK310** · rank 310 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Reinforcement learning / execution |
| Potential effectiveness rank | 310 (1 = strongest) |
| AI implementability rank | 368 (1 = easiest) |
| Retail advantage rank | 7,421 (1 = strongest) |
| Fit with this project | ⛔ (large-order liquidation; RL rejected for now, A1) |
| Implemented in volatility-ai | **Research code** in `research.catalog.execution`: `train_multi_agent_liquidation`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK312, RK358, A1 |

## In one paragraph

Train several execution agents together in a simulated order book, so
each learns to liquidate while the others trade too. In a multi-agent
ABIDES simulation a double-DQN execution agent converged toward TWAP in
some scenarios, which says the learned policy can collapse to the simple
schedule.

## Evidence

* **Karpe, Fang, Ma & Wang (2020), "Multi-Agent Reinforcement Learning
  in a Realistic Limit Order Book Market Simulation," ICAIF '20 (arXiv
  2006.05574):** a double-DQN execution agent in a multi-agent ABIDES
  simulation converges toward TWAP in some scenarios. (Abstract.)
* **Ning, Lin & Jaimungal (2021), "Double Deep Q-Learning for Optimal
  Execution," *Applied Mathematical Finance* 28(4), 361–380 (arXiv
  1812.06600):** double DQN on order-book state outperforms the standard
  benchmark on most of nine stocks by mean and median out-performance,
  probability of out-performance and gain-loss ratio. (Abstract.)

## Against, and failure modes

* Agents are trained and tested on replayed or simulated books; replay
  ignores the agent's own impact.
* The benchmark gain is a fraction of the spread; it matters for large
  parent orders, not small ones.

## Fit with volatility-ai

The grid's orders are small against TQQQ's daily volume, price-triggered
and single-venue; there is no parent order to schedule and no impact
worth modelling.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Karpe, M., Fang, J., Ma, Z., Wang, C. (2020). ICAIF '20.
  <https://arxiv.org/abs/2006.05574>. Abstract.
* Ning, B., Lin, F. H. T., Jaimungal, S. (2021). *Applied Mathematical
  Finance* 28(4), 361–380. <https://arxiv.org/abs/1812.06600>. Abstract.
