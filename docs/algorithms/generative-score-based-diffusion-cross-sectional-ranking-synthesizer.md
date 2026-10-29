# Generative Score-Based Diffusion Cross-Sectional Ranking Synthesizer

**Ledger ID RK405** · rank 405 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-29

| | |
|---|---|
| Family | Generative AI / Diffusion models / Quantitative equity |
| Potential effectiveness rank | 405 (1 = strongest) |
| AI implementability rank | 190 (1 = easiest) |
| Retail advantage rank | 178 (1 = strongest) |
| Fit with this project | ⛔ (cross-sectional; no stock universe here) |
| Implemented in volatility-ai | **Research code** in `research.catalog.generative`: `synthesize_rankings`, `ranks_to_scores`, `scores_to_ranks`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK399, RK395, RK200 |

## In one paragraph

Train a score-based diffusion model to synthesize ranking scenarios from
panels of stock rankings, for stress-testing a quantitative equity
strategy. Factor-structured diffusion models have recent theory for
high-dimensional returns (RK399). The CSV's reference, arXiv 2210.02747,
is Lipman et al.'s flow-matching paper, a related generative method
rather than a finance study.

## Evidence

* **Chen, Xu, Xu & Zhang (2025), "Diffusion Factor Models" (arXiv
  2504.06566):** a factor-structured diffusion model for
  high-dimensional returns, with error bounds that depend on the factor
  dimension (see RK399). (Abstract.)

## Against, and failure modes

* Synthetic signals inherit the training sample's regimes; validation is
  hard.

## Fit with volatility-ai

A cross-sectional stock-selection model; this project trades one
leveraged index ETF and has no stock universe, fundamentals or relation
data.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Chen, M., Xu, R., Xu, Y., Zhang, R. (2025).
  <https://arxiv.org/abs/2504.06566>. Abstract.
