# Multi-Agent Deep Deterministic Policy Gradient (MADDPG) Portfolio Allocation

**Ledger ID RK351** · rank 351 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Reinforcement learning / Multi-agent allocation |
| Potential effectiveness rank | 351 (1 = strongest) |
| AI implementability rank | 308 (1 = easiest) |
| Retail advantage rank | 140 (1 = strongest) |
| Fit with this project | ⛔ (multi-asset allocator; weak evidence) |
| Implemented in volatility-ai | **Research code** in `research.catalog.deep_rl`: `MADDPGAllocator`, `MADDPG`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK227, RK346 |

## In one paragraph

Give each asset or sub-portfolio its own deep deterministic
policy-gradient agent, trained with critics that see all agents' actions
(MADDPG), and let them allocate jointly. In one study MADDPG did
markedly worse than a genetic algorithm on the same portfolio problem
(27.9% return and Sharpe 1.28 against 70.4% and 3.15), which the authors
put down to flat policy gradients.

## Evidence

* **Lowe et al. (2017), "Multi-Agent Actor-Critic for Mixed
  Cooperative-Competitive Environments," NeurIPS:** MADDPG. (Standard
  reference.)
* **"Balancing Profit, Risk, and Sustainability for Portfolio
  Management" (arXiv 2207.02134):** MADDPG returned about 27.9% (Sharpe
  1.28) against about 70.4% (Sharpe 3.15) for a genetic algorithm.
  (Table excerpt.)
* **CPPI-MADDPG and TIPP-MADDPG (arXiv 2303.11959):**
  portfolio-insurance variants on 100 shares generally beat their
  traditional counterparts. (Abstract.)

## Against, and failure modes

* Agents overfit the back-test; reported profits are often false
  positives (Gort et al.).
* Reward design, hyperparameters and seeds move results more than the
  algorithm does.

## Fit with volatility-ai

An allocator for a multi-asset book; the engine trades one symbol and
the allocator in ledger §11 is not built. Without published evidence, it
is not a candidate.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Lowe, R., et al. (2017). NeurIPS. <https://arxiv.org/abs/1706.02275>.
* <https://arxiv.org/abs/2207.02134>. Excerpt.
* <https://arxiv.org/abs/2303.11959>. Abstract.
