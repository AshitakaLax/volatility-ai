# Geometry-aware approach to factor risk-parity allocation

**Concept page** · shared by **63** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(8 of them in ranks 426–700; best-ranked member #467) ·
researched 2026-10-29

| | |
|---|---|
| Task | Factor risk-parity allocation |
| Method | Geometry-aware (Riemannian) optimisation |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | No factor risk parity; HRP is built (`hrp.hrp_weights`, A5) and minimum variance is research code (Q13). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK61, A5, RK60 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Riemannian Scholarly Factor
Risk Parity Framework Mod-425") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Solve factor risk parity with optimisation that respects the geometry of
covariance matrices. Factor risk parity itself is established (Roncalli
and Weisang); I found no study applying this method to it.

## The CSV's description

Proposed geometry-aware approach to factor risk-parity allocation:
Estimate factor volatility and dependence, then choose portfolio weights
so risk contributions align with a target risk budget. This is a
concept-level interpretation of the title, not a complete trading
specification: the exact model inputs/target, calibration, entry/exit or
rebalance rules, and position sizing are not fully defined here.

## Evidence

* **Roncalli & Weisang (2016), "Risk parity portfolios with risk
  factors," *Quantitative Finance* 16(3), 377–388:** decompose portfolio
  risk into factor contributions and equalise those instead of asset
  contributions; applied to a pension fund's strategic allocation. Later
  work notes the factor version can lack a unique solution and is
  unstable as asset-factor loadings drift. (Abstract and citing papers.)
* **Meucci (2009), "Managing diversification," *Risk*:** the effective
  number of uncorrelated bets as a diversification measure, the basis of
  factor risk budgeting. (Standard reference; not re-checked here.)
* **Asness, Frazzini & Pedersen (2012), "Leverage aversion and risk
  parity," *Financial Analysts Journal*:** risk parity's historical edge
  relies on leverage (see RK61). (Standard reference.)
* **No portfolio study of Riemannian optimisation found** (see RK230).

## Against, and failure modes

* Factor risk parity needs a factor model whose loadings drift;
  solutions can be non-unique.
* Unlevered risk parity is a low-volatility bond-heavy portfolio; its
  historical edge came with leverage (RK61).

## Fit with volatility-ai

An allocator for a multi-asset book; the engine trades one symbol and
the allocator in ledger §11 is not built. HRP (A5) is the built
allocator, and equal-risk-contribution is not (RK61). Factor risk parity
adds a factor model on top, which a book of a few ETFs does not need.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Roncalli, T., Weisang, G. (2016). "Risk parity portfolios with risk
  factors." *Quantitative Finance* 16(3), 377–388. Abstract.
* Meucci, A. (2009). "Managing diversification." *Risk*. Not re-checked.
* Asness, C., Frazzini, A., Pedersen, L. H. (2012). *Financial Analysts
  Journal* 68(1). Standard reference.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 467 | Riemannian Scholarly Factor Risk Parity Framework Mod-425 | Rough path theory / Tensor signatures / Stock trend forecasting | 4062 | 7754 | No |
| 473 | Riemannian Scholarly Factor Risk Parity Framework Mod-905 | Rough path theory / Tensor signatures / Stock trend forecasting | 4088 | 7784 | No |
| 479 | Riemannian Scholarly Factor Risk Parity Framework Mod-1385 | Rough path theory / Tensor signatures / Stock trend forecasting | 4114 | 7814 | No |
| 485 | Riemannian Scholarly Factor Risk Parity Framework Mod-1865 | Rough path theory / Tensor signatures / Stock trend forecasting | 4140 | 7844 | No |
| 491 | Riemannian Scholarly Factor Risk Parity Framework Mod-2345 | Rough path theory / Tensor signatures / Stock trend forecasting | 4166 | 7874 | No |
| 497 | Riemannian Scholarly Factor Risk Parity Framework Mod-2825 | Rough path theory / Tensor signatures / Stock trend forecasting | 4192 | 7904 | No |
| 503 | Riemannian Scholarly Factor Risk Parity Framework Mod-3305 | Rough path theory / Tensor signatures / Stock trend forecasting | 4218 | 7934 | No |
| 509 | Riemannian Scholarly Factor Risk Parity Framework Mod-3785 | Rough path theory / Tensor signatures / Stock trend forecasting | 4244 | 7964 | No |
| 958 | Riemannian Scholarly Factor Risk Parity Framework Mod-137 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2399 | 6746 | No |
| 971 | Riemannian Scholarly Factor Risk Parity Framework Mod-617 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2438 | 6780 | No |
| 984 | Riemannian Scholarly Factor Risk Parity Framework Mod-1097 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2477 | 6814 | No |
| 997 | Riemannian Scholarly Factor Risk Parity Framework Mod-1577 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2516 | 6848 | No |
| 1010 | Riemannian Scholarly Factor Risk Parity Framework Mod-2057 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2555 | 6882 | No |
| 1023 | Riemannian Scholarly Factor Risk Parity Framework Mod-2537 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2594 | 6916 | No |
| 1036 | Riemannian Scholarly Factor Risk Parity Framework Mod-3017 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2633 | 6950 | No |
| 1049 | Riemannian Scholarly Factor Risk Parity Framework Mod-3497 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2672 | 6984 | No |
| 1062 | Riemannian Scholarly Factor Risk Parity Framework Mod-3977 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2711 | 7018 | No |
| 1871 | Riemannian Scholarly Factor Risk Parity Framework Sys-359 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2227 | 8493 | No |
| 1920 | Riemannian Scholarly Factor Risk Parity Framework Sys-839 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2274 | 8528 | No |
| 1969 | Riemannian Scholarly Factor Risk Parity Framework Sys-1319 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2321 | 8563 | No |
| 2018 | Riemannian Scholarly Factor Risk Parity Framework Sys-1799 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2368 | 8598 | No |
| 2045 | Riemannian Scholarly Factor Risk Parity Framework Mod-41 | Graph attention / Sector contagion / Stock baskets | 12111 | 13772 | No |
| 2098 | Riemannian Scholarly Factor Risk Parity Framework Mod-521 | Graph attention / Sector contagion / Stock baskets | 12118 | 13781 | No |
| 2151 | Riemannian Scholarly Factor Risk Parity Framework Mod-1001 | Graph attention / Sector contagion / Stock baskets | 12125 | 13790 | No |
| 2204 | Riemannian Scholarly Factor Risk Parity Framework Mod-1481 | Graph attention / Sector contagion / Stock baskets | 12132 | 13799 | No |
| 2257 | Riemannian Scholarly Factor Risk Parity Framework Mod-1961 | Graph attention / Sector contagion / Stock baskets | 12139 | 13808 | No |
| 2310 | Riemannian Scholarly Factor Risk Parity Framework Mod-2441 | Graph attention / Sector contagion / Stock baskets | 12146 | 13817 | No |
| 2363 | Riemannian Scholarly Factor Risk Parity Framework Mod-2921 | Graph attention / Sector contagion / Stock baskets | 12153 | 13826 | No |
| 2416 | Riemannian Scholarly Factor Risk Parity Framework Mod-3401 | Graph attention / Sector contagion / Stock baskets | 12160 | 13835 | No |
| 2469 | Riemannian Scholarly Factor Risk Parity Framework Mod-3881 | Graph attention / Sector contagion / Stock baskets | 12167 | 13844 | No |
| 3964 | Riemannian Scholarly Factor Risk Parity Framework Sys-71 | Delay differential equations / Controlled ODEs / Stock execution | 12070 | 13735 | No |
| 3982 | Riemannian Scholarly Factor Risk Parity Framework Sys-167 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 8333 | 10779 | No |
| 3998 | Riemannian Scholarly Factor Risk Parity Framework Sys-263 | Topological data analysis / Betti persistence / Stock pairs | 11351 | 11934 | No |
| 4033 | Riemannian Scholarly Factor Risk Parity Framework Sys-455 | Neural SDEs / Adversarial robustness / Stock options hedging | 10075 | 10296 | No |
| 4050 | Riemannian Scholarly Factor Risk Parity Framework Sys-551 | Delay differential equations / Controlled ODEs / Stock execution | 12080 | 13744 | No |
| 4068 | Riemannian Scholarly Factor Risk Parity Framework Sys-647 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 8373 | 10802 | No |
| 4084 | Riemannian Scholarly Factor Risk Parity Framework Sys-743 | Topological data analysis / Betti persistence / Stock pairs | 11377 | 11957 | No |
| 4119 | Riemannian Scholarly Factor Risk Parity Framework Sys-935 | Neural SDEs / Adversarial robustness / Stock options hedging | 10086 | 10298 | No |
| 4136 | Riemannian Scholarly Factor Risk Parity Framework Sys-1031 | Delay differential equations / Controlled ODEs / Stock execution | 12090 | 13753 | No |
| 4154 | Riemannian Scholarly Factor Risk Parity Framework Sys-1127 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 8413 | 10825 | No |
| 4170 | Riemannian Scholarly Factor Risk Parity Framework Sys-1223 | Topological data analysis / Betti persistence / Stock pairs | 11403 | 11980 | No |
| 4205 | Riemannian Scholarly Factor Risk Parity Framework Sys-1415 | Neural SDEs / Adversarial robustness / Stock options hedging | 10097 | 10300 | No |
| 4222 | Riemannian Scholarly Factor Risk Parity Framework Sys-1511 | Delay differential equations / Controlled ODEs / Stock execution | 12100 | 13762 | No |
| 4240 | Riemannian Scholarly Factor Risk Parity Framework Sys-1607 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 8453 | 10848 | No |
| 4256 | Riemannian Scholarly Factor Risk Parity Framework Sys-1703 | Topological data analysis / Betti persistence / Stock pairs | 11429 | 12003 | No |
| 4291 | Riemannian Scholarly Factor Risk Parity Framework Sys-1895 | Neural SDEs / Adversarial robustness / Stock options hedging | 10108 | 10302 | No |
| 4308 | Riemannian Scholarly Factor Risk Parity Framework Sys-1991 | Delay differential equations / Controlled ODEs / Stock execution | 12110 | 13771 | No |
| 4354 | Riemannian Scholarly Factor Risk Parity Framework Mod-233 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13741 | 13526 | No |
| 4369 | Riemannian Scholarly Factor Risk Parity Framework Mod-329 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6772 | 8637 | No |
| 4439 | Riemannian Scholarly Factor Risk Parity Framework Mod-713 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13742 | 13533 | No |
| 4454 | Riemannian Scholarly Factor Risk Parity Framework Mod-809 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6814 | 8674 | No |
| 4524 | Riemannian Scholarly Factor Risk Parity Framework Mod-1193 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13743 | 13540 | No |
| 4539 | Riemannian Scholarly Factor Risk Parity Framework Mod-1289 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6856 | 8711 | No |
| 4609 | Riemannian Scholarly Factor Risk Parity Framework Mod-1673 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13744 | 13547 | No |
| 4624 | Riemannian Scholarly Factor Risk Parity Framework Mod-1769 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6898 | 8748 | No |
| 4694 | Riemannian Scholarly Factor Risk Parity Framework Mod-2153 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13745 | 13554 | No |
| 4709 | Riemannian Scholarly Factor Risk Parity Framework Mod-2249 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6940 | 8785 | No |
| 4779 | Riemannian Scholarly Factor Risk Parity Framework Mod-2633 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13746 | 13561 | No |
| 4794 | Riemannian Scholarly Factor Risk Parity Framework Mod-2729 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6982 | 8822 | No |
| 4864 | Riemannian Scholarly Factor Risk Parity Framework Mod-3113 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13747 | 13568 | No |
| 4879 | Riemannian Scholarly Factor Risk Parity Framework Mod-3209 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7024 | 8859 | No |
| 4949 | Riemannian Scholarly Factor Risk Parity Framework Mod-3593 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13748 | 13575 | No |
| 4964 | Riemannian Scholarly Factor Risk Parity Framework Mod-3689 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7066 | 8896 | No |
