# Robust approach to candidate alpha-signal generation

**Concept page** · shared by **10** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,762) ·
researched 2026-10-30

| | |
|---|---|
| Task | Candidate alpha-signal generation |
| Method | Robust (outlier-resistant) estimation |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Mass-producing candidate signals raises the multiple-testing bar faster than it finds edge; the staged sweep already generates candidates. |
| Implemented in volatility-ai | Nothing; the staged indicator sweep (`plan.md`) is the project's generator. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK395, RK222 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Robust Scholarly Alpha
Diffusion Generator Ref-345") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Use a generative model to propose or transform candidate signals, each
still needing out-of-sample validation and trading rules. The robust
version estimates its inputs with outlier-resistant statistics, so a few
extreme days do not drive the result. I found no study of this method on
this task.

## The CSV's description

Proposed robust approach to candidate alpha-signal generation: Use a
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
* Robust estimators trade efficiency for stability; in calm data they
  add little.

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
| 1762 | Robust Scholarly Alpha Diffusion Generator Ref-345 | Rough path theory / Tensor signatures / Stock trend forecasting | 5607 | 2164 | No |
| 1817 | Robust Scholarly Alpha Diffusion Generator Ref-825 | Rough path theory / Tensor signatures / Stock trend forecasting | 5615 | 2189 | No |
| 3815 | Robust Scholarly Alpha Diffusion Generator Ref-249 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6512 | 3071 | No |
| 3901 | Robust Scholarly Alpha Diffusion Generator Ref-729 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6555 | 3188 | No |
| 6190 | Robust Scholarly Alpha Diffusion Generator Ref-57 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 398 | 1845 | No |
| 6236 | Robust Scholarly Alpha Diffusion Generator Ref-537 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 410 | 1857 | No |
| 8737 | Robust Scholarly Alpha Diffusion Generator Ref-153 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7785 | 7593 | No |
| 8848 | Robust Scholarly Alpha Diffusion Generator Ref-441 | Graph attention / Sector contagion / Stock baskets | 717 | 1037 | No |
| 8928 | Robust Scholarly Alpha Diffusion Generator Ref-633 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7802 | 7617 | No |
| 9039 | Robust Scholarly Alpha Diffusion Generator Ref-921 | Graph attention / Sector contagion / Stock baskets | 733 | 1072 | No |
