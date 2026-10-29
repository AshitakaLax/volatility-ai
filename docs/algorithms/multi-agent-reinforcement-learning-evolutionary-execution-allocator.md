# Multi-Agent Reinforcement Learning Evolutionary Execution Allocator

**Ledger ID RK360** · rank 360 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Multi-agent reinforcement learning / Evolutionary algorithms / Execution |
| Potential effectiveness rank | 360 (1 = strongest) |
| AI implementability rank | 387 (1 = easiest) |
| Retail advantage rank | 10,237 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **Research code** in `research.catalog.execution`: `evolve_execution`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK358, RK310 |

## In one paragraph

Evolve a population of RL agents that allocate a parent order over time
and venues. RL execution has evidence (RK312); I found no study adding
evolutionary multi-agent search, which compounds the over-fitting risk.

## Evidence

* **Ning, Lin & Jaimungal (2021), "Double Deep Q-Learning for Optimal
  Execution," *Applied Mathematical Finance* 28(4), 361–380 (arXiv
  1812.06600):** double DQN on order-book state outperforms the standard
  benchmark on most of nine stocks by mean and median out-performance,
  probability of out-performance and gain-loss ratio. (Abstract.)
* **No study found** of evolutionary multi-agent execution.

## Against, and failure modes

* Agents are trained and tested on replayed or simulated books; replay
  ignores the agent's own impact.
* The benchmark gain is a fraction of the spread; it matters for large
  parent orders, not small ones.
* Two search procedures stacked (see RK227).

## Fit with volatility-ai

The grid's orders are small against TQQQ's daily volume, price-triggered
and single-venue; there is no parent order to schedule and no impact
worth modelling. Alpaca routes orders itself.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Ning, B., Lin, F. H. T., Jaimungal, S. (2021). *Applied Mathematical
  Finance* 28(4), 361–380. <https://arxiv.org/abs/1812.06600>. Abstract.
