# Evolutionary-optimization-based approach to candidate alpha-signal generation

**Concept page** · shared by **63** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #2,484) ·
researched 2026-10-30

| | |
|---|---|
| Task | Candidate alpha-signal generation |
| Method | Evolutionary / genetic optimisation |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Mass-producing candidate signals raises the multiple-testing bar faster than it finds edge; the staged sweep already generates candidates. |
| Implemented in volatility-ai | Nothing; the staged indicator sweep (`plan.md`) is the project's generator. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK395, RK222 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Evolutionary Scholarly
Alpha Diffusion Generator Eng-45") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Use a generative model to propose or transform candidate signals, each
still needing out-of-sample validation and trading rules. The
evolutionary version searches parameters or weights with genetic
algorithms. I found no study of this method on this task.

## The CSV's description

Proposed evolutionary-optimization-based approach to candidate
alpha-signal generation: Use a diffusion-style generative model to
propose or transform candidate market features/signals; each signal
would still require independent out-of-sample validation and explicit
trading rules. This is a concept-level interpretation of the title, not
a complete trading specification: the exact model inputs/target,
calibration, entry/exit or rebalance rules, and position sizing are not
fully defined here.

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
* A genetic search over a backtest is a large multiple-testing exercise
  that finds the noise that fits best.

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
| 2484 | Evolutionary Scholarly Alpha Diffusion Generator Eng-45 | Rough path theory / Tensor signatures / Stock trend forecasting | 5692 | 2473 | No |
| 2539 | Evolutionary Scholarly Alpha Diffusion Generator Eng-525 | Rough path theory / Tensor signatures / Stock trend forecasting | 5700 | 2496 | No |
| 2594 | Evolutionary Scholarly Alpha Diffusion Generator Eng-1005 | Rough path theory / Tensor signatures / Stock trend forecasting | 5708 | 2519 | No |
| 2649 | Evolutionary Scholarly Alpha Diffusion Generator Eng-1485 | Rough path theory / Tensor signatures / Stock trend forecasting | 5716 | 2542 | No |
| 2704 | Evolutionary Scholarly Alpha Diffusion Generator Eng-1965 | Rough path theory / Tensor signatures / Stock trend forecasting | 5724 | 2565 | No |
| 2759 | Evolutionary Scholarly Alpha Diffusion Generator Eng-2445 | Rough path theory / Tensor signatures / Stock trend forecasting | 5732 | 2588 | No |
| 2814 | Evolutionary Scholarly Alpha Diffusion Generator Eng-2925 | Rough path theory / Tensor signatures / Stock trend forecasting | 5740 | 2611 | No |
| 2869 | Evolutionary Scholarly Alpha Diffusion Generator Eng-3405 | Rough path theory / Tensor signatures / Stock trend forecasting | 5748 | 2634 | No |
| 2924 | Evolutionary Scholarly Alpha Diffusion Generator Eng-3885 | Rough path theory / Tensor signatures / Stock trend forecasting | 5756 | 2657 | No |
| 2979 | Evolutionary Scholarly Alpha Diffusion Generator Eng-4365 | Rough path theory / Tensor signatures / Stock trend forecasting | 5764 | 2680 | No |
| 3034 | Evolutionary Scholarly Alpha Diffusion Generator Eng-4845 | Rough path theory / Tensor signatures / Stock trend forecasting | 5772 | 2703 | No |
| 3089 | Evolutionary Scholarly Alpha Diffusion Generator Eng-5325 | Rough path theory / Tensor signatures / Stock trend forecasting | 5780 | 2726 | No |
| 3144 | Evolutionary Scholarly Alpha Diffusion Generator Eng-5805 | Rough path theory / Tensor signatures / Stock trend forecasting | 5788 | 2749 | No |
| 5099 | Evolutionary Scholarly Alpha Diffusion Generator Eng-429 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7133 | 4530 | No |
| 5185 | Evolutionary Scholarly Alpha Diffusion Generator Eng-909 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7175 | 4623 | No |
| 5271 | Evolutionary Scholarly Alpha Diffusion Generator Eng-1389 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7217 | 4716 | No |
| 5357 | Evolutionary Scholarly Alpha Diffusion Generator Eng-1869 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7259 | 4809 | No |
| 5443 | Evolutionary Scholarly Alpha Diffusion Generator Eng-2349 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7301 | 4902 | No |
| 5529 | Evolutionary Scholarly Alpha Diffusion Generator Eng-2829 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7343 | 4995 | No |
| 5615 | Evolutionary Scholarly Alpha Diffusion Generator Eng-3309 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7385 | 5088 | No |
| 5701 | Evolutionary Scholarly Alpha Diffusion Generator Eng-3789 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7427 | 5181 | No |
| 5787 | Evolutionary Scholarly Alpha Diffusion Generator Eng-4269 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7469 | 5274 | No |
| 5873 | Evolutionary Scholarly Alpha Diffusion Generator Eng-4749 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7511 | 5367 | No |
| 5959 | Evolutionary Scholarly Alpha Diffusion Generator Eng-5229 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7553 | 5460 | No |
| 6045 | Evolutionary Scholarly Alpha Diffusion Generator Eng-5709 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7595 | 5553 | No |
| 6852 | Evolutionary Scholarly Alpha Diffusion Generator Eng-237 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 545 | 1972 | No |
| 6898 | Evolutionary Scholarly Alpha Diffusion Generator Eng-717 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 557 | 1984 | No |
| 6944 | Evolutionary Scholarly Alpha Diffusion Generator Eng-1197 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 569 | 1996 | No |
| 6990 | Evolutionary Scholarly Alpha Diffusion Generator Eng-1677 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 581 | 2008 | No |
| 7036 | Evolutionary Scholarly Alpha Diffusion Generator Eng-2157 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 593 | 2020 | No |
| 7082 | Evolutionary Scholarly Alpha Diffusion Generator Eng-2637 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 605 | 2032 | No |
| 7128 | Evolutionary Scholarly Alpha Diffusion Generator Eng-3117 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 617 | 2044 | No |
| 7174 | Evolutionary Scholarly Alpha Diffusion Generator Eng-3597 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 629 | 2056 | No |
| 7220 | Evolutionary Scholarly Alpha Diffusion Generator Eng-4077 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 641 | 2068 | No |
| 7266 | Evolutionary Scholarly Alpha Diffusion Generator Eng-4557 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 653 | 2080 | No |
| 7312 | Evolutionary Scholarly Alpha Diffusion Generator Eng-5037 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 665 | 2092 | No |
| 7358 | Evolutionary Scholarly Alpha Diffusion Generator Eng-5517 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 677 | 2104 | No |
| 7404 | Evolutionary Scholarly Alpha Diffusion Generator Eng-5997 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 689 | 2116 | No |
| 11500 | Evolutionary Scholarly Alpha Diffusion Generator Eng-141 | Graph attention / Sector contagion / Stock baskets | 840 | 1390 | No |
| 11573 | Evolutionary Scholarly Alpha Diffusion Generator Eng-333 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7965 | 8000 | No |
| 11691 | Evolutionary Scholarly Alpha Diffusion Generator Eng-621 | Graph attention / Sector contagion / Stock baskets | 852 | 1416 | No |
| 11764 | Evolutionary Scholarly Alpha Diffusion Generator Eng-813 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7982 | 8032 | No |
| 11882 | Evolutionary Scholarly Alpha Diffusion Generator Eng-1101 | Graph attention / Sector contagion / Stock baskets | 864 | 1442 | No |
| 11955 | Evolutionary Scholarly Alpha Diffusion Generator Eng-1293 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7999 | 8064 | No |
| 12073 | Evolutionary Scholarly Alpha Diffusion Generator Eng-1581 | Graph attention / Sector contagion / Stock baskets | 876 | 1468 | No |
| 12146 | Evolutionary Scholarly Alpha Diffusion Generator Eng-1773 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8016 | 8096 | No |
| 12264 | Evolutionary Scholarly Alpha Diffusion Generator Eng-2061 | Graph attention / Sector contagion / Stock baskets | 888 | 1494 | No |
| 12337 | Evolutionary Scholarly Alpha Diffusion Generator Eng-2253 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8033 | 8128 | No |
| 12455 | Evolutionary Scholarly Alpha Diffusion Generator Eng-2541 | Graph attention / Sector contagion / Stock baskets | 900 | 1520 | No |
| 12528 | Evolutionary Scholarly Alpha Diffusion Generator Eng-2733 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8050 | 8160 | No |
| 12646 | Evolutionary Scholarly Alpha Diffusion Generator Eng-3021 | Graph attention / Sector contagion / Stock baskets | 912 | 1546 | No |
| 12719 | Evolutionary Scholarly Alpha Diffusion Generator Eng-3213 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8067 | 8192 | No |
| 12837 | Evolutionary Scholarly Alpha Diffusion Generator Eng-3501 | Graph attention / Sector contagion / Stock baskets | 924 | 1572 | No |
| 12910 | Evolutionary Scholarly Alpha Diffusion Generator Eng-3693 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8084 | 8224 | No |
| 13028 | Evolutionary Scholarly Alpha Diffusion Generator Eng-3981 | Graph attention / Sector contagion / Stock baskets | 936 | 1598 | No |
| 13101 | Evolutionary Scholarly Alpha Diffusion Generator Eng-4173 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8101 | 8256 | No |
| 13219 | Evolutionary Scholarly Alpha Diffusion Generator Eng-4461 | Graph attention / Sector contagion / Stock baskets | 948 | 1624 | No |
| 13292 | Evolutionary Scholarly Alpha Diffusion Generator Eng-4653 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8118 | 8288 | No |
| 13410 | Evolutionary Scholarly Alpha Diffusion Generator Eng-4941 | Graph attention / Sector contagion / Stock baskets | 960 | 1650 | No |
| 13483 | Evolutionary Scholarly Alpha Diffusion Generator Eng-5133 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8135 | 8320 | No |
| 13601 | Evolutionary Scholarly Alpha Diffusion Generator Eng-5421 | Graph attention / Sector contagion / Stock baskets | 972 | 1676 | No |
| 13674 | Evolutionary Scholarly Alpha Diffusion Generator Eng-5613 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8152 | 8352 | No |
| 13792 | Evolutionary Scholarly Alpha Diffusion Generator Eng-5901 | Graph attention / Sector contagion / Stock baskets | 984 | 1702 | No |
