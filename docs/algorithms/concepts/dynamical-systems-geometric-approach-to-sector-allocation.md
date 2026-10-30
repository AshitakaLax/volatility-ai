# Dynamical-systems/geometric approach to sector allocation

**Concept page** · shared by **63** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,400) ·
researched 2026-10-30

| | |
|---|---|
| Task | Sector allocation |
| Method | Dynamical-systems / geometric (e.g. Hamiltonian) models |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of imposed dynamical-systems models improving sector allocation; industry momentum (RK19, X3) is the documented signal. |
| Implemented in volatility-ai | `tools/rotation.py --mode relative_strength` (X3) rotates across a small ETF universe, including sector momentum (RK19), with an HRP mode (A5). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | X3, RK19, RK3, RK7, A5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Hamiltonian Scholarly
Sector Allocation Strategy Eng-105") combine a method word, "Scholarly",
a task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Compare sector-level return, trend or risk signals and periodically
re-weight among sector funds, controlling concentration and turnover.
The dynamical-systems version models the market as a Hamiltonian or
delay-differential system and acts on its fitted state. I found no study
of this method on this task.

## The CSV's description

Proposed dynamical-systems/geometric approach to sector allocation:
Compare sector-level return, trend, or risk signals and periodically
adjust weights among sector funds; concentration and turnover need to be
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
* The physics is imposed, not estimated from evidence; no trading study
  found.

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
| 1400 | Hamiltonian Scholarly Sector Allocation Strategy Eng-105 | Rough path theory / Tensor signatures / Stock trend forecasting | 5693 | 2476 | No |
| 1411 | Hamiltonian Scholarly Sector Allocation Strategy Eng-585 | Rough path theory / Tensor signatures / Stock trend forecasting | 5701 | 2499 | No |
| 1422 | Hamiltonian Scholarly Sector Allocation Strategy Eng-1065 | Rough path theory / Tensor signatures / Stock trend forecasting | 5709 | 2522 | No |
| 1433 | Hamiltonian Scholarly Sector Allocation Strategy Eng-1545 | Rough path theory / Tensor signatures / Stock trend forecasting | 5717 | 2545 | No |
| 1444 | Hamiltonian Scholarly Sector Allocation Strategy Eng-2025 | Rough path theory / Tensor signatures / Stock trend forecasting | 5725 | 2568 | No |
| 1455 | Hamiltonian Scholarly Sector Allocation Strategy Eng-2505 | Rough path theory / Tensor signatures / Stock trend forecasting | 5733 | 2591 | No |
| 1466 | Hamiltonian Scholarly Sector Allocation Strategy Eng-2985 | Rough path theory / Tensor signatures / Stock trend forecasting | 5741 | 2614 | No |
| 1477 | Hamiltonian Scholarly Sector Allocation Strategy Eng-3465 | Rough path theory / Tensor signatures / Stock trend forecasting | 5749 | 2637 | No |
| 1488 | Hamiltonian Scholarly Sector Allocation Strategy Eng-3945 | Rough path theory / Tensor signatures / Stock trend forecasting | 5757 | 2660 | No |
| 1499 | Hamiltonian Scholarly Sector Allocation Strategy Eng-4425 | Rough path theory / Tensor signatures / Stock trend forecasting | 5765 | 2683 | No |
| 1510 | Hamiltonian Scholarly Sector Allocation Strategy Eng-4905 | Rough path theory / Tensor signatures / Stock trend forecasting | 5773 | 2706 | No |
| 1521 | Hamiltonian Scholarly Sector Allocation Strategy Eng-5385 | Rough path theory / Tensor signatures / Stock trend forecasting | 5781 | 2729 | No |
| 1532 | Hamiltonian Scholarly Sector Allocation Strategy Eng-5865 | Rough path theory / Tensor signatures / Stock trend forecasting | 5789 | 2752 | No |
| 3463 | Hamiltonian Scholarly Sector Allocation Strategy Eng-297 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 547 | 1974 | No |
| 3479 | Hamiltonian Scholarly Sector Allocation Strategy Eng-777 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 559 | 1986 | No |
| 3495 | Hamiltonian Scholarly Sector Allocation Strategy Eng-1257 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 571 | 1998 | No |
| 3511 | Hamiltonian Scholarly Sector Allocation Strategy Eng-1737 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 583 | 2010 | No |
| 3527 | Hamiltonian Scholarly Sector Allocation Strategy Eng-2217 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 595 | 2022 | No |
| 3543 | Hamiltonian Scholarly Sector Allocation Strategy Eng-2697 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 607 | 2034 | No |
| 3559 | Hamiltonian Scholarly Sector Allocation Strategy Eng-3177 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 619 | 2046 | No |
| 3575 | Hamiltonian Scholarly Sector Allocation Strategy Eng-3657 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 631 | 2058 | No |
| 3591 | Hamiltonian Scholarly Sector Allocation Strategy Eng-4137 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 643 | 2070 | No |
| 3607 | Hamiltonian Scholarly Sector Allocation Strategy Eng-4617 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 655 | 2082 | No |
| 3623 | Hamiltonian Scholarly Sector Allocation Strategy Eng-5097 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 667 | 2094 | No |
| 3639 | Hamiltonian Scholarly Sector Allocation Strategy Eng-5577 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 679 | 2106 | No |
| 5025 | Hamiltonian Scholarly Sector Allocation Strategy Eng-9 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7093 | 4443 | No |
| 5111 | Hamiltonian Scholarly Sector Allocation Strategy Eng-489 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7135 | 4536 | No |
| 5197 | Hamiltonian Scholarly Sector Allocation Strategy Eng-969 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7177 | 4629 | No |
| 5283 | Hamiltonian Scholarly Sector Allocation Strategy Eng-1449 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7219 | 4722 | No |
| 5369 | Hamiltonian Scholarly Sector Allocation Strategy Eng-1929 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7261 | 4815 | No |
| 5455 | Hamiltonian Scholarly Sector Allocation Strategy Eng-2409 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7303 | 4908 | No |
| 5541 | Hamiltonian Scholarly Sector Allocation Strategy Eng-2889 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7345 | 5001 | No |
| 5627 | Hamiltonian Scholarly Sector Allocation Strategy Eng-3369 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7387 | 5094 | No |
| 5713 | Hamiltonian Scholarly Sector Allocation Strategy Eng-3849 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7429 | 5187 | No |
| 5799 | Hamiltonian Scholarly Sector Allocation Strategy Eng-4329 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7471 | 5280 | No |
| 5885 | Hamiltonian Scholarly Sector Allocation Strategy Eng-4809 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7513 | 5373 | No |
| 5971 | Hamiltonian Scholarly Sector Allocation Strategy Eng-5289 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7555 | 5466 | No |
| 6057 | Hamiltonian Scholarly Sector Allocation Strategy Eng-5769 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7597 | 5559 | No |
| 7932 | Hamiltonian Scholarly Sector Allocation Strategy Eng-201 | Graph attention / Sector contagion / Stock baskets | 841 | 1392 | No |
| 7966 | Hamiltonian Scholarly Sector Allocation Strategy Eng-681 | Graph attention / Sector contagion / Stock baskets | 853 | 1418 | No |
| 8000 | Hamiltonian Scholarly Sector Allocation Strategy Eng-1161 | Graph attention / Sector contagion / Stock baskets | 865 | 1444 | No |
| 8034 | Hamiltonian Scholarly Sector Allocation Strategy Eng-1641 | Graph attention / Sector contagion / Stock baskets | 877 | 1470 | No |
| 8068 | Hamiltonian Scholarly Sector Allocation Strategy Eng-2121 | Graph attention / Sector contagion / Stock baskets | 889 | 1496 | No |
| 8102 | Hamiltonian Scholarly Sector Allocation Strategy Eng-2601 | Graph attention / Sector contagion / Stock baskets | 901 | 1522 | No |
| 8136 | Hamiltonian Scholarly Sector Allocation Strategy Eng-3081 | Graph attention / Sector contagion / Stock baskets | 913 | 1548 | No |
| 8170 | Hamiltonian Scholarly Sector Allocation Strategy Eng-3561 | Graph attention / Sector contagion / Stock baskets | 925 | 1574 | No |
| 8204 | Hamiltonian Scholarly Sector Allocation Strategy Eng-4041 | Graph attention / Sector contagion / Stock baskets | 937 | 1600 | No |
| 8238 | Hamiltonian Scholarly Sector Allocation Strategy Eng-4521 | Graph attention / Sector contagion / Stock baskets | 949 | 1626 | No |
| 8272 | Hamiltonian Scholarly Sector Allocation Strategy Eng-5001 | Graph attention / Sector contagion / Stock baskets | 961 | 1652 | No |
| 8306 | Hamiltonian Scholarly Sector Allocation Strategy Eng-5481 | Graph attention / Sector contagion / Stock baskets | 973 | 1678 | No |
| 8340 | Hamiltonian Scholarly Sector Allocation Strategy Eng-5961 | Graph attention / Sector contagion / Stock baskets | 985 | 1704 | No |
| 11600 | Hamiltonian Scholarly Sector Allocation Strategy Eng-393 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7967 | 8004 | No |
| 11791 | Hamiltonian Scholarly Sector Allocation Strategy Eng-873 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7984 | 8036 | No |
| 11982 | Hamiltonian Scholarly Sector Allocation Strategy Eng-1353 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8001 | 8068 | No |
| 12173 | Hamiltonian Scholarly Sector Allocation Strategy Eng-1833 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8018 | 8100 | No |
| 12364 | Hamiltonian Scholarly Sector Allocation Strategy Eng-2313 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8035 | 8132 | No |
| 12555 | Hamiltonian Scholarly Sector Allocation Strategy Eng-2793 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8052 | 8164 | No |
| 12746 | Hamiltonian Scholarly Sector Allocation Strategy Eng-3273 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8069 | 8196 | No |
| 12937 | Hamiltonian Scholarly Sector Allocation Strategy Eng-3753 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8086 | 8228 | No |
| 13128 | Hamiltonian Scholarly Sector Allocation Strategy Eng-4233 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8103 | 8260 | No |
| 13319 | Hamiltonian Scholarly Sector Allocation Strategy Eng-4713 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8120 | 8292 | No |
| 13510 | Hamiltonian Scholarly Sector Allocation Strategy Eng-5193 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8137 | 8324 | No |
| 13701 | Hamiltonian Scholarly Sector Allocation Strategy Eng-5673 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8154 | 8356 | No |
