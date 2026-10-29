# Dynamic Latent Factor Graph Neural Network (FactorGNN)

**Ledger ID RK380** · rank 380 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Graph neural networks / Quantitative equity |
| Potential effectiveness rank | 380 (1 = strongest) |
| AI implementability rank | 279 (1 = easiest) |
| Retail advantage rank | 271 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK318, RK89 |

## In one paragraph

Learn latent factors and a time-varying stock graph jointly and forecast
returns from both. I found no paper of this name for stocks. The nearest
is FactorVAE, a dynamic factor model inside a variational autoencoder
that predicts returns and their variance and reports beating baselines
on Chinese stocks. The CSV's reference, arXiv 2206.01234, looks like a
placeholder ID (sequential digits, like arXiv 1908.01234 on RK97) and
could not be identified.

## Evidence

* **Duan, Wang, Zhang & Li (2022), "FactorVAE: A Probabilistic Dynamic
  Factor Model Based on Variational Autoencoder for Predicting
  Cross-Sectional Stock Returns," AAAI 36(4), 4468–4476:** outperforms
  baselines on real stock data; also estimates return variance.
  Self-reported. (Abstract.)

## Against, and failure modes

* Latent graphs and factors are unidentified; results are self-reported.

## Fit with volatility-ai

A cross-sectional stock-selection model; this project trades one
leveraged index ETF and has no stock universe, fundamentals or relation
data.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Duan, Y., Wang, L., Zhang, Q., Li, J. (2022). AAAI 36(4), 4468–4476.
  doi:10.1609/aaai.v36i4.20369. Abstract.
