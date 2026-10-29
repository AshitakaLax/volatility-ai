# Neural Jump-Diffusion Rough Heston Smile Predictor

**Ledger ID RK303** · rank 303 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Stochastic volatility / Deep learning / Derivatives pricing |
| Potential effectiveness rank | 303 (1 = strongest) |
| AI implementability rank | 379 (1 = easiest) |
| Retail advantage rank | 10,661 (1 = strongest) |
| Fit with this project | ⛔ (options) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK379, RK391, RK377 |

## In one paragraph

Predict the implied-volatility smile with a rough Heston model, whose
volatility is driven by a fractional kernel with Hurst exponent near
0.1, extended with jumps and neural-network components. Rough volatility
fits the term structure of at-the-money skew with very few parameters,
and the rough Heston model has a semi-closed-form characteristic
function. The CSV's reference, arXiv 2009.08295, is Morrill et al.'s
*Neural Rough Differential Equations for Long Time Series*, a
sequence-modelling paper, not a pricing or hedging one.

## Evidence

* **Gatheral, Jaisson & Rosenbaum (2018), "Volatility is rough,"
  *Quantitative Finance* 18(6):** log realised volatility behaves like
  fractional Brownian motion with Hurst exponent near 0.1, at all time
  scales tested. (Standard reference.)
* **El Euch & Rosenbaum (2019), "The characteristic function of rough
  Heston models," *Mathematical Finance* 29(1):** semi-closed-form
  pricing via a fractional Riccati equation. (Standard reference; not
  re-checked here.)

## Against, and failure modes

* Calibration of the fractional kernel is slow; neural surrogates add
  their own error.

## Fit with volatility-ai

Options are outside the owner's instrument rule (long-only stocks and
ETFs), and the engine has no options data or pricing.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Gatheral, J., Jaisson, T., Rosenbaum, M. (2018). "Volatility is
  rough." *Quantitative Finance* 18(6).
  <https://arxiv.org/abs/1410.3394>.
* El Euch, O., Rosenbaum, M. (2019). *Mathematical Finance* 29(1). Not
  re-checked.
