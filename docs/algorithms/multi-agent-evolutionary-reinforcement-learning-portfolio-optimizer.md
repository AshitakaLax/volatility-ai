# Multi-Agent Evolutionary Reinforcement Learning Portfolio Optimizer

**Ledger ID RK227** · rank 227 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Evolutionary algorithms / Reinforcement learning / Portfolio construction |
| Potential effectiveness rank | 227 (1 = strongest) |
| AI implementability rank | 265 (1 = easiest) |
| Retail advantage rank | 99 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK220, RK234 |

## In one paragraph

Evolve populations of reinforcement-learning portfolio agents with
genetic algorithms to find allocations robust across regimes.
Evolutionary search and multi-agent RL are each common in finance
papers; I found no out-of-sample study of this combination. The CSV's
reference, arXiv 2006.09876, could not be identified.

## Evidence

* **No study found** with out-of-sample results for evolutionary
  multi-agent RL allocation.

## Against, and failure modes

* Two search procedures stacked: maximal data-snooping risk.

## Fit with volatility-ai

An allocator for a multi-asset book; the engine trades one symbol and
the allocator in ledger §11 is not built. Without published evidence, it
is not a candidate.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* The CSV's references: DEAP; arXiv 2006.09876 (not identified).
