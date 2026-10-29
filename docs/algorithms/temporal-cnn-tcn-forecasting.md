# Temporal CNN / TCN Forecasting

**Ledger ID RK316** · rank 316 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Machine learning |
| Potential effectiveness rank | 316 (1 = strongest) |
| AI implementability rank | 108 (1 = easiest) |
| Retail advantage rank | 128 (1 = strongest) |
| Fit with this project | ⛔ (no evidence it beats the LightGBM baseline) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK301, RK292, C-RJ4 |

## In one paragraph

A temporal convolutional network forecasts with stacked causal, dilated
1-D convolutions and residual connections, which see a long history
without recurrence. On generic sequence benchmarks it often matches or
beats recurrent networks. On stock prices the comparisons with LSTMs are
mixed and measure forecast error, not trading results, and in Qlib's
equity benchmark it trails LightGBM.

## Evidence

* **Bai, Kolter & Koltun (2018), "An Empirical Evaluation of Generic
  Convolutional and Recurrent Networks for Sequence Modeling" (arXiv
  1803.01271):** a simple TCN outperforms canonical recurrent networks
  across a broad set of sequence tasks. (Standard reference; not
  re-checked here.)
* **Qlib benchmark (microsoft/qlib `examples/benchmarks`, CSI300,
  Alpha158 features):** LightGBM's information coefficient (about 0.048)
  is above TFT's (about 0.034–0.036) and TCN's (about 0.028), and its
  simulated annualised excess return is higher. Figures differ between
  Qlib data versions. (README mirrors; not re-run.)
* **TCN against LSTM on stock prices:** a study of 16 Indonesian stocks
  finds the TCN slightly more accurate (MAE 0.0140 against 0.0148,
  better on 11 of 16); an NSE India comparison finds LSTM and GRU more
  accurate than TCN, TFT and N-BEATS. Forecast error only. (Abstracts.)

## Against, and failure modes

* Forecast error, not profit; results flip with the market and setup.

## Fit with volatility-ai

The ML pipeline here (docs/ml_plan.md) already struggles to beat a coin
flip with LightGBM on daily features. A deeper sequence model is not the
bottleneck; a signal is. Same verdict as the LSTM (RK292) and the
rejected deep-forecaster collection (C-RJ4).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Bai, S., Kolter, J. Z., Koltun, V. (2018).
  <https://arxiv.org/abs/1803.01271>. Not re-checked.
* Microsoft Qlib benchmarks README.
  <https://github.com/microsoft/qlib/tree/main/examples/benchmarks>.
  Mirrors read; version-dependent.
