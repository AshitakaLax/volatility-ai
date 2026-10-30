# Koopman-operator-based approach to sector allocation

**Concept page** · shared by **62** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #2,532) ·
researched 2026-10-30

| | |
|---|---|
| Task | Sector allocation |
| Method | Koopman operators (DMD / EDMD) |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of Koopman operators improving sector allocation; industry momentum (RK19, X3) is the documented signal. |
| Implemented in volatility-ai | `tools/rotation.py --mode relative_strength` (X3) rotates across a small ETF universe, including sector momentum (RK19), with an HRP mode (A5). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | X3, RK19, RK3, RK7, A5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Koopman Scholarly Sector
Allocation Strategy Eng-465") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Compare sector-level return, trend or risk signals and periodically
re-weight among sector funds, controlling concentration and turnover.
The Koopman version linearises the dynamics in a lifted feature space
and forecasts with the linear operator. I found no study of this method
on this task.

## The CSV's description

Proposed Koopman-operator-based approach to sector allocation: Compare
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
* The Koopman entries in the list have no peer-reviewed trading evidence
  (RK206).

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
| 2532 | Koopman Scholarly Sector Allocation Strategy Eng-465 | Rough path theory / Tensor signatures / Stock trend forecasting | 5699 | 2493 | No |
| 2587 | Koopman Scholarly Sector Allocation Strategy Eng-945 | Rough path theory / Tensor signatures / Stock trend forecasting | 5707 | 2516 | No |
| 2642 | Koopman Scholarly Sector Allocation Strategy Eng-1425 | Rough path theory / Tensor signatures / Stock trend forecasting | 5715 | 2539 | No |
| 2697 | Koopman Scholarly Sector Allocation Strategy Eng-1905 | Rough path theory / Tensor signatures / Stock trend forecasting | 5723 | 2562 | No |
| 2752 | Koopman Scholarly Sector Allocation Strategy Eng-2385 | Rough path theory / Tensor signatures / Stock trend forecasting | 5731 | 2585 | No |
| 2807 | Koopman Scholarly Sector Allocation Strategy Eng-2865 | Rough path theory / Tensor signatures / Stock trend forecasting | 5739 | 2608 | No |
| 2862 | Koopman Scholarly Sector Allocation Strategy Eng-3345 | Rough path theory / Tensor signatures / Stock trend forecasting | 5747 | 2631 | No |
| 2917 | Koopman Scholarly Sector Allocation Strategy Eng-3825 | Rough path theory / Tensor signatures / Stock trend forecasting | 5755 | 2654 | No |
| 2972 | Koopman Scholarly Sector Allocation Strategy Eng-4305 | Rough path theory / Tensor signatures / Stock trend forecasting | 5763 | 2677 | No |
| 3027 | Koopman Scholarly Sector Allocation Strategy Eng-4785 | Rough path theory / Tensor signatures / Stock trend forecasting | 5771 | 2700 | No |
| 3082 | Koopman Scholarly Sector Allocation Strategy Eng-5265 | Rough path theory / Tensor signatures / Stock trend forecasting | 5779 | 2723 | No |
| 3137 | Koopman Scholarly Sector Allocation Strategy Eng-5745 | Rough path theory / Tensor signatures / Stock trend forecasting | 5787 | 2746 | No |
| 5089 | Koopman Scholarly Sector Allocation Strategy Eng-369 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7125 | 4513 | No |
| 5175 | Koopman Scholarly Sector Allocation Strategy Eng-849 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7167 | 4606 | No |
| 5261 | Koopman Scholarly Sector Allocation Strategy Eng-1329 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7209 | 4699 | No |
| 5347 | Koopman Scholarly Sector Allocation Strategy Eng-1809 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7251 | 4792 | No |
| 5433 | Koopman Scholarly Sector Allocation Strategy Eng-2289 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7293 | 4885 | No |
| 5519 | Koopman Scholarly Sector Allocation Strategy Eng-2769 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7335 | 4978 | No |
| 5605 | Koopman Scholarly Sector Allocation Strategy Eng-3249 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7377 | 5071 | No |
| 5691 | Koopman Scholarly Sector Allocation Strategy Eng-3729 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7419 | 5164 | No |
| 5777 | Koopman Scholarly Sector Allocation Strategy Eng-4209 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7461 | 5257 | No |
| 5863 | Koopman Scholarly Sector Allocation Strategy Eng-4689 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7503 | 5350 | No |
| 5949 | Koopman Scholarly Sector Allocation Strategy Eng-5169 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7545 | 5443 | No |
| 6035 | Koopman Scholarly Sector Allocation Strategy Eng-5649 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7587 | 5536 | No |
| 6846 | Koopman Scholarly Sector Allocation Strategy Eng-177 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 544 | 1971 | No |
| 6892 | Koopman Scholarly Sector Allocation Strategy Eng-657 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 556 | 1983 | No |
| 6938 | Koopman Scholarly Sector Allocation Strategy Eng-1137 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 568 | 1995 | No |
| 6984 | Koopman Scholarly Sector Allocation Strategy Eng-1617 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 580 | 2007 | No |
| 7030 | Koopman Scholarly Sector Allocation Strategy Eng-2097 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 592 | 2019 | No |
| 7076 | Koopman Scholarly Sector Allocation Strategy Eng-2577 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 604 | 2031 | No |
| 7122 | Koopman Scholarly Sector Allocation Strategy Eng-3057 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 616 | 2043 | No |
| 7168 | Koopman Scholarly Sector Allocation Strategy Eng-3537 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 628 | 2055 | No |
| 7214 | Koopman Scholarly Sector Allocation Strategy Eng-4017 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 640 | 2067 | No |
| 7260 | Koopman Scholarly Sector Allocation Strategy Eng-4497 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 652 | 2079 | No |
| 7306 | Koopman Scholarly Sector Allocation Strategy Eng-4977 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 664 | 2091 | No |
| 7352 | Koopman Scholarly Sector Allocation Strategy Eng-5457 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 676 | 2103 | No |
| 7398 | Koopman Scholarly Sector Allocation Strategy Eng-5937 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 688 | 2115 | No |
| 11475 | Koopman Scholarly Sector Allocation Strategy Eng-81 | Graph attention / Sector contagion / Stock baskets | 838 | 1385 | No |
| 11554 | Koopman Scholarly Sector Allocation Strategy Eng-273 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7963 | 7996 | No |
| 11666 | Koopman Scholarly Sector Allocation Strategy Eng-561 | Graph attention / Sector contagion / Stock baskets | 850 | 1411 | No |
| 11745 | Koopman Scholarly Sector Allocation Strategy Eng-753 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7980 | 8028 | No |
| 11857 | Koopman Scholarly Sector Allocation Strategy Eng-1041 | Graph attention / Sector contagion / Stock baskets | 862 | 1437 | No |
| 11936 | Koopman Scholarly Sector Allocation Strategy Eng-1233 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7997 | 8060 | No |
| 12048 | Koopman Scholarly Sector Allocation Strategy Eng-1521 | Graph attention / Sector contagion / Stock baskets | 874 | 1463 | No |
| 12127 | Koopman Scholarly Sector Allocation Strategy Eng-1713 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8014 | 8092 | No |
| 12239 | Koopman Scholarly Sector Allocation Strategy Eng-2001 | Graph attention / Sector contagion / Stock baskets | 886 | 1489 | No |
| 12318 | Koopman Scholarly Sector Allocation Strategy Eng-2193 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8031 | 8124 | No |
| 12430 | Koopman Scholarly Sector Allocation Strategy Eng-2481 | Graph attention / Sector contagion / Stock baskets | 898 | 1515 | No |
| 12509 | Koopman Scholarly Sector Allocation Strategy Eng-2673 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8048 | 8156 | No |
| 12621 | Koopman Scholarly Sector Allocation Strategy Eng-2961 | Graph attention / Sector contagion / Stock baskets | 910 | 1541 | No |
| 12700 | Koopman Scholarly Sector Allocation Strategy Eng-3153 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8065 | 8188 | No |
| 12812 | Koopman Scholarly Sector Allocation Strategy Eng-3441 | Graph attention / Sector contagion / Stock baskets | 922 | 1567 | No |
| 12891 | Koopman Scholarly Sector Allocation Strategy Eng-3633 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8082 | 8220 | No |
| 13003 | Koopman Scholarly Sector Allocation Strategy Eng-3921 | Graph attention / Sector contagion / Stock baskets | 934 | 1593 | No |
| 13082 | Koopman Scholarly Sector Allocation Strategy Eng-4113 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8099 | 8252 | No |
| 13194 | Koopman Scholarly Sector Allocation Strategy Eng-4401 | Graph attention / Sector contagion / Stock baskets | 946 | 1619 | No |
| 13273 | Koopman Scholarly Sector Allocation Strategy Eng-4593 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8116 | 8284 | No |
| 13385 | Koopman Scholarly Sector Allocation Strategy Eng-4881 | Graph attention / Sector contagion / Stock baskets | 958 | 1645 | No |
| 13464 | Koopman Scholarly Sector Allocation Strategy Eng-5073 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8133 | 8316 | No |
| 13576 | Koopman Scholarly Sector Allocation Strategy Eng-5361 | Graph attention / Sector contagion / Stock baskets | 970 | 1671 | No |
| 13655 | Koopman Scholarly Sector Allocation Strategy Eng-5553 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8150 | 8348 | No |
| 13767 | Koopman Scholarly Sector Allocation Strategy Eng-5841 | Graph attention / Sector contagion / Stock baskets | 982 | 1697 | No |
