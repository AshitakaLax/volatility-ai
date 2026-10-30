# Attention-weighted approach to candidate alpha-signal generation

**Concept page** · shared by **10** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,774) ·
researched 2026-10-30

| | |
|---|---|
| Task | Candidate alpha-signal generation |
| Method | Attention networks |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Mass-producing candidate signals raises the multiple-testing bar faster than it finds edge; the staged sweep already generates candidates. |
| Implemented in volatility-ai | Nothing; the staged indicator sweep (`plan.md`) is the project's generator. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK395, RK222 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Attentional Scholarly Alpha
Diffusion Generator Ref-465") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Use a generative model to propose or transform candidate signals, each
still needing out-of-sample validation and trading rules. The attention
version weights its inputs with a learned attention network. I found no
study of this method on this task.

## The CSV's description

Proposed attention-weighted approach to candidate alpha-signal
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
* Attention networks need far more data than daily bars of a few ETFs
  provide.

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
| 1774 | Attentional Scholarly Alpha Diffusion Generator Ref-465 | Rough path theory / Tensor signatures / Stock trend forecasting | 5609 | 2170 | No |
| 1829 | Attentional Scholarly Alpha Diffusion Generator Ref-945 | Rough path theory / Tensor signatures / Stock trend forecasting | 5617 | 2195 | No |
| 3837 | Attentional Scholarly Alpha Diffusion Generator Ref-369 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6523 | 3100 | No |
| 3923 | Attentional Scholarly Alpha Diffusion Generator Ref-849 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6566 | 3217 | No |
| 6204 | Attentional Scholarly Alpha Diffusion Generator Ref-177 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 401 | 1848 | No |
| 6250 | Attentional Scholarly Alpha Diffusion Generator Ref-657 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 413 | 1860 | No |
| 8707 | Attentional Scholarly Alpha Diffusion Generator Ref-81 | Graph attention / Sector contagion / Stock baskets | 705 | 1011 | No |
| 8785 | Attentional Scholarly Alpha Diffusion Generator Ref-273 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7790 | 7599 | No |
| 8898 | Attentional Scholarly Alpha Diffusion Generator Ref-561 | Graph attention / Sector contagion / Stock baskets | 721 | 1046 | No |
| 8976 | Attentional Scholarly Alpha Diffusion Generator Ref-753 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7807 | 7623 | No |
