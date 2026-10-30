# Attention-weighted approach to ETF rotation

**Concept page** · shared by **69** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,235) ·
researched 2026-10-30

| | |
|---|---|
| Task | ETF rotation |
| Method | Attention networks |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of attention networks improving ETF rotation over relative strength with an absolute filter (X3, RK3). |
| Implemented in volatility-ai | `tools/rotation.py` runs relative strength (X3), defensive rotation (X2), dual momentum (RK3) and HRP weights (A5); Faber's moving-average filter is built (`tactical_allocation`, C-E2, RK17). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | X3, X2, RK3, RK17, C-E2, A5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Attentional Scholarly ETF
Rotation Model Sys-425") combine a method word, "Scholarly", a task and
a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Rank a defined ETF universe by momentum, trend or risk and rotate on a
fixed schedule, with a defensive asset and a cost model. The attention
version weights its inputs with a learned attention network. I found no
study of this method on this task.

## The CSV's description

Proposed attention-weighted approach to ETF rotation: Rank a defined ETF
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
* Attention networks need far more data than daily bars of a few ETFs
  provide.

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
| 1235 | Attentional Scholarly ETF Rotation Model Sys-425 | Rough path theory / Tensor signatures / Stock trend forecasting | 8357 | 7656 | No |
| 1252 | Attentional Scholarly ETF Rotation Model Sys-905 | Rough path theory / Tensor signatures / Stock trend forecasting | 8397 | 7678 | No |
| 1269 | Attentional Scholarly ETF Rotation Model Sys-1385 | Rough path theory / Tensor signatures / Stock trend forecasting | 8437 | 7700 | No |
| 1286 | Attentional Scholarly ETF Rotation Model Sys-1865 | Rough path theory / Tensor signatures / Stock trend forecasting | 8477 | 7722 | No |
| 3216 | Attentional Scholarly ETF Rotation Model Sys-137 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6591 | 6595 | No |
| 3238 | Attentional Scholarly ETF Rotation Model Sys-617 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6630 | 6631 | No |
| 3260 | Attentional Scholarly ETF Rotation Model Sys-1097 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6669 | 6667 | No |
| 3282 | Attentional Scholarly ETF Rotation Model Sys-1577 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6708 | 6703 | No |
| 4012 | Attentional Scholarly ETF Rotation Model Sys-329 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6608 | 8491 | No |
| 4098 | Attentional Scholarly ETF Rotation Model Sys-809 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6647 | 8526 | No |
| 4184 | Attentional Scholarly ETF Rotation Model Sys-1289 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6686 | 8561 | No |
| 4270 | Attentional Scholarly ETF Rotation Model Sys-1769 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6725 | 8596 | No |
| 4391 | Attentional Scholarly ETF Rotation Model Mod-455 | Neural SDEs / Adversarial robustness / Stock options hedging | 10415 | 8647 | No |
| 4476 | Attentional Scholarly ETF Rotation Model Mod-935 | Neural SDEs / Adversarial robustness / Stock options hedging | 10423 | 8684 | No |
| 4561 | Attentional Scholarly ETF Rotation Model Mod-1415 | Neural SDEs / Adversarial robustness / Stock options hedging | 10431 | 8721 | No |
| 4646 | Attentional Scholarly ETF Rotation Model Mod-1895 | Neural SDEs / Adversarial robustness / Stock options hedging | 10439 | 8758 | No |
| 4731 | Attentional Scholarly ETF Rotation Model Mod-2375 | Neural SDEs / Adversarial robustness / Stock options hedging | 10447 | 8795 | No |
| 4816 | Attentional Scholarly ETF Rotation Model Mod-2855 | Neural SDEs / Adversarial robustness / Stock options hedging | 10455 | 8832 | No |
| 4901 | Attentional Scholarly ETF Rotation Model Mod-3335 | Neural SDEs / Adversarial robustness / Stock options hedging | 10463 | 8869 | No |
| 4986 | Attentional Scholarly ETF Rotation Model Mod-3815 | Neural SDEs / Adversarial robustness / Stock options hedging | 10471 | 8906 | No |
| 7523 | Attentional Scholarly ETF Rotation Model Sys-41 | Graph attention / Sector contagion / Stock baskets | 12276 | 13159 | No |
| 7554 | Attentional Scholarly ETF Rotation Model Sys-521 | Graph attention / Sector contagion / Stock baskets | 12286 | 13173 | No |
| 7585 | Attentional Scholarly ETF Rotation Model Sys-1001 | Graph attention / Sector contagion / Stock baskets | 12296 | 13187 | No |
| 7616 | Attentional Scholarly ETF Rotation Model Sys-1481 | Graph attention / Sector contagion / Stock baskets | 12306 | 13201 | No |
| 7647 | Attentional Scholarly ETF Rotation Model Sys-1961 | Graph attention / Sector contagion / Stock baskets | 12316 | 13215 | No |
| 7673 | Attentional Scholarly ETF Rotation Model Mod-359 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6774 | 8640 | No |
| 7705 | Attentional Scholarly ETF Rotation Model Mod-839 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6816 | 8677 | No |
| 7737 | Attentional Scholarly ETF Rotation Model Mod-1319 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6858 | 8714 | No |
| 7769 | Attentional Scholarly ETF Rotation Model Mod-1799 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6900 | 8751 | No |
| 7801 | Attentional Scholarly ETF Rotation Model Mod-2279 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6942 | 8788 | No |
| 7833 | Attentional Scholarly ETF Rotation Model Mod-2759 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6984 | 8825 | No |
| 7865 | Attentional Scholarly ETF Rotation Model Mod-3239 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7026 | 8862 | No |
| 7897 | Attentional Scholarly ETF Rotation Model Mod-3719 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7068 | 8899 | No |
| 8422 | Attention-Weighted Scholarly ETF Rotation Engine Ver-13 | Quantum computing / Adiabatic evolution / Stock index rebalancing | 7756 | 5934 | No |
| 8451 | Attention-Weighted Scholarly ETF Rotation Engine Ver-113 | Quantum computing / Adiabatic evolution / Stock index rebalancing | 13751 | 12782 | No |
| 8485 | Attentional Scholarly ETF Rotation Model Alpha-27 | Reinforcement learning / Policy gradient / ETF arbitrage | 4602 | 10710 | No |
| 8525 | Attentional Scholarly ETF Rotation Model Alpha-127 | Reinforcement learning / Policy gradient / ETF arbitrage | 12515 | 12514 | No |
| 8565 | Attentional Scholarly ETF Rotation Model Alpha-227 | Reinforcement learning / Policy gradient / ETF arbitrage | 10864 | 10720 | No |
| 8605 | Attentional Scholarly ETF Rotation Model Alpha-327 | Reinforcement learning / Policy gradient / ETF arbitrage | 4630 | 10724 | No |
| 8645 | Attentional Scholarly ETF Rotation Model Alpha-427 | Reinforcement learning / Policy gradient / ETF arbitrage | 12519 | 12529 | No |
| 9165 | Attentional Scholarly ETF Rotation Model Sys-233 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13780 | 12813 | No |
| 9352 | Attentional Scholarly ETF Rotation Model Sys-713 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13788 | 12825 | No |
| 9539 | Attentional Scholarly ETF Rotation Model Sys-1193 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13796 | 12837 | No |
| 9726 | Attentional Scholarly ETF Rotation Model Sys-1673 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13804 | 12849 | No |
| 9879 | Attentional Scholarly ETF Rotation Model Mod-71 | Delay differential equations / Controlled ODEs / Stock execution | 13217 | 13217 | No |
| 9915 | Attentional Scholarly ETF Rotation Model Mod-167 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10910 | 10873 | No |
| 9957 | Attentional Scholarly ETF Rotation Model Mod-263 | Topological data analysis / Betti persistence / Stock pairs | 11462 | 12030 | No |
| 10070 | Attentional Scholarly ETF Rotation Model Mod-551 | Delay differential equations / Controlled ODEs / Stock execution | 13229 | 13231 | No |
| 10106 | Attentional Scholarly ETF Rotation Model Mod-647 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10918 | 10892 | No |
| 10148 | Attentional Scholarly ETF Rotation Model Mod-743 | Topological data analysis / Betti persistence / Stock pairs | 11489 | 12053 | No |
| 10261 | Attentional Scholarly ETF Rotation Model Mod-1031 | Delay differential equations / Controlled ODEs / Stock execution | 13241 | 13245 | No |
| 10297 | Attentional Scholarly ETF Rotation Model Mod-1127 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10926 | 10911 | No |
| 10339 | Attentional Scholarly ETF Rotation Model Mod-1223 | Topological data analysis / Betti persistence / Stock pairs | 11516 | 12076 | No |
| 10452 | Attentional Scholarly ETF Rotation Model Mod-1511 | Delay differential equations / Controlled ODEs / Stock execution | 13253 | 13259 | No |
| 10488 | Attentional Scholarly ETF Rotation Model Mod-1607 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10934 | 10930 | No |
| 10530 | Attentional Scholarly ETF Rotation Model Mod-1703 | Topological data analysis / Betti persistence / Stock pairs | 11543 | 12099 | No |
| 10643 | Attentional Scholarly ETF Rotation Model Mod-1991 | Delay differential equations / Controlled ODEs / Stock execution | 13265 | 13273 | No |
| 10679 | Attentional Scholarly ETF Rotation Model Mod-2087 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10942 | 10949 | No |
| 10721 | Attentional Scholarly ETF Rotation Model Mod-2183 | Topological data analysis / Betti persistence / Stock pairs | 11570 | 12122 | No |
| 10834 | Attentional Scholarly ETF Rotation Model Mod-2471 | Delay differential equations / Controlled ODEs / Stock execution | 13277 | 13287 | No |
| 10870 | Attentional Scholarly ETF Rotation Model Mod-2567 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10950 | 10968 | No |
| 10912 | Attentional Scholarly ETF Rotation Model Mod-2663 | Topological data analysis / Betti persistence / Stock pairs | 11597 | 12145 | No |
| 11025 | Attentional Scholarly ETF Rotation Model Mod-2951 | Delay differential equations / Controlled ODEs / Stock execution | 13289 | 13301 | No |
| 11061 | Attentional Scholarly ETF Rotation Model Mod-3047 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10958 | 10987 | No |
| 11103 | Attentional Scholarly ETF Rotation Model Mod-3143 | Topological data analysis / Betti persistence / Stock pairs | 11624 | 12168 | No |
| 11216 | Attentional Scholarly ETF Rotation Model Mod-3431 | Delay differential equations / Controlled ODEs / Stock execution | 13301 | 13315 | No |
| 11252 | Attentional Scholarly ETF Rotation Model Mod-3527 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10966 | 11006 | No |
| 11294 | Attentional Scholarly ETF Rotation Model Mod-3623 | Topological data analysis / Betti persistence / Stock pairs | 11651 | 12191 | No |
| 11407 | Attentional Scholarly ETF Rotation Model Mod-3911 | Delay differential equations / Controlled ODEs / Stock execution | 13313 | 13329 | No |
