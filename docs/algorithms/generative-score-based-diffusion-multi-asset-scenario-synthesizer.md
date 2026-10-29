# Generative Score-Based Diffusion Multi-Asset Scenario Synthesizer

**Ledger ID RK200** · rank 200 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Generative AI / Diffusion models / Risk management |
| Potential effectiveness rank | 200 (1 = strongest) |
| AI implementability rank | 320 (1 = easiest) |
| Retail advantage rank | 298 (1 = strongest) |
| Fit with this project | ⏳ as a stress-test scenario generator · not a strategy |
| Implemented in volatility-ai | **Research code** in `research.catalog.generative`: `DDPM`, `scenario_portfolio`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK228, RK21 |

## In one paragraph

Train a score-based (denoising) diffusion model on multi-asset returns
and macro panels, then sample many joint scenario paths for stress
testing. Diffusion models for financial series are recent: one 2024
study turns prices, volumes and spreads into wavelet images, trains a
denoising diffusion model on them and reports reproducing the stylized
facts (fat tails, volatility clustering) that earlier GAN and VAE
generators missed. It is a risk tool, not a strategy.

## Evidence

* **Takahashi & Mizuno (2024), "Generation of synthetic financial time
  series by diffusion models" (arXiv 2410.18897):** DDPM on
  wavelet-transformed series; reproduces stylized facts that GAN and VAE
  models did not. (Abstract.)
* **Kim, Choi & Kim (2025, arXiv 2507.19003):** a diffusion forward
  process with geometric-Brownian noise and a Transformer score network;
  better heavy tails, volatility clustering and leverage effect.
  (Abstract.)
* The CSV's reference, arXiv 2210.02747, is Lipman et al.'s *Flow
  Matching for Generative Modeling* (RK228), not a finance paper.

## Against, and failure modes

* Generated scenarios inherit the training sample's regimes; a crash
  unlike any in the data will not appear.
* Validating a generator needs statistics the generator was not trained
  to match.

## Fit with volatility-ai

Useful in principle for stress-testing the grid: thousands of plausible
crash paths would show how lots accumulate and how the regime exit
behaves, beyond the four or five real drawdowns in the data. A block
bootstrap of real returns is the cheaper first step.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Takahashi, T., Mizuno, T. (2024). <https://arxiv.org/abs/2410.18897>.
  Abstract.
* Kim, Choi, Kim (2025). <https://arxiv.org/abs/2507.19003>. Abstract.
