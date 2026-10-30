# Koopman-operator-based approach to candidate alpha-signal generation

**Concept page** · shared by **16** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,664) ·
researched 2026-10-30

| | |
|---|---|
| Task | Candidate alpha-signal generation |
| Method | Koopman operators (DMD / EDMD) |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Mass-producing candidate signals raises the multiple-testing bar faster than it finds edge; the staged sweep already generates candidates. |
| Implemented in volatility-ai | Nothing; the staged indicator sweep (`plan.md`) is the project's generator. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK395, RK222 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Koopman Scholarly Alpha
Diffusion Generator Alpha-45") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Use a generative model to propose or transform candidate signals, each
still needing out-of-sample validation and trading rules. The Koopman
version linearises the dynamics in a lifted feature space and forecasts
with the linear operator. I found no study of this method on this task.

## The CSV's description

Proposed Koopman-operator-based approach to candidate alpha-signal
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
* The Koopman entries in the list have no peer-reviewed trading evidence
  (RK206).

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
| 1664 | Koopman Scholarly Alpha Diffusion Generator Alpha-45 | Rough path theory / Signature transforms / Stock momentum | 1887 | 309 | No |
| 1677 | Koopman Scholarly Alpha Diffusion Generator Alpha-145 | Rough path theory / Signature transforms / Stock momentum | 2091 | 445 | No |
| 1690 | Koopman Scholarly Alpha Diffusion Generator Alpha-245 | Rough path theory / Signature transforms / Stock momentum | 3851 | 2141 | No |
| 1703 | Koopman Scholarly Alpha Diffusion Generator Alpha-345 | Rough path theory / Signature transforms / Stock momentum | 1895 | 313 | No |
| 1716 | Koopman Scholarly Alpha Diffusion Generator Alpha-445 | Rough path theory / Signature transforms / Stock momentum | 2121 | 459 | No |
| 1734 | Koopman Scholarly Alpha Diffusion Generator Ref-105 | Rough path theory / Tensor signatures / Stock trend forecasting | 5603 | 2152 | No |
| 1789 | Koopman Scholarly Alpha Diffusion Generator Ref-585 | Rough path theory / Tensor signatures / Stock trend forecasting | 5611 | 2177 | No |
| 3772 | Koopman Scholarly Alpha Diffusion Generator Ref-9 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6491 | 3012 | No |
| 3858 | Koopman Scholarly Alpha Diffusion Generator Ref-489 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6534 | 3129 | No |
| 3944 | Koopman Scholarly Alpha Diffusion Generator Ref-969 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6577 | 3246 | No |
| 6215 | Koopman Scholarly Alpha Diffusion Generator Ref-297 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 404 | 1851 | No |
| 6261 | Koopman Scholarly Alpha Diffusion Generator Ref-777 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 416 | 1863 | No |
| 8754 | Koopman Scholarly Alpha Diffusion Generator Ref-201 | Graph attention / Sector contagion / Stock baskets | 709 | 1020 | No |
| 8832 | Koopman Scholarly Alpha Diffusion Generator Ref-393 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7794 | 7605 | No |
| 8945 | Koopman Scholarly Alpha Diffusion Generator Ref-681 | Graph attention / Sector contagion / Stock baskets | 725 | 1055 | No |
| 9023 | Koopman Scholarly Alpha Diffusion Generator Ref-873 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7811 | 7629 | No |
