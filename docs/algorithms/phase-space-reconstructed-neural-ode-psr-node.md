# Phase Space Reconstructed Neural ODE (PSR-NODE)

**Ledger ID RK348** · rank 348 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Continuous-time deep learning / Physics-informed ML |
| Potential effectiveness rank | 348 (1 = strongest) |
| AI implementability rank | 375 (1 = easiest) |
| Retail advantage rank | 10,218 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **Research code** in `research.catalog.neural_models`: `PSRNeuralODE`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK376, RK219 |

## In one paragraph

Reconstruct a phase space from delay coordinates of a price series
(Takens embedding) and fit a neural ODE to its flow. Delay embedding
assumes a low-dimensional deterministic attractor, which returns do not
show. The CSV cites a NeurIPS 2021 proceedings entry and a GitHub
repository I could not identify, and I found no finance study.

## Evidence

* **Chen, Rubanova, Bettencourt & Duvenaud (2018), "Neural Ordinary
  Differential Equations," NeurIPS:** the model class. (Standard
  reference.)
* **No finance study found.**

## Against, and failure modes

* Embedding dimension and delay are free parameters; noise destroys
  attractor reconstruction.

## Fit with volatility-ai

No mechanism or evidence for markets. Not a candidate.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Chen, R. T. Q., et al. (2018). "Neural Ordinary Differential
  Equations." NeurIPS. <https://arxiv.org/abs/1806.07366>.
