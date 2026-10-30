# Wasserstein Generative Adversarial Network Multi-Asset Allocation (WGAN-MA)

**Ledger ID RK198** · rank 198 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Generative machine learning / Robust portfolio allocation |
| Potential effectiveness rank | 198 (1 = strongest) |
| AI implementability rank | 315 (1 = easiest) |
| Retail advantage rank | 191 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** A multi-asset allocator over generated scenarios; no performance evidence was found. |
| Implemented in volatility-ai | **Research code** `research.catalog.generative`: `ConditionalWGANGP`, `scenario_portfolio`. |
| Related ledger entries | RK200, RK228, RK383 |

## In one paragraph

Train a Wasserstein GAN with gradient penalty on return scenarios and
optimise weights over its samples. The closest work (an autoencoding
conditional GAN for allocation; a decision-aware conditional GAN)
describes methods without results I could read; a NeurIPS 2025
diffusion-model relative reports beating Markowitz and 1/N.

## Evidence

* **Lu & Yi (2022, arXiv 2207.05701):** WGAN-GP scenario generation with
  an embedded autoencoder for allocation; method seen, results not.
  (Abstract.)
* **Aghapour, Bayraktar & Yuan (NeurIPS 2025):** score-based diffusion
  scenarios for dynamic portfolio selection, reported to beat Markowitz,
  1/N and the S&P 500. (Abstract.)
* **This repository:** `generative.ConditionalWGANGP` and
  `scenario_portfolio`.

## Against, and failure modes

* Generated scenarios inherit the training window's regime; optimising
  over them over-fits that window.

## Fit with volatility-ai

A portfolio-construction rule for a multi-asset book. The engine trades
one symbol and the multi-asset allocator in ledger §11 is not built; it
becomes relevant only if a multi-ETF book is added (as X2/X3 explore).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Lu, Yi (2022). Autoencoding Conditional GAN for Portfolio Allocation
  Diversification. <https://arxiv.org/abs/2207.05701>. Abstract.
* Arjovsky, M., Chintala, S., Bottou, L. (2017). Wasserstein GAN.
  <https://arxiv.org/abs/1701.07875>. The CSV's reference; the method
  paper.
