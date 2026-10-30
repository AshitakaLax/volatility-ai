# Adversarially robust approach to sector allocation

**Concept page** · shared by **63** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,292) ·
researched 2026-10-30

| | |
|---|---|
| Task | Sector allocation |
| Method | Adversarial training |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of adversarial training improving sector allocation; industry momentum (RK19, X3) is the documented signal. |
| Implemented in volatility-ai | `tools/rotation.py --mode relative_strength` (X3) rotates across a small ETF universe, including sector momentum (RK19), with an HRP mode (A5). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | X3, RK19, RK3, RK7, A5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Adversarial Scholarly
Sector Allocation Strategy Mod-45") combine a method word, "Scholarly",
a task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Compare sector-level return, trend or risk signals and periodically
re-weight among sector funds, controlling concentration and turnover.
The adversarially robust version trains against worst-case perturbations
of its inputs. I found no study of this method on this task.

## The CSV's description

Proposed adversarially robust approach to sector allocation: Compare
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
* Adversarial robustness defends against manipulated inputs; market data
  are noisy, not adversarial.

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
| 1292 | Adversarial Scholarly Sector Allocation Strategy Mod-45 | Rough path theory / Tensor signatures / Stock trend forecasting | 5634 | 2281 | No |
| 1305 | Adversarial Scholarly Sector Allocation Strategy Mod-525 | Rough path theory / Tensor signatures / Stock trend forecasting | 5641 | 2304 | No |
| 1318 | Adversarial Scholarly Sector Allocation Strategy Mod-1005 | Rough path theory / Tensor signatures / Stock trend forecasting | 5648 | 2327 | No |
| 1331 | Adversarial Scholarly Sector Allocation Strategy Mod-1485 | Rough path theory / Tensor signatures / Stock trend forecasting | 5655 | 2350 | No |
| 1344 | Adversarial Scholarly Sector Allocation Strategy Mod-1965 | Rough path theory / Tensor signatures / Stock trend forecasting | 5662 | 2373 | No |
| 1357 | Adversarial Scholarly Sector Allocation Strategy Mod-2445 | Rough path theory / Tensor signatures / Stock trend forecasting | 5669 | 2396 | No |
| 1370 | Adversarial Scholarly Sector Allocation Strategy Mod-2925 | Rough path theory / Tensor signatures / Stock trend forecasting | 5676 | 2419 | No |
| 1383 | Adversarial Scholarly Sector Allocation Strategy Mod-3405 | Rough path theory / Tensor signatures / Stock trend forecasting | 5683 | 2442 | No |
| 1396 | Adversarial Scholarly Sector Allocation Strategy Mod-3885 | Rough path theory / Tensor signatures / Stock trend forecasting | 5690 | 2465 | No |
| 3311 | Adversarial Scholarly Sector Allocation Strategy Mod-237 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 461 | 1889 | No |
| 3329 | Adversarial Scholarly Sector Allocation Strategy Mod-717 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 471 | 1899 | No |
| 3347 | Adversarial Scholarly Sector Allocation Strategy Mod-1197 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 481 | 1909 | No |
| 3365 | Adversarial Scholarly Sector Allocation Strategy Mod-1677 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 491 | 1919 | No |
| 3383 | Adversarial Scholarly Sector Allocation Strategy Mod-2157 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 501 | 1929 | No |
| 3401 | Adversarial Scholarly Sector Allocation Strategy Mod-2637 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 511 | 1939 | No |
| 3419 | Adversarial Scholarly Sector Allocation Strategy Mod-3117 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 521 | 1949 | No |
| 3437 | Adversarial Scholarly Sector Allocation Strategy Mod-3597 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 531 | 1959 | No |
| 3989 | Adversarial Scholarly Sector Allocation Strategy Sys-195 | Neural SDEs / Adversarial robustness / Stock options hedging | 8336 | 2803 | No |
| 4075 | Adversarial Scholarly Sector Allocation Strategy Sys-675 | Neural SDEs / Adversarial robustness / Stock options hedging | 8376 | 2809 | No |
| 4161 | Adversarial Scholarly Sector Allocation Strategy Sys-1155 | Neural SDEs / Adversarial robustness / Stock options hedging | 8416 | 2815 | No |
| 4247 | Adversarial Scholarly Sector Allocation Strategy Sys-1635 | Neural SDEs / Adversarial robustness / Stock options hedging | 8456 | 2821 | No |
| 4387 | Adversarial Scholarly Sector Allocation Strategy Mod-429 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6780 | 3738 | No |
| 4472 | Adversarial Scholarly Sector Allocation Strategy Mod-909 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6822 | 3833 | No |
| 4557 | Adversarial Scholarly Sector Allocation Strategy Mod-1389 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6864 | 3928 | No |
| 4642 | Adversarial Scholarly Sector Allocation Strategy Mod-1869 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6906 | 4023 | No |
| 4727 | Adversarial Scholarly Sector Allocation Strategy Mod-2349 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6948 | 4118 | No |
| 4812 | Adversarial Scholarly Sector Allocation Strategy Mod-2829 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6990 | 4213 | No |
| 4897 | Adversarial Scholarly Sector Allocation Strategy Mod-3309 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7032 | 4308 | No |
| 4982 | Adversarial Scholarly Sector Allocation Strategy Mod-3789 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7074 | 4403 | No |
| 7527 | Adversarial Scholarly Sector Allocation Strategy Sys-99 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2203 | 3275 | No |
| 7558 | Adversarial Scholarly Sector Allocation Strategy Sys-579 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2250 | 3370 | No |
| 7589 | Adversarial Scholarly Sector Allocation Strategy Sys-1059 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2297 | 3465 | No |
| 7620 | Adversarial Scholarly Sector Allocation Strategy Sys-1539 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2344 | 3560 | No |
| 7660 | Adversarial Scholarly Sector Allocation Strategy Mod-141 | Graph attention / Sector contagion / Stock baskets | 755 | 1188 | No |
| 7692 | Adversarial Scholarly Sector Allocation Strategy Mod-621 | Graph attention / Sector contagion / Stock baskets | 765 | 1212 | No |
| 7724 | Adversarial Scholarly Sector Allocation Strategy Mod-1101 | Graph attention / Sector contagion / Stock baskets | 775 | 1236 | No |
| 7756 | Adversarial Scholarly Sector Allocation Strategy Mod-1581 | Graph attention / Sector contagion / Stock baskets | 785 | 1260 | No |
| 7788 | Adversarial Scholarly Sector Allocation Strategy Mod-2061 | Graph attention / Sector contagion / Stock baskets | 795 | 1284 | No |
| 7820 | Adversarial Scholarly Sector Allocation Strategy Mod-2541 | Graph attention / Sector contagion / Stock baskets | 805 | 1308 | No |
| 7852 | Adversarial Scholarly Sector Allocation Strategy Mod-3021 | Graph attention / Sector contagion / Stock baskets | 815 | 1332 | No |
| 7884 | Adversarial Scholarly Sector Allocation Strategy Mod-3501 | Graph attention / Sector contagion / Stock baskets | 825 | 1356 | No |
| 7916 | Adversarial Scholarly Sector Allocation Strategy Mod-3981 | Graph attention / Sector contagion / Stock baskets | 835 | 1380 | No |
| 9074 | Adversarial Scholarly Sector Allocation Strategy Sys-3 | Topological data analysis / Betti persistence / Stock pairs | 2193 | 6585 | No |
| 9187 | Adversarial Scholarly Sector Allocation Strategy Sys-291 | Delay differential equations / Controlled ODEs / Stock execution | 3936 | 1094 | No |
| 9226 | Adversarial Scholarly Sector Allocation Strategy Sys-387 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4726 | 10789 | No |
| 9261 | Adversarial Scholarly Sector Allocation Strategy Sys-483 | Topological data analysis / Betti persistence / Stock pairs | 2240 | 6621 | No |
| 9374 | Adversarial Scholarly Sector Allocation Strategy Sys-771 | Delay differential equations / Controlled ODEs / Stock execution | 3965 | 1118 | No |
| 9413 | Adversarial Scholarly Sector Allocation Strategy Sys-867 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4757 | 10812 | No |
| 9448 | Adversarial Scholarly Sector Allocation Strategy Sys-963 | Topological data analysis / Betti persistence / Stock pairs | 2287 | 6657 | No |
| 9561 | Adversarial Scholarly Sector Allocation Strategy Sys-1251 | Delay differential equations / Controlled ODEs / Stock execution | 3994 | 1142 | No |
| 9600 | Adversarial Scholarly Sector Allocation Strategy Sys-1347 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4788 | 10835 | No |
| 9635 | Adversarial Scholarly Sector Allocation Strategy Sys-1443 | Topological data analysis / Betti persistence / Stock pairs | 2334 | 6693 | No |
| 9748 | Adversarial Scholarly Sector Allocation Strategy Sys-1731 | Delay differential equations / Controlled ODEs / Stock execution | 4023 | 1166 | No |
| 9787 | Adversarial Scholarly Sector Allocation Strategy Sys-1827 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4819 | 10858 | No |
| 9822 | Adversarial Scholarly Sector Allocation Strategy Sys-1923 | Topological data analysis / Betti persistence / Stock pairs | 2381 | 6729 | No |
| 9987 | Adversarial Scholarly Sector Allocation Strategy Mod-333 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7847 | 7750 | No |
| 10178 | Adversarial Scholarly Sector Allocation Strategy Mod-813 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7861 | 7780 | No |
| 10369 | Adversarial Scholarly Sector Allocation Strategy Mod-1293 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7875 | 7810 | No |
| 10560 | Adversarial Scholarly Sector Allocation Strategy Mod-1773 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7889 | 7840 | No |
| 10751 | Adversarial Scholarly Sector Allocation Strategy Mod-2253 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7903 | 7870 | No |
| 10942 | Adversarial Scholarly Sector Allocation Strategy Mod-2733 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7917 | 7900 | No |
| 11133 | Adversarial Scholarly Sector Allocation Strategy Mod-3213 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7931 | 7930 | No |
| 11324 | Adversarial Scholarly Sector Allocation Strategy Mod-3693 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7945 | 7960 | No |
