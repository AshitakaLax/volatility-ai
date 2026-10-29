# Conditional Wasserstein GAN-GP Yield Curve Synthesizer

**Ledger ID RK383** · rank 383 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Generative Machine Learning / Fixed Income |
| Potential effectiveness rank | 383 (1 = strongest) |
| AI implementability rank | 334 (1 = easiest) |
| Retail advantage rank | 273 (1 = strongest) |
| Fit with this project | ⛔ (rates scenarios; no use here) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK226, RK349 |

## In one paragraph

Generate yield-curve scenarios conditioned on the current curve with a
Wasserstein GAN with gradient penalty. A comparison on historical US
yield curves found historical simulation, GARCH and a conditional
Wasserstein GAN the best performers, so the GAN matched simple methods
rather than beating them. The CSV's reference, arXiv 2003.02345, looks
like a placeholder ID (sequential digits, like arXiv 1908.01234 on RK97)
and could not be identified.

## Evidence

* **Gulrajani et al. (2017), "Improved Training of Wasserstein GANs":**
  the gradient penalty. (Standard reference.)
* **Guo (2024, arXiv 2401.10370):** deep generative models for
  conditional time series on historical USD yield curves and GARCH/CIR
  simulations; historical simulation, GARCH and conditional WGAN are the
  top performers. (Abstract.)

## Against, and failure modes

* Matches historical simulation at much higher cost.

## Fit with volatility-ai

Rates scenarios have no direct use for this book.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Gulrajani, I., et al. (2017). "Improved Training of Wasserstein GANs."
  NeurIPS.
* Guo, S. (2024). <https://arxiv.org/abs/2401.10370>. Abstract.
