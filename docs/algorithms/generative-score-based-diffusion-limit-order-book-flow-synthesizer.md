# Generative Score-Based Diffusion Limit Order Book Flow Synthesizer

**Ledger ID RK343** · rank 343 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Generative AI / Diffusion models / Microstructure |
| Potential effectiveness rank | 343 (1 = strongest) |
| AI implementability rank | 700 (1 = easiest) |
| Retail advantage rank | 7,429 (1 = strongest) |
| Fit with this project | ⛔ (needs order-book data) |
| Implemented in volatility-ai | **Research code** in `research.catalog.generative`: `DDPM`, `order_messages`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK336, RK332 |

## In one paragraph

Synthesize order-book flow with a score-based diffusion model, the same
idea as RK336 used to augment training data rather than to simulate.
TRADES is the nearest published system.

## Evidence

* **Berti, Prenkaj & Velardi (2025), "TRADES: Generating Realistic
  Market Simulations with Diffusion Models," ECAI 2025 (arXiv
  2502.07071):** a transformer-based denoising diffusion model generates
  order flow conditioned on the market state and reacts to an
  experimental agent; scored by training a price predictor on synthetic
  data and testing on real data. Released as the DeepMarket framework.
  (Abstract.)

## Against, and failure modes

* Synthetic flow inherits the training period's regime.

## Fit with volatility-ai

The warehouse holds minute bars only; no historical quotes, trades or
depth. An order-book model, forecaster or simulator has nothing to train
on or test against here, and the grid's decisions are made on one-minute
bars.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Berti, L., Prenkaj, B., Velardi, P. (2025). "TRADES." ECAI 2025.
  <https://arxiv.org/abs/2502.07071>. Abstract.
