# Nonlinear approach to candidate alpha-signal generation

**Concept page** · shared by **62** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #2,078) ·
researched 2026-10-30

| | |
|---|---|
| Task | Candidate alpha-signal generation |
| Method | Nonlinear models |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Mass-producing candidate signals raises the multiple-testing bar faster than it finds edge; the staged sweep already generates candidates. |
| Implemented in volatility-ai | Nothing; the staged indicator sweep (`plan.md`) is the project's generator. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK395, RK222 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Non-Linear Scholarly Alpha
Diffusion Generator Mod-345") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Use a generative model to propose or transform candidate signals, each
still needing out-of-sample validation and trading rules. The nonlinear
version replaces linear rules with nonlinear regressions or filters. I
found no study of this method on this task.

## The CSV's description

Proposed nonlinear approach to candidate alpha-signal generation: Use a
diffusion-style generative model to propose or transform candidate
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
* Nonlinear fits on a few thousand daily bars overfit easily; gains over
  linear rules are usually small out of sample.

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
| 2078 | Non-Linear Scholarly Alpha Diffusion Generator Mod-345 | Rough path theory / Tensor signatures / Stock trend forecasting | 5638 | 2294 | No |
| 2131 | Non-Linear Scholarly Alpha Diffusion Generator Mod-825 | Rough path theory / Tensor signatures / Stock trend forecasting | 5645 | 2317 | No |
| 2184 | Non-Linear Scholarly Alpha Diffusion Generator Mod-1305 | Rough path theory / Tensor signatures / Stock trend forecasting | 5652 | 2340 | No |
| 2237 | Non-Linear Scholarly Alpha Diffusion Generator Mod-1785 | Rough path theory / Tensor signatures / Stock trend forecasting | 5659 | 2363 | No |
| 2290 | Non-Linear Scholarly Alpha Diffusion Generator Mod-2265 | Rough path theory / Tensor signatures / Stock trend forecasting | 5666 | 2386 | No |
| 2343 | Non-Linear Scholarly Alpha Diffusion Generator Mod-2745 | Rough path theory / Tensor signatures / Stock trend forecasting | 5673 | 2409 | No |
| 2396 | Non-Linear Scholarly Alpha Diffusion Generator Mod-3225 | Rough path theory / Tensor signatures / Stock trend forecasting | 5680 | 2432 | No |
| 2449 | Non-Linear Scholarly Alpha Diffusion Generator Mod-3705 | Rough path theory / Tensor signatures / Stock trend forecasting | 5687 | 2455 | No |
| 4018 | Non-Linear Scholarly Alpha Diffusion Generator Sys-375 | Neural SDEs / Adversarial robustness / Stock options hedging | 8352 | 2806 | No |
| 4104 | Non-Linear Scholarly Alpha Diffusion Generator Sys-855 | Neural SDEs / Adversarial robustness / Stock options hedging | 8392 | 2812 | No |
| 4190 | Non-Linear Scholarly Alpha Diffusion Generator Sys-1335 | Neural SDEs / Adversarial robustness / Stock options hedging | 8432 | 2818 | No |
| 4276 | Non-Linear Scholarly Alpha Diffusion Generator Sys-1815 | Neural SDEs / Adversarial robustness / Stock options hedging | 8472 | 2824 | No |
| 4358 | Non-Linear Scholarly Alpha Diffusion Generator Mod-249 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6765 | 3700 | No |
| 4443 | Non-Linear Scholarly Alpha Diffusion Generator Mod-729 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6807 | 3795 | No |
| 4528 | Non-Linear Scholarly Alpha Diffusion Generator Mod-1209 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6849 | 3890 | No |
| 4613 | Non-Linear Scholarly Alpha Diffusion Generator Mod-1689 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6891 | 3985 | No |
| 4698 | Non-Linear Scholarly Alpha Diffusion Generator Mod-2169 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6933 | 4080 | No |
| 4783 | Non-Linear Scholarly Alpha Diffusion Generator Mod-2649 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6975 | 4175 | No |
| 4868 | Non-Linear Scholarly Alpha Diffusion Generator Mod-3129 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7017 | 4270 | No |
| 4953 | Non-Linear Scholarly Alpha Diffusion Generator Mod-3609 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7059 | 4365 | No |
| 6459 | Non-Linear Scholarly Alpha Diffusion Generator Mod-57 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 456 | 1885 | No |
| 6504 | Non-Linear Scholarly Alpha Diffusion Generator Mod-537 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 466 | 1895 | No |
| 6549 | Non-Linear Scholarly Alpha Diffusion Generator Mod-1017 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 476 | 1905 | No |
| 6594 | Non-Linear Scholarly Alpha Diffusion Generator Mod-1497 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 486 | 1915 | No |
| 6639 | Non-Linear Scholarly Alpha Diffusion Generator Mod-1977 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 496 | 1925 | No |
| 6684 | Non-Linear Scholarly Alpha Diffusion Generator Mod-2457 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 506 | 1935 | No |
| 6729 | Non-Linear Scholarly Alpha Diffusion Generator Mod-2937 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 516 | 1945 | No |
| 6774 | Non-Linear Scholarly Alpha Diffusion Generator Mod-3417 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 526 | 1955 | No |
| 6819 | Non-Linear Scholarly Alpha Diffusion Generator Mod-3897 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 536 | 1965 | No |
| 9106 | Non-Linear Scholarly Alpha Diffusion Generator Sys-87 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4707 | 10775 | No |
| 9143 | Non-Linear Scholarly Alpha Diffusion Generator Sys-183 | Topological data analysis / Betti persistence / Stock pairs | 2212 | 6598 | No |
| 9183 | Non-Linear Scholarly Alpha Diffusion Generator Sys-279 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2219 | 3312 | No |
| 9293 | Non-Linear Scholarly Alpha Diffusion Generator Sys-567 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4738 | 10798 | No |
| 9330 | Non-Linear Scholarly Alpha Diffusion Generator Sys-663 | Topological data analysis / Betti persistence / Stock pairs | 2259 | 6634 | No |
| 9370 | Non-Linear Scholarly Alpha Diffusion Generator Sys-759 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2266 | 3407 | No |
| 9480 | Non-Linear Scholarly Alpha Diffusion Generator Sys-1047 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4769 | 10821 | No |
| 9517 | Non-Linear Scholarly Alpha Diffusion Generator Sys-1143 | Topological data analysis / Betti persistence / Stock pairs | 2306 | 6670 | No |
| 9557 | Non-Linear Scholarly Alpha Diffusion Generator Sys-1239 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2313 | 3502 | No |
| 9667 | Non-Linear Scholarly Alpha Diffusion Generator Sys-1527 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4800 | 10844 | No |
| 9704 | Non-Linear Scholarly Alpha Diffusion Generator Sys-1623 | Topological data analysis / Betti persistence / Stock pairs | 2353 | 6706 | No |
| 9744 | Non-Linear Scholarly Alpha Diffusion Generator Sys-1719 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2360 | 3597 | No |
| 9911 | Non-Linear Scholarly Alpha Diffusion Generator Mod-153 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7840 | 7737 | No |
| 10028 | Non-Linear Scholarly Alpha Diffusion Generator Mod-441 | Graph attention / Sector contagion / Stock baskets | 761 | 1201 | No |
| 10102 | Non-Linear Scholarly Alpha Diffusion Generator Mod-633 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7854 | 7767 | No |
| 10219 | Non-Linear Scholarly Alpha Diffusion Generator Mod-921 | Graph attention / Sector contagion / Stock baskets | 771 | 1225 | No |
| 10293 | Non-Linear Scholarly Alpha Diffusion Generator Mod-1113 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7868 | 7797 | No |
| 10410 | Non-Linear Scholarly Alpha Diffusion Generator Mod-1401 | Graph attention / Sector contagion / Stock baskets | 781 | 1249 | No |
| 10484 | Non-Linear Scholarly Alpha Diffusion Generator Mod-1593 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7882 | 7827 | No |
| 10601 | Non-Linear Scholarly Alpha Diffusion Generator Mod-1881 | Graph attention / Sector contagion / Stock baskets | 791 | 1273 | No |
| 10675 | Non-Linear Scholarly Alpha Diffusion Generator Mod-2073 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7896 | 7857 | No |
| 10792 | Non-Linear Scholarly Alpha Diffusion Generator Mod-2361 | Graph attention / Sector contagion / Stock baskets | 801 | 1297 | No |
| 10866 | Non-Linear Scholarly Alpha Diffusion Generator Mod-2553 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7910 | 7887 | No |
| 10983 | Non-Linear Scholarly Alpha Diffusion Generator Mod-2841 | Graph attention / Sector contagion / Stock baskets | 811 | 1321 | No |
| 11057 | Non-Linear Scholarly Alpha Diffusion Generator Mod-3033 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7924 | 7917 | No |
| 11174 | Non-Linear Scholarly Alpha Diffusion Generator Mod-3321 | Graph attention / Sector contagion / Stock baskets | 821 | 1345 | No |
| 11248 | Non-Linear Scholarly Alpha Diffusion Generator Mod-3513 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7938 | 7947 | No |
| 11365 | Non-Linear Scholarly Alpha Diffusion Generator Mod-3801 | Graph attention / Sector contagion / Stock baskets | 831 | 1369 | No |
| 11439 | Non-Linear Scholarly Alpha Diffusion Generator Mod-3993 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7952 | 7977 | No |
| 13915 | Non-Linear Scholarly Alpha Diffusion Generator Sys-471 | Delay differential equations / Controlled ODEs / Stock execution | 3946 | 1103 | No |
| 13933 | Non-Linear Scholarly Alpha Diffusion Generator Sys-951 | Delay differential equations / Controlled ODEs / Stock execution | 3975 | 1127 | No |
| 13951 | Non-Linear Scholarly Alpha Diffusion Generator Sys-1431 | Delay differential equations / Controlled ODEs / Stock execution | 4004 | 1151 | No |
| 13969 | Non-Linear Scholarly Alpha Diffusion Generator Sys-1911 | Delay differential equations / Controlled ODEs / Stock execution | 4033 | 1175 | No |
