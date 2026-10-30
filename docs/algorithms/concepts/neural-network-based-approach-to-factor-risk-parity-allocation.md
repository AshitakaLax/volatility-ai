# Neural-network-based approach to factor risk-parity allocation

**Concept page** · shared by **68** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #769) ·
researched 2026-10-30

| | |
|---|---|
| Task | Factor risk-parity allocation |
| Method | Neural networks |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of neural networks improving factor risk parity, and the book has no factors to budget. |
| Implemented in volatility-ai | Factor risk parity is research code (`concepts.factor_risk_parity`); HRP is built (A5). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK61, A5, RK60 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Neural Scholarly Factor
Risk Parity Framework Eng-125") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Estimate factor volatility and dependence, then choose weights so the
factors' risk contributions match a target budget. The neural-network
version fits a neural network to the task. I found no study of this
method on this task.

## The CSV's description

Proposed neural-network-based approach to factor risk-parity allocation:
Estimate factor volatility and dependence, then choose portfolio weights
so risk contributions align with a target risk budget. This is a
concept-level interpretation of the title, not a complete trading
specification: the exact model inputs/target, calibration, entry/exit or
rebalance rules, and position sizing are not fully defined here.

## Evidence

* **Roncalli & Weisang (2016), "Risk parity portfolios with risk
  factors," *Quantitative Finance* 16(3), 377–388:** equalise factor
  risk contributions instead of asset contributions; the solution can be
  non-unique. (Abstract.)
* **Asness, Frazzini & Pedersen (2012), *Financial Analysts Journal*:**
  risk parity's historical edge relies on leverage (see RK61). (Standard
  reference.)

## Against, and failure modes

* Factor risk parity needs a factor model whose loadings drift;
  solutions can be non-unique.
* Unlevered risk parity is a low-volatility, bond-heavy portfolio; its
  historical edge came with leverage (RK61).
* Neural forecasts on one index have not reliably beaten simple rules;
  an LSTM's stock picks were largely short-term reversal (Fischer &
  Krauss 2018, RK292).

## Fit with volatility-ai

An allocator for a multi-asset book; the engine trades one symbol. HRP
(A5) is the built allocator, and factor risk parity adds a factor model
a book of a few ETFs does not need.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Roncalli, T., Weisang, G. (2016). *Quantitative Finance* 16(3),
  377–388. Abstract.
* Asness, C., Frazzini, A., Pedersen, L. H. (2012). "Leverage aversion
  and risk parity." *Financial Analysts Journal* 68(1). Standard
  reference.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 769 | Neural Scholarly Factor Risk Parity Framework Eng-125 | Rough path theory / Tensor signatures / Stock trend forecasting | 4264 | 7986 | No |
| 775 | Neural Scholarly Factor Risk Parity Framework Eng-605 | Rough path theory / Tensor signatures / Stock trend forecasting | 4290 | 8018 | No |
| 781 | Neural Scholarly Factor Risk Parity Framework Eng-1085 | Rough path theory / Tensor signatures / Stock trend forecasting | 4316 | 8050 | No |
| 787 | Neural Scholarly Factor Risk Parity Framework Eng-1565 | Rough path theory / Tensor signatures / Stock trend forecasting | 4342 | 8082 | No |
| 793 | Neural Scholarly Factor Risk Parity Framework Eng-2045 | Rough path theory / Tensor signatures / Stock trend forecasting | 4368 | 8114 | No |
| 799 | Neural Scholarly Factor Risk Parity Framework Eng-2525 | Rough path theory / Tensor signatures / Stock trend forecasting | 4394 | 8146 | No |
| 805 | Neural Scholarly Factor Risk Parity Framework Eng-3005 | Rough path theory / Tensor signatures / Stock trend forecasting | 4420 | 8178 | No |
| 811 | Neural Scholarly Factor Risk Parity Framework Eng-3485 | Rough path theory / Tensor signatures / Stock trend forecasting | 4446 | 8210 | No |
| 817 | Neural Scholarly Factor Risk Parity Framework Eng-3965 | Rough path theory / Tensor signatures / Stock trend forecasting | 4472 | 8242 | No |
| 823 | Neural Scholarly Factor Risk Parity Framework Eng-4445 | Rough path theory / Tensor signatures / Stock trend forecasting | 4498 | 8274 | No |
| 829 | Neural Scholarly Factor Risk Parity Framework Eng-4925 | Rough path theory / Tensor signatures / Stock trend forecasting | 4524 | 8306 | No |
| 835 | Neural Scholarly Factor Risk Parity Framework Eng-5405 | Rough path theory / Tensor signatures / Stock trend forecasting | 4550 | 8338 | No |
| 841 | Neural Scholarly Factor Risk Parity Framework Eng-5885 | Rough path theory / Tensor signatures / Stock trend forecasting | 4576 | 8370 | No |
| 1563 | Neural Scholarly Factor Risk Parity Framework Eng-317 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2735 | 7040 | No |
| 1566 | Neural Scholarly Factor Risk Parity Framework Eng-797 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2773 | 7072 | No |
| 1569 | Neural Scholarly Factor Risk Parity Framework Eng-1277 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2811 | 7104 | No |
| 1572 | Neural Scholarly Factor Risk Parity Framework Eng-1757 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2849 | 7136 | No |
| 1575 | Neural Scholarly Factor Risk Parity Framework Eng-2237 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2887 | 7168 | No |
| 1578 | Neural Scholarly Factor Risk Parity Framework Eng-2717 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2925 | 7200 | No |
| 1581 | Neural Scholarly Factor Risk Parity Framework Eng-3197 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 2963 | 7232 | No |
| 1584 | Neural Scholarly Factor Risk Parity Framework Eng-3677 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 3001 | 7264 | No |
| 1587 | Neural Scholarly Factor Risk Parity Framework Eng-4157 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 3039 | 7296 | No |
| 1590 | Neural Scholarly Factor Risk Parity Framework Eng-4637 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 3077 | 7328 | No |
| 1593 | Neural Scholarly Factor Risk Parity Framework Eng-5117 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 3115 | 7360 | No |
| 1596 | Neural Scholarly Factor Risk Parity Framework Eng-5597 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 3153 | 7392 | No |
| 3691 | Neural Scholarly Factor Risk Parity Framework Alpha-29 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6462 | 8395 | No |
| 3708 | Neural Scholarly Factor Risk Parity Framework Alpha-129 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6466 | 2925 | No |
| 3725 | Neural Scholarly Factor Risk Parity Framework Alpha-229 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8204 | 2949 | No |
| 3742 | Neural Scholarly Factor Risk Parity Framework Alpha-329 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6480 | 8413 | No |
| 3759 | Neural Scholarly Factor Risk Parity Framework Alpha-429 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6484 | 2993 | No |
| 5028 | Neural Scholarly Factor Risk Parity Framework Eng-29 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7096 | 8923 | No |
| 5062 | Neural Scholarly Factor Risk Parity Framework Eng-221 | Graph attention / Sector contagion / Stock baskets | 10655 | 13338 | No |
| 5096 | Neural Scholarly Factor Risk Parity Framework Eng-413 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13120 | 12914 | No |
| 5114 | Neural Scholarly Factor Risk Parity Framework Eng-509 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7138 | 8958 | No |
| 5148 | Neural Scholarly Factor Risk Parity Framework Eng-701 | Graph attention / Sector contagion / Stock baskets | 10661 | 13352 | No |
| 5182 | Neural Scholarly Factor Risk Parity Framework Eng-893 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13124 | 12922 | No |
| 5200 | Neural Scholarly Factor Risk Parity Framework Eng-989 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7180 | 8993 | No |
| 5234 | Neural Scholarly Factor Risk Parity Framework Eng-1181 | Graph attention / Sector contagion / Stock baskets | 10667 | 13366 | No |
| 5268 | Neural Scholarly Factor Risk Parity Framework Eng-1373 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13128 | 12930 | No |
| 5286 | Neural Scholarly Factor Risk Parity Framework Eng-1469 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7222 | 9028 | No |
| 5320 | Neural Scholarly Factor Risk Parity Framework Eng-1661 | Graph attention / Sector contagion / Stock baskets | 10673 | 13380 | No |
| 5354 | Neural Scholarly Factor Risk Parity Framework Eng-1853 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13132 | 12938 | No |
| 5372 | Neural Scholarly Factor Risk Parity Framework Eng-1949 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7264 | 9063 | No |
| 5406 | Neural Scholarly Factor Risk Parity Framework Eng-2141 | Graph attention / Sector contagion / Stock baskets | 10679 | 13394 | No |
| 5440 | Neural Scholarly Factor Risk Parity Framework Eng-2333 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13136 | 12946 | No |
| 5458 | Neural Scholarly Factor Risk Parity Framework Eng-2429 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7306 | 9098 | No |
| 5492 | Neural Scholarly Factor Risk Parity Framework Eng-2621 | Graph attention / Sector contagion / Stock baskets | 10685 | 13408 | No |
| 5526 | Neural Scholarly Factor Risk Parity Framework Eng-2813 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13140 | 12954 | No |
| 5544 | Neural Scholarly Factor Risk Parity Framework Eng-2909 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7348 | 9133 | No |
| 5578 | Neural Scholarly Factor Risk Parity Framework Eng-3101 | Graph attention / Sector contagion / Stock baskets | 10691 | 13422 | No |
| 5612 | Neural Scholarly Factor Risk Parity Framework Eng-3293 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13144 | 12962 | No |
| 5630 | Neural Scholarly Factor Risk Parity Framework Eng-3389 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7390 | 9168 | No |
| 5664 | Neural Scholarly Factor Risk Parity Framework Eng-3581 | Graph attention / Sector contagion / Stock baskets | 10697 | 13436 | No |
| 5698 | Neural Scholarly Factor Risk Parity Framework Eng-3773 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13148 | 12970 | No |
| 5716 | Neural Scholarly Factor Risk Parity Framework Eng-3869 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7432 | 9203 | No |
| 5750 | Neural Scholarly Factor Risk Parity Framework Eng-4061 | Graph attention / Sector contagion / Stock baskets | 10703 | 13450 | No |
| 5784 | Neural Scholarly Factor Risk Parity Framework Eng-4253 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13152 | 12978 | No |
| 5802 | Neural Scholarly Factor Risk Parity Framework Eng-4349 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7474 | 9238 | No |
| 5836 | Neural Scholarly Factor Risk Parity Framework Eng-4541 | Graph attention / Sector contagion / Stock baskets | 10709 | 13464 | No |
| 5870 | Neural Scholarly Factor Risk Parity Framework Eng-4733 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13156 | 12986 | No |
| 5888 | Neural Scholarly Factor Risk Parity Framework Eng-4829 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7516 | 9273 | No |
| 5922 | Neural Scholarly Factor Risk Parity Framework Eng-5021 | Graph attention / Sector contagion / Stock baskets | 10715 | 13478 | No |
| 5956 | Neural Scholarly Factor Risk Parity Framework Eng-5213 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13160 | 12994 | No |
| 5974 | Neural Scholarly Factor Risk Parity Framework Eng-5309 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7558 | 9308 | No |
| 6008 | Neural Scholarly Factor Risk Parity Framework Eng-5501 | Graph attention / Sector contagion / Stock baskets | 10721 | 13492 | No |
| 6042 | Neural Scholarly Factor Risk Parity Framework Eng-5693 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13164 | 13002 | No |
| 6060 | Neural Scholarly Factor Risk Parity Framework Eng-5789 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7600 | 9343 | No |
| 6094 | Neural Scholarly Factor Risk Parity Framework Eng-5981 | Graph attention / Sector contagion / Stock baskets | 10727 | 13506 | No |
