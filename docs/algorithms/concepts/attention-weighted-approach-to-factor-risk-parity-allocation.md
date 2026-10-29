# Attention-weighted approach to factor risk-parity allocation

**Concept page** · shared by **10** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(2 of them in ranks 426–700; best-ranked member #429) ·
researched 2026-10-29

| | |
|---|---|
| Task | Factor risk-parity allocation |
| Method | Attention networks |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **Research code** in `research.catalog.concepts`: `attention_factor_risk_parity`, `attention_budgets`; tested on synthetic data, not wired into the engine. Related code already here: No factor risk parity; HRP is built (`hrp.hrp_weights`, A5) and minimum variance is research code (Q13). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK61, A5, RK60 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Attentional Scholarly
Factor Risk Parity Framework Ref-145") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Weight factor risk contributions with an attention network. Factor risk
parity itself is established (Roncalli and Weisang); I found no study
applying this method to it.

## The CSV's description

Proposed attention-weighted approach to factor risk-parity allocation:
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
| 429 | Attentional Scholarly Factor Risk Parity Framework Ref-145 | Rough path theory / Tensor signatures / Stock trend forecasting | 2134 | 3045 | No |
| 435 | Attentional Scholarly Factor Risk Parity Framework Ref-625 | Rough path theory / Tensor signatures / Stock trend forecasting | 2166 | 3162 | No |
| 891 | Attentional Scholarly Factor Risk Parity Framework Ref-337 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 5841 | 11310 | No |
| 901 | Attentional Scholarly Factor Risk Parity Framework Ref-817 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 5866 | 11331 | No |
| 1754 | Attentional Scholarly Factor Risk Parity Framework Ref-241 | Graph attention / Sector contagion / Stock baskets | 710 | 1024 | No |
| 1809 | Attentional Scholarly Factor Risk Parity Framework Ref-721 | Graph attention / Sector contagion / Stock baskets | 726 | 1059 | No |
| 3779 | Attentional Scholarly Factor Risk Parity Framework Ref-49 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8239 | 3023 | No |
| 3849 | Attentional Scholarly Factor Risk Parity Framework Ref-433 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7795 | 5979 | No |
| 3865 | Attentional Scholarly Factor Risk Parity Framework Ref-529 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8280 | 3140 | No |
| 3935 | Attentional Scholarly Factor Risk Parity Framework Ref-913 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7812 | 5999 | No |
