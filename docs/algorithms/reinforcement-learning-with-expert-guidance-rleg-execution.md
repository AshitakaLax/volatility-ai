# Reinforcement Learning with Expert Guidance (RLEG) Execution

**Ledger ID RK419** · rank 419 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-29

| | |
|---|---|
| Family | Reinforcement learning / Optimal execution |
| Potential effectiveness rank | 419 (1 = strongest) |
| AI implementability rank | 369 (1 = easiest) |
| Retail advantage rank | 8,378 (1 = strongest) |
| Fit with this project | ⛔ (large-order execution; RL rejected for now, A1) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK312, RK363, A1 |

## In one paragraph

Stabilise an RL execution agent by imitating expert schedules (TWAP,
VWAP or a human trader) before or while it optimises cost. The closest
published form uses an oracle teacher with perfect future information to
guide a student that sees only the noisy market state, and reports
significant gains over strong baselines.

## Evidence

* **Fang et al. (2021), "Universal Trading for Order Execution with
  Oracle Policy Distillation," AAAI 35(1), 107–115 (arXiv 2103.10860):**
  a teacher policy with perfect future information guides a student that
  sees only the noisy market state; significant gains over strong
  baselines in the authors' tests on Chinese stocks. (Abstract.)
* **Ning, Lin & Jaimungal (2021), *Applied Mathematical Finance*
  28(4):** double DQN beats the standard execution benchmark on most of
  nine stocks (see RK312). (Abstract.)

## Against, and failure modes

* Imitation anchors the agent to its teacher's mistakes; gains are a
  fraction of the spread and matter for large parent orders.

## Fit with volatility-ai

The grid's orders are small against TQQQ's daily volume, price-triggered
and single-venue; there is no parent order to schedule and no impact
worth modelling.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Fang, Y., Ren, K., Liu, W., Zhou, D., Zhang, W., Bian, J., Yu, Y.,
  Liu, T.-Y. (2021). AAAI 35(1), 107–115.
  <https://arxiv.org/abs/2103.10860>. Abstract.
* Ning, B., Lin, F. H. T., Jaimungal, S. (2021).
  <https://arxiv.org/abs/1812.06600>. Abstract.
