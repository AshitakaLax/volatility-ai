# Nonlinear approach to factor risk-parity allocation

**Concept page** · shared by **62** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(8 of them in ranks 426–700; best-ranked member #465) ·
researched 2026-10-29

| | |
|---|---|
| Task | Factor risk-parity allocation |
| Method | Nonlinear factor models |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **Research code** in `research.catalog.concepts`: `kernel_pca_factor_risk_parity`; tested on synthetic data, not wired into the engine. Related code already here: No factor risk parity; HRP is built (`hrp.hrp_weights`, A5) and minimum variance is research code (Q13). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK61, A5, RK60 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Non-Linear Scholarly Factor
Risk Parity Framework Mod-185") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Equalise risk across factors from a nonlinear factor model. Factor risk
parity itself is established (Roncalli and Weisang); I found no study
applying this method to it.

## The CSV's description

Proposed nonlinear approach to factor risk-parity allocation: Estimate
factor volatility and dependence, then choose portfolio weights so risk
contributions align with a target risk budget. This is a concept-level
interpretation of the title, not a complete trading specification: the
exact model inputs/target, calibration, entry/exit or rebalance rules,
and position sizing are not fully defined here.

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
| 465 | Non-Linear Scholarly Factor Risk Parity Framework Mod-185 | Rough path theory / Tensor signatures / Stock trend forecasting | 4049 | 7739 | No |
| 471 | Non-Linear Scholarly Factor Risk Parity Framework Mod-665 | Rough path theory / Tensor signatures / Stock trend forecasting | 4075 | 7769 | No |
| 477 | Non-Linear Scholarly Factor Risk Parity Framework Mod-1145 | Rough path theory / Tensor signatures / Stock trend forecasting | 4101 | 7799 | No |
| 483 | Non-Linear Scholarly Factor Risk Parity Framework Mod-1625 | Rough path theory / Tensor signatures / Stock trend forecasting | 4127 | 7829 | No |
| 489 | Non-Linear Scholarly Factor Risk Parity Framework Mod-2105 | Rough path theory / Tensor signatures / Stock trend forecasting | 4153 | 7859 | No |
| 495 | Non-Linear Scholarly Factor Risk Parity Framework Mod-2585 | Rough path theory / Tensor signatures / Stock trend forecasting | 4179 | 7889 | No |
| 501 | Non-Linear Scholarly Factor Risk Parity Framework Mod-3065 | Rough path theory / Tensor signatures / Stock trend forecasting | 4205 | 7919 | No |
| 507 | Non-Linear Scholarly Factor Risk Parity Framework Mod-3545 | Rough path theory / Tensor signatures / Stock trend forecasting | 4231 | 7949 | No |
| 964 | Non-Linear Scholarly Factor Risk Parity Framework Mod-377 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2419 | 6763 | No |
| 977 | Non-Linear Scholarly Factor Risk Parity Framework Mod-857 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2458 | 6797 | No |
| 990 | Non-Linear Scholarly Factor Risk Parity Framework Mod-1337 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2497 | 6831 | No |
| 1003 | Non-Linear Scholarly Factor Risk Parity Framework Mod-1817 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2536 | 6865 | No |
| 1016 | Non-Linear Scholarly Factor Risk Parity Framework Mod-2297 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2575 | 6899 | No |
| 1029 | Non-Linear Scholarly Factor Risk Parity Framework Mod-2777 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2614 | 6933 | No |
| 1042 | Non-Linear Scholarly Factor Risk Parity Framework Mod-3257 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2653 | 6967 | No |
| 1055 | Non-Linear Scholarly Factor Risk Parity Framework Mod-3737 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2692 | 7001 | No |
| 1848 | Non-Linear Scholarly Factor Risk Parity Framework Sys-119 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2205 | 8476 | No |
| 1897 | Non-Linear Scholarly Factor Risk Parity Framework Sys-599 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2252 | 8511 | No |
| 1946 | Non-Linear Scholarly Factor Risk Parity Framework Sys-1079 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2299 | 8546 | No |
| 1995 | Non-Linear Scholarly Factor Risk Parity Framework Sys-1559 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2346 | 8581 | No |
| 2069 | Non-Linear Scholarly Factor Risk Parity Framework Mod-281 | Graph attention / Sector contagion / Stock baskets | 10606 | 13223 | No |
| 2122 | Non-Linear Scholarly Factor Risk Parity Framework Mod-761 | Graph attention / Sector contagion / Stock baskets | 10612 | 13237 | No |
| 2175 | Non-Linear Scholarly Factor Risk Parity Framework Mod-1241 | Graph attention / Sector contagion / Stock baskets | 10618 | 13251 | No |
| 2228 | Non-Linear Scholarly Factor Risk Parity Framework Mod-1721 | Graph attention / Sector contagion / Stock baskets | 10624 | 13265 | No |
| 2281 | Non-Linear Scholarly Factor Risk Parity Framework Mod-2201 | Graph attention / Sector contagion / Stock baskets | 10630 | 13279 | No |
| 2334 | Non-Linear Scholarly Factor Risk Parity Framework Mod-2681 | Graph attention / Sector contagion / Stock baskets | 10636 | 13293 | No |
| 2387 | Non-Linear Scholarly Factor Risk Parity Framework Mod-3161 | Graph attention / Sector contagion / Stock baskets | 10642 | 13307 | No |
| 2440 | Non-Linear Scholarly Factor Risk Parity Framework Mod-3641 | Graph attention / Sector contagion / Stock baskets | 10648 | 13321 | No |
| 3955 | Non-Linear Scholarly Factor Risk Parity Framework Sys-23 | Topological data analysis / Betti persistence / Stock pairs | 11338 | 11923 | No |
| 3992 | Non-Linear Scholarly Factor Risk Parity Framework Sys-215 | Neural SDEs / Adversarial robustness / Stock options hedging | 6600 | 8483 | No |
| 4008 | Non-Linear Scholarly Factor Risk Parity Framework Sys-311 | Delay differential equations / Controlled ODEs / Stock execution | 12076 | 13167 | No |
| 4023 | Non-Linear Scholarly Factor Risk Parity Framework Sys-407 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 8355 | 10790 | No |
| 4041 | Non-Linear Scholarly Factor Risk Parity Framework Sys-503 | Topological data analysis / Betti persistence / Stock pairs | 11364 | 11946 | No |
| 4078 | Non-Linear Scholarly Factor Risk Parity Framework Sys-695 | Neural SDEs / Adversarial robustness / Stock options hedging | 6639 | 8518 | No |
| 4094 | Non-Linear Scholarly Factor Risk Parity Framework Sys-791 | Delay differential equations / Controlled ODEs / Stock execution | 12086 | 13181 | No |
| 4109 | Non-Linear Scholarly Factor Risk Parity Framework Sys-887 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 8395 | 10813 | No |
| 4127 | Non-Linear Scholarly Factor Risk Parity Framework Sys-983 | Topological data analysis / Betti persistence / Stock pairs | 11390 | 11969 | No |
| 4164 | Non-Linear Scholarly Factor Risk Parity Framework Sys-1175 | Neural SDEs / Adversarial robustness / Stock options hedging | 6678 | 8553 | No |
| 4180 | Non-Linear Scholarly Factor Risk Parity Framework Sys-1271 | Delay differential equations / Controlled ODEs / Stock execution | 12096 | 13195 | No |
| 4195 | Non-Linear Scholarly Factor Risk Parity Framework Sys-1367 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 8435 | 10836 | No |
| 4213 | Non-Linear Scholarly Factor Risk Parity Framework Sys-1463 | Topological data analysis / Betti persistence / Stock pairs | 11416 | 11992 | No |
| 4250 | Non-Linear Scholarly Factor Risk Parity Framework Sys-1655 | Neural SDEs / Adversarial robustness / Stock options hedging | 6717 | 8588 | No |
| 4266 | Non-Linear Scholarly Factor Risk Parity Framework Sys-1751 | Delay differential equations / Controlled ODEs / Stock execution | 12106 | 13209 | No |
| 4281 | Non-Linear Scholarly Factor Risk Parity Framework Sys-1847 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 8475 | 10859 | No |
| 4299 | Non-Linear Scholarly Factor Risk Parity Framework Sys-1943 | Topological data analysis / Betti persistence / Stock pairs | 11442 | 12015 | No |
| 4328 | Non-Linear Scholarly Factor Risk Parity Framework Mod-89 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6751 | 8619 | No |
| 4394 | Non-Linear Scholarly Factor Risk Parity Framework Mod-473 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13101 | 12863 | No |
| 4413 | Non-Linear Scholarly Factor Risk Parity Framework Mod-569 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6793 | 8656 | No |
| 4479 | Non-Linear Scholarly Factor Risk Parity Framework Mod-953 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13103 | 12869 | No |
| 4498 | Non-Linear Scholarly Factor Risk Parity Framework Mod-1049 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6835 | 8693 | No |
| 4564 | Non-Linear Scholarly Factor Risk Parity Framework Mod-1433 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13105 | 12875 | No |
| 4583 | Non-Linear Scholarly Factor Risk Parity Framework Mod-1529 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6877 | 8730 | No |
| 4649 | Non-Linear Scholarly Factor Risk Parity Framework Mod-1913 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13107 | 12881 | No |
| 4668 | Non-Linear Scholarly Factor Risk Parity Framework Mod-2009 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6919 | 8767 | No |
| 4734 | Non-Linear Scholarly Factor Risk Parity Framework Mod-2393 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13109 | 12887 | No |
| 4753 | Non-Linear Scholarly Factor Risk Parity Framework Mod-2489 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6961 | 8804 | No |
| 4819 | Non-Linear Scholarly Factor Risk Parity Framework Mod-2873 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13111 | 12893 | No |
| 4838 | Non-Linear Scholarly Factor Risk Parity Framework Mod-2969 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7003 | 8841 | No |
| 4904 | Non-Linear Scholarly Factor Risk Parity Framework Mod-3353 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13113 | 12899 | No |
| 4923 | Non-Linear Scholarly Factor Risk Parity Framework Mod-3449 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7045 | 8878 | No |
| 4989 | Non-Linear Scholarly Factor Risk Parity Framework Mod-3833 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13115 | 12905 | No |
| 5008 | Non-Linear Scholarly Factor Risk Parity Framework Mod-3929 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7087 | 8915 | No |
