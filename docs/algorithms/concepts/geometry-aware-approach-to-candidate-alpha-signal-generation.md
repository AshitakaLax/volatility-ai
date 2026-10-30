# Geometry-aware approach to candidate alpha-signal generation

**Concept page** · shared by **63** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #2,050) ·
researched 2026-10-30

| | |
|---|---|
| Task | Candidate alpha-signal generation |
| Method | Geometry-aware (Riemannian) methods |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Mass-producing candidate signals raises the multiple-testing bar faster than it finds edge; the staged sweep already generates candidates. |
| Implemented in volatility-ai | Nothing; the staged indicator sweep (`plan.md`) is the project's generator. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK395, RK222 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Riemannian Scholarly Alpha
Diffusion Generator Mod-105") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Use a generative model to propose or transform candidate signals, each
still needing out-of-sample validation and trading rules. The
geometry-aware version works on the curved space of covariance matrices
or another manifold. I found no study of this method on this task.

## The CSV's description

Proposed geometry-aware approach to candidate alpha-signal generation:
Use a diffusion-style generative model to propose or transform candidate
market features/signals; each signal would still require independent
out-of-sample validation and explicit trading rules. This is a
concept-level interpretation of the title, not a complete trading
specification: the exact model inputs/target, calibration, entry/exit or
rebalance rules, and position sizing are not fully defined here.

## Evidence

* **Harvey, Liu & Zhu (2016), "... and the Cross-Section of Expected
  Returns," *Review of Financial Studies* 29(1), 5–68:** after hundreds
  of tested factors, a new one needs a t-statistic above about 3.0, not
  2.0. (Abstract.)
* **McLean & Pontiff (2016), "Does Academic Research Destroy Stock
  Return Predictability?" *Journal of Finance* 71(1):** anomaly
  portfolio returns are 26% lower out of sample and 58% lower after
  publication. (Abstract.)

## Against, and failure modes

* Every extra candidate raises the bar a survivor must clear (Harvey,
  Liu & Zhu); published anomalies decay.
* No portfolio study shows Riemannian methods beating shrinkage (RK230).

## Fit with volatility-ai

The project's staged sweep (`plan.md`) is already its candidate
generator. Generating more candidates without a matching
multiple-testing correction adds false discoveries, not edge.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Harvey, C. R., Liu, Y., Zhu, H. (2016). *Review of Financial Studies*
  29(1), 5–68. Abstract.
* McLean, R. D., Pontiff, J. (2016). *Journal of Finance* 71(1).
  Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 2050 | Riemannian Scholarly Alpha Diffusion Generator Mod-105 | Rough path theory / Tensor signatures / Stock trend forecasting | 5635 | 2283 | No |
| 2103 | Riemannian Scholarly Alpha Diffusion Generator Mod-585 | Rough path theory / Tensor signatures / Stock trend forecasting | 5642 | 2306 | No |
| 2156 | Riemannian Scholarly Alpha Diffusion Generator Mod-1065 | Rough path theory / Tensor signatures / Stock trend forecasting | 5649 | 2329 | No |
| 2209 | Riemannian Scholarly Alpha Diffusion Generator Mod-1545 | Rough path theory / Tensor signatures / Stock trend forecasting | 5656 | 2352 | No |
| 2262 | Riemannian Scholarly Alpha Diffusion Generator Mod-2025 | Rough path theory / Tensor signatures / Stock trend forecasting | 5663 | 2375 | No |
| 2315 | Riemannian Scholarly Alpha Diffusion Generator Mod-2505 | Rough path theory / Tensor signatures / Stock trend forecasting | 5670 | 2398 | No |
| 2368 | Riemannian Scholarly Alpha Diffusion Generator Mod-2985 | Rough path theory / Tensor signatures / Stock trend forecasting | 5677 | 2421 | No |
| 2421 | Riemannian Scholarly Alpha Diffusion Generator Mod-3465 | Rough path theory / Tensor signatures / Stock trend forecasting | 5684 | 2444 | No |
| 2474 | Riemannian Scholarly Alpha Diffusion Generator Mod-3945 | Rough path theory / Tensor signatures / Stock trend forecasting | 5691 | 2467 | No |
| 3975 | Riemannian Scholarly Alpha Diffusion Generator Sys-135 | Neural SDEs / Adversarial robustness / Stock options hedging | 10746 | 7644 | No |
| 4061 | Riemannian Scholarly Alpha Diffusion Generator Sys-615 | Neural SDEs / Adversarial robustness / Stock options hedging | 10754 | 7666 | No |
| 4147 | Riemannian Scholarly Alpha Diffusion Generator Sys-1095 | Neural SDEs / Adversarial robustness / Stock options hedging | 10762 | 7688 | No |
| 4233 | Riemannian Scholarly Alpha Diffusion Generator Sys-1575 | Neural SDEs / Adversarial robustness / Stock options hedging | 10770 | 7710 | No |
| 4313 | Riemannian Scholarly Alpha Diffusion Generator Mod-9 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6744 | 3652 | No |
| 4398 | Riemannian Scholarly Alpha Diffusion Generator Mod-489 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6786 | 3747 | No |
| 4483 | Riemannian Scholarly Alpha Diffusion Generator Mod-969 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6828 | 3842 | No |
| 4568 | Riemannian Scholarly Alpha Diffusion Generator Mod-1449 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6870 | 3937 | No |
| 4653 | Riemannian Scholarly Alpha Diffusion Generator Mod-1929 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6912 | 4032 | No |
| 4738 | Riemannian Scholarly Alpha Diffusion Generator Mod-2409 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6954 | 4127 | No |
| 4823 | Riemannian Scholarly Alpha Diffusion Generator Mod-2889 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6996 | 4222 | No |
| 4908 | Riemannian Scholarly Alpha Diffusion Generator Mod-3369 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7038 | 4317 | No |
| 4993 | Riemannian Scholarly Alpha Diffusion Generator Mod-3849 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7080 | 4412 | No |
| 6482 | Riemannian Scholarly Alpha Diffusion Generator Mod-297 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2411 | 6756 | No |
| 6527 | Riemannian Scholarly Alpha Diffusion Generator Mod-777 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2450 | 6790 | No |
| 6572 | Riemannian Scholarly Alpha Diffusion Generator Mod-1257 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2489 | 6824 | No |
| 6617 | Riemannian Scholarly Alpha Diffusion Generator Mod-1737 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2528 | 6858 | No |
| 6662 | Riemannian Scholarly Alpha Diffusion Generator Mod-2217 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2567 | 6892 | No |
| 6707 | Riemannian Scholarly Alpha Diffusion Generator Mod-2697 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2606 | 6926 | No |
| 6752 | Riemannian Scholarly Alpha Diffusion Generator Mod-3177 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2645 | 6960 | No |
| 6797 | Riemannian Scholarly Alpha Diffusion Generator Mod-3657 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2684 | 6994 | No |
| 9088 | Riemannian Scholarly Alpha Diffusion Generator Sys-39 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2196 | 3263 | No |
| 9202 | Riemannian Scholarly Alpha Diffusion Generator Sys-327 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 8349 | 10786 | No |
| 9238 | Riemannian Scholarly Alpha Diffusion Generator Sys-423 | Topological data analysis / Betti persistence / Stock pairs | 2234 | 6616 | No |
| 9275 | Riemannian Scholarly Alpha Diffusion Generator Sys-519 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2243 | 3358 | No |
| 9389 | Riemannian Scholarly Alpha Diffusion Generator Sys-807 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 8389 | 10809 | No |
| 9425 | Riemannian Scholarly Alpha Diffusion Generator Sys-903 | Topological data analysis / Betti persistence / Stock pairs | 2281 | 6652 | No |
| 9462 | Riemannian Scholarly Alpha Diffusion Generator Sys-999 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2290 | 3453 | No |
| 9576 | Riemannian Scholarly Alpha Diffusion Generator Sys-1287 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 8429 | 10832 | No |
| 9612 | Riemannian Scholarly Alpha Diffusion Generator Sys-1383 | Topological data analysis / Betti persistence / Stock pairs | 2328 | 6688 | No |
| 9649 | Riemannian Scholarly Alpha Diffusion Generator Sys-1479 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2337 | 3548 | No |
| 9763 | Riemannian Scholarly Alpha Diffusion Generator Sys-1767 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 8469 | 10855 | No |
| 9799 | Riemannian Scholarly Alpha Diffusion Generator Sys-1863 | Topological data analysis / Betti persistence / Stock pairs | 2375 | 6724 | No |
| 9836 | Riemannian Scholarly Alpha Diffusion Generator Sys-1959 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2384 | 3643 | No |
| 9931 | Riemannian Scholarly Alpha Diffusion Generator Mod-201 | Graph attention / Sector contagion / Stock baskets | 4051 | 3691 | No |
| 10010 | Riemannian Scholarly Alpha Diffusion Generator Mod-393 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 10608 | 10265 | No |
| 10122 | Riemannian Scholarly Alpha Diffusion Generator Mod-681 | Graph attention / Sector contagion / Stock baskets | 4077 | 3786 | No |
| 10201 | Riemannian Scholarly Alpha Diffusion Generator Mod-873 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 10614 | 10267 | No |
| 10313 | Riemannian Scholarly Alpha Diffusion Generator Mod-1161 | Graph attention / Sector contagion / Stock baskets | 4103 | 3881 | No |
| 10392 | Riemannian Scholarly Alpha Diffusion Generator Mod-1353 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 10620 | 10269 | No |
| 10504 | Riemannian Scholarly Alpha Diffusion Generator Mod-1641 | Graph attention / Sector contagion / Stock baskets | 4129 | 3976 | No |
| 10583 | Riemannian Scholarly Alpha Diffusion Generator Mod-1833 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 10626 | 10271 | No |
| 10695 | Riemannian Scholarly Alpha Diffusion Generator Mod-2121 | Graph attention / Sector contagion / Stock baskets | 4155 | 4071 | No |
| 10774 | Riemannian Scholarly Alpha Diffusion Generator Mod-2313 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 10632 | 10273 | No |
| 10886 | Riemannian Scholarly Alpha Diffusion Generator Mod-2601 | Graph attention / Sector contagion / Stock baskets | 4181 | 4166 | No |
| 10965 | Riemannian Scholarly Alpha Diffusion Generator Mod-2793 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 10638 | 10275 | No |
| 11077 | Riemannian Scholarly Alpha Diffusion Generator Mod-3081 | Graph attention / Sector contagion / Stock baskets | 4207 | 4261 | No |
| 11156 | Riemannian Scholarly Alpha Diffusion Generator Mod-3273 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 10644 | 10277 | No |
| 11268 | Riemannian Scholarly Alpha Diffusion Generator Mod-3561 | Graph attention / Sector contagion / Stock baskets | 4233 | 4356 | No |
| 11347 | Riemannian Scholarly Alpha Diffusion Generator Mod-3753 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 10650 | 10279 | No |
| 13905 | Riemannian Scholarly Alpha Diffusion Generator Sys-231 | Delay differential equations / Controlled ODEs / Stock execution | 3932 | 3300 | No |
| 13923 | Riemannian Scholarly Alpha Diffusion Generator Sys-711 | Delay differential equations / Controlled ODEs / Stock execution | 3961 | 3395 | No |
| 13941 | Riemannian Scholarly Alpha Diffusion Generator Sys-1191 | Delay differential equations / Controlled ODEs / Stock execution | 3990 | 3490 | No |
| 13959 | Riemannian Scholarly Alpha Diffusion Generator Sys-1671 | Delay differential equations / Controlled ODEs / Stock execution | 4019 | 3585 | No |
