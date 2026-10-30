# Entropy-regularized approach to trade-execution optimization

**Concept page** · shared by **63** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #2,089) ·
researched 2026-10-30

| | |
|---|---|
| Task | Trade-execution optimisation |
| Method | Entropy regularisation |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** The book's orders are too small for impact to matter; execution optimisation solves a problem it does not have. |
| Implemented in volatility-ai | Schedules and execution agents are research code (`execution`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK363, RK366, RK244 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Entropic Scholarly
Execution Trajectory Planner Mod-445") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Plan order timing and slicing over a horizon to balance slippage,
impact, completion risk and liquidity. The entropy-regularised version
penalises concentrated weights or forecasts, pulling them toward
uniform. I found no study of this method on this task.

## The CSV's description

Proposed entropy-regularized approach to trade-execution optimization:
Plan order timing and slicing over an execution horizon to balance
expected slippage, market impact, completion risk, and liquidity. This
is a concept-level interpretation of the title, not a complete trading
specification: the exact model inputs/target, calibration, entry/exit or
rebalance rules, and position sizing are not fully defined here.

## Evidence

* **Almgren & Chriss (2001), "Optimal execution of portfolio
  transactions," *Journal of Risk* 3(2):** the mean-variance trade-off
  between impact and timing risk for a large order (see RK366).
  (Standard reference.)
* **Frazzini, Israel & Moskowitz (2018), "Trading Costs" (SSRN
  3229719):** on $1.7 trillion of live institutional trades, market
  impact averaged under 9 bp for orders completed within a day, an order
  of magnitude below earlier estimates. (Abstract and summaries.)

## Against, and failure modes

* Execution schedules address impact, which is a few basis points even
  for institutional orders (Frazzini, Israel & Moskowitz).
* Entropy regularisation is shrinkage toward equal weights; it adds no
  information.

## Fit with volatility-ai

The engine's orders are small against TQQQ's volume; slicing schedules
solve a problem this book does not have (RK363, RK366). A spread gate
(RK244) covers what matters.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Almgren, R., Chriss, N. (2001). *Journal of Risk* 3(2), 5–39. Standard
  reference.
* Frazzini, A., Israel, R., Moskowitz, T. J. (2018). "Trading Costs."
  SSRN 3229719. Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 2089 | Entropic Scholarly Execution Trajectory Planner Mod-445 | Rough path theory / Tensor signatures / Stock trend forecasting | 6782 | 3741 | No |
| 2142 | Entropic Scholarly Execution Trajectory Planner Mod-925 | Rough path theory / Tensor signatures / Stock trend forecasting | 6824 | 3836 | No |
| 2195 | Entropic Scholarly Execution Trajectory Planner Mod-1405 | Rough path theory / Tensor signatures / Stock trend forecasting | 6866 | 3931 | No |
| 2248 | Entropic Scholarly Execution Trajectory Planner Mod-1885 | Rough path theory / Tensor signatures / Stock trend forecasting | 6908 | 4026 | No |
| 2301 | Entropic Scholarly Execution Trajectory Planner Mod-2365 | Rough path theory / Tensor signatures / Stock trend forecasting | 6950 | 4121 | No |
| 2354 | Entropic Scholarly Execution Trajectory Planner Mod-2845 | Rough path theory / Tensor signatures / Stock trend forecasting | 6992 | 4216 | No |
| 2407 | Entropic Scholarly Execution Trajectory Planner Mod-3325 | Rough path theory / Tensor signatures / Stock trend forecasting | 7034 | 4311 | No |
| 2460 | Entropic Scholarly Execution Trajectory Planner Mod-3805 | Rough path theory / Tensor signatures / Stock trend forecasting | 7076 | 4406 | No |
| 6467 | Entropic Scholarly Execution Trajectory Planner Mod-157 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10116 | 11384 | No |
| 6512 | Entropic Scholarly Execution Trajectory Planner Mod-637 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10128 | 11398 | No |
| 6557 | Entropic Scholarly Execution Trajectory Planner Mod-1117 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10140 | 11412 | No |
| 6602 | Entropic Scholarly Execution Trajectory Planner Mod-1597 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10152 | 11426 | No |
| 6647 | Entropic Scholarly Execution Trajectory Planner Mod-2077 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10164 | 11440 | No |
| 6692 | Entropic Scholarly Execution Trajectory Planner Mod-2557 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10176 | 11454 | No |
| 6737 | Entropic Scholarly Execution Trajectory Planner Mod-3037 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10188 | 11468 | No |
| 6782 | Entropic Scholarly Execution Trajectory Planner Mod-3517 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10200 | 11482 | No |
| 6827 | Entropic Scholarly Execution Trajectory Planner Mod-3997 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10212 | 11496 | No |
| 7529 | Entropic Scholarly Execution Trajectory Planner Sys-115 | Neural SDEs / Adversarial robustness / Stock options hedging | 9749 | 5640 | No |
| 7560 | Entropic Scholarly Execution Trajectory Planner Sys-595 | Neural SDEs / Adversarial robustness / Stock options hedging | 9753 | 5657 | No |
| 7591 | Entropic Scholarly Execution Trajectory Planner Sys-1075 | Neural SDEs / Adversarial robustness / Stock options hedging | 9757 | 5674 | No |
| 7622 | Entropic Scholarly Execution Trajectory Planner Sys-1555 | Neural SDEs / Adversarial robustness / Stock options hedging | 9761 | 5691 | No |
| 7672 | Entropic Scholarly Execution Trajectory Planner Mod-349 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8514 | 3722 | No |
| 7704 | Entropic Scholarly Execution Trajectory Planner Mod-829 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8552 | 3817 | No |
| 7736 | Entropic Scholarly Execution Trajectory Planner Mod-1309 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8590 | 3912 | No |
| 7768 | Entropic Scholarly Execution Trajectory Planner Mod-1789 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8628 | 4007 | No |
| 7800 | Entropic Scholarly Execution Trajectory Planner Mod-2269 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8666 | 4102 | No |
| 7832 | Entropic Scholarly Execution Trajectory Planner Mod-2749 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8704 | 4197 | No |
| 7864 | Entropic Scholarly Execution Trajectory Planner Mod-3229 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8742 | 4292 | No |
| 7896 | Entropic Scholarly Execution Trajectory Planner Mod-3709 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8780 | 4387 | No |
| 9080 | Entropic Scholarly Execution Trajectory Planner Sys-19 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 8322 | 3258 | No |
| 9156 | Entropic Scholarly Execution Trajectory Planner Sys-211 | Delay differential equations / Controlled ODEs / Stock execution | 3930 | 1091 | No |
| 9267 | Entropic Scholarly Execution Trajectory Planner Sys-499 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 8362 | 3353 | No |
| 9343 | Entropic Scholarly Execution Trajectory Planner Sys-691 | Delay differential equations / Controlled ODEs / Stock execution | 3959 | 1115 | No |
| 9454 | Entropic Scholarly Execution Trajectory Planner Sys-979 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 8402 | 3448 | No |
| 9530 | Entropic Scholarly Execution Trajectory Planner Sys-1171 | Delay differential equations / Controlled ODEs / Stock execution | 3988 | 1139 | No |
| 9641 | Entropic Scholarly Execution Trajectory Planner Sys-1459 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 8442 | 3543 | No |
| 9717 | Entropic Scholarly Execution Trajectory Planner Sys-1651 | Delay differential equations / Controlled ODEs / Stock execution | 4017 | 1163 | No |
| 9828 | Entropic Scholarly Execution Trajectory Planner Sys-1939 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 8482 | 3638 | No |
| 9874 | Entropic Scholarly Execution Trajectory Planner Mod-61 | Graph attention / Sector contagion / Stock baskets | 753 | 1182 | No |
| 10065 | Entropic Scholarly Execution Trajectory Planner Mod-541 | Graph attention / Sector contagion / Stock baskets | 763 | 1206 | No |
| 10256 | Entropic Scholarly Execution Trajectory Planner Mod-1021 | Graph attention / Sector contagion / Stock baskets | 773 | 1230 | No |
| 10447 | Entropic Scholarly Execution Trajectory Planner Mod-1501 | Graph attention / Sector contagion / Stock baskets | 783 | 1254 | No |
| 10638 | Entropic Scholarly Execution Trajectory Planner Mod-1981 | Graph attention / Sector contagion / Stock baskets | 793 | 1278 | No |
| 10829 | Entropic Scholarly Execution Trajectory Planner Mod-2461 | Graph attention / Sector contagion / Stock baskets | 803 | 1302 | No |
| 11020 | Entropic Scholarly Execution Trajectory Planner Mod-2941 | Graph attention / Sector contagion / Stock baskets | 813 | 1326 | No |
| 11211 | Entropic Scholarly Execution Trajectory Planner Mod-3421 | Graph attention / Sector contagion / Stock baskets | 823 | 1350 | No |
| 11402 | Entropic Scholarly Execution Trajectory Planner Mod-3901 | Graph attention / Sector contagion / Stock baskets | 833 | 1374 | No |
| 13909 | Entropic Scholarly Execution Trajectory Planner Sys-307 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12547 | 12568 | No |
| 13912 | Entropic Scholarly Execution Trajectory Planner Sys-403 | Topological data analysis / Betti persistence / Stock pairs | 2231 | 3338 | No |
| 13927 | Entropic Scholarly Execution Trajectory Planner Sys-787 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12554 | 12580 | No |
| 13930 | Entropic Scholarly Execution Trajectory Planner Sys-883 | Topological data analysis / Betti persistence / Stock pairs | 2278 | 3433 | No |
| 13945 | Entropic Scholarly Execution Trajectory Planner Sys-1267 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12561 | 12592 | No |
| 13948 | Entropic Scholarly Execution Trajectory Planner Sys-1363 | Topological data analysis / Betti persistence / Stock pairs | 2325 | 3528 | No |
| 13963 | Entropic Scholarly Execution Trajectory Planner Sys-1747 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12568 | 12604 | No |
| 13966 | Entropic Scholarly Execution Trajectory Planner Sys-1843 | Topological data analysis / Betti persistence / Stock pairs | 2372 | 3623 | No |
| 13979 | Entropic Scholarly Execution Trajectory Planner Mod-253 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7844 | 6077 | No |
| 13993 | Entropic Scholarly Execution Trajectory Planner Mod-733 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7858 | 6094 | No |
| 14007 | Entropic Scholarly Execution Trajectory Planner Mod-1213 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7872 | 6111 | No |
| 14021 | Entropic Scholarly Execution Trajectory Planner Mod-1693 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7886 | 6128 | No |
| 14035 | Entropic Scholarly Execution Trajectory Planner Mod-2173 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7900 | 6145 | No |
| 14049 | Entropic Scholarly Execution Trajectory Planner Mod-2653 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7914 | 6162 | No |
| 14063 | Entropic Scholarly Execution Trajectory Planner Mod-3133 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7928 | 6179 | No |
| 14077 | Entropic Scholarly Execution Trajectory Planner Mod-3613 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7942 | 6196 | No |
