# Wavelet Transform Denoised Breakout System

**Ledger ID RK113** · rank 113 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Signal processing / Technical trend |
| Potential effectiveness rank | 113 (1 = strongest) |
| AI implementability rank | 255 (1 = easiest) |
| Retail advantage rank | 7,556 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** Denoising has not been shown to help, and whole-series transforms leak the future. |
| Implemented in volatility-ai | **Research code** `research.catalog.neural_models`: `causal_haar`. |
| Related ledger entries | RK272, RK315 |

## In one paragraph

Decompose prices with a discrete or stationary wavelet transform,
discard the noisy detail levels, and look for breakouts on the smooth
part. Transforming the whole series at once lets later bars into earlier
coefficients; done causally, a forecasting study found wavelet denoising
generally does not improve accuracy (see RK272).

## Evidence

* **Wavelet denoising** did not generally improve forecast accuracy in
  the study cited on RK272.
* **This repository:** `neural_models.causal_haar` gives a causal à
  trous decomposition for honest tests.
* **No study found** that tests this combination as a trading strategy.

## Against, and failure modes

* A causal wavelet smoother is a lagged average; a non-causal one is
  look-ahead bias.

## Fit with volatility-ai

A breakout entry contradicts the grid, and the smoothing adds lag;
nothing to gain.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* See RK272's references.
* The CSV's references are PyWavelets and TA-Lib.
