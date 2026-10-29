# Robust approach to factor risk-parity allocation

**Concept page** · shared by **18** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(3 of them in ranks 426–700; best-ranked member #428) ·
researched 2026-10-29

| | |
|---|---|
| Task | Factor risk-parity allocation |
| Method | Robust estimation of the factor covariance |
| Fit with this project | ⏳ for a multi-ETF book · no method-specific evidence |
| Implemented in volatility-ai | **Research code** in `research.catalog.concepts`: `robust_factor_risk_parity`, `factor_risk_parity`; tested on synthetic data, not wired into the engine. Related code already here: No factor risk parity; HRP is built (`hrp.hrp_weights`, A5) and minimum variance is research code (Q13). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK61, A5, RK60 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Robust Scholarly Factor
Risk Parity Framework Ref-25") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Equalise factor risk contributions using robust estimates of the factor
covariance, so outliers and estimation error matter less. Robust
estimators make minimum-variance portfolios less sensitive to the return
distribution (DeMiguel and Nogales); I found no study of robust factor
risk parity specifically.

## The CSV's description

Proposed robust approach to factor risk-parity allocation: Estimate
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
* **DeMiguel & Nogales (2009), "Portfolio selection with robust
  estimation," *Operations Research* 57(3), 560–577:** M- and
  S-estimators make minimum-variance weights more stable and less
  sensitive to the return distribution. (Abstract and review.)

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
* DeMiguel, V., Nogales, F. J. (2009). *Operations Research* 57(3),
  560–577. doi:10.1287/opre.1080.0566. Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 428 | Robust Scholarly Factor Risk Parity Framework Ref-25 | Rough path theory / Tensor signatures / Stock trend forecasting | 2128 | 3016 | No |
| 434 | Robust Scholarly Factor Risk Parity Framework Ref-505 | Rough path theory / Tensor signatures / Stock trend forecasting | 2160 | 3133 | No |
| 440 | Robust Scholarly Factor Risk Parity Framework Ref-985 | Rough path theory / Tensor signatures / Stock trend forecasting | 2192 | 3250 | No |
| 887 | Robust Scholarly Factor Risk Parity Framework Ref-217 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 5835 | 11305 | No |
| 897 | Robust Scholarly Factor Risk Parity Framework Ref-697 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 5860 | 11326 | No |
| 1611 | Robust Scholarly Factor Risk Parity Strategy Ver-4 | Operator theory / Fixed income / ETF allocation | 3819 | 967 | No |
| 1635 | Robust Scholarly Factor Risk Parity Strategy Ver-104 | Operator theory / Fixed income / ETF allocation | 2067 | 2874 | No |
| 1739 | Robust Scholarly Factor Risk Parity Framework Ref-121 | Graph attention / Sector contagion / Stock baskets | 706 | 1014 | No |
| 1794 | Robust Scholarly Factor Risk Parity Framework Ref-601 | Graph attention / Sector contagion / Stock baskets | 722 | 1049 | No |
| 3688 | Robust Scholarly Factor Risk Parity Framework Alpha-9 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6460 | 2898 | No |
| 3705 | Robust Scholarly Factor Risk Parity Framework Alpha-109 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8190 | 2923 | No |
| 3722 | Robust Scholarly Factor Risk Parity Framework Alpha-209 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6473 | 8408 | No |
| 3739 | Robust Scholarly Factor Risk Parity Framework Alpha-309 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6478 | 2966 | No |
| 3756 | Robust Scholarly Factor Risk Parity Framework Alpha-409 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8223 | 2991 | No |
| 3826 | Robust Scholarly Factor Risk Parity Framework Ref-313 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7791 | 5974 | No |
| 3845 | Robust Scholarly Factor Risk Parity Framework Ref-409 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8268 | 3112 | No |
| 3912 | Robust Scholarly Factor Risk Parity Framework Ref-793 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7808 | 5994 | No |
| 3931 | Robust Scholarly Factor Risk Parity Framework Ref-889 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8309 | 3229 | No |
