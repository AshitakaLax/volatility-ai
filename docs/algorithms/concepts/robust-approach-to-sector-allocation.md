# Robust approach to sector allocation

**Concept page** · shared by **63** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,404) ·
researched 2026-10-30

| | |
|---|---|
| Task | Sector allocation |
| Method | Robust (outlier-resistant) estimation |
| Fit with this project | ⏳ reference only · background, nothing to build now |
| Useful for volatility-ai | **Reference only.** Robust estimation could weight a sector sleeve, but no study shows it beating plain sector momentum; background until X3 is measured. |
| Implemented in volatility-ai | `tools/rotation.py --mode relative_strength` (X3) rotates across a small ETF universe, including sector momentum (RK19), with an HRP mode (A5). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | X3, RK19, RK3, RK7, A5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Robust Scholarly Sector
Allocation Strategy Eng-225") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Compare sector-level return, trend or risk signals and periodically
re-weight among sector funds, controlling concentration and turnover.
The robust version estimates its inputs with outlier-resistant
statistics, so a few extreme days do not drive the result. I found no
study of this method on this task.

## The CSV's description

Proposed robust approach to sector allocation: Compare sector-level
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
* Robust estimators trade efficiency for stability; in calm data they
  add little.

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
| 1404 | Robust Scholarly Sector Allocation Strategy Eng-225 | Rough path theory / Tensor signatures / Stock trend forecasting | 5695 | 2482 | No |
| 1415 | Robust Scholarly Sector Allocation Strategy Eng-705 | Rough path theory / Tensor signatures / Stock trend forecasting | 5703 | 2505 | No |
| 1426 | Robust Scholarly Sector Allocation Strategy Eng-1185 | Rough path theory / Tensor signatures / Stock trend forecasting | 5711 | 2528 | No |
| 1437 | Robust Scholarly Sector Allocation Strategy Eng-1665 | Rough path theory / Tensor signatures / Stock trend forecasting | 5719 | 2551 | No |
| 1448 | Robust Scholarly Sector Allocation Strategy Eng-2145 | Rough path theory / Tensor signatures / Stock trend forecasting | 5727 | 2574 | No |
| 1459 | Robust Scholarly Sector Allocation Strategy Eng-2625 | Rough path theory / Tensor signatures / Stock trend forecasting | 5735 | 2597 | No |
| 1470 | Robust Scholarly Sector Allocation Strategy Eng-3105 | Rough path theory / Tensor signatures / Stock trend forecasting | 5743 | 2620 | No |
| 1481 | Robust Scholarly Sector Allocation Strategy Eng-3585 | Rough path theory / Tensor signatures / Stock trend forecasting | 5751 | 2643 | No |
| 1492 | Robust Scholarly Sector Allocation Strategy Eng-4065 | Rough path theory / Tensor signatures / Stock trend forecasting | 5759 | 2666 | No |
| 1503 | Robust Scholarly Sector Allocation Strategy Eng-4545 | Rough path theory / Tensor signatures / Stock trend forecasting | 5767 | 2689 | No |
| 1514 | Robust Scholarly Sector Allocation Strategy Eng-5025 | Rough path theory / Tensor signatures / Stock trend forecasting | 5775 | 2712 | No |
| 1525 | Robust Scholarly Sector Allocation Strategy Eng-5505 | Rough path theory / Tensor signatures / Stock trend forecasting | 5783 | 2735 | No |
| 1536 | Robust Scholarly Sector Allocation Strategy Eng-5985 | Rough path theory / Tensor signatures / Stock trend forecasting | 5791 | 2758 | No |
| 3468 | Robust Scholarly Sector Allocation Strategy Eng-417 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 550 | 1977 | No |
| 3484 | Robust Scholarly Sector Allocation Strategy Eng-897 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 562 | 1989 | No |
| 3500 | Robust Scholarly Sector Allocation Strategy Eng-1377 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 574 | 2001 | No |
| 3516 | Robust Scholarly Sector Allocation Strategy Eng-1857 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 586 | 2013 | No |
| 3532 | Robust Scholarly Sector Allocation Strategy Eng-2337 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 598 | 2025 | No |
| 3548 | Robust Scholarly Sector Allocation Strategy Eng-2817 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 610 | 2037 | No |
| 3564 | Robust Scholarly Sector Allocation Strategy Eng-3297 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 622 | 2049 | No |
| 3580 | Robust Scholarly Sector Allocation Strategy Eng-3777 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 634 | 2061 | No |
| 3596 | Robust Scholarly Sector Allocation Strategy Eng-4257 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 646 | 2073 | No |
| 3612 | Robust Scholarly Sector Allocation Strategy Eng-4737 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 658 | 2085 | No |
| 3628 | Robust Scholarly Sector Allocation Strategy Eng-5217 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 670 | 2097 | No |
| 3644 | Robust Scholarly Sector Allocation Strategy Eng-5697 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 682 | 2109 | No |
| 5045 | Robust Scholarly Sector Allocation Strategy Eng-129 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7103 | 4466 | No |
| 5131 | Robust Scholarly Sector Allocation Strategy Eng-609 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7145 | 4559 | No |
| 5217 | Robust Scholarly Sector Allocation Strategy Eng-1089 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7187 | 4652 | No |
| 5303 | Robust Scholarly Sector Allocation Strategy Eng-1569 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7229 | 4745 | No |
| 5389 | Robust Scholarly Sector Allocation Strategy Eng-2049 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7271 | 4838 | No |
| 5475 | Robust Scholarly Sector Allocation Strategy Eng-2529 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7313 | 4931 | No |
| 5561 | Robust Scholarly Sector Allocation Strategy Eng-3009 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7355 | 5024 | No |
| 5647 | Robust Scholarly Sector Allocation Strategy Eng-3489 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7397 | 5117 | No |
| 5733 | Robust Scholarly Sector Allocation Strategy Eng-3969 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7439 | 5210 | No |
| 5819 | Robust Scholarly Sector Allocation Strategy Eng-4449 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7481 | 5303 | No |
| 5905 | Robust Scholarly Sector Allocation Strategy Eng-4929 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7523 | 5396 | No |
| 5991 | Robust Scholarly Sector Allocation Strategy Eng-5409 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7565 | 5489 | No |
| 6077 | Robust Scholarly Sector Allocation Strategy Eng-5889 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7607 | 5582 | No |
| 7942 | Robust Scholarly Sector Allocation Strategy Eng-321 | Graph attention / Sector contagion / Stock baskets | 844 | 1398 | No |
| 7976 | Robust Scholarly Sector Allocation Strategy Eng-801 | Graph attention / Sector contagion / Stock baskets | 856 | 1424 | No |
| 8010 | Robust Scholarly Sector Allocation Strategy Eng-1281 | Graph attention / Sector contagion / Stock baskets | 868 | 1450 | No |
| 8044 | Robust Scholarly Sector Allocation Strategy Eng-1761 | Graph attention / Sector contagion / Stock baskets | 880 | 1476 | No |
| 8078 | Robust Scholarly Sector Allocation Strategy Eng-2241 | Graph attention / Sector contagion / Stock baskets | 892 | 1502 | No |
| 8112 | Robust Scholarly Sector Allocation Strategy Eng-2721 | Graph attention / Sector contagion / Stock baskets | 904 | 1528 | No |
| 8146 | Robust Scholarly Sector Allocation Strategy Eng-3201 | Graph attention / Sector contagion / Stock baskets | 916 | 1554 | No |
| 8180 | Robust Scholarly Sector Allocation Strategy Eng-3681 | Graph attention / Sector contagion / Stock baskets | 928 | 1580 | No |
| 8214 | Robust Scholarly Sector Allocation Strategy Eng-4161 | Graph attention / Sector contagion / Stock baskets | 940 | 1606 | No |
| 8248 | Robust Scholarly Sector Allocation Strategy Eng-4641 | Graph attention / Sector contagion / Stock baskets | 952 | 1632 | No |
| 8282 | Robust Scholarly Sector Allocation Strategy Eng-5121 | Graph attention / Sector contagion / Stock baskets | 964 | 1658 | No |
| 8316 | Robust Scholarly Sector Allocation Strategy Eng-5601 | Graph attention / Sector contagion / Stock baskets | 976 | 1684 | No |
| 11458 | Robust Scholarly Sector Allocation Strategy Eng-33 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7954 | 7980 | No |
| 11649 | Robust Scholarly Sector Allocation Strategy Eng-513 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7971 | 8012 | No |
| 11840 | Robust Scholarly Sector Allocation Strategy Eng-993 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7988 | 8044 | No |
| 12031 | Robust Scholarly Sector Allocation Strategy Eng-1473 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8005 | 8076 | No |
| 12222 | Robust Scholarly Sector Allocation Strategy Eng-1953 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8022 | 8108 | No |
| 12413 | Robust Scholarly Sector Allocation Strategy Eng-2433 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8039 | 8140 | No |
| 12604 | Robust Scholarly Sector Allocation Strategy Eng-2913 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8056 | 8172 | No |
| 12795 | Robust Scholarly Sector Allocation Strategy Eng-3393 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8073 | 8204 | No |
| 12986 | Robust Scholarly Sector Allocation Strategy Eng-3873 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8090 | 8236 | No |
| 13177 | Robust Scholarly Sector Allocation Strategy Eng-4353 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8107 | 8268 | No |
| 13368 | Robust Scholarly Sector Allocation Strategy Eng-4833 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8124 | 8300 | No |
| 13559 | Robust Scholarly Sector Allocation Strategy Eng-5313 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8141 | 8332 | No |
| 13750 | Robust Scholarly Sector Allocation Strategy Eng-5793 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8158 | 8364 | No |
