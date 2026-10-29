# Path-signature-based approach to factor risk-parity allocation

**Concept page** · shared by **63** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(13 of them in ranks 426–700; best-ranked member #513) ·
researched 2026-10-29

| | |
|---|---|
| Task | Factor risk-parity allocation |
| Method | Path signatures |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **Research code** in `research.catalog.concepts`: `signature_factor_risk_parity`, `lead_lag_signature_covariance`; tested on synthetic data, not wired into the engine. Related code already here: No factor risk parity; HRP is built (`hrp.hrp_weights`, A5) and minimum variance is research code (Q13). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK61, A5, RK60 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Signature Scholarly Factor
Risk Parity Framework Eng-5") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Describe factor paths by their signatures and budget risk on those
features. Factor risk parity itself is established (Roncalli and
Weisang); I found no study applying this method to it.

## The CSV's description

Proposed path-signature-based approach to factor risk-parity allocation:
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
* **Futter, Horvath & Wiese (2023):** signature trading gives a
  path-dependent mean-variance solution (see RK328); not a risk-parity
  method.

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
| 513 | Signature Scholarly Factor Risk Parity Framework Eng-5 | Rough path theory / Tensor signatures / Stock trend forecasting | 4258 | 7978 | No |
| 519 | Signature Scholarly Factor Risk Parity Framework Eng-485 | Rough path theory / Tensor signatures / Stock trend forecasting | 4284 | 8010 | No |
| 525 | Signature Scholarly Factor Risk Parity Framework Eng-965 | Rough path theory / Tensor signatures / Stock trend forecasting | 4310 | 8042 | No |
| 531 | Signature Scholarly Factor Risk Parity Framework Eng-1445 | Rough path theory / Tensor signatures / Stock trend forecasting | 4336 | 8074 | No |
| 537 | Signature Scholarly Factor Risk Parity Framework Eng-1925 | Rough path theory / Tensor signatures / Stock trend forecasting | 4362 | 8106 | No |
| 543 | Signature Scholarly Factor Risk Parity Framework Eng-2405 | Rough path theory / Tensor signatures / Stock trend forecasting | 4388 | 8138 | No |
| 549 | Signature Scholarly Factor Risk Parity Framework Eng-2885 | Rough path theory / Tensor signatures / Stock trend forecasting | 4414 | 8170 | No |
| 555 | Signature Scholarly Factor Risk Parity Framework Eng-3365 | Rough path theory / Tensor signatures / Stock trend forecasting | 4440 | 8202 | No |
| 561 | Signature Scholarly Factor Risk Parity Framework Eng-3845 | Rough path theory / Tensor signatures / Stock trend forecasting | 4466 | 8234 | No |
| 567 | Signature Scholarly Factor Risk Parity Framework Eng-4325 | Rough path theory / Tensor signatures / Stock trend forecasting | 4492 | 8266 | No |
| 573 | Signature Scholarly Factor Risk Parity Framework Eng-4805 | Rough path theory / Tensor signatures / Stock trend forecasting | 4518 | 8298 | No |
| 579 | Signature Scholarly Factor Risk Parity Framework Eng-5285 | Rough path theory / Tensor signatures / Stock trend forecasting | 4544 | 8330 | No |
| 585 | Signature Scholarly Factor Risk Parity Framework Eng-5765 | Rough path theory / Tensor signatures / Stock trend forecasting | 4570 | 8362 | No |
| 1066 | Signature Scholarly Factor Risk Parity Framework Eng-197 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2726 | 7032 | No |
| 1076 | Signature Scholarly Factor Risk Parity Framework Eng-677 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2764 | 7064 | No |
| 1086 | Signature Scholarly Factor Risk Parity Framework Eng-1157 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2802 | 7096 | No |
| 1096 | Signature Scholarly Factor Risk Parity Framework Eng-1637 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2840 | 7128 | No |
| 1106 | Signature Scholarly Factor Risk Parity Framework Eng-2117 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2878 | 7160 | No |
| 1116 | Signature Scholarly Factor Risk Parity Framework Eng-2597 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2916 | 7192 | No |
| 1126 | Signature Scholarly Factor Risk Parity Framework Eng-3077 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2954 | 7224 | No |
| 1136 | Signature Scholarly Factor Risk Parity Framework Eng-3557 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2992 | 7256 | No |
| 1146 | Signature Scholarly Factor Risk Parity Framework Eng-4037 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 3030 | 7288 | No |
| 1156 | Signature Scholarly Factor Risk Parity Framework Eng-4517 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 3068 | 7320 | No |
| 1166 | Signature Scholarly Factor Risk Parity Framework Eng-4997 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 3106 | 7352 | No |
| 1176 | Signature Scholarly Factor Risk Parity Framework Eng-5477 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 3144 | 7384 | No |
| 1186 | Signature Scholarly Factor Risk Parity Framework Eng-5957 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 3182 | 7416 | No |
| 2491 | Signature Scholarly Factor Risk Parity Framework Eng-101 | Graph attention / Sector contagion / Stock baskets | 10654 | 13335 | No |
| 2546 | Signature Scholarly Factor Risk Parity Framework Eng-581 | Graph attention / Sector contagion / Stock baskets | 10660 | 13349 | No |
| 2601 | Signature Scholarly Factor Risk Parity Framework Eng-1061 | Graph attention / Sector contagion / Stock baskets | 10666 | 13363 | No |
| 2656 | Signature Scholarly Factor Risk Parity Framework Eng-1541 | Graph attention / Sector contagion / Stock baskets | 10672 | 13377 | No |
| 2711 | Signature Scholarly Factor Risk Parity Framework Eng-2021 | Graph attention / Sector contagion / Stock baskets | 10678 | 13391 | No |
| 2766 | Signature Scholarly Factor Risk Parity Framework Eng-2501 | Graph attention / Sector contagion / Stock baskets | 10684 | 13405 | No |
| 2821 | Signature Scholarly Factor Risk Parity Framework Eng-2981 | Graph attention / Sector contagion / Stock baskets | 10690 | 13419 | No |
| 2876 | Signature Scholarly Factor Risk Parity Framework Eng-3461 | Graph attention / Sector contagion / Stock baskets | 10696 | 13433 | No |
| 2931 | Signature Scholarly Factor Risk Parity Framework Eng-3941 | Graph attention / Sector contagion / Stock baskets | 10702 | 13447 | No |
| 2986 | Signature Scholarly Factor Risk Parity Framework Eng-4421 | Graph attention / Sector contagion / Stock baskets | 10708 | 13461 | No |
| 3041 | Signature Scholarly Factor Risk Parity Framework Eng-4901 | Graph attention / Sector contagion / Stock baskets | 10714 | 13475 | No |
| 3096 | Signature Scholarly Factor Risk Parity Framework Eng-5381 | Graph attention / Sector contagion / Stock baskets | 10720 | 13489 | No |
| 3151 | Signature Scholarly Factor Risk Parity Framework Eng-5861 | Graph attention / Sector contagion / Stock baskets | 10726 | 13503 | No |
| 5074 | Signature Scholarly Factor Risk Parity Framework Eng-293 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13119 | 12912 | No |
| 5092 | Signature Scholarly Factor Risk Parity Framework Eng-389 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7128 | 8948 | No |
| 5160 | Signature Scholarly Factor Risk Parity Framework Eng-773 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13123 | 12920 | No |
| 5178 | Signature Scholarly Factor Risk Parity Framework Eng-869 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7170 | 8983 | No |
| 5246 | Signature Scholarly Factor Risk Parity Framework Eng-1253 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13127 | 12928 | No |
| 5264 | Signature Scholarly Factor Risk Parity Framework Eng-1349 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7212 | 9018 | No |
| 5332 | Signature Scholarly Factor Risk Parity Framework Eng-1733 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13131 | 12936 | No |
| 5350 | Signature Scholarly Factor Risk Parity Framework Eng-1829 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7254 | 9053 | No |
| 5418 | Signature Scholarly Factor Risk Parity Framework Eng-2213 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13135 | 12944 | No |
| 5436 | Signature Scholarly Factor Risk Parity Framework Eng-2309 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7296 | 9088 | No |
| 5504 | Signature Scholarly Factor Risk Parity Framework Eng-2693 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13139 | 12952 | No |
| 5522 | Signature Scholarly Factor Risk Parity Framework Eng-2789 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7338 | 9123 | No |
| 5590 | Signature Scholarly Factor Risk Parity Framework Eng-3173 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13143 | 12960 | No |
| 5608 | Signature Scholarly Factor Risk Parity Framework Eng-3269 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7380 | 9158 | No |
| 5676 | Signature Scholarly Factor Risk Parity Framework Eng-3653 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13147 | 12968 | No |
| 5694 | Signature Scholarly Factor Risk Parity Framework Eng-3749 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7422 | 9193 | No |
| 5762 | Signature Scholarly Factor Risk Parity Framework Eng-4133 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13151 | 12976 | No |
| 5780 | Signature Scholarly Factor Risk Parity Framework Eng-4229 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7464 | 9228 | No |
| 5848 | Signature Scholarly Factor Risk Parity Framework Eng-4613 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13155 | 12984 | No |
| 5866 | Signature Scholarly Factor Risk Parity Framework Eng-4709 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7506 | 9263 | No |
| 5934 | Signature Scholarly Factor Risk Parity Framework Eng-5093 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13159 | 12992 | No |
| 5952 | Signature Scholarly Factor Risk Parity Framework Eng-5189 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7548 | 9298 | No |
| 6020 | Signature Scholarly Factor Risk Parity Framework Eng-5573 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13163 | 13000 | No |
| 6038 | Signature Scholarly Factor Risk Parity Framework Eng-5669 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7590 | 9333 | No |
