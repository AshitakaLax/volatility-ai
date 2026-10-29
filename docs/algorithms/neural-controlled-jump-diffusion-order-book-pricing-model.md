# Neural Controlled Jump Diffusion Order Book Pricing Model

**Ledger ID RK337** · rank 337 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Neural CDEs / Jump diffusion / Microstructure |
| Potential effectiveness rank | 337 (1 = strongest) |
| AI implementability rank | 3,189 (1 = easiest) |
| Retail advantage rank | 9,359 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **Research code** in `research.catalog.neural_models`: `CDEJumpPricer`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK334, RK333 |

## In one paragraph

Combine a neural CDE driven by the order book with jump terms to price
the next mid-quote. The CSV's reference is the neural CDE paper itself
(arXiv 2005.08926). I found no order-book study using neural CDEs;
signature features of the book have helped mid-price forecasts in one
study.

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
