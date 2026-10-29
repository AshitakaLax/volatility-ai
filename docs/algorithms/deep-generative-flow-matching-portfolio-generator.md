# Deep Generative Flow Matching Portfolio Generator

**Ledger ID RK228** · rank 228 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Generative AI / Continuous normalizing flows / Portfolio allocation |
| Potential effectiveness rank | 228 (1 = strongest) |
| AI implementability rank | 356 (1 = easiest) |
| Retail advantage rank | 286 (1 = strongest) |
| Fit with this project | ⛔ (no evidence for portfolio use) |
| Implemented in volatility-ai | **Research code** in `research.catalog.generative`: `FlowMatching`, `scenario_portfolio`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK200 |

## In one paragraph

Generate return scenarios with flow matching (training a continuous
normalising flow by regressing its vector field) and optimise weights
over them. Flow matching itself is the CSV's reference (Lipman et al.,
2022) and is a well-established generative method; I found no study
using it for portfolio allocation.

## Evidence

* **Lipman, Chen, Ben-Hamu, Nickel & Le (2022), "Flow Matching for
  Generative Modeling" (arXiv 2210.02747, the CSV's reference):** the
  method. (Standard reference.)
* **No portfolio study found.**

## Against, and failure modes

* Scenario-based optimisation inherits the generator's errors;
  distribution shift is exactly what a trained generator misses.

## Fit with volatility-ai

An allocator for a multi-asset book; the engine trades one symbol and
the allocator in ledger §11 is not built. Without published evidence, it
is not a candidate.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Lipman, Y., et al. (2022). "Flow Matching for Generative Modeling."
  <https://arxiv.org/abs/2210.02747>.
