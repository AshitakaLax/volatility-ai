# Neural Controlled Differential Equation LOB Trend Anticipator

**Ledger ID RK334** · rank 334 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Rough path theory / Neural CDEs / Microstructure |
| Potential effectiveness rank | 334 (1 = strongest) |
| AI implementability rank | 382 (1 = easiest) |
| Retail advantage rank | 10,444 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK331, RK288, RK337 |

## In one paragraph

Drive a neural CDE with the order-book path, which handles irregular
event times natively, to anticipate short-term trends. The CSV's
reference is the neural CDE paper itself (arXiv 2005.08926). I found no
order-book study using neural CDEs; signature features of the book have
helped mid-price forecasts in one study.

## Evidence

* **Kidger, Morrill, Foster & Lyons (2020), "Neural Controlled
  Differential Equations for Irregular Time Series," NeurIPS (arXiv
  2005.08926):** the model class (see RK288). (Standard reference.)
* **Sidogi et al. (2023), "A Signature Transform of Limit Order Book
  Data for Stock Price Prediction," *IEEE Access*:** signature features
  of the order book make a DNN's mean-mid-price forecasts more accurate
  and cheaper than raw order-book inputs. Forecast error, not trading.
  (Abstract.)

## Against, and failure modes

* Tick-horizon models; GPU solvers; no finance benchmark.

## Fit with volatility-ai

The warehouse holds minute bars only; no historical quotes, trades or
depth. An order-book model, forecaster or simulator has nothing to train
on or test against here, and the grid's decisions are made on one-minute
bars.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Kidger, P., Morrill, J., Foster, J., Lyons, T. (2020). NeurIPS.
  <https://arxiv.org/abs/2005.08926>.
* Sidogi et al. (2023). "A Signature Transform of Limit Order Book Data
  for Stock Price Prediction." *IEEE Access*. Abstract.
