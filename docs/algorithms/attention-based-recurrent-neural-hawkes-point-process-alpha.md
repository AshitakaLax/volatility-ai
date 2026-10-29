# Attention-Based Recurrent Neural Hawkes Point Process Alpha

**Ledger ID RK414** · rank 414 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-29

| | |
|---|---|
| Family | Recurrent neural networks / Attention / Point processes |
| Potential effectiveness rank | 414 (1 = strongest) |
| AI implementability rank | 1,878 (1 = easiest) |
| Retail advantage rank | 10,662 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **Research code** in `research.catalog.point_processes`: `NeuralHawkes`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK304, RK248 |

## In one paragraph

Replace the recurrent intensity of a neural Hawkes process with
self-attention (as in the Transformer Hawkes process) and trade
short-term order-arrival bursts. Attention-based Hawkes models exist in
machine learning; I found no alpha study, and the CSV's reference, arXiv
2104.09876, is a heat-pump health-monitoring paper, unrelated to
trading.

## Evidence

* **Zuo et al. (2020), "Transformer Hawkes Process," ICML:**
  self-attention intensities for event sequences. (Standard reference;
  not re-checked here.)
* **Mei & Eisner (2017), "The Neural Hawkes Process," NeurIPS:**
  continuous-time LSTM intensities for event streams, none of them
  markets (see RK304).

## Against, and failure modes

* Needs event data; order-arrival bursts are a microsecond-to-second
  signal.

## Fit with volatility-ai

The warehouse holds minute bars only; no historical quotes, trades or
depth. Event-time alpha is out of scope.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Zuo, S., Jiang, H., Li, Z., Zhao, T., Zha, H. (2020). "Transformer
  Hawkes Process." ICML. Not re-checked.
* Mei, H., Eisner, J. (2017). NeurIPS 30.
  <https://arxiv.org/abs/1612.09328>. Abstract.
