# Recurrent Neural Hawkes Point Process Liquidity Shock Detector

**Ledger ID RK338** · rank 338 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Point processes / Recurrent neural networks / Microstructure |
| Potential effectiveness rank | 338 (1 = strongest) |
| AI implementability rank | 693 (1 = easiest) |
| Retail advantage rank | 10,231 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK304, RK280, RK259 |

## In one paragraph

Detect liquidity shocks (spread blow-outs, depth withdrawals) from the
intensity of a neural Hawkes process over order-book events. The model
is established in machine learning (Mei and Eisner); I found no market
application of this kind, and the CSV's reference, arXiv 2104.09876,
looks like a placeholder ID (sequential digits, like arXiv 1908.01234 on
RK97) and could not be identified. Classical Hawkes models of market
events are well studied (RK248).

## Evidence

* **Mei & Eisner (2017), "The Neural Hawkes Process: A Neurally
  Self-Modulating Multivariate Point Process," NeurIPS 30, 6754–6764
  (arXiv 1612.09328):** each event type's intensity is set by a
  continuous-time LSTM over past events; competitive likelihood and
  prediction on real and synthetic event streams, none of them markets.
  (Abstract.)
* **Bacry, Mastromatteo & Muzy (2015), "Hawkes processes in finance"
  (arXiv 1502.04592):** review of Hawkes models for volatility, market
  stability, contagion, execution and order-book dynamics (see RK248).

## Against, and failure modes

* Needs event-level (tick) data; parameters drift across regimes.
* Neural intensities add capacity to a problem whose limit is data, not
  model form.

## Fit with volatility-ai

The warehouse holds minute bars only; no historical quotes, trades or
depth. An order-book model, forecaster or simulator has nothing to train
on or test against here, and the grid's decisions are made on one-minute
bars.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Mei, H., Eisner, J. (2017). "The Neural Hawkes Process." NeurIPS 30.
  <https://arxiv.org/abs/1612.09328>. Abstract.
* Bacry, E., Mastromatteo, I., Muzy, J.-F. (2015). "Hawkes processes in
  finance." *Market Microstructure and Liquidity*.
  <https://arxiv.org/abs/1502.04592>. Abstract.
