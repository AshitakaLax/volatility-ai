# Deep Markov State-Space Intraday Volume Profile Predictor

**Ledger ID RK256** · rank 256 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Deep state-space models / Market microstructure |
| Potential effectiveness rank | 256 (1 = strongest) |
| AI implementability rank | 1,877 (1 = easiest) |
| Retail advantage rank | 10,496 (1 = strongest) |
| Fit with this project | ⛔ (execution-volume forecasting not needed here) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK251 |

## In one paragraph

Forecast intraday volume curves with a deep Markov (variational
state-space) model, for execution scheduling. Classical intraday volume
models (dynamic market-plus-stock decompositions, Kalman filters) are
the baseline. I found no study of the deep variant, and the CSV's
reference, arXiv 2006.12345, could not be identified.

## Evidence

* **Deep Markov models (Krishnan, Shalit & Sontag 2017, AAAI):** the
  model class. (Standard reference; not re-checked here.)
* **Białkowski, Darolles & Le Fol (2008):** the classical dynamic volume
  baseline (see RK251).
* **No finance study found** of deep Markov volume forecasting.

## Against, and failure modes

* Variational training is unstable under extreme volume spikes (the
  CSV's caveat).

## Fit with volatility-ai

This book does not schedule orders by volume (see RK251). Nothing to
build.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Krishnan, R. G., Shalit, U., Sontag, D. (2017). "Structured Inference
  Networks for Nonlinear State Space Models." AAAI. Not re-checked.
* The CSV's references: Pyro; arXiv 2006.12345 (not identified).
