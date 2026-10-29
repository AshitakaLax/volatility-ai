# Neural Jump ODE (NJ-ODE) High-Frequency Price Predictor

**Ledger ID RK408** · rank 408 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-29

| | |
|---|---|
| Family | Continuous-Time Deep Learning / Microstructure |
| Potential effectiveness rank | 408 (1 = strongest) |
| AI implementability rank | 373 (1 = easiest) |
| Retail advantage rank | 10,224 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **Research code** in `research.catalog.neural_models`: `NeuralJumpODE`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK333, RK334 |

## In one paragraph

Predict prices between irregular tick observations with a neural jump
ODE, which evolves a neural ODE between observations and jumps when one
arrives, and provably converges to the optimal (conditional-expectation)
prediction. The method is from Herrera, Krach and Teichmann (ICLR 2021,
arXiv 2006.04727); the CSV cites a different ID, and the CSV's
reference, arXiv 2006.05221, could not be identified. I found no
high-frequency price study with it.

## Evidence

* **Herrera, Krach & Teichmann (2021), "Neural Jump Ordinary
  Differential Equations: Consistent Continuous-Time Prediction and
  Filtering," ICLR (arXiv 2006.04727):** convergence to the L2-optimal
  prediction; beats GRU-ODE-Bayes and ODE-RNN baselines on harder tasks
  and real data. (Abstract.)

## Against, and failure modes

* The optimal prediction of a near-martingale price is close to the last
  price; the gain is in filtering, not alpha.

## Fit with volatility-ai

The warehouse holds minute bars only; no historical quotes, trades or
depth. Tick prediction is out of scope.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Herrera, C., Krach, F., Teichmann, J. (2021). ICLR.
  <https://arxiv.org/abs/2006.04727>. Abstract.
