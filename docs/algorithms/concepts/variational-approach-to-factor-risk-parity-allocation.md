# Variational approach to factor risk-parity allocation

**Concept page** · shared by **62** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(8 of them in ranks 426–700; best-ranked member #466) ·
researched 2026-10-29

| | |
|---|---|
| Task | Factor risk-parity allocation |
| Method | Variational inference / variational autoencoders |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | No factor risk parity; HRP is built (`hrp.hrp_weights`, A5) and minimum variance is research code (Q13). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK61, A5, RK60 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Variational Scholarly
Factor Risk Parity Framework Mod-305") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Learn latent factors with a variational model and equalise their risk
contributions. Factor risk parity itself is established (Roncalli and
Weisang); I found no study applying this method to it.

## The CSV's description

Proposed variational approach to factor risk-parity allocation: Estimate
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
| 466 | Variational Scholarly Factor Risk Parity Framework Mod-305 | Rough path theory / Tensor signatures / Stock trend forecasting | 4056 | 7747 | No |
| 472 | Variational Scholarly Factor Risk Parity Framework Mod-785 | Rough path theory / Tensor signatures / Stock trend forecasting | 4082 | 7777 | No |
| 478 | Variational Scholarly Factor Risk Parity Framework Mod-1265 | Rough path theory / Tensor signatures / Stock trend forecasting | 4108 | 7807 | No |
| 484 | Variational Scholarly Factor Risk Parity Framework Mod-1745 | Rough path theory / Tensor signatures / Stock trend forecasting | 4134 | 7837 | No |
| 490 | Variational Scholarly Factor Risk Parity Framework Mod-2225 | Rough path theory / Tensor signatures / Stock trend forecasting | 4160 | 7867 | No |
| 496 | Variational Scholarly Factor Risk Parity Framework Mod-2705 | Rough path theory / Tensor signatures / Stock trend forecasting | 4186 | 7897 | No |
| 502 | Variational Scholarly Factor Risk Parity Framework Mod-3185 | Rough path theory / Tensor signatures / Stock trend forecasting | 4212 | 7927 | No |
| 508 | Variational Scholarly Factor Risk Parity Framework Mod-3665 | Rough path theory / Tensor signatures / Stock trend forecasting | 4238 | 7957 | No |
| 954 | Variational Scholarly Factor Risk Parity Framework Mod-17 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2390 | 6738 | No |
| 967 | Variational Scholarly Factor Risk Parity Framework Mod-497 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2429 | 6772 | No |
| 980 | Variational Scholarly Factor Risk Parity Framework Mod-977 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2468 | 6806 | No |
| 993 | Variational Scholarly Factor Risk Parity Framework Mod-1457 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2507 | 6840 | No |
| 1006 | Variational Scholarly Factor Risk Parity Framework Mod-1937 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2546 | 6874 | No |
| 1019 | Variational Scholarly Factor Risk Parity Framework Mod-2417 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2585 | 6908 | No |
| 1032 | Variational Scholarly Factor Risk Parity Framework Mod-2897 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2624 | 6942 | No |
| 1045 | Variational Scholarly Factor Risk Parity Framework Mod-3377 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2663 | 6976 | No |
| 1058 | Variational Scholarly Factor Risk Parity Framework Mod-3857 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2702 | 7010 | No |
| 1885 | Variational Scholarly Factor Risk Parity Framework Sys-479 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2239 | 8502 | No |
| 1934 | Variational Scholarly Factor Risk Parity Framework Sys-959 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2286 | 8537 | No |
| 1983 | Variational Scholarly Factor Risk Parity Framework Sys-1439 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2333 | 8572 | No |
| 2032 | Variational Scholarly Factor Risk Parity Framework Sys-1919 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2380 | 8607 | No |
| 2084 | Variational Scholarly Factor Risk Parity Framework Mod-401 | Graph attention / Sector contagion / Stock baskets | 10609 | 13227 | No |
| 2137 | Variational Scholarly Factor Risk Parity Framework Mod-881 | Graph attention / Sector contagion / Stock baskets | 10615 | 13241 | No |
| 2190 | Variational Scholarly Factor Risk Parity Framework Mod-1361 | Graph attention / Sector contagion / Stock baskets | 10621 | 13255 | No |
| 2243 | Variational Scholarly Factor Risk Parity Framework Mod-1841 | Graph attention / Sector contagion / Stock baskets | 10627 | 13269 | No |
| 2296 | Variational Scholarly Factor Risk Parity Framework Mod-2321 | Graph attention / Sector contagion / Stock baskets | 10633 | 13283 | No |
| 2349 | Variational Scholarly Factor Risk Parity Framework Mod-2801 | Graph attention / Sector contagion / Stock baskets | 10639 | 13297 | No |
| 2402 | Variational Scholarly Factor Risk Parity Framework Mod-3281 | Graph attention / Sector contagion / Stock baskets | 10645 | 13311 | No |
| 2455 | Variational Scholarly Factor Risk Parity Framework Mod-3761 | Graph attention / Sector contagion / Stock baskets | 10651 | 13325 | No |
| 3969 | Variational Scholarly Factor Risk Parity Framework Sys-95 | Neural SDEs / Adversarial robustness / Stock options hedging | 6589 | 8474 | No |
| 3987 | Variational Scholarly Factor Risk Parity Framework Sys-191 | Delay differential equations / Controlled ODEs / Stock execution | 12072 | 13163 | No |
| 4003 | Variational Scholarly Factor Risk Parity Framework Sys-287 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 8344 | 10785 | No |
| 4019 | Variational Scholarly Factor Risk Parity Framework Sys-383 | Topological data analysis / Betti persistence / Stock pairs | 11357 | 11940 | No |
| 4055 | Variational Scholarly Factor Risk Parity Framework Sys-575 | Neural SDEs / Adversarial robustness / Stock options hedging | 6628 | 8509 | No |
| 4073 | Variational Scholarly Factor Risk Parity Framework Sys-671 | Delay differential equations / Controlled ODEs / Stock execution | 12082 | 13177 | No |
| 4089 | Variational Scholarly Factor Risk Parity Framework Sys-767 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 8384 | 10808 | No |
| 4105 | Variational Scholarly Factor Risk Parity Framework Sys-863 | Topological data analysis / Betti persistence / Stock pairs | 11383 | 11963 | No |
| 4141 | Variational Scholarly Factor Risk Parity Framework Sys-1055 | Neural SDEs / Adversarial robustness / Stock options hedging | 6667 | 8544 | No |
| 4159 | Variational Scholarly Factor Risk Parity Framework Sys-1151 | Delay differential equations / Controlled ODEs / Stock execution | 12092 | 13191 | No |
| 4175 | Variational Scholarly Factor Risk Parity Framework Sys-1247 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 8424 | 10831 | No |
| 4191 | Variational Scholarly Factor Risk Parity Framework Sys-1343 | Topological data analysis / Betti persistence / Stock pairs | 11409 | 11986 | No |
| 4227 | Variational Scholarly Factor Risk Parity Framework Sys-1535 | Neural SDEs / Adversarial robustness / Stock options hedging | 6706 | 8579 | No |
| 4245 | Variational Scholarly Factor Risk Parity Framework Sys-1631 | Delay differential equations / Controlled ODEs / Stock execution | 12102 | 13205 | No |
| 4261 | Variational Scholarly Factor Risk Parity Framework Sys-1727 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 8464 | 10854 | No |
| 4277 | Variational Scholarly Factor Risk Parity Framework Sys-1823 | Topological data analysis / Betti persistence / Stock pairs | 11435 | 12009 | No |
| 4333 | Variational Scholarly Factor Risk Parity Framework Mod-113 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13100 | 12859 | No |
| 4349 | Variational Scholarly Factor Risk Parity Framework Mod-209 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6761 | 8628 | No |
| 4418 | Variational Scholarly Factor Risk Parity Framework Mod-593 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13102 | 12865 | No |
| 4434 | Variational Scholarly Factor Risk Parity Framework Mod-689 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6803 | 8665 | No |
| 4503 | Variational Scholarly Factor Risk Parity Framework Mod-1073 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13104 | 12871 | No |
| 4519 | Variational Scholarly Factor Risk Parity Framework Mod-1169 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6845 | 8702 | No |
| 4588 | Variational Scholarly Factor Risk Parity Framework Mod-1553 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13106 | 12877 | No |
| 4604 | Variational Scholarly Factor Risk Parity Framework Mod-1649 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6887 | 8739 | No |
| 4673 | Variational Scholarly Factor Risk Parity Framework Mod-2033 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13108 | 12883 | No |
| 4689 | Variational Scholarly Factor Risk Parity Framework Mod-2129 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6929 | 8776 | No |
| 4758 | Variational Scholarly Factor Risk Parity Framework Mod-2513 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13110 | 12889 | No |
| 4774 | Variational Scholarly Factor Risk Parity Framework Mod-2609 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6971 | 8813 | No |
| 4843 | Variational Scholarly Factor Risk Parity Framework Mod-2993 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13112 | 12895 | No |
| 4859 | Variational Scholarly Factor Risk Parity Framework Mod-3089 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7013 | 8850 | No |
| 4928 | Variational Scholarly Factor Risk Parity Framework Mod-3473 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13114 | 12901 | No |
| 4944 | Variational Scholarly Factor Risk Parity Framework Mod-3569 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7055 | 8887 | No |
| 5013 | Variational Scholarly Factor Risk Parity Framework Mod-3953 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13116 | 12907 | No |
