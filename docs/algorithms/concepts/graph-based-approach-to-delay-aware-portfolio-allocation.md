# Graph-based approach to delay-aware portfolio allocation

**Concept page** · shared by **68** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,298) ·
researched 2026-10-30

| | |
|---|---|
| Task | Delay-aware portfolio allocation |
| Method | Graph / network models |
| Fit with this project | ⏳ reference only · background, nothing to build now |
| Useful for volatility-ai | **Reference only.** A network model could model lagged dynamics, but the established result (trade partway toward an aim) needs a multi-asset book this project does not run; background. |
| Implemented in volatility-ai | Nothing; the closest is the top-K dropout turnover rule (RK216). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK216, RK366 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Graph Scholarly Delay
Differential Allocator Mod-245") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Model delayed or lagged relationships in market variables and use the
estimated dynamics to adjust portfolio weights. The graph-based version
represents assets as a network of correlation or causality links and
acts on its structure. I found no study of this method on this task.

## The CSV's description

Proposed graph-based approach to delay-aware portfolio allocation: Model
delayed or lagged relationships in market variables and use the
estimated dynamics to adjust portfolio weights; the state equations and
decision rules require specification. This is a concept-level
interpretation of the title, not a complete trading specification: the
exact model inputs/target, calibration, entry/exit or rebalance rules,
and position sizing are not fully defined here.

## Evidence

* **Gârleanu & Pedersen (2013), "Dynamic Trading with Predictable
  Returns and Transaction Costs," *Journal of Finance* 68(6),
  2309–2340:** with costs, aim in front of the target and trade only
  partway toward the aim; slower-decaying signals get more weight. Net
  of costs it beat naive rules on commodity futures. (Abstract.)

## Against, and failure modes

* The title's delay-differential dynamics are unspecified; lagged
  relations between liquid ETFs are small and quickly arbitraged.
* Networks estimated from correlations are noisy and change with the
  window.

## Fit with volatility-ai

Trading partway toward a moving target matters for a multi-asset book
turned over at cost. The engine trades one symbol in lots, which is
already a form of partial trading.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Gârleanu, N., Pedersen, L. H. (2013). *Journal of Finance* 68(6),
  2309–2340. doi:10.1111/jofi.12080. Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 1298 | Graph Scholarly Delay Differential Allocator Mod-245 | Rough path theory / Tensor signatures / Stock trend forecasting | 8507 | 7744 | No |
| 1311 | Graph Scholarly Delay Differential Allocator Mod-725 | Rough path theory / Tensor signatures / Stock trend forecasting | 8545 | 7774 | No |
| 1324 | Graph Scholarly Delay Differential Allocator Mod-1205 | Rough path theory / Tensor signatures / Stock trend forecasting | 8583 | 7804 | No |
| 1337 | Graph Scholarly Delay Differential Allocator Mod-1685 | Rough path theory / Tensor signatures / Stock trend forecasting | 8621 | 7834 | No |
| 1350 | Graph Scholarly Delay Differential Allocator Mod-2165 | Rough path theory / Tensor signatures / Stock trend forecasting | 8659 | 7864 | No |
| 1363 | Graph Scholarly Delay Differential Allocator Mod-2645 | Rough path theory / Tensor signatures / Stock trend forecasting | 8697 | 7894 | No |
| 1376 | Graph Scholarly Delay Differential Allocator Mod-3125 | Rough path theory / Tensor signatures / Stock trend forecasting | 8735 | 7924 | No |
| 1389 | Graph Scholarly Delay Differential Allocator Mod-3605 | Rough path theory / Tensor signatures / Stock trend forecasting | 8773 | 7954 | No |
| 3318 | Graph Scholarly Delay Differential Allocator Mod-437 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6781 | 6766 | No |
| 3336 | Graph Scholarly Delay Differential Allocator Mod-917 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6823 | 6800 | No |
| 3354 | Graph Scholarly Delay Differential Allocator Mod-1397 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6865 | 6834 | No |
| 3372 | Graph Scholarly Delay Differential Allocator Mod-1877 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6907 | 6868 | No |
| 3390 | Graph Scholarly Delay Differential Allocator Mod-2357 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6949 | 6902 | No |
| 3408 | Graph Scholarly Delay Differential Allocator Mod-2837 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6991 | 6936 | No |
| 3426 | Graph Scholarly Delay Differential Allocator Mod-3317 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 7033 | 6970 | No |
| 3444 | Graph Scholarly Delay Differential Allocator Mod-3797 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 7075 | 7004 | No |
| 3979 | Graph Scholarly Delay Differential Allocator Sys-155 | Neural SDEs / Adversarial robustness / Stock options hedging | 10392 | 8479 | No |
| 4065 | Graph Scholarly Delay Differential Allocator Sys-635 | Neural SDEs / Adversarial robustness / Stock options hedging | 10396 | 8514 | No |
| 4151 | Graph Scholarly Delay Differential Allocator Sys-1115 | Neural SDEs / Adversarial robustness / Stock options hedging | 10400 | 8549 | No |
| 4237 | Graph Scholarly Delay Differential Allocator Sys-1595 | Neural SDEs / Adversarial robustness / Stock options hedging | 10404 | 8584 | No |
| 4340 | Graph Scholarly Delay Differential Allocator Mod-149 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6755 | 8624 | No |
| 4425 | Graph Scholarly Delay Differential Allocator Mod-629 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6797 | 8661 | No |
| 4510 | Graph Scholarly Delay Differential Allocator Mod-1109 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6839 | 8698 | No |
| 4595 | Graph Scholarly Delay Differential Allocator Mod-1589 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6881 | 8735 | No |
| 4680 | Graph Scholarly Delay Differential Allocator Mod-2069 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6923 | 8772 | No |
| 4765 | Graph Scholarly Delay Differential Allocator Mod-2549 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6965 | 8809 | No |
| 4850 | Graph Scholarly Delay Differential Allocator Mod-3029 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7007 | 8846 | No |
| 4935 | Graph Scholarly Delay Differential Allocator Mod-3509 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7049 | 8883 | No |
| 5020 | Graph Scholarly Delay Differential Allocator Mod-3989 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7091 | 8920 | No |
| 7524 | Graph Scholarly Delay Differential Allocator Sys-59 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6584 | 8471 | No |
| 7555 | Graph Scholarly Delay Differential Allocator Sys-539 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6623 | 8506 | No |
| 7586 | Graph Scholarly Delay Differential Allocator Sys-1019 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6662 | 8541 | No |
| 7617 | Graph Scholarly Delay Differential Allocator Sys-1499 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6701 | 8576 | No |
| 7648 | Graph Scholarly Delay Differential Allocator Sys-1979 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6740 | 8611 | No |
| 7671 | Graph Scholarly Delay Differential Allocator Mod-341 | Graph attention / Sector contagion / Stock baskets | 12322 | 13225 | No |
| 7703 | Graph Scholarly Delay Differential Allocator Mod-821 | Graph attention / Sector contagion / Stock baskets | 12330 | 13239 | No |
| 7735 | Graph Scholarly Delay Differential Allocator Mod-1301 | Graph attention / Sector contagion / Stock baskets | 12338 | 13253 | No |
| 7767 | Graph Scholarly Delay Differential Allocator Mod-1781 | Graph attention / Sector contagion / Stock baskets | 12346 | 13267 | No |
| 7799 | Graph Scholarly Delay Differential Allocator Mod-2261 | Graph attention / Sector contagion / Stock baskets | 12354 | 13281 | No |
| 7831 | Graph Scholarly Delay Differential Allocator Mod-2741 | Graph attention / Sector contagion / Stock baskets | 12362 | 13295 | No |
| 7863 | Graph Scholarly Delay Differential Allocator Mod-3221 | Graph attention / Sector contagion / Stock baskets | 12370 | 13309 | No |
| 7895 | Graph Scholarly Delay Differential Allocator Mod-3701 | Graph attention / Sector contagion / Stock baskets | 12378 | 13323 | No |
| 8496 | Graph Scholarly Delay Differential Allocator Alpha-53 | Quantum computing / QAOA combinatorial / Stock index rebalancing | 13753 | 12784 | No |
| 8536 | Graph Scholarly Delay Differential Allocator Alpha-153 | Quantum computing / QAOA combinatorial / Stock index rebalancing | 7768 | 7575 | No |
| 8576 | Graph Scholarly Delay Differential Allocator Alpha-253 | Quantum computing / QAOA combinatorial / Stock index rebalancing | 7771 | 5950 | No |
| 8616 | Graph Scholarly Delay Differential Allocator Alpha-353 | Quantum computing / QAOA combinatorial / Stock index rebalancing | 13758 | 12789 | No |
| 8656 | Graph Scholarly Delay Differential Allocator Alpha-453 | Quantum computing / QAOA combinatorial / Stock index rebalancing | 7778 | 7584 | No |
| 9171 | Graph Scholarly Delay Differential Allocator Sys-251 | Delay differential equations / Controlled ODEs / Stock execution | 13192 | 13165 | No |
| 9210 | Graph Scholarly Delay Differential Allocator Sys-347 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10880 | 10788 | No |
| 9246 | Graph Scholarly Delay Differential Allocator Sys-443 | Topological data analysis / Betti persistence / Stock pairs | 11360 | 11943 | No |
| 9358 | Graph Scholarly Delay Differential Allocator Sys-731 | Delay differential equations / Controlled ODEs / Stock execution | 13198 | 13179 | No |
| 9397 | Graph Scholarly Delay Differential Allocator Sys-827 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10888 | 10811 | No |
| 9433 | Graph Scholarly Delay Differential Allocator Sys-923 | Topological data analysis / Betti persistence / Stock pairs | 11386 | 11966 | No |
| 9545 | Graph Scholarly Delay Differential Allocator Sys-1211 | Delay differential equations / Controlled ODEs / Stock execution | 13204 | 13193 | No |
| 9584 | Graph Scholarly Delay Differential Allocator Sys-1307 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10896 | 10834 | No |
| 9620 | Graph Scholarly Delay Differential Allocator Sys-1403 | Topological data analysis / Betti persistence / Stock pairs | 11412 | 11989 | No |
| 9732 | Graph Scholarly Delay Differential Allocator Sys-1691 | Delay differential equations / Controlled ODEs / Stock execution | 13210 | 13207 | No |
| 9771 | Graph Scholarly Delay Differential Allocator Sys-1787 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10904 | 10857 | No |
| 9807 | Graph Scholarly Delay Differential Allocator Sys-1883 | Topological data analysis / Betti persistence / Stock pairs | 11438 | 12012 | No |
| 9873 | Graph Scholarly Delay Differential Allocator Mod-53 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13810 | 12858 | No |
| 10064 | Graph Scholarly Delay Differential Allocator Mod-533 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13815 | 12864 | No |
| 10255 | Graph Scholarly Delay Differential Allocator Mod-1013 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13820 | 12870 | No |
| 10446 | Graph Scholarly Delay Differential Allocator Mod-1493 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13825 | 12876 | No |
| 10637 | Graph Scholarly Delay Differential Allocator Mod-1973 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13830 | 12882 | No |
| 10828 | Graph Scholarly Delay Differential Allocator Mod-2453 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13835 | 12888 | No |
| 11019 | Graph Scholarly Delay Differential Allocator Mod-2933 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13840 | 12894 | No |
| 11210 | Graph Scholarly Delay Differential Allocator Mod-3413 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13845 | 12900 | No |
| 11401 | Graph Scholarly Delay Differential Allocator Mod-3893 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13850 | 12906 | No |
