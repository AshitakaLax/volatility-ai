# Deep Recurrent Attentive Execution Agent (DR-Attn-Exec)

**Ledger ID RK425** · rank 425 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-29

| | |
|---|---|
| Family | Reinforcement learning / Attention mechanisms / Optimal execution |
| Potential effectiveness rank | 425 (1 = strongest) |
| AI implementability rank | 5,369 (1 = easiest) |
| Retail advantage rank | 10,334 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **Research code** in `research.catalog.execution`: `AttentiveExecutionPolicy`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK312, RK419 |

## In one paragraph

Schedule liquidation with a recurrent RL agent that attends over
multi-level order-book depth. RL execution has evidence (RK312, RK419);
I found no study of this specific form. The CSV's reference, arXiv
2105.04321, could not be identified.

## Evidence

* **Ning, Lin & Jaimungal (2021), *Applied Mathematical Finance*
  28(4):** double DQN beats the standard execution benchmark on most of
  nine stocks (see RK312). (Abstract.)
* **Fang et al. (2021), "Universal Trading for Order Execution with
  Oracle Policy Distillation," AAAI 35(1), 107–115 (arXiv 2103.10860):**
  a teacher policy with perfect future information guides a student that
  sees only the noisy market state; significant gains over strong
  baselines in the authors' tests on Chinese stocks. (Abstract.)

## Against, and failure modes

* Trained on replayed or simulated books that ignore the agent's own
  impact; gains matter only for large orders.

## Fit with volatility-ai

The grid's orders are small against TQQQ's daily volume, price-triggered
and single-venue; there is no parent order to schedule and no impact
worth modelling.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Ning, B., Lin, F. H. T., Jaimungal, S. (2021).
  <https://arxiv.org/abs/1812.06600>. Abstract.
* Fang, Y., Ren, K., Liu, W., Zhou, D., Zhang, W., Bian, J., Yu, Y.,
  Liu, T.-Y. (2021). AAAI 35(1), 107–115.
  <https://arxiv.org/abs/2103.10860>. Abstract.
