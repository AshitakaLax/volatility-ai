# Manifold Learning Diffusion Map Statistical Arbitrage

**Ledger ID RK178** · rank 178 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Manifold learning / Statistical arbitrage |
| Potential effectiveness rank | 178 (1 = strongest) |
| AI implementability rank | 295 (1 = easiest) |
| Retail advantage rank | 10,219 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** A stock-universe residual trade with no study found. |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK76, RK89 |

## In one paragraph

Embed asset return histories with diffusion maps and trade mean
reversion of residuals in the learned coordinates. Diffusion maps are
used for dynamic factor modelling (Baker, Capponi and Sidaoui) and
stress testing, not trading in the work found; the CSV's reference,
arXiv 1806.01234, could not be identified.

## Evidence

* **Baker, Capponi & Sidaoui (2025, arXiv 2506.19945):** anisotropic
  diffusion maps with Kalman filtering for dynamic factor modelling;
  prediction and stress tests, not trading. (Abstract.)
* **No study found** that tests this combination as a trading strategy.

## Against, and failure modes

* Embeddings change with bandwidth and window; residual trades need
  short legs.

## Fit with volatility-ai

A cross-sectional stock-selection model; this project trades one
leveraged index ETF and has no stock universe, fundamentals or relation
data.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Baker, Capponi, Sidaoui (2025). <https://arxiv.org/abs/2506.19945>.
  Abstract.
* The CSV's reference, arXiv 1806.01234 (not identified).
