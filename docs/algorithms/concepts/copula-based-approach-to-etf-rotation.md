# Copula-based approach to ETF rotation

**Concept page** · shared by **13** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #3,823) ·
researched 2026-10-30

| | |
|---|---|
| Task | ETF rotation |
| Method | Copula models of dependence |
| Fit with this project | ⏳ reference only · background, nothing to build now |
| Useful for volatility-ai | **Reference only.** A copula model could rank or weight the rotation, but no study shows it beating plain relative strength with an absolute-momentum filter; background until X3 is measured. |
| Implemented in volatility-ai | `tools/rotation.py` runs relative strength (X3), defensive rotation (X2), dual momentum (RK3) and HRP weights (A5); Faber's moving-average filter is built (`tactical_allocation`, C-E2, RK17). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | X3, X2, RK3, RK17, C-E2, A5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Copula Scholarly ETF
Rotation Model Ref-295") combine a method word, "Scholarly", a task and
a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Rank a defined ETF universe by momentum, trend or risk and rotate on a
fixed schedule, with a defensive asset and a cost model. The
copula-based version models joint and tail dependence between assets
separately from each asset's own distribution. I found no study of this
method on this task.

## The CSV's description

Proposed copula-based approach to ETF rotation: Rank a defined ETF
universe using a specified momentum, trend, or risk signal and rotate
exposure on a fixed schedule, with a defined defensive allocation and
trading-cost model. This is a concept-level interpretation of the title,
not a complete trading specification: the exact model inputs/target,
calibration, entry/exit or rebalance rules, and position sizing are not
fully defined here.

## Evidence

* **Faber (2007), "A Quantitative Approach to Tactical Asset
  Allocation":** a 10-month moving-average filter across asset classes
  gave comparable returns with much lower volatility and drawdown (see
  RK17). (Summaries.)
* **Antonacci (2012, published 2017), "Risk Premia Harvesting Through
  Dual Momentum":** relative strength picks the asset, absolute momentum
  against T-bills decides whether to hold it (see RK3). (Paper summary.)

## Against, and failure modes

* Rotation results depend heavily on the universe and the rebalance day;
  many published variants are fitted on the same few decades.
* Momentum-based rotation lags turning points and whipsaws in sideways
  markets.
* Copula families and parameters are hard to pin down from the few joint
  extremes the data hold.

## Fit with volatility-ai

Built as X3 (relative-strength rotation), X2 (defensive rotation), RK3
(dual momentum) and C-E2 (Faber TAA), none yet measured. A rotation
sleeve sits beside the TQQQ grid.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Faber, M. T. (2007). "A Quantitative Approach to Tactical Asset
  Allocation." *Journal of Wealth Management*. Summaries; see RK17.
* Antonacci, G. (2017). "Risk Premia Harvesting Through Dual Momentum."
  See RK3.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 3823 | Copula Scholarly ETF Rotation Model Ref-295 | Neural SDEs / Adversarial robustness / Stock options hedging | 10567 | 9384 | No |
| 3909 | Copula Scholarly ETF Rotation Model Ref-775 | Neural SDEs / Adversarial robustness / Stock options hedging | 10569 | 9390 | No |
| 7466 | Copula Scholarly ETF Rotation Model Ref-199 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10050 | 3060 | No |
| 7500 | Copula Scholarly ETF Rotation Model Ref-679 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10060 | 3177 | No |
| 8390 | Copula-Based Scholarly ETF Rotation Engine MK-11 | Delay differential equations / Jump diffusion / Stock trading | 13599 | 13684 | No |
| 8408 | Copula-Based Scholarly ETF Rotation Engine MK-71 | Delay differential equations / Jump diffusion / Stock trading | 13601 | 13687 | No |
| 8678 | Copula Scholarly ETF Rotation Model Ref-7 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12822 | 12533 | No |
| 8716 | Copula Scholarly ETF Rotation Model Ref-103 | Topological data analysis / Betti persistence / Stock pairs | 4650 | 3037 | No |
| 8830 | Copula Scholarly ETF Rotation Model Ref-391 | Delay differential equations / Controlled ODEs / Stock execution | 5844 | 3107 | No |
| 8869 | Copula Scholarly ETF Rotation Model Ref-487 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12827 | 12546 | No |
| 8907 | Copula Scholarly ETF Rotation Model Ref-583 | Topological data analysis / Betti persistence / Stock pairs | 4677 | 3154 | No |
| 9021 | Copula Scholarly ETF Rotation Model Ref-871 | Delay differential equations / Controlled ODEs / Stock execution | 5869 | 3224 | No |
| 9060 | Copula Scholarly ETF Rotation Model Ref-967 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12832 | 12559 | No |
