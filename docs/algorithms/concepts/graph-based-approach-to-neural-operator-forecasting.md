# Graph-based approach to neural-operator forecasting

**Concept page** · shared by **10** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #3,850) ·
researched 2026-10-30

| | |
|---|---|
| Task | Neural-operator forecasting |
| Method | Graph / network models |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Neural operators have no trading evidence and need far more data than this book has. |
| Implemented in volatility-ai | Nothing. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK291 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Graph Scholarly Neural
Operator Forecaster Ref-435") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Learn a map from market-state histories or feature fields to a forecast
or allocation. The graph-based version represents assets as a network of
correlation or causality links and acts on its structure. I found no
study of this method on this task.

## The CSV's description

Proposed graph-based approach to neural-operator forecasting: Learn a
mapping from market-state histories or feature fields to a forecast or
allocation output; the predicted variable, forecast horizon, and
validation protocol must be defined. This is a concept-level
interpretation of the title, not a complete trading specification: the
exact model inputs/target, calibration, entry/exit or rebalance rules,
and position sizing are not fully defined here.

## Evidence

* **Li et al. (2021), "Fourier Neural Operator for Parametric Partial
  Differential Equations," ICLR:** neural operators learn solution maps
  of PDE families (Burgers, Darcy, Navier-Stokes); the paper has no
  financial experiment, and I found no trading study. (Abstract.)

## Against, and failure modes

* Neural operators are built for smooth PDE solution maps, not noisy
  return series.
* Networks estimated from correlations are noisy and change with the
  window.

## Fit with volatility-ai

No trading evidence, and daily bars of one ETF are far too little data
for an operator network.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Li, Z., Kovachki, N., et al. (2021). "Fourier Neural Operator for
  Parametric Partial Differential Equations." ICLR. arXiv 2010.08895.
  Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 3850 | Graph Scholarly Neural Operator Forecaster Ref-435 | Neural SDEs / Adversarial robustness / Stock options hedging | 8270 | 7608 | No |
| 3936 | Graph Scholarly Neural Operator Forecaster Ref-915 | Neural SDEs / Adversarial robustness / Stock options hedging | 8311 | 7632 | No |
| 8732 | Graph Scholarly Neural Operator Forecaster Ref-147 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9295 | 10737 | No |
| 8770 | Graph Scholarly Neural Operator Forecaster Ref-243 | Topological data analysis / Betti persistence / Stock pairs | 6511 | 6543 | No |
| 8809 | Graph Scholarly Neural Operator Forecaster Ref-339 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6521 | 3094 | No |
| 8923 | Graph Scholarly Neural Operator Forecaster Ref-627 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9311 | 10756 | No |
| 8961 | Graph Scholarly Neural Operator Forecaster Ref-723 | Topological data analysis / Betti persistence / Stock pairs | 6554 | 6569 | No |
| 9000 | Graph Scholarly Neural Operator Forecaster Ref-819 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6564 | 3211 | No |
| 13876 | Graph Scholarly Neural Operator Forecaster Ref-51 | Delay differential equations / Controlled ODEs / Stock execution | 8240 | 3024 | No |
| 13887 | Graph Scholarly Neural Operator Forecaster Ref-531 | Delay differential equations / Controlled ODEs / Stock execution | 8281 | 3141 | No |
