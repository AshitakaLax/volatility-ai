# Koopman-operator-based approach to ETF rotation

**Concept page** · shared by **63** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,845) ·
researched 2026-10-30

| | |
|---|---|
| Task | ETF rotation |
| Method | Koopman operators (DMD / EDMD) |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of Koopman operators improving ETF rotation over relative strength with an absolute filter (X3, RK3). |
| Implemented in volatility-ai | `tools/rotation.py` runs relative strength (X3), defensive rotation (X2), dual momentum (RK3) and HRP weights (A5); Faber's moving-average filter is built (`tactical_allocation`, C-E2, RK17). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | X3, X2, RK3, RK17, C-E2, A5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Koopman Scholarly ETF
Rotation Model Sys-65") combine a method word, "Scholarly", a task and a
serial number, and the rows' references are software libraries or papers
the CSV's own review calls unrelated. There is no specific algorithm
behind each name to research, so this page researches what the members
share: the task, done with the method.

## In one paragraph

Rank a defined ETF universe by momentum, trend or risk and rotate on a
fixed schedule, with a defensive asset and a cost model. The Koopman
version linearises the dynamics in a lifted feature space and forecasts
with the linear operator. I found no study of this method on this task.

## The CSV's description

Proposed Koopman-operator-based approach to ETF rotation: Rank a defined
ETF universe using a specified momentum, trend, or risk signal and
rotate exposure on a fixed schedule, with a defined defensive allocation
and trading-cost model. This is a concept-level interpretation of the
title, not a complete trading specification: the exact model
inputs/target, calibration, entry/exit or rebalance rules, and position
sizing are not fully defined here.

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
* The Koopman entries in the list have no peer-reviewed trading evidence
  (RK206).

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
| 1845 | Koopman Scholarly ETF Rotation Model Sys-65 | Rough path theory / Tensor signatures / Stock trend forecasting | 8325 | 7640 | No |
| 1894 | Koopman Scholarly ETF Rotation Model Sys-545 | Rough path theory / Tensor signatures / Stock trend forecasting | 8365 | 7662 | No |
| 1943 | Koopman Scholarly ETF Rotation Model Sys-1025 | Rough path theory / Tensor signatures / Stock trend forecasting | 8405 | 7684 | No |
| 1992 | Koopman Scholarly ETF Rotation Model Sys-1505 | Rough path theory / Tensor signatures / Stock trend forecasting | 8445 | 7706 | No |
| 2041 | Koopman Scholarly ETF Rotation Model Sys-1985 | Rough path theory / Tensor signatures / Stock trend forecasting | 8485 | 7728 | No |
| 4032 | Koopman Scholarly ETF Rotation Model Sys-449 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6617 | 8500 | No |
| 4118 | Koopman Scholarly ETF Rotation Model Sys-929 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6656 | 8535 | No |
| 4204 | Koopman Scholarly ETF Rotation Model Sys-1409 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6695 | 8570 | No |
| 4290 | Koopman Scholarly ETF Rotation Model Sys-1889 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6734 | 8605 | No |
| 4370 | Koopman Scholarly ETF Rotation Model Mod-335 | Neural SDEs / Adversarial robustness / Stock options hedging | 10413 | 8638 | No |
| 4455 | Koopman Scholarly ETF Rotation Model Mod-815 | Neural SDEs / Adversarial robustness / Stock options hedging | 10421 | 8675 | No |
| 4540 | Koopman Scholarly ETF Rotation Model Mod-1295 | Neural SDEs / Adversarial robustness / Stock options hedging | 10429 | 8712 | No |
| 4625 | Koopman Scholarly ETF Rotation Model Mod-1775 | Neural SDEs / Adversarial robustness / Stock options hedging | 10437 | 8749 | No |
| 4710 | Koopman Scholarly ETF Rotation Model Mod-2255 | Neural SDEs / Adversarial robustness / Stock options hedging | 10445 | 8786 | No |
| 4795 | Koopman Scholarly ETF Rotation Model Mod-2735 | Neural SDEs / Adversarial robustness / Stock options hedging | 10453 | 8823 | No |
| 4880 | Koopman Scholarly ETF Rotation Model Mod-3215 | Neural SDEs / Adversarial robustness / Stock options hedging | 10461 | 8860 | No |
| 4965 | Koopman Scholarly ETF Rotation Model Mod-3695 | Neural SDEs / Adversarial robustness / Stock options hedging | 10469 | 8897 | No |
| 6303 | Koopman Scholarly ETF Rotation Model Sys-257 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6602 | 6604 | No |
| 6344 | Koopman Scholarly ETF Rotation Model Sys-737 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6641 | 6640 | No |
| 6385 | Koopman Scholarly ETF Rotation Model Sys-1217 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6680 | 6676 | No |
| 6426 | Koopman Scholarly ETF Rotation Model Sys-1697 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6719 | 6712 | No |
| 9135 | Koopman Scholarly ETF Rotation Model Sys-161 | Graph attention / Sector contagion / Stock baskets | 12279 | 13162 | No |
| 9213 | Koopman Scholarly ETF Rotation Model Sys-353 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13782 | 12816 | No |
| 9322 | Koopman Scholarly ETF Rotation Model Sys-641 | Graph attention / Sector contagion / Stock baskets | 12289 | 13176 | No |
| 9400 | Koopman Scholarly ETF Rotation Model Sys-833 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13790 | 12828 | No |
| 9509 | Koopman Scholarly ETF Rotation Model Sys-1121 | Graph attention / Sector contagion / Stock baskets | 12299 | 13190 | No |
| 9587 | Koopman Scholarly ETF Rotation Model Sys-1313 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13798 | 12840 | No |
| 9696 | Koopman Scholarly ETF Rotation Model Sys-1601 | Graph attention / Sector contagion / Stock baskets | 12309 | 13204 | No |
| 9774 | Koopman Scholarly ETF Rotation Model Sys-1793 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13806 | 12852 | No |
| 9869 | Koopman Scholarly ETF Rotation Model Mod-47 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10908 | 10869 | No |
| 9905 | Koopman Scholarly ETF Rotation Model Mod-143 | Topological data analysis / Betti persistence / Stock pairs | 11454 | 12024 | No |
| 9948 | Koopman Scholarly ETF Rotation Model Mod-239 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6763 | 8630 | No |
| 10060 | Koopman Scholarly ETF Rotation Model Mod-527 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10916 | 10888 | No |
| 10096 | Koopman Scholarly ETF Rotation Model Mod-623 | Topological data analysis / Betti persistence / Stock pairs | 11481 | 12047 | No |
| 10139 | Koopman Scholarly ETF Rotation Model Mod-719 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6805 | 8667 | No |
| 10251 | Koopman Scholarly ETF Rotation Model Mod-1007 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10924 | 10907 | No |
| 10287 | Koopman Scholarly ETF Rotation Model Mod-1103 | Topological data analysis / Betti persistence / Stock pairs | 11508 | 12070 | No |
| 10330 | Koopman Scholarly ETF Rotation Model Mod-1199 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6847 | 8704 | No |
| 10442 | Koopman Scholarly ETF Rotation Model Mod-1487 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10932 | 10926 | No |
| 10478 | Koopman Scholarly ETF Rotation Model Mod-1583 | Topological data analysis / Betti persistence / Stock pairs | 11535 | 12093 | No |
| 10521 | Koopman Scholarly ETF Rotation Model Mod-1679 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6889 | 8741 | No |
| 10633 | Koopman Scholarly ETF Rotation Model Mod-1967 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10940 | 10945 | No |
| 10669 | Koopman Scholarly ETF Rotation Model Mod-2063 | Topological data analysis / Betti persistence / Stock pairs | 11562 | 12116 | No |
| 10712 | Koopman Scholarly ETF Rotation Model Mod-2159 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6931 | 8778 | No |
| 10824 | Koopman Scholarly ETF Rotation Model Mod-2447 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10948 | 10964 | No |
| 10860 | Koopman Scholarly ETF Rotation Model Mod-2543 | Topological data analysis / Betti persistence / Stock pairs | 11589 | 12139 | No |
| 10903 | Koopman Scholarly ETF Rotation Model Mod-2639 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6973 | 8815 | No |
| 11015 | Koopman Scholarly ETF Rotation Model Mod-2927 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10956 | 10983 | No |
| 11051 | Koopman Scholarly ETF Rotation Model Mod-3023 | Topological data analysis / Betti persistence / Stock pairs | 11616 | 12162 | No |
| 11094 | Koopman Scholarly ETF Rotation Model Mod-3119 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7015 | 8852 | No |
| 11206 | Koopman Scholarly ETF Rotation Model Mod-3407 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10964 | 11002 | No |
| 11242 | Koopman Scholarly ETF Rotation Model Mod-3503 | Topological data analysis / Betti persistence / Stock pairs | 11643 | 12185 | No |
| 11285 | Koopman Scholarly ETF Rotation Model Mod-3599 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7057 | 8889 | No |
| 11397 | Koopman Scholarly ETF Rotation Model Mod-3887 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10972 | 11021 | No |
| 11433 | Koopman Scholarly ETF Rotation Model Mod-3983 | Topological data analysis / Betti persistence / Stock pairs | 11670 | 12208 | No |
| 13984 | Koopman Scholarly ETF Rotation Model Mod-431 | Delay differential equations / Controlled ODEs / Stock execution | 13226 | 13228 | No |
| 13998 | Koopman Scholarly ETF Rotation Model Mod-911 | Delay differential equations / Controlled ODEs / Stock execution | 13238 | 13242 | No |
| 14012 | Koopman Scholarly ETF Rotation Model Mod-1391 | Delay differential equations / Controlled ODEs / Stock execution | 13250 | 13256 | No |
| 14026 | Koopman Scholarly ETF Rotation Model Mod-1871 | Delay differential equations / Controlled ODEs / Stock execution | 13262 | 13270 | No |
| 14040 | Koopman Scholarly ETF Rotation Model Mod-2351 | Delay differential equations / Controlled ODEs / Stock execution | 13274 | 13284 | No |
| 14054 | Koopman Scholarly ETF Rotation Model Mod-2831 | Delay differential equations / Controlled ODEs / Stock execution | 13286 | 13298 | No |
| 14068 | Koopman Scholarly ETF Rotation Model Mod-3311 | Delay differential equations / Controlled ODEs / Stock execution | 13298 | 13312 | No |
| 14082 | Koopman Scholarly ETF Rotation Model Mod-3791 | Delay differential equations / Controlled ODEs / Stock execution | 13310 | 13326 | No |
