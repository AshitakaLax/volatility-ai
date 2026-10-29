# Score-Based Generative Diffusion Limit Order Book Simulator

**Ledger ID RK336** · rank 336 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Generative AI / Diffusion models / Market microstructure |
| Potential effectiveness rank | 336 (1 = strongest) |
| AI implementability rank | 5,370 (1 = easiest) |
| Retail advantage rank | 10,335 (1 = strongest) |
| Fit with this project | ⛔ (needs order-book data; a simulator for execution research) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK343, RK332, RK200 |

## In one paragraph

Train a denoising diffusion model on order-book messages so it generates
realistic order flow conditioned on the market state, and use it as a
reactive simulator for testing strategies. TRADES (2025) does this with
a transformer denoiser, reacts to an experimental agent, and is open
source; it is evaluated by how well a predictor trained on its synthetic
data does on real data. The CSV's reference, arXiv 2210.02747, is Lipman
et al.'s flow-matching paper, not an order-book one.

## Evidence

* **Berti, Prenkaj & Velardi (2025), "TRADES: Generating Realistic
  Market Simulations with Diffusion Models," ECAI 2025 (arXiv
  2502.07071):** a transformer-based denoising diffusion model generates
  order flow conditioned on the market state and reacts to an
  experimental agent; scored by training a price predictor on synthetic
  data and testing on real data. Released as the DeepMarket framework.
  (Abstract.)
* **Limit order book simulation review (arXiv 2402.17359):** surveys
  agent-based, stochastic and deep generative simulators and the lack of
  agreed realism metrics. (Abstract.)

## Against, and failure modes

* Realism metrics are immature; a simulator trained on the past cannot
  produce the market impact of a new agent reliably.

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
* Limit Order Book Simulations: A Review.
  <https://arxiv.org/abs/2402.17359>. Abstract.
