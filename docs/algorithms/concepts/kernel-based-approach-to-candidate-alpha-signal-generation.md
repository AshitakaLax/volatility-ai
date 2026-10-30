# Kernel-based approach to candidate alpha-signal generation

**Concept page** · shared by **63** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #2,525) ·
researched 2026-10-30

| | |
|---|---|
| Task | Candidate alpha-signal generation |
| Method | Kernel methods |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Mass-producing candidate signals raises the multiple-testing bar faster than it finds edge; the staged sweep already generates candidates. |
| Implemented in volatility-ai | Nothing; the staged indicator sweep (`plan.md`) is the project's generator. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK395, RK222 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Kernel Scholarly Alpha
Diffusion Generator Eng-405") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Use a generative model to propose or transform candidate signals, each
still needing out-of-sample validation and trading rules. The
kernel-based version replaces linear rules with kernel regressions or
similarity-weighted estimates. I found no study of this method on this
task.

## The CSV's description

Proposed kernel-based approach to candidate alpha-signal generation: Use
a diffusion-style generative model to propose or transform candidate
market features/signals; each signal would still require independent
out-of-sample validation and explicit trading rules. This is a
concept-level interpretation of the title, not a complete trading
specification: the exact model inputs/target, calibration, entry/exit or
rebalance rules, and position sizing are not fully defined here.

## Evidence

* **Harvey, Liu & Zhu (2016), "... and the Cross-Section of Expected
  Returns," *Review of Financial Studies* 29(1), 5–68:** after hundreds
  of tested factors, a new one needs a t-statistic above about 3.0, not
  2.0. (Abstract.)
* **McLean & Pontiff (2016), "Does Academic Research Destroy Stock
  Return Predictability?" *Journal of Finance* 71(1):** anomaly
  portfolio returns are 26% lower out of sample and 58% lower after
  publication. (Abstract.)

## Against, and failure modes

* Every extra candidate raises the bar a survivor must clear (Harvey,
  Liu & Zhu); published anomalies decay.
* Kernel bandwidths are tuning parameters, and with few independent
  episodes they overfit.

## Fit with volatility-ai

The project's staged sweep (`plan.md`) is already its candidate
generator. Generating more candidates without a matching
multiple-testing correction adds false discoveries, not edge.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Harvey, C. R., Liu, Y., Zhu, H. (2016). *Review of Financial Studies*
  29(1), 5–68. Abstract.
* McLean, R. D., Pontiff, J. (2016). *Journal of Finance* 71(1).
  Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 2525 | Kernel Scholarly Alpha Diffusion Generator Eng-405 | Rough path theory / Tensor signatures / Stock trend forecasting | 5698 | 2490 | No |
| 2580 | Kernel Scholarly Alpha Diffusion Generator Eng-885 | Rough path theory / Tensor signatures / Stock trend forecasting | 5706 | 2513 | No |
| 2635 | Kernel Scholarly Alpha Diffusion Generator Eng-1365 | Rough path theory / Tensor signatures / Stock trend forecasting | 5714 | 2536 | No |
| 2690 | Kernel Scholarly Alpha Diffusion Generator Eng-1845 | Rough path theory / Tensor signatures / Stock trend forecasting | 5722 | 2559 | No |
| 2745 | Kernel Scholarly Alpha Diffusion Generator Eng-2325 | Rough path theory / Tensor signatures / Stock trend forecasting | 5730 | 2582 | No |
| 2800 | Kernel Scholarly Alpha Diffusion Generator Eng-2805 | Rough path theory / Tensor signatures / Stock trend forecasting | 5738 | 2605 | No |
| 2855 | Kernel Scholarly Alpha Diffusion Generator Eng-3285 | Rough path theory / Tensor signatures / Stock trend forecasting | 5746 | 2628 | No |
| 2910 | Kernel Scholarly Alpha Diffusion Generator Eng-3765 | Rough path theory / Tensor signatures / Stock trend forecasting | 5754 | 2651 | No |
| 2965 | Kernel Scholarly Alpha Diffusion Generator Eng-4245 | Rough path theory / Tensor signatures / Stock trend forecasting | 5762 | 2674 | No |
| 3020 | Kernel Scholarly Alpha Diffusion Generator Eng-4725 | Rough path theory / Tensor signatures / Stock trend forecasting | 5770 | 2697 | No |
| 3075 | Kernel Scholarly Alpha Diffusion Generator Eng-5205 | Rough path theory / Tensor signatures / Stock trend forecasting | 5778 | 2720 | No |
| 3130 | Kernel Scholarly Alpha Diffusion Generator Eng-5685 | Rough path theory / Tensor signatures / Stock trend forecasting | 5786 | 2743 | No |
| 5078 | Kernel Scholarly Alpha Diffusion Generator Eng-309 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7122 | 4506 | No |
| 5164 | Kernel Scholarly Alpha Diffusion Generator Eng-789 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7164 | 4599 | No |
| 5250 | Kernel Scholarly Alpha Diffusion Generator Eng-1269 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7206 | 4692 | No |
| 5336 | Kernel Scholarly Alpha Diffusion Generator Eng-1749 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7248 | 4785 | No |
| 5422 | Kernel Scholarly Alpha Diffusion Generator Eng-2229 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7290 | 4878 | No |
| 5508 | Kernel Scholarly Alpha Diffusion Generator Eng-2709 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7332 | 4971 | No |
| 5594 | Kernel Scholarly Alpha Diffusion Generator Eng-3189 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7374 | 5064 | No |
| 5680 | Kernel Scholarly Alpha Diffusion Generator Eng-3669 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7416 | 5157 | No |
| 5766 | Kernel Scholarly Alpha Diffusion Generator Eng-4149 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7458 | 5250 | No |
| 5852 | Kernel Scholarly Alpha Diffusion Generator Eng-4629 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7500 | 5343 | No |
| 5938 | Kernel Scholarly Alpha Diffusion Generator Eng-5109 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7542 | 5436 | No |
| 6024 | Kernel Scholarly Alpha Diffusion Generator Eng-5589 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7584 | 5529 | No |
| 6840 | Kernel Scholarly Alpha Diffusion Generator Eng-117 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 542 | 1969 | No |
| 6886 | Kernel Scholarly Alpha Diffusion Generator Eng-597 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 554 | 1981 | No |
| 6932 | Kernel Scholarly Alpha Diffusion Generator Eng-1077 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 566 | 1993 | No |
| 6978 | Kernel Scholarly Alpha Diffusion Generator Eng-1557 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 578 | 2005 | No |
| 7024 | Kernel Scholarly Alpha Diffusion Generator Eng-2037 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 590 | 2017 | No |
| 7070 | Kernel Scholarly Alpha Diffusion Generator Eng-2517 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 602 | 2029 | No |
| 7116 | Kernel Scholarly Alpha Diffusion Generator Eng-2997 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 614 | 2041 | No |
| 7162 | Kernel Scholarly Alpha Diffusion Generator Eng-3477 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 626 | 2053 | No |
| 7208 | Kernel Scholarly Alpha Diffusion Generator Eng-3957 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 638 | 2065 | No |
| 7254 | Kernel Scholarly Alpha Diffusion Generator Eng-4437 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 650 | 2077 | No |
| 7300 | Kernel Scholarly Alpha Diffusion Generator Eng-4917 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 662 | 2089 | No |
| 7346 | Kernel Scholarly Alpha Diffusion Generator Eng-5397 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 674 | 2101 | No |
| 7392 | Kernel Scholarly Alpha Diffusion Generator Eng-5877 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 686 | 2113 | No |
| 11450 | Kernel Scholarly Alpha Diffusion Generator Eng-21 | Graph attention / Sector contagion / Stock baskets | 837 | 1384 | No |
| 11528 | Kernel Scholarly Alpha Diffusion Generator Eng-213 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7961 | 7992 | No |
| 11641 | Kernel Scholarly Alpha Diffusion Generator Eng-501 | Graph attention / Sector contagion / Stock baskets | 849 | 1410 | No |
| 11719 | Kernel Scholarly Alpha Diffusion Generator Eng-693 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7978 | 8024 | No |
| 11832 | Kernel Scholarly Alpha Diffusion Generator Eng-981 | Graph attention / Sector contagion / Stock baskets | 861 | 1436 | No |
| 11910 | Kernel Scholarly Alpha Diffusion Generator Eng-1173 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7995 | 8056 | No |
| 12023 | Kernel Scholarly Alpha Diffusion Generator Eng-1461 | Graph attention / Sector contagion / Stock baskets | 873 | 1462 | No |
| 12101 | Kernel Scholarly Alpha Diffusion Generator Eng-1653 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8012 | 8088 | No |
| 12214 | Kernel Scholarly Alpha Diffusion Generator Eng-1941 | Graph attention / Sector contagion / Stock baskets | 885 | 1488 | No |
| 12292 | Kernel Scholarly Alpha Diffusion Generator Eng-2133 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8029 | 8120 | No |
| 12405 | Kernel Scholarly Alpha Diffusion Generator Eng-2421 | Graph attention / Sector contagion / Stock baskets | 897 | 1514 | No |
| 12483 | Kernel Scholarly Alpha Diffusion Generator Eng-2613 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8046 | 8152 | No |
| 12596 | Kernel Scholarly Alpha Diffusion Generator Eng-2901 | Graph attention / Sector contagion / Stock baskets | 909 | 1540 | No |
| 12674 | Kernel Scholarly Alpha Diffusion Generator Eng-3093 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8063 | 8184 | No |
| 12787 | Kernel Scholarly Alpha Diffusion Generator Eng-3381 | Graph attention / Sector contagion / Stock baskets | 921 | 1566 | No |
| 12865 | Kernel Scholarly Alpha Diffusion Generator Eng-3573 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8080 | 8216 | No |
| 12978 | Kernel Scholarly Alpha Diffusion Generator Eng-3861 | Graph attention / Sector contagion / Stock baskets | 933 | 1592 | No |
| 13056 | Kernel Scholarly Alpha Diffusion Generator Eng-4053 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8097 | 8248 | No |
| 13169 | Kernel Scholarly Alpha Diffusion Generator Eng-4341 | Graph attention / Sector contagion / Stock baskets | 945 | 1618 | No |
| 13247 | Kernel Scholarly Alpha Diffusion Generator Eng-4533 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8114 | 8280 | No |
| 13360 | Kernel Scholarly Alpha Diffusion Generator Eng-4821 | Graph attention / Sector contagion / Stock baskets | 957 | 1644 | No |
| 13438 | Kernel Scholarly Alpha Diffusion Generator Eng-5013 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8131 | 8312 | No |
| 13551 | Kernel Scholarly Alpha Diffusion Generator Eng-5301 | Graph attention / Sector contagion / Stock baskets | 969 | 1670 | No |
| 13629 | Kernel Scholarly Alpha Diffusion Generator Eng-5493 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8148 | 8344 | No |
| 13742 | Kernel Scholarly Alpha Diffusion Generator Eng-5781 | Graph attention / Sector contagion / Stock baskets | 981 | 1696 | No |
| 13820 | Kernel Scholarly Alpha Diffusion Generator Eng-5973 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8165 | 8376 | No |
