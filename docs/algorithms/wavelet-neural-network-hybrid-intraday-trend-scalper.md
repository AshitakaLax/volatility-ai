# Wavelet-Neural Network Hybrid Intraday Trend Scalper

**Ledger ID RK272** · rank 272 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Signal processing / Machine learning trend |
| Potential effectiveness rank | 272 (1 = strongest) |
| AI implementability rank | 322 (1 = easiest) |
| Retail advantage rank | 2,828 (1 = strongest) |
| Fit with this project | ⏳ only with causal (trailing) wavelets · ⛔ as an intraday scalper |
| Implemented in volatility-ai | **Research code** in `research.catalog.neural_models`: `WaveletScalper`, `causal_haar`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK292, RK219 |

## In one paragraph

Decompose intraday prices with a discrete wavelet transform, keep the
smooth components, and feed them to a small neural network that trades
the short-term trend. Many published wavelet-plus-network forecasts
transform the whole series at once, which lets future bars into past
coefficients; the CSV's caveat names exactly this. A forecasting study
found that a wavelet denoising step generally does not improve forecast
accuracy. I found no clean, causal, cost-inclusive test of the trading
strategy.

## The rule

```text
on a trailing window only: coefficients = DWT(prices[t-W..t]); denoise (threshold the detail levels)
features = last values of the reconstructed smooth series and levels; NN -> next-bar direction; trade with costs
```

## Evidence

* **Bašta (2018), *Acta Oeconomica Pragensia*:** adding a wavelet
  denoising step to standard forecasting models generally does not
  improve accuracy. (Abstract; M3 yearly data, not markets.)
* Critiques of wavelet-plus-LSTM stock forecasts attribute their very
  high accuracy to look-ahead from full-sample transforms. (Informal
  sources only.)
* **No causal, cost-inclusive trading test found.**

## Against, and failure modes

* Boundary effects: the last coefficients of a window are the least
  reliable, and they are the ones a live system uses.
* Intraday scalping costs; neural nets on noisy targets overfit.

## Fit with volatility-ai

Out of scope as a scalper. A causal wavelet volatility measure could in
principle feed the regime, but the existing NATR regime already does
that job with nothing to fit.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Bašta, M. (2018). Wavelet denoising and forecast accuracy. *Acta
  Oeconomica Pragensia*. Abstract.
* The CSV's references: PyWavelets; scikit-learn.
