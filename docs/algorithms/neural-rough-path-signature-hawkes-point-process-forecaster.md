# Neural Rough Path Signature Hawkes Point Process Forecaster

**Ledger ID RK342** · rank 342 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Rough path theory / Point processes / Microstructure |
| Potential effectiveness rank | 342 (1 = strongest) |
| AI implementability rank | 990 (1 = easiest) |
| Retail advantage rank | 10,448 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK328, RK248 |

## In one paragraph

Summarise the order-flow path with its signature (iterated integrals
from rough path theory) and use the features to forecast Hawkes event
intensities. Signature features of the order book have improved
mid-price forecasts in one study; I found no signature-Hawkes
forecaster, and the CSV's reference, arXiv 2102.05678, looks like a
placeholder ID (sequential digits, like arXiv 1908.01234 on RK97) and
could not be identified.

## Evidence

* **Sidogi et al. (2023), "A Signature Transform of Limit Order Book
  Data for Stock Price Prediction," *IEEE Access*:** signature features
  of the order book make a DNN's mean-mid-price forecasts more accurate
  and cheaper than raw order-book inputs. Forecast error, not trading.
  (Abstract.)
* **Bacry, Mastromatteo & Muzy (2015), "Hawkes processes in finance"
  (arXiv 1502.04592):** review of Hawkes models for volatility, market
  stability, contagion, execution and order-book dynamics (see RK248).

## Against, and failure modes

* Signature dimension grows quickly with depth and channels; event data
  required.

## Fit with volatility-ai

The warehouse holds minute bars only; no historical quotes, trades or
depth. An order-book model, forecaster or simulator has nothing to train
on or test against here, and the grid's decisions are made on one-minute
bars.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Sidogi et al. (2023). "A Signature Transform of Limit Order Book Data
  for Stock Price Prediction." *IEEE Access*. Abstract.
* Bacry, E., Mastromatteo, I., Muzy, J.-F. (2015). "Hawkes processes in
  finance." *Market Microstructure and Liquidity*.
  <https://arxiv.org/abs/1502.04592>. Abstract.
