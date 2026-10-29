# DDPG / TD3 Continuous-Control Trader

**Ledger ID RK347** · rank 347 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Reinforcement learning |
| Potential effectiveness rank | 347 (1 = strongest) |
| AI implementability rank | 256 (1 = easiest) |
| Retail advantage rank | 247 (1 = strongest) |
| Fit with this project | 🧪 research code (A1) · ❌ for now as a trader (A1) |
| Implemented in volatility-ai | **Research code.** The algorithm's update targets are in `research/catalog/rl_agents.py` (ledger A1); no trained agent. |
| Related ledger entries | RK346, RK372, A1, C-RL4 |

## In one paragraph

Train a deep RL agent to choose positions or portfolio weights directly
from market state, rewarded by profit or a risk-adjusted return. DDPG
learns a deterministic policy for continuous actions with an off-policy
critic; TD3 adds twin critics, delayed policy updates and target
smoothing to curb DDPG's overestimation (Lillicrap et al. 2016; Fujimoto
et al. 2018). FinRL packages these agents for trading; its authors'
ensemble of PPO, A2C and DDPG beat the Dow on Sharpe ratio in their own
back-test. The same group later showed many such profits are back-test
overfitting.

## Evidence

* **Yang, Liu, Zhong & Walid (2020), "Deep Reinforcement Learning for
  Automated Stock Trading: An Ensemble Strategy," ICAIF '20:** an
  ensemble of PPO, A2C and DDPG on the 30 Dow stocks beats each
  algorithm alone, the index and a minimum-variance portfolio on Sharpe
  ratio. The FinRL authors' own back-test. (Abstract.)
* **Gort, Liu, et al. (2022), "Deep Reinforcement Learning for
  Cryptocurrency Trading: Practical Approach to Address Backtest
  Overfitting" (arXiv 2209.05559):** earlier DRL trading profits may be
  false positives from overfitting; the authors estimate each agent's
  probability of backtest overfitting and discard the overfitted ones,
  which then do better out of sample. (Abstract.)
* **Hambly, Xu & Yang (2023), "Recent Advances in Reinforcement Learning
  in Finance," *Mathematical Finance* 33(3), 437–503:** survey of RL for
  execution, portfolios, hedging, market making and routing. (Abstract.)

## Against, and failure modes

* Agents overfit the back-test; reported profits are often false
  positives (Gort et al.).
* Reward design, hyperparameters and seeds move results more than the
  algorithm does.

## Fit with volatility-ai

Deep RL agents are rejected for now in this project (ledger A1): far
more free parameters than the repository's multiple-comparison
discipline can support, and few correction episodes in the data to learn
from. An agent that chose lot sizes at grid triggers would also need the
no-loss guard around it, leaving it only the size decision, which V13's
supervised model already makes with far fewer parameters.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Fujimoto, S., van Hoof, H., Meger, D. (2018). "Addressing Function
  Approximation Error in Actor-Critic Methods." ICML.
  <https://arxiv.org/abs/1802.09477>.
* Yang, H., Liu, X.-Y., Zhong, S., Walid, A. (2020). "Deep Reinforcement
  Learning for Automated Stock Trading: An Ensemble Strategy." ICAIF
  '20. Abstract.
* Gort, B., Liu, X.-Y., et al. (2022).
  <https://arxiv.org/abs/2209.05559>. Abstract.
* This repository: `research/catalog/rl_agents.py` (A1).
