# Evolutionary-optimization-based approach to factor risk-parity allocation

**Concept page** · shared by **62** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(12 of them in ranks 426–700; best-ranked member #517) ·
researched 2026-10-29

| | |
|---|---|
| Task | Factor risk-parity allocation |
| Method | Evolutionary / genetic optimisation |
| Fit with this project | ⛔ (risk parity is convex; nothing to search) |
| Implemented in volatility-ai | No factor risk parity; HRP is built (`hrp.hrp_weights`, A5) and minimum variance is research code (Q13). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK61, A5, RK60 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Evolutionary Scholarly
Factor Risk Parity Framework Eng-365") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Search for risk-parity weights with genetic algorithms instead of convex
solvers. Factor risk parity itself is established (Roncalli and
Weisang); I found no study applying this method to it.

## The CSV's description

Proposed evolutionary-optimization-based approach to factor risk-parity
allocation: Estimate factor volatility and dependence, then choose
portfolio weights so risk contributions align with a target risk budget.
This is a concept-level interpretation of the title, not a complete
trading specification: the exact model inputs/target, calibration,
entry/exit or rebalance rules, and position sizing are not fully defined
here.

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
* Equal risk contributions are a convex problem with a unique solution
  for assets (not always for factors); a genetic search adds noise, not
  quality.

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
| 517 | Evolutionary Scholarly Factor Risk Parity Framework Eng-365 | Rough path theory / Tensor signatures / Stock trend forecasting | 4277 | 8002 | No |
| 523 | Evolutionary Scholarly Factor Risk Parity Framework Eng-845 | Rough path theory / Tensor signatures / Stock trend forecasting | 4303 | 8034 | No |
| 529 | Evolutionary Scholarly Factor Risk Parity Framework Eng-1325 | Rough path theory / Tensor signatures / Stock trend forecasting | 4329 | 8066 | No |
| 535 | Evolutionary Scholarly Factor Risk Parity Framework Eng-1805 | Rough path theory / Tensor signatures / Stock trend forecasting | 4355 | 8098 | No |
| 541 | Evolutionary Scholarly Factor Risk Parity Framework Eng-2285 | Rough path theory / Tensor signatures / Stock trend forecasting | 4381 | 8130 | No |
| 547 | Evolutionary Scholarly Factor Risk Parity Framework Eng-2765 | Rough path theory / Tensor signatures / Stock trend forecasting | 4407 | 8162 | No |
| 553 | Evolutionary Scholarly Factor Risk Parity Framework Eng-3245 | Rough path theory / Tensor signatures / Stock trend forecasting | 4433 | 8194 | No |
| 559 | Evolutionary Scholarly Factor Risk Parity Framework Eng-3725 | Rough path theory / Tensor signatures / Stock trend forecasting | 4459 | 8226 | No |
| 565 | Evolutionary Scholarly Factor Risk Parity Framework Eng-4205 | Rough path theory / Tensor signatures / Stock trend forecasting | 4485 | 8258 | No |
| 571 | Evolutionary Scholarly Factor Risk Parity Framework Eng-4685 | Rough path theory / Tensor signatures / Stock trend forecasting | 4511 | 8290 | No |
| 577 | Evolutionary Scholarly Factor Risk Parity Framework Eng-5165 | Rough path theory / Tensor signatures / Stock trend forecasting | 4537 | 8322 | No |
| 583 | Evolutionary Scholarly Factor Risk Parity Framework Eng-5645 | Rough path theory / Tensor signatures / Stock trend forecasting | 4563 | 8354 | No |
| 1064 | Evolutionary Scholarly Factor Risk Parity Framework Eng-77 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2717 | 7024 | No |
| 1074 | Evolutionary Scholarly Factor Risk Parity Framework Eng-557 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2755 | 7056 | No |
| 1084 | Evolutionary Scholarly Factor Risk Parity Framework Eng-1037 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2793 | 7088 | No |
| 1094 | Evolutionary Scholarly Factor Risk Parity Framework Eng-1517 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2831 | 7120 | No |
| 1104 | Evolutionary Scholarly Factor Risk Parity Framework Eng-1997 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2869 | 7152 | No |
| 1114 | Evolutionary Scholarly Factor Risk Parity Framework Eng-2477 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2907 | 7184 | No |
| 1124 | Evolutionary Scholarly Factor Risk Parity Framework Eng-2957 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2945 | 7216 | No |
| 1134 | Evolutionary Scholarly Factor Risk Parity Framework Eng-3437 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2983 | 7248 | No |
| 1144 | Evolutionary Scholarly Factor Risk Parity Framework Eng-3917 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 3021 | 7280 | No |
| 1154 | Evolutionary Scholarly Factor Risk Parity Framework Eng-4397 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 3059 | 7312 | No |
| 1164 | Evolutionary Scholarly Factor Risk Parity Framework Eng-4877 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 3097 | 7344 | No |
| 1174 | Evolutionary Scholarly Factor Risk Parity Framework Eng-5357 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 3135 | 7376 | No |
| 1184 | Evolutionary Scholarly Factor Risk Parity Framework Eng-5837 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 3173 | 7408 | No |
| 2531 | Evolutionary Scholarly Factor Risk Parity Framework Eng-461 | Graph attention / Sector contagion / Stock baskets | 10659 | 13345 | No |
| 2586 | Evolutionary Scholarly Factor Risk Parity Framework Eng-941 | Graph attention / Sector contagion / Stock baskets | 10665 | 13359 | No |
| 2641 | Evolutionary Scholarly Factor Risk Parity Framework Eng-1421 | Graph attention / Sector contagion / Stock baskets | 10671 | 13373 | No |
| 2696 | Evolutionary Scholarly Factor Risk Parity Framework Eng-1901 | Graph attention / Sector contagion / Stock baskets | 10677 | 13387 | No |
| 2751 | Evolutionary Scholarly Factor Risk Parity Framework Eng-2381 | Graph attention / Sector contagion / Stock baskets | 10683 | 13401 | No |
| 2806 | Evolutionary Scholarly Factor Risk Parity Framework Eng-2861 | Graph attention / Sector contagion / Stock baskets | 10689 | 13415 | No |
| 2861 | Evolutionary Scholarly Factor Risk Parity Framework Eng-3341 | Graph attention / Sector contagion / Stock baskets | 10695 | 13429 | No |
| 2916 | Evolutionary Scholarly Factor Risk Parity Framework Eng-3821 | Graph attention / Sector contagion / Stock baskets | 10701 | 13443 | No |
| 2971 | Evolutionary Scholarly Factor Risk Parity Framework Eng-4301 | Graph attention / Sector contagion / Stock baskets | 10707 | 13457 | No |
| 3026 | Evolutionary Scholarly Factor Risk Parity Framework Eng-4781 | Graph attention / Sector contagion / Stock baskets | 10713 | 13471 | No |
| 3081 | Evolutionary Scholarly Factor Risk Parity Framework Eng-5261 | Graph attention / Sector contagion / Stock baskets | 10719 | 13485 | No |
| 3136 | Evolutionary Scholarly Factor Risk Parity Framework Eng-5741 | Graph attention / Sector contagion / Stock baskets | 10725 | 13499 | No |
| 5053 | Evolutionary Scholarly Factor Risk Parity Framework Eng-173 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13118 | 12910 | No |
| 5070 | Evolutionary Scholarly Factor Risk Parity Framework Eng-269 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7117 | 8938 | No |
| 5139 | Evolutionary Scholarly Factor Risk Parity Framework Eng-653 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13122 | 12918 | No |
| 5156 | Evolutionary Scholarly Factor Risk Parity Framework Eng-749 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7159 | 8973 | No |
| 5225 | Evolutionary Scholarly Factor Risk Parity Framework Eng-1133 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13126 | 12926 | No |
| 5242 | Evolutionary Scholarly Factor Risk Parity Framework Eng-1229 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7201 | 9008 | No |
| 5311 | Evolutionary Scholarly Factor Risk Parity Framework Eng-1613 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13130 | 12934 | No |
| 5328 | Evolutionary Scholarly Factor Risk Parity Framework Eng-1709 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7243 | 9043 | No |
| 5397 | Evolutionary Scholarly Factor Risk Parity Framework Eng-2093 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13134 | 12942 | No |
| 5414 | Evolutionary Scholarly Factor Risk Parity Framework Eng-2189 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7285 | 9078 | No |
| 5483 | Evolutionary Scholarly Factor Risk Parity Framework Eng-2573 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13138 | 12950 | No |
| 5500 | Evolutionary Scholarly Factor Risk Parity Framework Eng-2669 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7327 | 9113 | No |
| 5569 | Evolutionary Scholarly Factor Risk Parity Framework Eng-3053 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13142 | 12958 | No |
| 5586 | Evolutionary Scholarly Factor Risk Parity Framework Eng-3149 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7369 | 9148 | No |
| 5655 | Evolutionary Scholarly Factor Risk Parity Framework Eng-3533 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13146 | 12966 | No |
| 5672 | Evolutionary Scholarly Factor Risk Parity Framework Eng-3629 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7411 | 9183 | No |
| 5741 | Evolutionary Scholarly Factor Risk Parity Framework Eng-4013 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13150 | 12974 | No |
| 5758 | Evolutionary Scholarly Factor Risk Parity Framework Eng-4109 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7453 | 9218 | No |
| 5827 | Evolutionary Scholarly Factor Risk Parity Framework Eng-4493 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13154 | 12982 | No |
| 5844 | Evolutionary Scholarly Factor Risk Parity Framework Eng-4589 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7495 | 9253 | No |
| 5913 | Evolutionary Scholarly Factor Risk Parity Framework Eng-4973 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13158 | 12990 | No |
| 5930 | Evolutionary Scholarly Factor Risk Parity Framework Eng-5069 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7537 | 9288 | No |
| 5999 | Evolutionary Scholarly Factor Risk Parity Framework Eng-5453 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13162 | 12998 | No |
| 6016 | Evolutionary Scholarly Factor Risk Parity Framework Eng-5549 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7579 | 9323 | No |
| 6085 | Evolutionary Scholarly Factor Risk Parity Framework Eng-5933 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13166 | 13006 | No |
