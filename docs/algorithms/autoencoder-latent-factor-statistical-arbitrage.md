# Autoencoder Latent-Factor Statistical Arbitrage

**Ledger ID RK89** · rank 89 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | ML / statistical arbitrage |
| Potential effectiveness rank | 89 (1 = strongest) |
| AI implementability rank | 254 (1 = easiest) |
| Retail advantage rank | 226 (1 = strongest) |
| Fit with this project | ⛔ (market-neutral stock book) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK76, RK96, RK33 |

## In one paragraph

RK76 with a neural network in place of PCA. An autoencoder learns a
low-dimensional, possibly nonlinear factor structure from returns (or
from characteristics, in the conditional form), and the strategy trades
each stock's residual against it. Conditional autoencoders price the
cross-section with much smaller out-of-sample errors than standard
factor models. A deep-learning stat-arb pipeline (residual factor model,
then a learned time-series signal and allocation) reports about 20% a
year at under 6% volatility, surviving costs.

## The rule

```
encoder: returns (or characteristics) -> k latent factors; decoder: factors -> fitted returns
residual = actual - fitted; signal = learned function of the recent residual path (CNN/transformer in Guijarro-Ordonez et al.)
long-short weights from the signal; walk-forward refits
```

## Evidence

* **Gu, Kelly & Xiu (2021), "Autoencoder asset pricing models," *Journal
  of Econometrics* 222(1), 429–450:** conditional autoencoder with
  no-arbitrage restriction; out-of-sample pricing errors much smaller
  than leading factor models and generally insignificant. (Abstract.)
* **Guijarro-Ordonez, Pelger & Zanotti, "Deep Learning Statistical
  Arbitrage" (arXiv 2106.04028):** consistently high out-of-sample
  returns and Sharpe ratios beating benchmarks; about 20% a year with
  under 6% volatility after realistic costs; the time-series signal
  matters most. (Abstract and authors' slides.)

## Against, and failure modes

* Latent residuals may be model error, not mispricing; overfitting;
  needs walk-forward refits and factor diagnostics (the CSV's caveat).
* Market-neutral with a short leg; a large point-in-time stock universe.

## Fit with volatility-ai

Out of scope.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Gu, S., Kelly, B., Xiu, D. (2021). *Journal of Econometrics* 222(1),
  429–450. <https://papers.ssrn.com/abstract=3335536>. Abstract.
* Guijarro-Ordonez, J., Pelger, M., Zanotti, G. "Deep Learning
  Statistical Arbitrage." <https://arxiv.org/abs/2106.04028>. Abstract
  and slides.
