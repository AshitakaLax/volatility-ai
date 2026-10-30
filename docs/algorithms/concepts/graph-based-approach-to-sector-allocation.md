# Graph-based approach to sector allocation

**Concept page** · shared by **63** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,302) ·
researched 2026-10-30

| | |
|---|---|
| Task | Sector allocation |
| Method | Graph / network models |
| Fit with this project | ⏳ reference only · background, nothing to build now |
| Useful for volatility-ai | **Reference only.** A network model could weight a sector sleeve, but no study shows it beating plain sector momentum; background until X3 is measured. |
| Implemented in volatility-ai | `tools/rotation.py --mode relative_strength` (X3) rotates across a small ETF universe, including sector momentum (RK19), with an HRP mode (A5). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | X3, RK19, RK3, RK7, A5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Graph Scholarly Sector
Allocation Strategy Mod-405") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Compare sector-level return, trend or risk signals and periodically
re-weight among sector funds, controlling concentration and turnover.
The graph-based version represents assets as a network of correlation or
causality links and acts on its structure. I found no study of this
method on this task.

## The CSV's description

Proposed graph-based approach to sector allocation: Compare sector-level
return, trend, or risk signals and periodically adjust weights among
sector funds; concentration and turnover need to be controlled. This is
a concept-level interpretation of the title, not a complete trading
specification: the exact model inputs/target, calibration, entry/exit or
rebalance rules, and position sizing are not fully defined here.

## Evidence

* **Moskowitz & Grinblatt (1999), "Do Industries Explain Momentum?"
  *Journal of Finance* 54(4), 1249–1290:** industry momentum is highly
  profitable after controls and accounts for much of stock momentum.
  (Abstract.)

## Against, and failure modes

* Sector rotation adds turnover and taxes; the long-only half keeps only
  part of the long-short industry-momentum premium.
* Networks estimated from correlations are noisy and change with the
  window.

## Fit with volatility-ai

Built as X3 (relative-strength rotation across a small ETF universe) and
RK19 (sector momentum), neither yet measured. A sector sleeve would sit
beside the grid, not inside it.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Moskowitz, T. J., Grinblatt, M. (1999). *Journal of Finance* 54(4),
  1249–1290. Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 1302 | Graph Scholarly Sector Allocation Strategy Mod-405 | Rough path theory / Tensor signatures / Stock trend forecasting | 5639 | 2298 | No |
| 1315 | Graph Scholarly Sector Allocation Strategy Mod-885 | Rough path theory / Tensor signatures / Stock trend forecasting | 5646 | 2321 | No |
| 1328 | Graph Scholarly Sector Allocation Strategy Mod-1365 | Rough path theory / Tensor signatures / Stock trend forecasting | 5653 | 2344 | No |
| 1341 | Graph Scholarly Sector Allocation Strategy Mod-1845 | Rough path theory / Tensor signatures / Stock trend forecasting | 5660 | 2367 | No |
| 1354 | Graph Scholarly Sector Allocation Strategy Mod-2325 | Rough path theory / Tensor signatures / Stock trend forecasting | 5667 | 2390 | No |
| 1367 | Graph Scholarly Sector Allocation Strategy Mod-2805 | Rough path theory / Tensor signatures / Stock trend forecasting | 5674 | 2413 | No |
| 1380 | Graph Scholarly Sector Allocation Strategy Mod-3285 | Rough path theory / Tensor signatures / Stock trend forecasting | 5681 | 2436 | No |
| 1393 | Graph Scholarly Sector Allocation Strategy Mod-3765 | Rough path theory / Tensor signatures / Stock trend forecasting | 5688 | 2459 | No |
| 3306 | Graph Scholarly Sector Allocation Strategy Mod-117 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 458 | 1886 | No |
| 3324 | Graph Scholarly Sector Allocation Strategy Mod-597 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 468 | 1896 | No |
| 3342 | Graph Scholarly Sector Allocation Strategy Mod-1077 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 478 | 1906 | No |
| 3360 | Graph Scholarly Sector Allocation Strategy Mod-1557 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 488 | 1916 | No |
| 3378 | Graph Scholarly Sector Allocation Strategy Mod-2037 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 498 | 1926 | No |
| 3396 | Graph Scholarly Sector Allocation Strategy Mod-2517 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 508 | 1936 | No |
| 3414 | Graph Scholarly Sector Allocation Strategy Mod-2997 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 518 | 1946 | No |
| 3432 | Graph Scholarly Sector Allocation Strategy Mod-3477 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 528 | 1956 | No |
| 3450 | Graph Scholarly Sector Allocation Strategy Mod-3957 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 538 | 1966 | No |
| 4010 | Graph Scholarly Sector Allocation Strategy Sys-315 | Neural SDEs / Adversarial robustness / Stock options hedging | 8347 | 2805 | No |
| 4096 | Graph Scholarly Sector Allocation Strategy Sys-795 | Neural SDEs / Adversarial robustness / Stock options hedging | 8387 | 2811 | No |
| 4182 | Graph Scholarly Sector Allocation Strategy Sys-1275 | Neural SDEs / Adversarial robustness / Stock options hedging | 8427 | 2817 | No |
| 4268 | Graph Scholarly Sector Allocation Strategy Sys-1755 | Neural SDEs / Adversarial robustness / Stock options hedging | 8467 | 2823 | No |
| 4366 | Graph Scholarly Sector Allocation Strategy Mod-309 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6769 | 3713 | No |
| 4451 | Graph Scholarly Sector Allocation Strategy Mod-789 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6811 | 3808 | No |
| 4536 | Graph Scholarly Sector Allocation Strategy Mod-1269 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6853 | 3903 | No |
| 4621 | Graph Scholarly Sector Allocation Strategy Mod-1749 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6895 | 3998 | No |
| 4706 | Graph Scholarly Sector Allocation Strategy Mod-2229 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6937 | 4093 | No |
| 4791 | Graph Scholarly Sector Allocation Strategy Mod-2709 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6979 | 4188 | No |
| 4876 | Graph Scholarly Sector Allocation Strategy Mod-3189 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7021 | 4283 | No |
| 4961 | Graph Scholarly Sector Allocation Strategy Mod-3669 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7063 | 4378 | No |
| 7535 | Graph Scholarly Sector Allocation Strategy Sys-219 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2215 | 3299 | No |
| 7566 | Graph Scholarly Sector Allocation Strategy Sys-699 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2262 | 3394 | No |
| 7597 | Graph Scholarly Sector Allocation Strategy Sys-1179 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2309 | 3489 | No |
| 7628 | Graph Scholarly Sector Allocation Strategy Sys-1659 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2356 | 3584 | No |
| 7651 | Graph Scholarly Sector Allocation Strategy Mod-21 | Graph attention / Sector contagion / Stock baskets | 752 | 1181 | No |
| 7683 | Graph Scholarly Sector Allocation Strategy Mod-501 | Graph attention / Sector contagion / Stock baskets | 762 | 1205 | No |
| 7715 | Graph Scholarly Sector Allocation Strategy Mod-981 | Graph attention / Sector contagion / Stock baskets | 772 | 1229 | No |
| 7747 | Graph Scholarly Sector Allocation Strategy Mod-1461 | Graph attention / Sector contagion / Stock baskets | 782 | 1253 | No |
| 7779 | Graph Scholarly Sector Allocation Strategy Mod-1941 | Graph attention / Sector contagion / Stock baskets | 792 | 1277 | No |
| 7811 | Graph Scholarly Sector Allocation Strategy Mod-2421 | Graph attention / Sector contagion / Stock baskets | 802 | 1301 | No |
| 7843 | Graph Scholarly Sector Allocation Strategy Mod-2901 | Graph attention / Sector contagion / Stock baskets | 812 | 1325 | No |
| 7875 | Graph Scholarly Sector Allocation Strategy Mod-3381 | Graph attention / Sector contagion / Stock baskets | 822 | 1349 | No |
| 7907 | Graph Scholarly Sector Allocation Strategy Mod-3861 | Graph attention / Sector contagion / Stock baskets | 832 | 1373 | No |
| 9084 | Graph Scholarly Sector Allocation Strategy Sys-27 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4704 | 10772 | No |
| 9120 | Graph Scholarly Sector Allocation Strategy Sys-123 | Topological data analysis / Betti persistence / Stock pairs | 2206 | 6594 | No |
| 9235 | Graph Scholarly Sector Allocation Strategy Sys-411 | Delay differential equations / Controlled ODEs / Stock execution | 3943 | 1100 | No |
| 9271 | Graph Scholarly Sector Allocation Strategy Sys-507 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4735 | 10795 | No |
| 9307 | Graph Scholarly Sector Allocation Strategy Sys-603 | Topological data analysis / Betti persistence / Stock pairs | 2253 | 6630 | No |
| 9422 | Graph Scholarly Sector Allocation Strategy Sys-891 | Delay differential equations / Controlled ODEs / Stock execution | 3972 | 1124 | No |
| 9458 | Graph Scholarly Sector Allocation Strategy Sys-987 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4766 | 10818 | No |
| 9494 | Graph Scholarly Sector Allocation Strategy Sys-1083 | Topological data analysis / Betti persistence / Stock pairs | 2300 | 6666 | No |
| 9609 | Graph Scholarly Sector Allocation Strategy Sys-1371 | Delay differential equations / Controlled ODEs / Stock execution | 4001 | 1148 | No |
| 9645 | Graph Scholarly Sector Allocation Strategy Sys-1467 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4797 | 10841 | No |
| 9681 | Graph Scholarly Sector Allocation Strategy Sys-1563 | Topological data analysis / Betti persistence / Stock pairs | 2347 | 6702 | No |
| 9796 | Graph Scholarly Sector Allocation Strategy Sys-1851 | Delay differential equations / Controlled ODEs / Stock execution | 4030 | 1172 | No |
| 9832 | Graph Scholarly Sector Allocation Strategy Sys-1947 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4828 | 10864 | No |
| 9938 | Graph Scholarly Sector Allocation Strategy Mod-213 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7842 | 7742 | No |
| 10129 | Graph Scholarly Sector Allocation Strategy Mod-693 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7856 | 7772 | No |
| 10320 | Graph Scholarly Sector Allocation Strategy Mod-1173 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7870 | 7802 | No |
| 10511 | Graph Scholarly Sector Allocation Strategy Mod-1653 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7884 | 7832 | No |
| 10702 | Graph Scholarly Sector Allocation Strategy Mod-2133 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7898 | 7862 | No |
| 10893 | Graph Scholarly Sector Allocation Strategy Mod-2613 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7912 | 7892 | No |
| 11084 | Graph Scholarly Sector Allocation Strategy Mod-3093 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7926 | 7922 | No |
| 11275 | Graph Scholarly Sector Allocation Strategy Mod-3573 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7940 | 7952 | No |
