# Temporal Fusion Transformer Forecasting

**Ledger ID RK301** · rank 301 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | ML / time-series forecasting |
| Potential effectiveness rank | 301 (1 = strongest) |
| AI implementability rank | 277 (1 = easiest) |
| Retail advantage rank | 249 (1 = strongest) |
| Fit with this project | ⛔ (no evidence it beats the LightGBM baseline) |
| Implemented in volatility-ai | **Research code** in `research.catalog.neural_models`: `TemporalFusionTransformer`; tested on synthetic data, not wired into the engine. The deep-forecaster collection (C-RJ4) and an LSTM forecaster exist as rejected catalog code. |
| Related ledger entries | RK292, RK316, C-RJ4, V14 |

## In one paragraph

The Temporal Fusion Transformer forecasts several horizons at once from
past values, known future inputs (calendars) and static covariates,
combining recurrent layers, attention and variable selection, with
interpretable attention weights. It is a strong general forecaster. For
stock returns the evidence is thin: in Microsoft Qlib's own
Chinese-equity benchmark it ranks below LightGBM, and the trading
studies found are single-stock and before costs.

## Evidence

* **Lim, Arık, Loeff & Pfister (2021), "Temporal Fusion Transformers for
  interpretable multi-horizon time series forecasting," *International
  Journal of Forecasting* 37(4), 1748–1764:** recurrent layers for local
  processing, interpretable self-attention for long-range dependence,
  variable-selection networks and gating; evaluated on forecasting
  benchmarks, not trading. (Abstract.)
* **Qlib benchmark (microsoft/qlib `examples/benchmarks`, CSI300,
  Alpha158 features):** LightGBM's information coefficient (about 0.048)
  is above TFT's (about 0.034–0.036) and TCN's (about 0.028), and its
  simulated annualised excess return is higher. Figures differ between
  Qlib data versions. (README mirrors; not re-run.)
* **A hybrid CNN-LSTM-TFT on Apple daily data (2016–2020, *Ingénierie
  des Systèmes d'Information* 30(11)):** reports an 80.7% long/short
  return against 38% for buy-and-hold, before transaction costs, on one
  stock and one period. (Abstract.)

## Against, and failure modes

* Forecast accuracy is not trading profit (the CSV's own caveat).
* Many hyperparameters and a small daily sample; leakage through scaling
  and feature windows.

## Fit with volatility-ai

The ML pipeline here (docs/ml_plan.md) already struggles to beat a coin
flip with LightGBM on daily features. A deeper sequence model is not the
bottleneck; a signal is. Same verdict as the LSTM (RK292) and the
rejected deep-forecaster collection (C-RJ4).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Lim, B., Arık, S. Ö., Loeff, N., Pfister, T. (2021). *International
  Journal of Forecasting* 37(4), 1748–1764.
  <https://arxiv.org/abs/1912.09363>. Abstract.
* Microsoft Qlib benchmarks README.
  <https://github.com/microsoft/qlib/tree/main/examples/benchmarks>.
  Mirrors read; version-dependent.
* Hybrid CNN–LSTM with TFT for stock forecasting. *Ingénierie des
  Systèmes d'Information* 30(11).
  <https://iieta.org/journals/isi/paper/10.18280/isi.301122>. Abstract.
