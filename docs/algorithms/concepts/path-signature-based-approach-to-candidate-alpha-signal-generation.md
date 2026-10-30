# Path-signature-based approach to candidate alpha-signal generation

**Concept page** · shared by **62** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #2,497) ·
researched 2026-10-30

| | |
|---|---|
| Task | Candidate alpha-signal generation |
| Method | Path signatures |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Mass-producing candidate signals raises the multiple-testing bar faster than it finds edge; the staged sweep already generates candidates. |
| Implemented in volatility-ai | Nothing; the staged indicator sweep (`plan.md`) is the project's generator. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK395, RK222 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Signature Scholarly Alpha
Diffusion Generator Eng-165") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Use a generative model to propose or transform candidate signals, each
still needing out-of-sample validation and trading rules. The
path-signature version describes price paths by their iterated-integral
signatures and fits on those features. I found no study of this method
on this task.

## The CSV's description

Proposed path-signature-based approach to candidate alpha-signal
generation: Use a diffusion-style generative model to propose or
transform candidate market features/signals; each signal would still
require independent out-of-sample validation and explicit trading rules.
This is a concept-level interpretation of the title, not a complete
trading specification: the exact model inputs/target, calibration,
entry/exit or rebalance rules, and position sizing are not fully defined
here.

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
* Signature features multiply with depth and dimension; no out-of-sample
  trading evidence found (RK328).

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
| 2497 | Signature Scholarly Alpha Diffusion Generator Eng-165 | Rough path theory / Tensor signatures / Stock trend forecasting | 5694 | 2479 | No |
| 2552 | Signature Scholarly Alpha Diffusion Generator Eng-645 | Rough path theory / Tensor signatures / Stock trend forecasting | 5702 | 2502 | No |
| 2607 | Signature Scholarly Alpha Diffusion Generator Eng-1125 | Rough path theory / Tensor signatures / Stock trend forecasting | 5710 | 2525 | No |
| 2662 | Signature Scholarly Alpha Diffusion Generator Eng-1605 | Rough path theory / Tensor signatures / Stock trend forecasting | 5718 | 2548 | No |
| 2717 | Signature Scholarly Alpha Diffusion Generator Eng-2085 | Rough path theory / Tensor signatures / Stock trend forecasting | 5726 | 2571 | No |
| 2772 | Signature Scholarly Alpha Diffusion Generator Eng-2565 | Rough path theory / Tensor signatures / Stock trend forecasting | 5734 | 2594 | No |
| 2827 | Signature Scholarly Alpha Diffusion Generator Eng-3045 | Rough path theory / Tensor signatures / Stock trend forecasting | 5742 | 2617 | No |
| 2882 | Signature Scholarly Alpha Diffusion Generator Eng-3525 | Rough path theory / Tensor signatures / Stock trend forecasting | 5750 | 2640 | No |
| 2937 | Signature Scholarly Alpha Diffusion Generator Eng-4005 | Rough path theory / Tensor signatures / Stock trend forecasting | 5758 | 2663 | No |
| 2992 | Signature Scholarly Alpha Diffusion Generator Eng-4485 | Rough path theory / Tensor signatures / Stock trend forecasting | 5766 | 2686 | No |
| 3047 | Signature Scholarly Alpha Diffusion Generator Eng-4965 | Rough path theory / Tensor signatures / Stock trend forecasting | 5774 | 2709 | No |
| 3102 | Signature Scholarly Alpha Diffusion Generator Eng-5445 | Rough path theory / Tensor signatures / Stock trend forecasting | 5782 | 2732 | No |
| 3157 | Signature Scholarly Alpha Diffusion Generator Eng-5925 | Rough path theory / Tensor signatures / Stock trend forecasting | 5790 | 2755 | No |
| 5035 | Signature Scholarly Alpha Diffusion Generator Eng-69 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7100 | 4458 | No |
| 5121 | Signature Scholarly Alpha Diffusion Generator Eng-549 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7142 | 4551 | No |
| 5207 | Signature Scholarly Alpha Diffusion Generator Eng-1029 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7184 | 4644 | No |
| 5293 | Signature Scholarly Alpha Diffusion Generator Eng-1509 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7226 | 4737 | No |
| 5379 | Signature Scholarly Alpha Diffusion Generator Eng-1989 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7268 | 4830 | No |
| 5465 | Signature Scholarly Alpha Diffusion Generator Eng-2469 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7310 | 4923 | No |
| 5551 | Signature Scholarly Alpha Diffusion Generator Eng-2949 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7352 | 5016 | No |
| 5637 | Signature Scholarly Alpha Diffusion Generator Eng-3429 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7394 | 5109 | No |
| 5723 | Signature Scholarly Alpha Diffusion Generator Eng-3909 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7436 | 5202 | No |
| 5809 | Signature Scholarly Alpha Diffusion Generator Eng-4389 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7478 | 5295 | No |
| 5895 | Signature Scholarly Alpha Diffusion Generator Eng-4869 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7520 | 5388 | No |
| 5981 | Signature Scholarly Alpha Diffusion Generator Eng-5349 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7562 | 5481 | No |
| 6067 | Signature Scholarly Alpha Diffusion Generator Eng-5829 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7604 | 5574 | No |
| 6862 | Signature Scholarly Alpha Diffusion Generator Eng-357 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 549 | 1975 | No |
| 6908 | Signature Scholarly Alpha Diffusion Generator Eng-837 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 561 | 1987 | No |
| 6954 | Signature Scholarly Alpha Diffusion Generator Eng-1317 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 573 | 1999 | No |
| 7000 | Signature Scholarly Alpha Diffusion Generator Eng-1797 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 585 | 2011 | No |
| 7046 | Signature Scholarly Alpha Diffusion Generator Eng-2277 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 597 | 2023 | No |
| 7092 | Signature Scholarly Alpha Diffusion Generator Eng-2757 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 609 | 2035 | No |
| 7138 | Signature Scholarly Alpha Diffusion Generator Eng-3237 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 621 | 2047 | No |
| 7184 | Signature Scholarly Alpha Diffusion Generator Eng-3717 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 633 | 2059 | No |
| 7230 | Signature Scholarly Alpha Diffusion Generator Eng-4197 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 645 | 2071 | No |
| 7276 | Signature Scholarly Alpha Diffusion Generator Eng-4677 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 657 | 2083 | No |
| 7322 | Signature Scholarly Alpha Diffusion Generator Eng-5157 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 669 | 2095 | No |
| 7368 | Signature Scholarly Alpha Diffusion Generator Eng-5637 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 681 | 2107 | No |
| 11546 | Signature Scholarly Alpha Diffusion Generator Eng-261 | Graph attention / Sector contagion / Stock baskets | 843 | 1397 | No |
| 11622 | Signature Scholarly Alpha Diffusion Generator Eng-453 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7969 | 8008 | No |
| 11737 | Signature Scholarly Alpha Diffusion Generator Eng-741 | Graph attention / Sector contagion / Stock baskets | 855 | 1423 | No |
| 11813 | Signature Scholarly Alpha Diffusion Generator Eng-933 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7986 | 8040 | No |
| 11928 | Signature Scholarly Alpha Diffusion Generator Eng-1221 | Graph attention / Sector contagion / Stock baskets | 867 | 1449 | No |
| 12004 | Signature Scholarly Alpha Diffusion Generator Eng-1413 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8003 | 8072 | No |
| 12119 | Signature Scholarly Alpha Diffusion Generator Eng-1701 | Graph attention / Sector contagion / Stock baskets | 879 | 1475 | No |
| 12195 | Signature Scholarly Alpha Diffusion Generator Eng-1893 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8020 | 8104 | No |
| 12310 | Signature Scholarly Alpha Diffusion Generator Eng-2181 | Graph attention / Sector contagion / Stock baskets | 891 | 1501 | No |
| 12386 | Signature Scholarly Alpha Diffusion Generator Eng-2373 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8037 | 8136 | No |
| 12501 | Signature Scholarly Alpha Diffusion Generator Eng-2661 | Graph attention / Sector contagion / Stock baskets | 903 | 1527 | No |
| 12577 | Signature Scholarly Alpha Diffusion Generator Eng-2853 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8054 | 8168 | No |
| 12692 | Signature Scholarly Alpha Diffusion Generator Eng-3141 | Graph attention / Sector contagion / Stock baskets | 915 | 1553 | No |
| 12768 | Signature Scholarly Alpha Diffusion Generator Eng-3333 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8071 | 8200 | No |
| 12883 | Signature Scholarly Alpha Diffusion Generator Eng-3621 | Graph attention / Sector contagion / Stock baskets | 927 | 1579 | No |
| 12959 | Signature Scholarly Alpha Diffusion Generator Eng-3813 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8088 | 8232 | No |
| 13074 | Signature Scholarly Alpha Diffusion Generator Eng-4101 | Graph attention / Sector contagion / Stock baskets | 939 | 1605 | No |
| 13150 | Signature Scholarly Alpha Diffusion Generator Eng-4293 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8105 | 8264 | No |
| 13265 | Signature Scholarly Alpha Diffusion Generator Eng-4581 | Graph attention / Sector contagion / Stock baskets | 951 | 1631 | No |
| 13341 | Signature Scholarly Alpha Diffusion Generator Eng-4773 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8122 | 8296 | No |
| 13456 | Signature Scholarly Alpha Diffusion Generator Eng-5061 | Graph attention / Sector contagion / Stock baskets | 963 | 1657 | No |
| 13532 | Signature Scholarly Alpha Diffusion Generator Eng-5253 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8139 | 8328 | No |
| 13647 | Signature Scholarly Alpha Diffusion Generator Eng-5541 | Graph attention / Sector contagion / Stock baskets | 975 | 1683 | No |
| 13723 | Signature Scholarly Alpha Diffusion Generator Eng-5733 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8156 | 8360 | No |
