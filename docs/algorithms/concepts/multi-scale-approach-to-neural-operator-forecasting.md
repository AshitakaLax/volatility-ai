# Multi-scale approach to neural-operator forecasting

**Concept page** · shared by **11** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #3,804) ·
researched 2026-10-30

| | |
|---|---|
| Task | Neural-operator forecasting |
| Method | Multi-scale (several horizons combined) |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Neural operators have no trading evidence and need far more data than this book has. |
| Implemented in volatility-ai | Nothing. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK291 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Multi-Scale Scholarly
Neural Operator Forecaster Ref-195") combine a method word, "Scholarly",
a task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Learn a map from market-state histories or feature fields to a forecast
or allocation. The multi-scale version combines signals or estimates
measured over several horizons. I found no study of this method on this
task.

## The CSV's description

Proposed multi-scale approach to neural-operator forecasting: Learn a
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
* More horizons mean more weights to choose, and the blend can be
  overfitted.

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
| 3804 | Multi-Scale Scholarly Neural Operator Forecaster Ref-195 | Neural SDEs / Adversarial robustness / Stock options hedging | 8251 | 7596 | No |
| 3890 | Multi-Scale Scholarly Neural Operator Forecaster Ref-675 | Neural SDEs / Adversarial robustness / Stock options hedging | 8292 | 7620 | No |
| 8675 | Multi-Scale Scholarly Neural Operator Forecaster Ref-3 | Topological data analysis / Betti persistence / Stock pairs | 6490 | 6530 | No |
| 8714 | Multi-Scale Scholarly Neural Operator Forecaster Ref-99 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6499 | 3036 | No |
| 8827 | Multi-Scale Scholarly Neural Operator Forecaster Ref-387 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9303 | 10746 | No |
| 8866 | Multi-Scale Scholarly Neural Operator Forecaster Ref-483 | Topological data analysis / Betti persistence / Stock pairs | 6533 | 6556 | No |
| 8905 | Multi-Scale Scholarly Neural Operator Forecaster Ref-579 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6542 | 3153 | No |
| 9018 | Multi-Scale Scholarly Neural Operator Forecaster Ref-867 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9319 | 10765 | No |
| 9057 | Multi-Scale Scholarly Neural Operator Forecaster Ref-963 | Topological data analysis / Betti persistence / Stock pairs | 6576 | 6582 | No |
| 13882 | Multi-Scale Scholarly Neural Operator Forecaster Ref-291 | Delay differential equations / Controlled ODEs / Stock execution | 8259 | 3082 | No |
| 13893 | Multi-Scale Scholarly Neural Operator Forecaster Ref-771 | Delay differential equations / Controlled ODEs / Stock execution | 8300 | 3199 | No |
