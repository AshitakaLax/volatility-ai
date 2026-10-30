# Attention-weighted approach to sector allocation

**Concept page** · shared by **62** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,406) ·
researched 2026-10-30

| | |
|---|---|
| Task | Sector allocation |
| Method | Attention networks |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of attention networks improving sector allocation; industry momentum (RK19, X3) is the documented signal. |
| Implemented in volatility-ai | `tools/rotation.py --mode relative_strength` (X3) rotates across a small ETF universe, including sector momentum (RK19), with an HRP mode (A5). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | X3, RK19, RK3, RK7, A5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Attentional Scholarly
Sector Allocation Strategy Eng-345") combine a method word, "Scholarly",
a task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Compare sector-level return, trend or risk signals and periodically
re-weight among sector funds, controlling concentration and turnover.
The attention version weights its inputs with a learned attention
network. I found no study of this method on this task.

## The CSV's description

Proposed attention-weighted approach to sector allocation: Compare
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
* Attention networks need far more data than daily bars of a few ETFs
  provide.

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
| 1406 | Attentional Scholarly Sector Allocation Strategy Eng-345 | Rough path theory / Tensor signatures / Stock trend forecasting | 5697 | 2487 | No |
| 1417 | Attentional Scholarly Sector Allocation Strategy Eng-825 | Rough path theory / Tensor signatures / Stock trend forecasting | 5705 | 2510 | No |
| 1428 | Attentional Scholarly Sector Allocation Strategy Eng-1305 | Rough path theory / Tensor signatures / Stock trend forecasting | 5713 | 2533 | No |
| 1439 | Attentional Scholarly Sector Allocation Strategy Eng-1785 | Rough path theory / Tensor signatures / Stock trend forecasting | 5721 | 2556 | No |
| 1450 | Attentional Scholarly Sector Allocation Strategy Eng-2265 | Rough path theory / Tensor signatures / Stock trend forecasting | 5729 | 2579 | No |
| 1461 | Attentional Scholarly Sector Allocation Strategy Eng-2745 | Rough path theory / Tensor signatures / Stock trend forecasting | 5737 | 2602 | No |
| 1472 | Attentional Scholarly Sector Allocation Strategy Eng-3225 | Rough path theory / Tensor signatures / Stock trend forecasting | 5745 | 2625 | No |
| 1483 | Attentional Scholarly Sector Allocation Strategy Eng-3705 | Rough path theory / Tensor signatures / Stock trend forecasting | 5753 | 2648 | No |
| 1494 | Attentional Scholarly Sector Allocation Strategy Eng-4185 | Rough path theory / Tensor signatures / Stock trend forecasting | 5761 | 2671 | No |
| 1505 | Attentional Scholarly Sector Allocation Strategy Eng-4665 | Rough path theory / Tensor signatures / Stock trend forecasting | 5769 | 2694 | No |
| 1516 | Attentional Scholarly Sector Allocation Strategy Eng-5145 | Rough path theory / Tensor signatures / Stock trend forecasting | 5777 | 2717 | No |
| 1527 | Attentional Scholarly Sector Allocation Strategy Eng-5625 | Rough path theory / Tensor signatures / Stock trend forecasting | 5785 | 2740 | No |
| 3455 | Attentional Scholarly Sector Allocation Strategy Eng-57 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 541 | 1968 | No |
| 3471 | Attentional Scholarly Sector Allocation Strategy Eng-537 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 553 | 1980 | No |
| 3487 | Attentional Scholarly Sector Allocation Strategy Eng-1017 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 565 | 1992 | No |
| 3503 | Attentional Scholarly Sector Allocation Strategy Eng-1497 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 577 | 2004 | No |
| 3519 | Attentional Scholarly Sector Allocation Strategy Eng-1977 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 589 | 2016 | No |
| 3535 | Attentional Scholarly Sector Allocation Strategy Eng-2457 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 601 | 2028 | No |
| 3551 | Attentional Scholarly Sector Allocation Strategy Eng-2937 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 613 | 2040 | No |
| 3567 | Attentional Scholarly Sector Allocation Strategy Eng-3417 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 625 | 2052 | No |
| 3583 | Attentional Scholarly Sector Allocation Strategy Eng-3897 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 637 | 2064 | No |
| 3599 | Attentional Scholarly Sector Allocation Strategy Eng-4377 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 649 | 2076 | No |
| 3615 | Attentional Scholarly Sector Allocation Strategy Eng-4857 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 661 | 2088 | No |
| 3631 | Attentional Scholarly Sector Allocation Strategy Eng-5337 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 673 | 2100 | No |
| 3647 | Attentional Scholarly Sector Allocation Strategy Eng-5817 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 685 | 2112 | No |
| 5067 | Attentional Scholarly Sector Allocation Strategy Eng-249 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7114 | 4490 | No |
| 5153 | Attentional Scholarly Sector Allocation Strategy Eng-729 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7156 | 4583 | No |
| 5239 | Attentional Scholarly Sector Allocation Strategy Eng-1209 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7198 | 4676 | No |
| 5325 | Attentional Scholarly Sector Allocation Strategy Eng-1689 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7240 | 4769 | No |
| 5411 | Attentional Scholarly Sector Allocation Strategy Eng-2169 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7282 | 4862 | No |
| 5497 | Attentional Scholarly Sector Allocation Strategy Eng-2649 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7324 | 4955 | No |
| 5583 | Attentional Scholarly Sector Allocation Strategy Eng-3129 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7366 | 5048 | No |
| 5669 | Attentional Scholarly Sector Allocation Strategy Eng-3609 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7408 | 5141 | No |
| 5755 | Attentional Scholarly Sector Allocation Strategy Eng-4089 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7450 | 5234 | No |
| 5841 | Attentional Scholarly Sector Allocation Strategy Eng-4569 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7492 | 5327 | No |
| 5927 | Attentional Scholarly Sector Allocation Strategy Eng-5049 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7534 | 5420 | No |
| 6013 | Attentional Scholarly Sector Allocation Strategy Eng-5529 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7576 | 5513 | No |
| 7949 | Attentional Scholarly Sector Allocation Strategy Eng-441 | Graph attention / Sector contagion / Stock baskets | 847 | 1404 | No |
| 7983 | Attentional Scholarly Sector Allocation Strategy Eng-921 | Graph attention / Sector contagion / Stock baskets | 859 | 1430 | No |
| 8017 | Attentional Scholarly Sector Allocation Strategy Eng-1401 | Graph attention / Sector contagion / Stock baskets | 871 | 1456 | No |
| 8051 | Attentional Scholarly Sector Allocation Strategy Eng-1881 | Graph attention / Sector contagion / Stock baskets | 883 | 1482 | No |
| 8085 | Attentional Scholarly Sector Allocation Strategy Eng-2361 | Graph attention / Sector contagion / Stock baskets | 895 | 1508 | No |
| 8119 | Attentional Scholarly Sector Allocation Strategy Eng-2841 | Graph attention / Sector contagion / Stock baskets | 907 | 1534 | No |
| 8153 | Attentional Scholarly Sector Allocation Strategy Eng-3321 | Graph attention / Sector contagion / Stock baskets | 919 | 1560 | No |
| 8187 | Attentional Scholarly Sector Allocation Strategy Eng-3801 | Graph attention / Sector contagion / Stock baskets | 931 | 1586 | No |
| 8221 | Attentional Scholarly Sector Allocation Strategy Eng-4281 | Graph attention / Sector contagion / Stock baskets | 943 | 1612 | No |
| 8255 | Attentional Scholarly Sector Allocation Strategy Eng-4761 | Graph attention / Sector contagion / Stock baskets | 955 | 1638 | No |
| 8289 | Attentional Scholarly Sector Allocation Strategy Eng-5241 | Graph attention / Sector contagion / Stock baskets | 967 | 1664 | No |
| 8323 | Attentional Scholarly Sector Allocation Strategy Eng-5721 | Graph attention / Sector contagion / Stock baskets | 979 | 1690 | No |
| 11508 | Attentional Scholarly Sector Allocation Strategy Eng-153 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7958 | 7988 | No |
| 11699 | Attentional Scholarly Sector Allocation Strategy Eng-633 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7975 | 8020 | No |
| 11890 | Attentional Scholarly Sector Allocation Strategy Eng-1113 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7992 | 8052 | No |
| 12081 | Attentional Scholarly Sector Allocation Strategy Eng-1593 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8009 | 8084 | No |
| 12272 | Attentional Scholarly Sector Allocation Strategy Eng-2073 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8026 | 8116 | No |
| 12463 | Attentional Scholarly Sector Allocation Strategy Eng-2553 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8043 | 8148 | No |
| 12654 | Attentional Scholarly Sector Allocation Strategy Eng-3033 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8060 | 8180 | No |
| 12845 | Attentional Scholarly Sector Allocation Strategy Eng-3513 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8077 | 8212 | No |
| 13036 | Attentional Scholarly Sector Allocation Strategy Eng-3993 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8094 | 8244 | No |
| 13227 | Attentional Scholarly Sector Allocation Strategy Eng-4473 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8111 | 8276 | No |
| 13418 | Attentional Scholarly Sector Allocation Strategy Eng-4953 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8128 | 8308 | No |
| 13609 | Attentional Scholarly Sector Allocation Strategy Eng-5433 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8145 | 8340 | No |
| 13800 | Attentional Scholarly Sector Allocation Strategy Eng-5913 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8162 | 8372 | No |
