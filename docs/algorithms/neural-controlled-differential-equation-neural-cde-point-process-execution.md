# Neural Controlled Differential Equation (Neural CDE) Point Process Execution

**Ledger ID RK288** · rank 288 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Neural CDEs / Point processes / Execution |
| Potential effectiveness rank | 288 (1 = strongest) |
| AI implementability rank | 5,372 (1 = easiest) |
| Retail advantage rank | 9,360 (1 = strongest) |
| Fit with this project | ⛔ (execution on event data; no evidence) |
| Implemented in volatility-ai | **Research code** in `research.catalog.neural_models`: `CDEIntensityExecution`, `NeuralCDE`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK277, RK289, RK250 |

## In one paragraph

Neural controlled differential equations model irregularly sampled time
series as continuous paths, which suits tick data; this algorithm would
pair them with point processes to time order execution. The model class
is real and well-cited (Kidger et al. 2020, the CSV's reference); I
found no study applying it to execution.

## Evidence

* **Kidger, Morrill, Foster & Lyons (2020), "Neural Controlled
  Differential Equations for Irregular Time Series," NeurIPS (arXiv
  2005.08926):** state-of-the-art results against ODE- and RNN-based
  models on irregular, partially observed series; universal
  approximation. (Abstract.)
* **No execution study found.**

## Against, and failure modes

* GPU training and specialised solvers (the CSV's caveat); no finance
  evidence.

## Fit with volatility-ai

Out of scope: execution timing on event data, and orders here are small
and price-triggered.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Kidger, P., Morrill, J., Foster, J., Lyons, T. (2020).
  <https://arxiv.org/abs/2005.08926>. Abstract.
