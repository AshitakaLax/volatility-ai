# Copula-based approach to factor risk-parity allocation

**Concept page** · shared by **69** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(9 of them in ranks 426–700; best-ranked member #463) ·
researched 2026-10-29

| | |
|---|---|
| Task | Factor risk-parity allocation |
| Method | Copulas / tail-risk budgets |
| Fit with this project | ⏳ for a multi-ETF book (CVaR budgets) |
| Implemented in volatility-ai | No factor risk parity; HRP is built (`hrp.hrp_weights`, A5) and minimum variance is research code (Q13). |
| Evidence | Evidence found (for the task; see the page for the method) |
| Related ledger entries | RK61, A5, RK60, RK296, RK53 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Copula Scholarly Factor
Risk Parity Framework Mod-65") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Budget risk with a copula model of tail dependence, so contributions are
equalised in expected shortfall rather than variance. The closest
evidence is CVaR budgeting: a minimum-CVaR-concentration portfolio of
bonds, commodities, equities and real estate (1984–2010) balanced risk,
return and turnover between the minimum-CVaR and equal-weight
portfolios. Vine copulas suit CVaR portfolios of 3–12 assets (RK296).

## The CSV's description

Proposed copula-based approach to factor risk-parity allocation:
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
* **Boudt, Carl & Peterson (2013), "Asset allocation with conditional
  value-at-risk budgets," *Journal of Risk* 15(3):** ex-ante CVaR
  contributions; the minimum CVaR concentration portfolio compromises
  between minimum-CVaR and equal-weight portfolios on risk-adjusted
  return and turnover. (Abstract.)
* **Low, Alcock, Faff & Brailsford (2013):** Clayton canonical vine
  copulas best for min-CVaR portfolios of 3–12 assets (see RK296).

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
* Boudt, K., Carl, P., Peterson, B. G. (2013). "Asset allocation with
  conditional value-at-risk budgets." *Journal of Risk* 15(3). Abstract.
* Low, R. K. Y., et al. (2013). *Journal of Banking & Finance* 37(8).
  Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 463 | Copula Scholarly Factor Risk Parity Framework Mod-65 | Rough path theory / Tensor signatures / Stock trend forecasting | 5963 | 7731 | No |
| 469 | Copula Scholarly Factor Risk Parity Framework Mod-545 | Rough path theory / Tensor signatures / Stock trend forecasting | 5987 | 7761 | No |
| 475 | Copula Scholarly Factor Risk Parity Framework Mod-1025 | Rough path theory / Tensor signatures / Stock trend forecasting | 6011 | 7791 | No |
| 481 | Copula Scholarly Factor Risk Parity Framework Mod-1505 | Rough path theory / Tensor signatures / Stock trend forecasting | 6035 | 7821 | No |
| 487 | Copula Scholarly Factor Risk Parity Framework Mod-1985 | Rough path theory / Tensor signatures / Stock trend forecasting | 6059 | 7851 | No |
| 493 | Copula Scholarly Factor Risk Parity Framework Mod-2465 | Rough path theory / Tensor signatures / Stock trend forecasting | 6083 | 7881 | No |
| 499 | Copula Scholarly Factor Risk Parity Framework Mod-2945 | Rough path theory / Tensor signatures / Stock trend forecasting | 6107 | 7911 | No |
| 505 | Copula Scholarly Factor Risk Parity Framework Mod-3425 | Rough path theory / Tensor signatures / Stock trend forecasting | 6131 | 7941 | No |
| 511 | Copula Scholarly Factor Risk Parity Framework Mod-3905 | Rough path theory / Tensor signatures / Stock trend forecasting | 6155 | 7971 | No |
| 961 | Copula Scholarly Factor Risk Parity Framework Mod-257 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 4845 | 6754 | No |
| 974 | Copula Scholarly Factor Risk Parity Framework Mod-737 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 4872 | 6788 | No |
| 987 | Copula Scholarly Factor Risk Parity Framework Mod-1217 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 4899 | 6822 | No |
| 1000 | Copula Scholarly Factor Risk Parity Framework Mod-1697 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 4926 | 6856 | No |
| 1013 | Copula Scholarly Factor Risk Parity Framework Mod-2177 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 4953 | 6890 | No |
| 1026 | Copula Scholarly Factor Risk Parity Framework Mod-2657 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 4980 | 6924 | No |
| 1039 | Copula Scholarly Factor Risk Parity Framework Mod-3137 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 5007 | 6958 | No |
| 1052 | Copula Scholarly Factor Risk Parity Framework Mod-3617 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 5034 | 6992 | No |
| 1628 | Copula-Based Scholarly Factor Risk Parity Strategy Ver-84 | Operator theory / Fixed income / ETF allocation | 4591 | 2869 | No |
| 1652 | Copula-Based Scholarly Factor Risk Parity Strategy Ver-184 | Operator theory / Fixed income / ETF allocation | 5803 | 2892 | No |
| 1860 | Copula Scholarly Factor Risk Parity Framework Sys-239 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 4715 | 8484 | No |
| 1909 | Copula Scholarly Factor Risk Parity Framework Sys-719 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 4746 | 8519 | No |
| 1958 | Copula Scholarly Factor Risk Parity Framework Sys-1199 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 4777 | 8554 | No |
| 2007 | Copula Scholarly Factor Risk Parity Framework Sys-1679 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 4808 | 8589 | No |
| 2056 | Copula Scholarly Factor Risk Parity Framework Mod-161 | Graph attention / Sector contagion / Stock baskets | 11456 | 13775 | No |
| 2109 | Copula Scholarly Factor Risk Parity Framework Mod-641 | Graph attention / Sector contagion / Stock baskets | 11483 | 13784 | No |
| 2162 | Copula Scholarly Factor Risk Parity Framework Mod-1121 | Graph attention / Sector contagion / Stock baskets | 11510 | 13793 | No |
| 2215 | Copula Scholarly Factor Risk Parity Framework Mod-1601 | Graph attention / Sector contagion / Stock baskets | 11537 | 13802 | No |
| 2268 | Copula Scholarly Factor Risk Parity Framework Mod-2081 | Graph attention / Sector contagion / Stock baskets | 11564 | 13811 | No |
| 2321 | Copula Scholarly Factor Risk Parity Framework Mod-2561 | Graph attention / Sector contagion / Stock baskets | 11591 | 13820 | No |
| 2374 | Copula Scholarly Factor Risk Parity Framework Mod-3041 | Graph attention / Sector contagion / Stock baskets | 11618 | 13829 | No |
| 2427 | Copula Scholarly Factor Risk Parity Framework Mod-3521 | Graph attention / Sector contagion / Stock baskets | 11645 | 13838 | No |
| 3697 | Copula Scholarly Factor Risk Parity Framework Alpha-69 | Geometric deep learning / Riemannian metrics / Stock risk parity | 9272 | 2911 | No |
| 3714 | Copula Scholarly Factor Risk Parity Framework Alpha-169 | Geometric deep learning / Riemannian metrics / Stock risk parity | 10034 | 2936 | No |
| 3731 | Copula Scholarly Factor Risk Parity Framework Alpha-269 | Geometric deep learning / Riemannian metrics / Stock risk parity | 9281 | 8411 | No |
| 3748 | Copula Scholarly Factor Risk Parity Framework Alpha-369 | Geometric deep learning / Riemannian metrics / Stock risk parity | 9284 | 2979 | No |
| 3765 | Copula Scholarly Factor Risk Parity Framework Alpha-469 | Geometric deep learning / Riemannian metrics / Stock risk parity | 10045 | 3004 | No |
| 3959 | Copula Scholarly Factor Risk Parity Framework Sys-47 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10068 | 10773 | No |
| 3977 | Copula Scholarly Factor Risk Parity Framework Sys-143 | Topological data analysis / Betti persistence / Stock pairs | 12278 | 11928 | No |
| 4013 | Copula Scholarly Factor Risk Parity Framework Sys-335 | Neural SDEs / Adversarial robustness / Stock options hedging | 9333 | 10295 | No |
| 4028 | Copula Scholarly Factor Risk Parity Framework Sys-431 | Delay differential equations / Controlled ODEs / Stock execution | 12657 | 13741 | No |
| 4045 | Copula Scholarly Factor Risk Parity Framework Sys-527 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10079 | 10796 | No |
| 4063 | Copula Scholarly Factor Risk Parity Framework Sys-623 | Topological data analysis / Betti persistence / Stock pairs | 12288 | 11951 | No |
| 4099 | Copula Scholarly Factor Risk Parity Framework Sys-815 | Neural SDEs / Adversarial robustness / Stock options hedging | 9349 | 10297 | No |
| 4114 | Copula Scholarly Factor Risk Parity Framework Sys-911 | Delay differential equations / Controlled ODEs / Stock execution | 12662 | 13750 | No |
| 4131 | Copula Scholarly Factor Risk Parity Framework Sys-1007 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10090 | 10819 | No |
| 4149 | Copula Scholarly Factor Risk Parity Framework Sys-1103 | Topological data analysis / Betti persistence / Stock pairs | 12298 | 11974 | No |
| 4185 | Copula Scholarly Factor Risk Parity Framework Sys-1295 | Neural SDEs / Adversarial robustness / Stock options hedging | 9365 | 10299 | No |
| 4200 | Copula Scholarly Factor Risk Parity Framework Sys-1391 | Delay differential equations / Controlled ODEs / Stock execution | 12667 | 13759 | No |
| 4217 | Copula Scholarly Factor Risk Parity Framework Sys-1487 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10101 | 10842 | No |
| 4235 | Copula Scholarly Factor Risk Parity Framework Sys-1583 | Topological data analysis / Betti persistence / Stock pairs | 12308 | 11997 | No |
| 4271 | Copula Scholarly Factor Risk Parity Framework Sys-1775 | Neural SDEs / Adversarial robustness / Stock options hedging | 9381 | 10301 | No |
| 4286 | Copula Scholarly Factor Risk Parity Framework Sys-1871 | Delay differential equations / Controlled ODEs / Stock execution | 12672 | 13768 | No |
| 4303 | Copula Scholarly Factor Risk Parity Framework Sys-1967 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10112 | 10865 | No |
| 4373 | Copula Scholarly Factor Risk Parity Framework Mod-353 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13591 | 13528 | No |
| 4390 | Copula Scholarly Factor Risk Parity Framework Mod-449 | Geometric deep learning / Riemannian metrics / Stock risk parity | 9403 | 8646 | No |
| 4458 | Copula Scholarly Factor Risk Parity Framework Mod-833 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13592 | 13535 | No |
| 4475 | Copula Scholarly Factor Risk Parity Framework Mod-929 | Geometric deep learning / Riemannian metrics / Stock risk parity | 9420 | 8683 | No |
| 4543 | Copula Scholarly Factor Risk Parity Framework Mod-1313 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13593 | 13542 | No |
| 4560 | Copula Scholarly Factor Risk Parity Framework Mod-1409 | Geometric deep learning / Riemannian metrics / Stock risk parity | 9437 | 8720 | No |
| 4628 | Copula Scholarly Factor Risk Parity Framework Mod-1793 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13594 | 13549 | No |
| 4645 | Copula Scholarly Factor Risk Parity Framework Mod-1889 | Geometric deep learning / Riemannian metrics / Stock risk parity | 9454 | 8757 | No |
| 4713 | Copula Scholarly Factor Risk Parity Framework Mod-2273 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13595 | 13556 | No |
| 4730 | Copula Scholarly Factor Risk Parity Framework Mod-2369 | Geometric deep learning / Riemannian metrics / Stock risk parity | 9471 | 8794 | No |
| 4798 | Copula Scholarly Factor Risk Parity Framework Mod-2753 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13596 | 13563 | No |
| 4815 | Copula Scholarly Factor Risk Parity Framework Mod-2849 | Geometric deep learning / Riemannian metrics / Stock risk parity | 9488 | 8831 | No |
| 4883 | Copula Scholarly Factor Risk Parity Framework Mod-3233 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13597 | 13570 | No |
| 4900 | Copula Scholarly Factor Risk Parity Framework Mod-3329 | Geometric deep learning / Riemannian metrics / Stock risk parity | 9505 | 8868 | No |
| 4968 | Copula Scholarly Factor Risk Parity Framework Mod-3713 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13598 | 13577 | No |
| 4985 | Copula Scholarly Factor Risk Parity Framework Mod-3809 | Geometric deep learning / Riemannian metrics / Stock risk parity | 9522 | 8905 | No |
