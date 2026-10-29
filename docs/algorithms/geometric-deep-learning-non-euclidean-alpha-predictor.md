# Geometric Deep Learning Non-Euclidean Alpha Predictor

**Ledger ID RK384** · rank 384 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Geometric deep learning / Riemannian manifolds / Quantitative equity |
| Potential effectiveness rank | 384 (1 = strongest) |
| AI implementability rank | 242 (1 = easiest) |
| Retail advantage rank | 189 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **Research code** in `research.catalog.cross_section`: `HyperbolicGCN`, `expmap0`, `logmap0`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK381, RK230 |

## In one paragraph

Forecast the cross-section of returns with networks on curved spaces
(hyperbolic or Riemannian manifolds). The one finance study found is
hyperbolic graph attention for stock selection (RK381); the CSV's
reference, arXiv 2106.09876, is a general graph anomaly-detection paper
("Anomaly Detection in Dynamic Graphs via Transformer"), not a finance
one.

## Evidence

* **Sawhney et al. (2021), HyperStockGAT:** hyperbolic graph attention
  beats Euclidean models on profit and Sharpe across four markets,
  self-reported (see RK381).

## Against, and failure modes

* Self-reported; geometry is a modelling choice with little economic
  grounding.

## Fit with volatility-ai

A cross-sectional stock-selection model; this project trades one
leveraged index ETF and has no stock universe, fundamentals or relation
data.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Sawhney, R., et al. (2021). WWW '21. doi:10.1145/3442381.3450095.
  Abstract.
