# Contractive Autoencoder Latent Factor Anomaly Detection

**Ledger ID RK382** · rank 382 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Deep learning / Contractive autoencoders / Anomaly detection |
| Potential effectiveness rank | 382 (1 = strongest) |
| AI implementability rank | 354 (1 = easiest) |
| Retail advantage rank | 7,425 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **Research code** in `research.catalog.cross_section`: `ContractiveAutoencoder`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK89, RK243 |

## In one paragraph

Train an autoencoder with a penalty on the encoder's Jacobian
(contractive), so its latent factors are robust to small input changes,
and flag returns it cannot reconstruct as anomalies. Plain autoencoders
have been used this way: prices an autoencoder of all stocks cannot
reconstruct were followed by biased moves in one Japanese study. I found
no contractive version in finance, and the CSV's reference, arXiv
1105.3911, could not be identified.

## Evidence

* **Rifai, Vincent, Muller, Glorot & Bengio (2011), "Contractive
  Auto-Encoders," ICML:** the method. (Standard reference; not
  re-checked here.)
* **Gotou & Suzuki (2016, *Journal of Signal Processing* 20(4)) and an
  IEICE follow-up:** prices a cross-stock autoencoder cannot reconstruct
  are flagged abnormal; the following moves are biased, tested
  statistically. (Abstracts.)

## Against, and failure modes

* Reconstruction error rises with volatility, so anomalies cluster in
  stress; the latent model must be refit.

## Fit with volatility-ai

As a data-quality flag (RK243) a simpler check suffices; as a signal it
is a stock-level method. Not a candidate.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Rifai, S., et al. (2011). "Contractive Auto-Encoders." ICML. Not
  re-checked.
* Gotou, Suzuki (2016). "Biased Reactions to Abnormal Stock Prices
  Detected by Autoencoder." *Journal of Signal Processing* 20(4).
  Abstract.
