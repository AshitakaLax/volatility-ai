# Nonlinear approach to ETF rotation

**Concept page** · shared by **10** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #3,800) ·
researched 2026-10-30

| | |
|---|---|
| Task | ETF rotation |
| Method | Nonlinear models |
| Fit with this project | ⏳ reference only · background, nothing to build now |
| Useful for volatility-ai | **Reference only.** A nonlinear model could rank or weight the rotation, but no study shows it beating plain relative strength with an absolute-momentum filter; background until X3 is measured. |
| Implemented in volatility-ai | `tools/rotation.py` runs relative strength (X3), defensive rotation (X2), dual momentum (RK3) and HRP weights (A5); Faber's moving-average filter is built (`tactical_allocation`, C-E2, RK17). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | X3, X2, RK3, RK17, C-E2, A5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Non-Linear Scholarly ETF
Rotation Model Ref-175") combine a method word, "Scholarly", a task and
a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Rank a defined ETF universe by momentum, trend or risk and rotate on a
fixed schedule, with a defensive asset and a cost model. The nonlinear
version replaces linear rules with nonlinear regressions or filters. I
found no study of this method on this task.

## The CSV's description

Proposed nonlinear approach to ETF rotation: Rank a defined ETF universe
using a specified momentum, trend, or risk signal and rotate exposure on
a fixed schedule, with a defined defensive allocation and trading-cost
model. This is a concept-level interpretation of the title, not a
complete trading specification: the exact model inputs/target,
calibration, entry/exit or rebalance rules, and position sizing are not
fully defined here.

## Evidence

* **Faber (2007), "A Quantitative Approach to Tactical Asset
  Allocation":** a 10-month moving-average filter across asset classes
  gave comparable returns with much lower volatility and drawdown (see
  RK17). (Summaries.)
* **Antonacci (2012, published 2017), "Risk Premia Harvesting Through
  Dual Momentum":** relative strength picks the asset, absolute momentum
  against T-bills decides whether to hold it (see RK3). (Paper summary.)

## Against, and failure modes

* Rotation results depend heavily on the universe and the rebalance day;
  many published variants are fitted on the same few decades.
* Momentum-based rotation lags turning points and whipsaws in sideways
  markets.
* Nonlinear fits on a few thousand daily bars overfit easily; gains over
  linear rules are usually small out of sample.

## Fit with volatility-ai

Built as X3 (relative-strength rotation), X2 (defensive rotation), RK3
(dual momentum) and C-E2 (Faber TAA), none yet measured. A rotation
sleeve sits beside the TQQQ grid.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Faber, M. T. (2007). "A Quantitative Approach to Tactical Asset
  Allocation." *Journal of Wealth Management*. Summaries; see RK17.
* Antonacci, G. (2017). "Risk Premia Harvesting Through Dual Momentum."
  See RK3.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 3800 | Non-Linear Scholarly ETF Rotation Model Ref-175 | Neural SDEs / Adversarial robustness / Stock options hedging | 9739 | 5619 | No |
| 3886 | Non-Linear Scholarly ETF Rotation Model Ref-655 | Neural SDEs / Adversarial robustness / Stock options hedging | 9745 | 5630 | No |
| 7457 | Non-Linear Scholarly ETF Rotation Model Ref-79 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 8242 | 3030 | No |
| 7491 | Non-Linear Scholarly ETF Rotation Model Ref-559 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 8283 | 3147 | No |
| 8783 | Non-Linear Scholarly ETF Rotation Model Ref-271 | Delay differential equations / Controlled ODEs / Stock execution | 3876 | 1027 | No |
| 8820 | Non-Linear Scholarly ETF Rotation Model Ref-367 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12527 | 12543 | No |
| 8858 | Non-Linear Scholarly ETF Rotation Model Ref-463 | Topological data analysis / Betti persistence / Stock pairs | 2158 | 3125 | No |
| 8974 | Non-Linear Scholarly ETF Rotation Model Ref-751 | Delay differential equations / Controlled ODEs / Stock execution | 3903 | 1062 | No |
| 9011 | Non-Linear Scholarly ETF Rotation Model Ref-847 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12538 | 12556 | No |
| 9049 | Non-Linear Scholarly ETF Rotation Model Ref-943 | Topological data analysis / Betti persistence / Stock pairs | 2190 | 3242 | No |
