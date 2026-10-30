# Geometry-aware approach to ETF rotation

**Concept page** · shared by **16** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #3,846) ·
researched 2026-10-30

| | |
|---|---|
| Task | ETF rotation |
| Method | Geometry-aware (Riemannian) methods |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of Riemannian geometry improving ETF rotation over relative strength with an absolute filter (X3, RK3). |
| Implemented in volatility-ai | `tools/rotation.py` runs relative strength (X3), defensive rotation (X2), dual momentum (RK3) and HRP weights (A5); Faber's moving-average filter is built (`tactical_allocation`, C-E2, RK17). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | X3, X2, RK3, RK17, C-E2, A5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Riemannian Scholarly ETF
Rotation Model Ref-415") combine a method word, "Scholarly", a task and
a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Rank a defined ETF universe by momentum, trend or risk and rotate on a
fixed schedule, with a defensive asset and a cost model. The
geometry-aware version works on the curved space of covariance matrices
or another manifold. I found no study of this method on this task.

## The CSV's description

Proposed geometry-aware approach to ETF rotation: Rank a defined ETF
universe using a specified momentum, trend, or risk signal and rotate
exposure on a fixed schedule, with a defined defensive allocation and
trading-cost model. This is a concept-level interpretation of the title,
not a complete trading specification: the exact model inputs/target,
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
* No portfolio study shows Riemannian methods beating shrinkage (RK230).

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
| 3846 | Riemannian Scholarly ETF Rotation Model Ref-415 | Neural SDEs / Adversarial robustness / Stock options hedging | 11094 | 9386 | No |
| 3932 | Riemannian Scholarly ETF Rotation Model Ref-895 | Neural SDEs / Adversarial robustness / Stock options hedging | 11096 | 9392 | No |
| 7475 | Riemannian Scholarly ETF Rotation Model Ref-319 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 8261 | 3089 | No |
| 7509 | Riemannian Scholarly ETF Rotation Model Ref-799 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 8302 | 3206 | No |
| 8510 | Riemannian Scholarly ETF Rotation Model Alpha-87 | Reinforcement learning / Policy gradient / ETF arbitrage | 8188 | 10713 | No |
| 8550 | Riemannian Scholarly ETF Rotation Model Alpha-187 | Reinforcement learning / Policy gradient / ETF arbitrage | 13469 | 12517 | No |
| 8590 | Riemannian Scholarly ETF Rotation Model Alpha-287 | Reinforcement learning / Policy gradient / ETF arbitrage | 10865 | 10723 | No |
| 8630 | Riemannian Scholarly ETF Rotation Model Alpha-387 | Reinforcement learning / Policy gradient / ETF arbitrage | 8221 | 10727 | No |
| 8670 | Riemannian Scholarly ETF Rotation Model Alpha-487 | Reinforcement learning / Policy gradient / ETF arbitrage | 13475 | 12532 | No |
| 8689 | Riemannian Scholarly ETF Rotation Model Ref-31 | Delay differential equations / Controlled ODEs / Stock execution | 3862 | 3018 | No |
| 8726 | Riemannian Scholarly ETF Rotation Model Ref-127 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 13476 | 12538 | No |
| 8763 | Riemannian Scholarly ETF Rotation Model Ref-223 | Topological data analysis / Betti persistence / Stock pairs | 2142 | 3066 | No |
| 8880 | Riemannian Scholarly ETF Rotation Model Ref-511 | Delay differential equations / Controlled ODEs / Stock execution | 3889 | 3135 | No |
| 8917 | Riemannian Scholarly ETF Rotation Model Ref-607 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 13478 | 12551 | No |
| 8954 | Riemannian Scholarly ETF Rotation Model Ref-703 | Topological data analysis / Betti persistence / Stock pairs | 2174 | 3183 | No |
| 9071 | Riemannian Scholarly ETF Rotation Model Ref-991 | Delay differential equations / Controlled ODEs / Stock execution | 3916 | 3252 | No |
