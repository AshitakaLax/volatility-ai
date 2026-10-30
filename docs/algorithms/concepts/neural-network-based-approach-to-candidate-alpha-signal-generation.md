# Neural-network-based approach to candidate alpha-signal generation

**Concept page** · shared by **62** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #2,511) ·
researched 2026-10-30

| | |
|---|---|
| Task | Candidate alpha-signal generation |
| Method | Neural networks |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Mass-producing candidate signals raises the multiple-testing bar faster than it finds edge; the staged sweep already generates candidates. |
| Implemented in volatility-ai | Nothing; the staged indicator sweep (`plan.md`) is the project's generator. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK395, RK222 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Neural Scholarly Alpha
Diffusion Generator Eng-285") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Use a generative model to propose or transform candidate signals, each
still needing out-of-sample validation and trading rules. The
neural-network version fits a neural network to the task. I found no
study of this method on this task.

## The CSV's description

Proposed neural-network-based approach to candidate alpha-signal
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
* Neural forecasts on one index have not reliably beaten simple rules;
  an LSTM's stock picks were largely short-term reversal (Fischer &
  Krauss 2018, RK292).

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
| 2511 | Neural Scholarly Alpha Diffusion Generator Eng-285 | Rough path theory / Tensor signatures / Stock trend forecasting | 5696 | 2485 | No |
| 2566 | Neural Scholarly Alpha Diffusion Generator Eng-765 | Rough path theory / Tensor signatures / Stock trend forecasting | 5704 | 2508 | No |
| 2621 | Neural Scholarly Alpha Diffusion Generator Eng-1245 | Rough path theory / Tensor signatures / Stock trend forecasting | 5712 | 2531 | No |
| 2676 | Neural Scholarly Alpha Diffusion Generator Eng-1725 | Rough path theory / Tensor signatures / Stock trend forecasting | 5720 | 2554 | No |
| 2731 | Neural Scholarly Alpha Diffusion Generator Eng-2205 | Rough path theory / Tensor signatures / Stock trend forecasting | 5728 | 2577 | No |
| 2786 | Neural Scholarly Alpha Diffusion Generator Eng-2685 | Rough path theory / Tensor signatures / Stock trend forecasting | 5736 | 2600 | No |
| 2841 | Neural Scholarly Alpha Diffusion Generator Eng-3165 | Rough path theory / Tensor signatures / Stock trend forecasting | 5744 | 2623 | No |
| 2896 | Neural Scholarly Alpha Diffusion Generator Eng-3645 | Rough path theory / Tensor signatures / Stock trend forecasting | 5752 | 2646 | No |
| 2951 | Neural Scholarly Alpha Diffusion Generator Eng-4125 | Rough path theory / Tensor signatures / Stock trend forecasting | 5760 | 2669 | No |
| 3006 | Neural Scholarly Alpha Diffusion Generator Eng-4605 | Rough path theory / Tensor signatures / Stock trend forecasting | 5768 | 2692 | No |
| 3061 | Neural Scholarly Alpha Diffusion Generator Eng-5085 | Rough path theory / Tensor signatures / Stock trend forecasting | 5776 | 2715 | No |
| 3116 | Neural Scholarly Alpha Diffusion Generator Eng-5565 | Rough path theory / Tensor signatures / Stock trend forecasting | 5784 | 2738 | No |
| 5056 | Neural Scholarly Alpha Diffusion Generator Eng-189 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7110 | 4482 | No |
| 5142 | Neural Scholarly Alpha Diffusion Generator Eng-669 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7152 | 4575 | No |
| 5228 | Neural Scholarly Alpha Diffusion Generator Eng-1149 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7194 | 4668 | No |
| 5314 | Neural Scholarly Alpha Diffusion Generator Eng-1629 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7236 | 4761 | No |
| 5400 | Neural Scholarly Alpha Diffusion Generator Eng-2109 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7278 | 4854 | No |
| 5486 | Neural Scholarly Alpha Diffusion Generator Eng-2589 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7320 | 4947 | No |
| 5572 | Neural Scholarly Alpha Diffusion Generator Eng-3069 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7362 | 5040 | No |
| 5658 | Neural Scholarly Alpha Diffusion Generator Eng-3549 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7404 | 5133 | No |
| 5744 | Neural Scholarly Alpha Diffusion Generator Eng-4029 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7446 | 5226 | No |
| 5830 | Neural Scholarly Alpha Diffusion Generator Eng-4509 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7488 | 5319 | No |
| 5916 | Neural Scholarly Alpha Diffusion Generator Eng-4989 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7530 | 5412 | No |
| 6002 | Neural Scholarly Alpha Diffusion Generator Eng-5469 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7572 | 5505 | No |
| 6088 | Neural Scholarly Alpha Diffusion Generator Eng-5949 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7614 | 5598 | No |
| 6873 | Neural Scholarly Alpha Diffusion Generator Eng-477 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 551 | 1978 | No |
| 6919 | Neural Scholarly Alpha Diffusion Generator Eng-957 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 563 | 1990 | No |
| 6965 | Neural Scholarly Alpha Diffusion Generator Eng-1437 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 575 | 2002 | No |
| 7011 | Neural Scholarly Alpha Diffusion Generator Eng-1917 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 587 | 2014 | No |
| 7057 | Neural Scholarly Alpha Diffusion Generator Eng-2397 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 599 | 2026 | No |
| 7103 | Neural Scholarly Alpha Diffusion Generator Eng-2877 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 611 | 2038 | No |
| 7149 | Neural Scholarly Alpha Diffusion Generator Eng-3357 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 623 | 2050 | No |
| 7195 | Neural Scholarly Alpha Diffusion Generator Eng-3837 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 635 | 2062 | No |
| 7241 | Neural Scholarly Alpha Diffusion Generator Eng-4317 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 647 | 2074 | No |
| 7287 | Neural Scholarly Alpha Diffusion Generator Eng-4797 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 659 | 2086 | No |
| 7333 | Neural Scholarly Alpha Diffusion Generator Eng-5277 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 671 | 2098 | No |
| 7379 | Neural Scholarly Alpha Diffusion Generator Eng-5757 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 683 | 2110 | No |
| 11481 | Neural Scholarly Alpha Diffusion Generator Eng-93 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7956 | 7984 | No |
| 11592 | Neural Scholarly Alpha Diffusion Generator Eng-381 | Graph attention / Sector contagion / Stock baskets | 846 | 1403 | No |
| 11672 | Neural Scholarly Alpha Diffusion Generator Eng-573 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7973 | 8016 | No |
| 11783 | Neural Scholarly Alpha Diffusion Generator Eng-861 | Graph attention / Sector contagion / Stock baskets | 858 | 1429 | No |
| 11863 | Neural Scholarly Alpha Diffusion Generator Eng-1053 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7990 | 8048 | No |
| 11974 | Neural Scholarly Alpha Diffusion Generator Eng-1341 | Graph attention / Sector contagion / Stock baskets | 870 | 1455 | No |
| 12054 | Neural Scholarly Alpha Diffusion Generator Eng-1533 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8007 | 8080 | No |
| 12165 | Neural Scholarly Alpha Diffusion Generator Eng-1821 | Graph attention / Sector contagion / Stock baskets | 882 | 1481 | No |
| 12245 | Neural Scholarly Alpha Diffusion Generator Eng-2013 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8024 | 8112 | No |
| 12356 | Neural Scholarly Alpha Diffusion Generator Eng-2301 | Graph attention / Sector contagion / Stock baskets | 894 | 1507 | No |
| 12436 | Neural Scholarly Alpha Diffusion Generator Eng-2493 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8041 | 8144 | No |
| 12547 | Neural Scholarly Alpha Diffusion Generator Eng-2781 | Graph attention / Sector contagion / Stock baskets | 906 | 1533 | No |
| 12627 | Neural Scholarly Alpha Diffusion Generator Eng-2973 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8058 | 8176 | No |
| 12738 | Neural Scholarly Alpha Diffusion Generator Eng-3261 | Graph attention / Sector contagion / Stock baskets | 918 | 1559 | No |
| 12818 | Neural Scholarly Alpha Diffusion Generator Eng-3453 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8075 | 8208 | No |
| 12929 | Neural Scholarly Alpha Diffusion Generator Eng-3741 | Graph attention / Sector contagion / Stock baskets | 930 | 1585 | No |
| 13009 | Neural Scholarly Alpha Diffusion Generator Eng-3933 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8092 | 8240 | No |
| 13120 | Neural Scholarly Alpha Diffusion Generator Eng-4221 | Graph attention / Sector contagion / Stock baskets | 942 | 1611 | No |
| 13200 | Neural Scholarly Alpha Diffusion Generator Eng-4413 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8109 | 8272 | No |
| 13311 | Neural Scholarly Alpha Diffusion Generator Eng-4701 | Graph attention / Sector contagion / Stock baskets | 954 | 1637 | No |
| 13391 | Neural Scholarly Alpha Diffusion Generator Eng-4893 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8126 | 8304 | No |
| 13502 | Neural Scholarly Alpha Diffusion Generator Eng-5181 | Graph attention / Sector contagion / Stock baskets | 966 | 1663 | No |
| 13582 | Neural Scholarly Alpha Diffusion Generator Eng-5373 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8143 | 8336 | No |
| 13693 | Neural Scholarly Alpha Diffusion Generator Eng-5661 | Graph attention / Sector contagion / Stock baskets | 978 | 1689 | No |
| 13773 | Neural Scholarly Alpha Diffusion Generator Eng-5853 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8160 | 8368 | No |
