# Neural Rough Differential Equation (Neural RDE) LOB Forecaster

**Ledger ID RK331** · rank 331 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Rough path theory / Deep learning / Microstructure |
| Potential effectiveness rank | 331 (1 = strongest) |
| AI implementability rank | 986 (1 = easiest) |
| Retail advantage rank | 10,282 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK334, RK288, RK328 |

## In one paragraph

Forecast order-book dynamics with a neural RDE, which feeds
log-signatures of short windows into a neural controlled differential
equation so long, irregular series train quickly. The method paper is
the one the CSV cites for several pricing entries (arXiv 2009.08295);
this entry cites a different ID, and the CSV's reference, arXiv
2005.08320, could not be identified. Signature features have helped
order-book forecasting (Sidogi et al.); I found no neural-RDE order-book
study.

## Evidence

* **Morrill, Salvi, Kidger, Foster & Lyons (2021), "Neural Rough
  Differential Equations for Long Time Series," ICML (arXiv
  2009.08295):** feeds log-signatures over short windows into a neural
  CDE; faster training, better accuracy and less memory on series up to
  17,000 steps long. Not a finance paper. (Abstract.)
* **Sidogi et al. (2023), "A Signature Transform of Limit Order Book
  Data for Stock Price Prediction," *IEEE Access*:** signature features
  of the order book make a DNN's mean-mid-price forecasts more accurate
  and cheaper than raw order-book inputs. Forecast error, not trading.
  (Abstract.)

## Against, and failure modes

* Order-book forecasting at tick horizons does not transfer to minute
  bars.

## Fit with volatility-ai

The warehouse holds minute bars only; no historical quotes, trades or
depth. An order-book model, forecaster or simulator has nothing to train
on or test against here, and the grid's decisions are made on one-minute
bars.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Morrill, J., Salvi, C., Kidger, P., Foster, J., Lyons, T. (2021).
  "Neural Rough Differential Equations for Long Time Series." ICML.
  <https://arxiv.org/abs/2009.08295>. Abstract.
* Sidogi et al. (2023). "A Signature Transform of Limit Order Book Data
  for Stock Price Prediction." *IEEE Access*. Abstract.
