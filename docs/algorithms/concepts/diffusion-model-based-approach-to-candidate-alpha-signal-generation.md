# Diffusion-model-based approach to candidate alpha-signal generation

**Concept page** · shared by **5** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,667) ·
researched 2026-10-30

| | |
|---|---|
| Task | Candidate alpha-signal generation |
| Method | Diffusion generative models |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Mass-producing candidate signals raises the multiple-testing bar faster than it finds edge; the staged sweep already generates candidates. |
| Implemented in volatility-ai | Nothing; the staged indicator sweep (`plan.md`) is the project's generator. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK395, RK222 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Diffusion Scholarly Alpha
Diffusion Generator Alpha-65") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Use a generative model to propose or transform candidate signals, each
still needing out-of-sample validation and trading rules. The
diffusion-model version trains a denoising generative model and samples
scenarios or forecasts from it. I found no study of this method on this
task.

## The CSV's description

Proposed diffusion-model-based approach to candidate alpha-signal
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
* Generative models trained on a few thousand days memorise more than
  they generalise; no trading evidence found.

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
| 1667 | Diffusion Scholarly Alpha Diffusion Generator Alpha-65 | Rough path theory / Signature transforms / Stock momentum | 3847 | 2137 | No |
| 1680 | Diffusion Scholarly Alpha Diffusion Generator Alpha-165 | Rough path theory / Signature transforms / Stock momentum | 1891 | 311 | No |
| 1693 | Diffusion Scholarly Alpha Diffusion Generator Alpha-265 | Rough path theory / Signature transforms / Stock momentum | 2104 | 451 | No |
| 1706 | Diffusion Scholarly Alpha Diffusion Generator Alpha-365 | Rough path theory / Signature transforms / Stock momentum | 3856 | 2145 | No |
| 1719 | Diffusion Scholarly Alpha Diffusion Generator Alpha-465 | Rough path theory / Signature transforms / Stock momentum | 1899 | 315 | No |
