# Time-Series Generative Adversarial Network (TimeGAN)

**Ledger ID RK349** · rank 349 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Generative machine learning / Data augmentation |
| Potential effectiveness rank | 349 (1 = strongest) |
| AI implementability rank | 314 (1 = easiest) |
| Retail advantage rank | 268 (1 = strongest) |
| Fit with this project | ⏳ as a stress-test generator (RK200) · not a strategy |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK200, RK373, RK378 |

## In one paragraph

TimeGAN generates realistic multivariate time series by training an
embedding and recovery network, a supervised next-step loss in the
latent space, and an adversarial loss together, so the generated series
keep their step-to-step dynamics. It beat earlier sequence GANs on
similarity and on how well models trained on synthetic data predict real
data. For finance it is a scenario generator, and newer diffusion models
claim to reproduce stylized facts it misses.

## Evidence

* **Yoon, Jarrett & van der Schaar (2019), "Time-series Generative
  Adversarial Networks," NeurIPS 32:** consistently and significantly
  outperforms earlier benchmarks on similarity and predictive measures
  across real and synthetic datasets. (Abstract.)
* **Takahashi & Mizuno (2024, arXiv 2410.18897):** a diffusion model
  reproduces stylized facts that GAN and VAE generators missed (see
  RK200).

## Against, and failure modes

* GAN training is unstable; mode collapse drops the rare crash paths a
  stress test most needs.

## Fit with volatility-ai

As a stress-testing tool (RK200): synthetic crash paths would show how
lots accumulate and how the regime exit behaves beyond the few real
drawdowns. A block bootstrap of real TQQQ returns is the cheaper first
step, and any generator must be validated on statistics it was not
trained to match.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Yoon, J., Jarrett, D., van der Schaar, M. (2019). "Time-series
  Generative Adversarial Networks." NeurIPS 32.
  <https://papers.nips.cc/paper/8789-time-series-generative-adversarial-networks>.
  Abstract.
