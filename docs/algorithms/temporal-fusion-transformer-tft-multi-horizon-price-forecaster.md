# Temporal Fusion Transformer (TFT) Multi-Horizon Price Forecaster

**Ledger ID RK413** · rank 413 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-29

| | |
|---|---|
| Family | Deep learning / Time-series forecasting |
| Potential effectiveness rank | 413 (1 = strongest) |
| AI implementability rank | 237 (1 = easiest) |
| Retail advantage rank | 238 (1 = strongest) |
| Fit with this project | ⛔ (no evidence it beats the LightGBM baseline; as RK301) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK301, RK316, C-RJ4 |

## In one paragraph

Forecast multi-horizon returns and volatility with a Temporal Fusion
Transformer. This duplicates RK301: the architecture (Lim et al. 2021)
is a strong general forecaster, but in Qlib's own Chinese-equity
benchmark it ranks below LightGBM, and the trading studies found are
single-stock and before costs.

## Evidence

* **Lim, Arık, Loeff & Pfister (2021), *International Journal of
  Forecasting* 37(4), 1748–1764:** the architecture, evaluated on
  forecasting benchmarks (see RK301). (Abstract.)
* **Qlib benchmark (CSI300, Alpha158):** LightGBM's information
  coefficient is above TFT's (see RK301). (README mirrors.)

## Against, and failure modes

* Forecast accuracy is not trading profit; tuning and leakage.

## Fit with volatility-ai

As RK301: the ML pipeline's problem is signal, not model capacity.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Lim, B., Arık, S. Ö., Loeff, N., Pfister, T. (2021). *International
  Journal of Forecasting* 37(4), 1748–1764.
  <https://arxiv.org/abs/1912.09363>. Abstract.
