# Variational Autoencoder (VAE) Latent Yield Curve Arbitrage

**Ledger ID RK177** · rank 177 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Deep Learning / Fixed Income Relative Value |
| Potential effectiveness rank | 177 (1 = strongest) |
| AI implementability rank | 264 (1 = easiest) |
| Retail advantage rank | 110 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** Treasury relative value needs leveraged bond positions; out of scope. |
| Implemented in volatility-ai | **Research code** `research.catalog.concepts`: `vae_factors`. |
| Related ledger entries | RK226, RK383 |

## In one paragraph

Compress Treasury curves into a low-dimensional latent space with a
variational autoencoder and trade points that sit far from the
reconstructed curve. Autoencoder curve models are an active research
line (Kondratyev; Lyashenko, Mercurio and Sokol); a 2026 preprint
reports good out-of-sample forecasts, and I found no relative-value
trading study; the CSV's reference, arXiv 1908.08825, could not be
identified.

## Evidence

* **Luo & Geman (2026, arXiv 2605.12764):** a Student-t conditional VAE
  with a no-arbitrage neural SDE forecasts USD, GBP and JPY curves with
  6.58 bp tenor RMSE out of sample; the authors' results (preprint).
* **No study found** that tests this combination as a trading strategy.

## Against, and failure modes

* Rich/cheap gaps on the curve are small and need leverage and financing
  to trade.

## Fit with volatility-ai

Rates relative value is a levered long-short bond trade, outside the
owner's rules.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Luo, Geman (2026). Yield Curves Dynamics Using Variational
  Autoencoders Under No-arbitrage. <https://arxiv.org/abs/2605.12764>.
  Abstract.
* The CSV's reference, arXiv 1908.08825 (not identified).
