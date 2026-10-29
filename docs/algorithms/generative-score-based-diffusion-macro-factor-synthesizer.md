# Generative Score-Based Diffusion Macro Factor Synthesizer

**Ledger ID RK395** · rank 395 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Generative AI / Diffusion models / Macroeconomic factor modeling |
| Potential effectiveness rank | 395 (1 = strongest) |
| AI implementability rank | 285 (1 = easiest) |
| Retail advantage rank | 206 (1 = strongest) |
| Fit with this project | ⏳ as a stress-test generator (RK200) · not a strategy |
| Implemented in volatility-ai | **Research code** in `research.catalog.generative`: `FactorDiffusion`, `DDPM`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK200, RK399 |

## In one paragraph

Generate joint scenarios of macro factors with a score-based diffusion
model for stress testing. Diffusion models with an explicit factor
structure have recent theory for high-dimensional returns; I found no
macro-factor application. It is the same tool as RK200 applied to a
different panel.

## Evidence

* **Chen, Xu, Xu & Zhang (2025), "Diffusion Factor Models: Generating
  High-Dimensional Returns with Factor Structure" (arXiv 2504.06566):**
  a diffusion model whose score network is split by time-varying
  orthogonal projections into a low-dimensional factor part and
  asset-specific noise; error bounds depend on the factor dimension, not
  the number of assets. Theory and simulations; the empirical results
  were not read. (Abstract.)
* **Takahashi & Mizuno (2024, arXiv 2410.18897):** diffusion-generated
  series reproduce stylized facts (see RK200).

## Against, and failure modes

* Macro series are short and low-frequency; a few hundred monthly points
  cannot train a diffusion model well.

## Fit with volatility-ai

As a stress-testing tool (RK200): synthetic crash paths would show how
lots accumulate and how the regime exit behaves beyond the few real
drawdowns. A block bootstrap of real TQQQ returns is the cheaper first
step, and any generator must be validated on statistics it was not
trained to match.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Chen, M., Xu, R., Xu, Y., Zhang, R. (2025). "Diffusion Factor Models."
  <https://arxiv.org/abs/2504.06566>. Abstract.
