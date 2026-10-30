# Entropy-regularized approach to sector allocation

**Concept page** · shared by **62** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,299) ·
researched 2026-10-30

| | |
|---|---|
| Task | Sector allocation |
| Method | Entropy regularisation |
| Fit with this project | ⏳ reference only · background, nothing to build now |
| Useful for volatility-ai | **Reference only.** Entropy regularisation could weight a sector sleeve, but no study shows it beating plain sector momentum; background until X3 is measured. |
| Implemented in volatility-ai | `tools/rotation.py --mode relative_strength` (X3) rotates across a small ETF universe, including sector momentum (RK19), with an HRP mode (A5). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | X3, RK19, RK3, RK7, A5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Entropic Scholarly Sector
Allocation Strategy Mod-285") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Compare sector-level return, trend or risk signals and periodically
re-weight among sector funds, controlling concentration and turnover.
The entropy-regularised version penalises concentrated weights or
forecasts, pulling them toward uniform. I found no study of this method
on this task.

## The CSV's description

Proposed entropy-regularized approach to sector allocation: Compare
sector-level return, trend, or risk signals and periodically adjust
weights among sector funds; concentration and turnover need to be
controlled. This is a concept-level interpretation of the title, not a
complete trading specification: the exact model inputs/target,
calibration, entry/exit or rebalance rules, and position sizing are not
fully defined here.

## Evidence

* **Moskowitz & Grinblatt (1999), "Do Industries Explain Momentum?"
  *Journal of Finance* 54(4), 1249–1290:** industry momentum is highly
  profitable after controls and accounts for much of stock momentum.
  (Abstract.)

## Against, and failure modes

* Sector rotation adds turnover and taxes; the long-only half keeps only
  part of the long-short industry-momentum premium.
* Entropy regularisation is shrinkage toward equal weights; it adds no
  information.

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
| 1299 | Entropic Scholarly Sector Allocation Strategy Mod-285 | Rough path theory / Tensor signatures / Stock trend forecasting | 5637 | 2293 | No |
| 1312 | Entropic Scholarly Sector Allocation Strategy Mod-765 | Rough path theory / Tensor signatures / Stock trend forecasting | 5644 | 2316 | No |
| 1325 | Entropic Scholarly Sector Allocation Strategy Mod-1245 | Rough path theory / Tensor signatures / Stock trend forecasting | 5651 | 2339 | No |
| 1338 | Entropic Scholarly Sector Allocation Strategy Mod-1725 | Rough path theory / Tensor signatures / Stock trend forecasting | 5658 | 2362 | No |
| 1351 | Entropic Scholarly Sector Allocation Strategy Mod-2205 | Rough path theory / Tensor signatures / Stock trend forecasting | 5665 | 2385 | No |
| 1364 | Entropic Scholarly Sector Allocation Strategy Mod-2685 | Rough path theory / Tensor signatures / Stock trend forecasting | 5672 | 2408 | No |
| 1377 | Entropic Scholarly Sector Allocation Strategy Mod-3165 | Rough path theory / Tensor signatures / Stock trend forecasting | 5679 | 2431 | No |
| 1390 | Entropic Scholarly Sector Allocation Strategy Mod-3645 | Rough path theory / Tensor signatures / Stock trend forecasting | 5686 | 2454 | No |
| 3319 | Entropic Scholarly Sector Allocation Strategy Mod-477 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 465 | 1893 | No |
| 3337 | Entropic Scholarly Sector Allocation Strategy Mod-957 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 475 | 1903 | No |
| 3355 | Entropic Scholarly Sector Allocation Strategy Mod-1437 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 485 | 1913 | No |
| 3373 | Entropic Scholarly Sector Allocation Strategy Mod-1917 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 495 | 1923 | No |
| 3391 | Entropic Scholarly Sector Allocation Strategy Mod-2397 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 505 | 1933 | No |
| 3409 | Entropic Scholarly Sector Allocation Strategy Mod-2877 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 515 | 1943 | No |
| 3427 | Entropic Scholarly Sector Allocation Strategy Mod-3357 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 525 | 1953 | No |
| 3445 | Entropic Scholarly Sector Allocation Strategy Mod-3837 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 535 | 1963 | No |
| 4030 | Entropic Scholarly Sector Allocation Strategy Sys-435 | Neural SDEs / Adversarial robustness / Stock options hedging | 8358 | 2807 | No |
| 4116 | Entropic Scholarly Sector Allocation Strategy Sys-915 | Neural SDEs / Adversarial robustness / Stock options hedging | 8398 | 2813 | No |
| 4202 | Entropic Scholarly Sector Allocation Strategy Sys-1395 | Neural SDEs / Adversarial robustness / Stock options hedging | 8438 | 2819 | No |
| 4288 | Entropic Scholarly Sector Allocation Strategy Sys-1875 | Neural SDEs / Adversarial robustness / Stock options hedging | 8478 | 2825 | No |
| 4346 | Entropic Scholarly Sector Allocation Strategy Mod-189 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6758 | 3688 | No |
| 4431 | Entropic Scholarly Sector Allocation Strategy Mod-669 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6800 | 3783 | No |
| 4516 | Entropic Scholarly Sector Allocation Strategy Mod-1149 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6842 | 3878 | No |
| 4601 | Entropic Scholarly Sector Allocation Strategy Mod-1629 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6884 | 3973 | No |
| 4686 | Entropic Scholarly Sector Allocation Strategy Mod-2109 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6926 | 4068 | No |
| 4771 | Entropic Scholarly Sector Allocation Strategy Mod-2589 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6968 | 4163 | No |
| 4856 | Entropic Scholarly Sector Allocation Strategy Mod-3069 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7010 | 4258 | No |
| 4941 | Entropic Scholarly Sector Allocation Strategy Mod-3549 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7052 | 4353 | No |
| 7541 | Entropic Scholarly Sector Allocation Strategy Sys-339 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2225 | 3324 | No |
| 7572 | Entropic Scholarly Sector Allocation Strategy Sys-819 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2272 | 3419 | No |
| 7603 | Entropic Scholarly Sector Allocation Strategy Sys-1299 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2319 | 3514 | No |
| 7634 | Entropic Scholarly Sector Allocation Strategy Sys-1779 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2366 | 3609 | No |
| 7675 | Entropic Scholarly Sector Allocation Strategy Mod-381 | Graph attention / Sector contagion / Stock baskets | 759 | 1198 | No |
| 7707 | Entropic Scholarly Sector Allocation Strategy Mod-861 | Graph attention / Sector contagion / Stock baskets | 769 | 1222 | No |
| 7739 | Entropic Scholarly Sector Allocation Strategy Mod-1341 | Graph attention / Sector contagion / Stock baskets | 779 | 1246 | No |
| 7771 | Entropic Scholarly Sector Allocation Strategy Mod-1821 | Graph attention / Sector contagion / Stock baskets | 789 | 1270 | No |
| 7803 | Entropic Scholarly Sector Allocation Strategy Mod-2301 | Graph attention / Sector contagion / Stock baskets | 799 | 1294 | No |
| 7835 | Entropic Scholarly Sector Allocation Strategy Mod-2781 | Graph attention / Sector contagion / Stock baskets | 809 | 1318 | No |
| 7867 | Entropic Scholarly Sector Allocation Strategy Mod-3261 | Graph attention / Sector contagion / Stock baskets | 819 | 1342 | No |
| 7899 | Entropic Scholarly Sector Allocation Strategy Mod-3741 | Graph attention / Sector contagion / Stock baskets | 829 | 1366 | No |
| 9093 | Entropic Scholarly Sector Allocation Strategy Sys-51 | Delay differential equations / Controlled ODEs / Stock execution | 3922 | 1083 | No |
| 9130 | Entropic Scholarly Sector Allocation Strategy Sys-147 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4711 | 10778 | No |
| 9168 | Entropic Scholarly Sector Allocation Strategy Sys-243 | Topological data analysis / Betti persistence / Stock pairs | 2217 | 6603 | No |
| 9280 | Entropic Scholarly Sector Allocation Strategy Sys-531 | Delay differential equations / Controlled ODEs / Stock execution | 3951 | 1107 | No |
| 9317 | Entropic Scholarly Sector Allocation Strategy Sys-627 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4742 | 10801 | No |
| 9355 | Entropic Scholarly Sector Allocation Strategy Sys-723 | Topological data analysis / Betti persistence / Stock pairs | 2264 | 6639 | No |
| 9467 | Entropic Scholarly Sector Allocation Strategy Sys-1011 | Delay differential equations / Controlled ODEs / Stock execution | 3980 | 1131 | No |
| 9504 | Entropic Scholarly Sector Allocation Strategy Sys-1107 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4773 | 10824 | No |
| 9542 | Entropic Scholarly Sector Allocation Strategy Sys-1203 | Topological data analysis / Betti persistence / Stock pairs | 2311 | 6675 | No |
| 9654 | Entropic Scholarly Sector Allocation Strategy Sys-1491 | Delay differential equations / Controlled ODEs / Stock execution | 4009 | 1155 | No |
| 9691 | Entropic Scholarly Sector Allocation Strategy Sys-1587 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4804 | 10847 | No |
| 9729 | Entropic Scholarly Sector Allocation Strategy Sys-1683 | Topological data analysis / Betti persistence / Stock pairs | 2358 | 6711 | No |
| 9841 | Entropic Scholarly Sector Allocation Strategy Sys-1971 | Delay differential equations / Controlled ODEs / Stock execution | 4038 | 1179 | No |
| 9890 | Entropic Scholarly Sector Allocation Strategy Mod-93 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7838 | 7734 | No |
| 10081 | Entropic Scholarly Sector Allocation Strategy Mod-573 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7852 | 7764 | No |
| 10272 | Entropic Scholarly Sector Allocation Strategy Mod-1053 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7866 | 7794 | No |
| 10463 | Entropic Scholarly Sector Allocation Strategy Mod-1533 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7880 | 7824 | No |
| 10654 | Entropic Scholarly Sector Allocation Strategy Mod-2013 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7894 | 7854 | No |
| 10845 | Entropic Scholarly Sector Allocation Strategy Mod-2493 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7908 | 7884 | No |
| 11036 | Entropic Scholarly Sector Allocation Strategy Mod-2973 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7922 | 7914 | No |
| 11227 | Entropic Scholarly Sector Allocation Strategy Mod-3453 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7936 | 7944 | No |
| 11418 | Entropic Scholarly Sector Allocation Strategy Mod-3933 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7950 | 7974 | No |
