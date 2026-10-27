# Dynamic Mode Decomposition (DMD) Market Mode Predictor

**Ledger ID RK219** · rank 219 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Signal Processing / Dynamical Systems |
| Potential effectiveness rank | 219 (1 = strongest) |
| AI implementability rank | 227 (1 = easiest) |
| Retail advantage rank | 303 (1 = strongest) |
| Fit with this project | ⛔ as a trading signal (no out-of-sample evidence) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK201, RK206 |

## In one paragraph

Dynamic mode decomposition, from fluid dynamics, extracts coherent
spatial structures and their growth or decay rates from a matrix of
prices over a window, and extrapolates them. One paper builds a trading
strategy on it, but tunes its windows by finding profitable "hot spots"
in the data, which is in-sample selection. The Koopman operator
represents a nonlinear system as a linear one acting on functions of the
state (observables); dynamic mode decomposition (DMD) is its standard
data-driven approximation. Model predictive control (MPC) then plans
actions over a horizon with that linear model and re-plans each step.

## The rule

```text
X = [x_1 .. x_(m-1)], X' = [x_2 .. x_m] over a window of n assets
A ~ X' X^+ via truncated SVD (rank r); eigen-decompose -> modes Phi, eigenvalues lambda
forecast x_(m+k) = Phi diag(lambda^k) b; trade the predicted direction
```

## Evidence

* **Mann & Kutz (2016), "Dynamic mode decomposition for financial
  trading strategies," *Quantitative Finance* 16(11), 1643–1655 (arXiv
  1508.04487):** DMD reduces a window of prices to low-rank modes and a
  best-fit linear model that drives buy/sell/hold decisions; the
  sampling and prediction windows are tuned by locating profitable
  "trading hot-spots", an in-sample step. (Abstract; results not read.)
* **Tu et al. (2014), "On dynamic mode decomposition: theory and
  applications" (arXiv 1312.0041, the CSV's reference):** the method.
  (Standard reference.)

## Against, and failure modes

* Window selection in sample; modes are unstable across windows for
  noisy returns.

## Fit with volatility-ai

No out-of-sample evidence for trading. Not a candidate.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Mann, J., Kutz, J. N. (2016). "Dynamic mode decomposition for
  financial trading strategies." *Quantitative Finance* 16(11),
  1643–1655. <https://arxiv.org/abs/1508.04487>. Abstract.
* Tu, J. H., Rowley, C. W., Luchtenburg, D. M., Brunton, S. L., Kutz, J.
  N. (2014). "On dynamic mode decomposition: theory and applications."
  *Journal of Computational Dynamics*.
  <https://arxiv.org/abs/1312.0041>.
