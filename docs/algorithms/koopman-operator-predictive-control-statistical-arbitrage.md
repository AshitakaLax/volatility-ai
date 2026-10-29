# Koopman Operator Predictive Control Statistical Arbitrage

**Ledger ID RK201** · rank 201 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Operator theory / Model predictive control / Statistical arbitrage |
| Potential effectiveness rank | 201 (1 = strongest) |
| AI implementability rank | 220 (1 = easiest) |
| Retail advantage rank | 426 (1 = strongest) |
| Fit with this project | ⛔ (stat arb with a short leg; no evidence) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK203, RK36, RK75 |

## In one paragraph

Lift nonlinear multi-asset cointegration dynamics into a dictionary of
observables so they evolve linearly, then run MPC to choose the
mean-reversion trades. The Koopman operator represents a nonlinear
system as a linear one acting on functions of the state (observables);
dynamic mode decomposition (DMD) is its standard data-driven
approximation. Model predictive control (MPC) then plans actions over a
horizon with that linear model and re-plans each step. I found no
peer-reviewed out-of-sample study of Koopman/MPC trading or allocation;
the nearest is a DMD trading paper whose windows were tuned in sample.
The CSV's reference, arXiv 2004.05678, is a mathematical-physics paper
("Stable polynomials and crystalline measures"), unrelated to trading.

## Evidence

* **Mann & Kutz (2016), "Dynamic mode decomposition for financial
  trading strategies," *Quantitative Finance* 16(11), 1643–1655 (arXiv
  1508.04487):** DMD reduces a window of prices to low-rank modes and a
  best-fit linear model that drives buy/sell/hold decisions; the
  sampling and prediction windows are tuned by locating profitable
  "trading hot-spots", an in-sample step. (Abstract; results not read.)
* A Koopman-autoencoder forecaster feeding a model-predictive-control
  portfolio optimiser reports +173% over 2021–2024 in a conference
  poster (Kobeissi, Li & Li, Université de Montréal); self-reported, not
  peer reviewed.
* Colbrook's review of Koopman operator methods (arXiv 2312.00137) cites
  market fluctuations as a motivating application, not as a demonstrated
  one. (Abstract.)

## Against, and failure modes

* A finite dictionary of observables makes a nonlinear system look
  linear only approximately; the fit is easy in sample and fragile out
  of it.
* MPC needs a model good enough to plan with; with weak return forecasts
  it optimises noise.

## Fit with volatility-ai

Spread trading needs a short leg, and there is no evidence the method
works out of sample.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Mann, J., Kutz, J. N. (2016). "Dynamic mode decomposition for
  financial trading strategies." *Quantitative Finance* 16(11),
  1643–1655. <https://arxiv.org/abs/1508.04487>. Abstract.
* Colbrook, M. J. Koopman operator review.
  <https://arxiv.org/abs/2312.00137>. Abstract.
* The CSV's references: PyKoopman; arXiv 2004.05678 (mathematical
  physics; unrelated).
