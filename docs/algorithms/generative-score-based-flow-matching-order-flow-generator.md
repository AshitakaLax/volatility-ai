# Generative Score-Based Flow Matching Order Flow Generator

**Ledger ID RK332** · rank 332 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Generative machine learning / Flow matching / Microstructure |
| Potential effectiveness rank | 332 (1 = strongest) |
| AI implementability rank | 9,256 (1 = easiest) |
| Retail advantage rank | 10,333 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **Research code** in `research.catalog.generative`: `FlowMatching`, `order_messages`, `decode_messages`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK336, RK343, RK228 |

## In one paragraph

Generate order flow with flow matching instead of diffusion. The CSV's
reference is the flow-matching method paper (Lipman et al., arXiv
2210.02747); I found no order-flow application. Diffusion order-book
simulators exist (RK336).

## Evidence

* **Lipman et al. (2022), Flow Matching (arXiv 2210.02747):** the
  method. (Standard reference.)
* **Berti, Prenkaj & Velardi (2025), "TRADES: Generating Realistic
  Market Simulations with Diffusion Models," ECAI 2025 (arXiv
  2502.07071):** a transformer-based denoising diffusion model generates
  order flow conditioned on the market state and reacts to an
  experimental agent; scored by training a price predictor on synthetic
  data and testing on real data. Released as the DeepMarket framework.
  (Abstract.)

## Against, and failure modes

* Same realism and regime problems as RK336, with less evidence.

## Fit with volatility-ai

The warehouse holds minute bars only; no historical quotes, trades or
depth. An order-book model, forecaster or simulator has nothing to train
on or test against here, and the grid's decisions are made on one-minute
bars.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Lipman, Y., et al. (2022). <https://arxiv.org/abs/2210.02747>.
* Berti, L., Prenkaj, B., Velardi, P. (2025). "TRADES." ECAI 2025.
  <https://arxiv.org/abs/2502.07071>. Abstract.
