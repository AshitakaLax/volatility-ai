# Robust approach to ETF rotation

**Concept page** · shared by **64** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,231) ·
researched 2026-10-30

| | |
|---|---|
| Task | ETF rotation |
| Method | Robust (outlier-resistant) estimation |
| Fit with this project | ⏳ reference only · background, nothing to build now |
| Useful for volatility-ai | **Reference only.** Robust estimation could rank or weight the rotation, but no study shows it beating plain relative strength with an absolute-momentum filter; background until X3 is measured. |
| Implemented in volatility-ai | `tools/rotation.py` runs relative strength (X3), defensive rotation (X2), dual momentum (RK3) and HRP weights (A5); Faber's moving-average filter is built (`tactical_allocation`, C-E2, RK17). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | X3, X2, RK3, RK17, C-E2, A5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Robust Scholarly ETF
Rotation Model Sys-305") combine a method word, "Scholarly", a task and
a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Rank a defined ETF universe by momentum, trend or risk and rotate on a
fixed schedule, with a defensive asset and a cost model. The robust
version estimates its inputs with outlier-resistant statistics, so a few
extreme days do not drive the result. I found no study of this method on
this task.

## The CSV's description

Proposed robust approach to ETF rotation: Rank a defined ETF universe
using a specified momentum, trend, or risk signal and rotate exposure on
a fixed schedule, with a defined defensive allocation and trading-cost
model. This is a concept-level interpretation of the title, not a
complete trading specification: the exact model inputs/target,
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
* Robust estimators trade efficiency for stability; in calm data they
  add little.

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
| 1231 | Robust Scholarly ETF Rotation Model Sys-305 | Rough path theory / Tensor signatures / Stock trend forecasting | 8346 | 7651 | No |
| 1248 | Robust Scholarly ETF Rotation Model Sys-785 | Rough path theory / Tensor signatures / Stock trend forecasting | 8386 | 7673 | No |
| 1265 | Robust Scholarly ETF Rotation Model Sys-1265 | Rough path theory / Tensor signatures / Stock trend forecasting | 8426 | 7695 | No |
| 1282 | Robust Scholarly ETF Rotation Model Sys-1745 | Rough path theory / Tensor signatures / Stock trend forecasting | 8466 | 7717 | No |
| 3210 | Robust Scholarly ETF Rotation Model Sys-17 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6581 | 6586 | No |
| 3232 | Robust Scholarly ETF Rotation Model Sys-497 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6620 | 6622 | No |
| 3254 | Robust Scholarly ETF Rotation Model Sys-977 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6659 | 6658 | No |
| 3276 | Robust Scholarly ETF Rotation Model Sys-1457 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6698 | 6694 | No |
| 3298 | Robust Scholarly ETF Rotation Model Sys-1937 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6737 | 6730 | No |
| 3991 | Robust Scholarly ETF Rotation Model Sys-209 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6598 | 8482 | No |
| 4077 | Robust Scholarly ETF Rotation Model Sys-689 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6637 | 8517 | No |
| 4163 | Robust Scholarly ETF Rotation Model Sys-1169 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6676 | 8552 | No |
| 4249 | Robust Scholarly ETF Rotation Model Sys-1649 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6715 | 8587 | No |
| 4329 | Robust Scholarly ETF Rotation Model Mod-95 | Neural SDEs / Adversarial robustness / Stock options hedging | 10409 | 8620 | No |
| 4414 | Robust Scholarly ETF Rotation Model Mod-575 | Neural SDEs / Adversarial robustness / Stock options hedging | 10417 | 8657 | No |
| 4499 | Robust Scholarly ETF Rotation Model Mod-1055 | Neural SDEs / Adversarial robustness / Stock options hedging | 10425 | 8694 | No |
| 4584 | Robust Scholarly ETF Rotation Model Mod-1535 | Neural SDEs / Adversarial robustness / Stock options hedging | 10433 | 8731 | No |
| 4669 | Robust Scholarly ETF Rotation Model Mod-2015 | Neural SDEs / Adversarial robustness / Stock options hedging | 10441 | 8768 | No |
| 4754 | Robust Scholarly ETF Rotation Model Mod-2495 | Neural SDEs / Adversarial robustness / Stock options hedging | 10449 | 8805 | No |
| 4839 | Robust Scholarly ETF Rotation Model Mod-2975 | Neural SDEs / Adversarial robustness / Stock options hedging | 10457 | 8842 | No |
| 4924 | Robust Scholarly ETF Rotation Model Mod-3455 | Neural SDEs / Adversarial robustness / Stock options hedging | 10465 | 8879 | No |
| 5009 | Robust Scholarly ETF Rotation Model Mod-3935 | Neural SDEs / Adversarial robustness / Stock options hedging | 10473 | 8916 | No |
| 7545 | Robust Scholarly ETF Rotation Model Sys-401 | Graph attention / Sector contagion / Stock baskets | 12284 | 13170 | No |
| 7576 | Robust Scholarly ETF Rotation Model Sys-881 | Graph attention / Sector contagion / Stock baskets | 12294 | 13184 | No |
| 7607 | Robust Scholarly ETF Rotation Model Sys-1361 | Graph attention / Sector contagion / Stock baskets | 12304 | 13198 | No |
| 7638 | Robust Scholarly ETF Rotation Model Sys-1841 | Graph attention / Sector contagion / Stock baskets | 12314 | 13212 | No |
| 7681 | Robust Scholarly ETF Rotation Model Mod-479 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6784 | 8649 | No |
| 7713 | Robust Scholarly ETF Rotation Model Mod-959 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6826 | 8686 | No |
| 7745 | Robust Scholarly ETF Rotation Model Mod-1439 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6868 | 8723 | No |
| 7777 | Robust Scholarly ETF Rotation Model Mod-1919 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6910 | 8760 | No |
| 7809 | Robust Scholarly ETF Rotation Model Mod-2399 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6952 | 8797 | No |
| 7841 | Robust Scholarly ETF Rotation Model Mod-2879 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6994 | 8834 | No |
| 7873 | Robust Scholarly ETF Rotation Model Mod-3359 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7036 | 8871 | No |
| 7905 | Robust Scholarly ETF Rotation Model Mod-3839 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7078 | 8908 | No |
| 8394 | Robust Scholarly ETF Rotation Engine MK-26 | Quantum machine learning / Support vector machines / Index forecasting | 13973 | 13970 | No |
| 8412 | Robust Scholarly ETF Rotation Engine MK-86 | Quantum machine learning / Support vector machines / Index forecasting | 13974 | 13971 | No |
| 9118 | Robust Scholarly ETF Rotation Model Sys-113 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13778 | 12810 | No |
| 9305 | Robust Scholarly ETF Rotation Model Sys-593 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13786 | 12822 | No |
| 9492 | Robust Scholarly ETF Rotation Model Sys-1073 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13794 | 12834 | No |
| 9679 | Robust Scholarly ETF Rotation Model Sys-1553 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13802 | 12846 | No |
| 9926 | Robust Scholarly ETF Rotation Model Mod-191 | Delay differential equations / Controlled ODEs / Stock execution | 13219 | 13220 | No |
| 9966 | Robust Scholarly ETF Rotation Model Mod-287 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10912 | 10877 | No |
| 10004 | Robust Scholarly ETF Rotation Model Mod-383 | Topological data analysis / Betti persistence / Stock pairs | 11468 | 12036 | No |
| 10117 | Robust Scholarly ETF Rotation Model Mod-671 | Delay differential equations / Controlled ODEs / Stock execution | 13231 | 13234 | No |
| 10157 | Robust Scholarly ETF Rotation Model Mod-767 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10920 | 10896 | No |
| 10195 | Robust Scholarly ETF Rotation Model Mod-863 | Topological data analysis / Betti persistence / Stock pairs | 11495 | 12059 | No |
| 10308 | Robust Scholarly ETF Rotation Model Mod-1151 | Delay differential equations / Controlled ODEs / Stock execution | 13243 | 13248 | No |
| 10348 | Robust Scholarly ETF Rotation Model Mod-1247 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10928 | 10915 | No |
| 10386 | Robust Scholarly ETF Rotation Model Mod-1343 | Topological data analysis / Betti persistence / Stock pairs | 11522 | 12082 | No |
| 10499 | Robust Scholarly ETF Rotation Model Mod-1631 | Delay differential equations / Controlled ODEs / Stock execution | 13255 | 13262 | No |
| 10539 | Robust Scholarly ETF Rotation Model Mod-1727 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10936 | 10934 | No |
| 10577 | Robust Scholarly ETF Rotation Model Mod-1823 | Topological data analysis / Betti persistence / Stock pairs | 11549 | 12105 | No |
| 10690 | Robust Scholarly ETF Rotation Model Mod-2111 | Delay differential equations / Controlled ODEs / Stock execution | 13267 | 13276 | No |
| 10730 | Robust Scholarly ETF Rotation Model Mod-2207 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10944 | 10953 | No |
| 10768 | Robust Scholarly ETF Rotation Model Mod-2303 | Topological data analysis / Betti persistence / Stock pairs | 11576 | 12128 | No |
| 10881 | Robust Scholarly ETF Rotation Model Mod-2591 | Delay differential equations / Controlled ODEs / Stock execution | 13279 | 13290 | No |
| 10921 | Robust Scholarly ETF Rotation Model Mod-2687 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10952 | 10972 | No |
| 10959 | Robust Scholarly ETF Rotation Model Mod-2783 | Topological data analysis / Betti persistence / Stock pairs | 11603 | 12151 | No |
| 11072 | Robust Scholarly ETF Rotation Model Mod-3071 | Delay differential equations / Controlled ODEs / Stock execution | 13291 | 13304 | No |
| 11112 | Robust Scholarly ETF Rotation Model Mod-3167 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10960 | 10991 | No |
| 11150 | Robust Scholarly ETF Rotation Model Mod-3263 | Topological data analysis / Betti persistence / Stock pairs | 11630 | 12174 | No |
| 11263 | Robust Scholarly ETF Rotation Model Mod-3551 | Delay differential equations / Controlled ODEs / Stock execution | 13303 | 13318 | No |
| 11303 | Robust Scholarly ETF Rotation Model Mod-3647 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10968 | 11010 | No |
| 11341 | Robust Scholarly ETF Rotation Model Mod-3743 | Topological data analysis / Betti persistence / Stock pairs | 11657 | 12197 | No |
