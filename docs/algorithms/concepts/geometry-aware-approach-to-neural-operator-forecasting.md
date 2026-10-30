# Geometry-aware approach to neural-operator forecasting

**Concept page** · shared by **62** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #5,091) ·
researched 2026-10-30

| | |
|---|---|
| Task | Neural-operator forecasting |
| Method | Geometry-aware (Riemannian) methods |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Neural operators have no trading evidence and need far more data than this book has. |
| Implemented in volatility-ai | Nothing. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK291 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Riemannian Scholarly Neural
Operator Forecaster Eng-375") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Learn a map from market-state histories or feature fields to a forecast
or allocation. The geometry-aware version works on the curved space of
covariance matrices or another manifold. I found no study of this method
on this task.

## The CSV's description

Proposed geometry-aware approach to neural-operator forecasting: Learn a
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
* No portfolio study shows Riemannian methods beating shrinkage (RK230).

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
| 5091 | Riemannian Scholarly Neural Operator Forecaster Eng-375 | Neural SDEs / Adversarial robustness / Stock options hedging | 10804 | 8003 | No |
| 5177 | Riemannian Scholarly Neural Operator Forecaster Eng-855 | Neural SDEs / Adversarial robustness / Stock options hedging | 10808 | 8035 | No |
| 5263 | Riemannian Scholarly Neural Operator Forecaster Eng-1335 | Neural SDEs / Adversarial robustness / Stock options hedging | 10812 | 8067 | No |
| 5349 | Riemannian Scholarly Neural Operator Forecaster Eng-1815 | Neural SDEs / Adversarial robustness / Stock options hedging | 10816 | 8099 | No |
| 5435 | Riemannian Scholarly Neural Operator Forecaster Eng-2295 | Neural SDEs / Adversarial robustness / Stock options hedging | 10820 | 8131 | No |
| 5521 | Riemannian Scholarly Neural Operator Forecaster Eng-2775 | Neural SDEs / Adversarial robustness / Stock options hedging | 10824 | 8163 | No |
| 5607 | Riemannian Scholarly Neural Operator Forecaster Eng-3255 | Neural SDEs / Adversarial robustness / Stock options hedging | 10828 | 8195 | No |
| 5693 | Riemannian Scholarly Neural Operator Forecaster Eng-3735 | Neural SDEs / Adversarial robustness / Stock options hedging | 10832 | 8227 | No |
| 5779 | Riemannian Scholarly Neural Operator Forecaster Eng-4215 | Neural SDEs / Adversarial robustness / Stock options hedging | 10836 | 8259 | No |
| 5865 | Riemannian Scholarly Neural Operator Forecaster Eng-4695 | Neural SDEs / Adversarial robustness / Stock options hedging | 10840 | 8291 | No |
| 5951 | Riemannian Scholarly Neural Operator Forecaster Eng-5175 | Neural SDEs / Adversarial robustness / Stock options hedging | 10844 | 8323 | No |
| 6037 | Riemannian Scholarly Neural Operator Forecaster Eng-5655 | Neural SDEs / Adversarial robustness / Stock options hedging | 10848 | 8355 | No |
| 11478 | Riemannian Scholarly Neural Operator Forecaster Eng-87 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10975 | 11027 | No |
| 11517 | Riemannian Scholarly Neural Operator Forecaster Eng-183 | Topological data analysis / Betti persistence / Stock pairs | 7109 | 7030 | No |
| 11555 | Riemannian Scholarly Neural Operator Forecaster Eng-279 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7119 | 4498 | No |
| 11669 | Riemannian Scholarly Neural Operator Forecaster Eng-567 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10984 | 11046 | No |
| 11708 | Riemannian Scholarly Neural Operator Forecaster Eng-663 | Topological data analysis / Betti persistence / Stock pairs | 7151 | 7062 | No |
| 11746 | Riemannian Scholarly Neural Operator Forecaster Eng-759 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7161 | 4591 | No |
| 11860 | Riemannian Scholarly Neural Operator Forecaster Eng-1047 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10993 | 11065 | No |
| 11899 | Riemannian Scholarly Neural Operator Forecaster Eng-1143 | Topological data analysis / Betti persistence / Stock pairs | 7193 | 7094 | No |
| 11937 | Riemannian Scholarly Neural Operator Forecaster Eng-1239 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7203 | 4684 | No |
| 12051 | Riemannian Scholarly Neural Operator Forecaster Eng-1527 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11002 | 11084 | No |
| 12090 | Riemannian Scholarly Neural Operator Forecaster Eng-1623 | Topological data analysis / Betti persistence / Stock pairs | 7235 | 7126 | No |
| 12128 | Riemannian Scholarly Neural Operator Forecaster Eng-1719 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7245 | 4777 | No |
| 12242 | Riemannian Scholarly Neural Operator Forecaster Eng-2007 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11011 | 11103 | No |
| 12281 | Riemannian Scholarly Neural Operator Forecaster Eng-2103 | Topological data analysis / Betti persistence / Stock pairs | 7277 | 7158 | No |
| 12319 | Riemannian Scholarly Neural Operator Forecaster Eng-2199 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7287 | 4870 | No |
| 12433 | Riemannian Scholarly Neural Operator Forecaster Eng-2487 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11020 | 11122 | No |
| 12472 | Riemannian Scholarly Neural Operator Forecaster Eng-2583 | Topological data analysis / Betti persistence / Stock pairs | 7319 | 7190 | No |
| 12510 | Riemannian Scholarly Neural Operator Forecaster Eng-2679 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7329 | 4963 | No |
| 12624 | Riemannian Scholarly Neural Operator Forecaster Eng-2967 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11029 | 11141 | No |
| 12663 | Riemannian Scholarly Neural Operator Forecaster Eng-3063 | Topological data analysis / Betti persistence / Stock pairs | 7361 | 7222 | No |
| 12701 | Riemannian Scholarly Neural Operator Forecaster Eng-3159 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7371 | 5056 | No |
| 12815 | Riemannian Scholarly Neural Operator Forecaster Eng-3447 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11038 | 11160 | No |
| 12854 | Riemannian Scholarly Neural Operator Forecaster Eng-3543 | Topological data analysis / Betti persistence / Stock pairs | 7403 | 7254 | No |
| 12892 | Riemannian Scholarly Neural Operator Forecaster Eng-3639 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7413 | 5149 | No |
| 13006 | Riemannian Scholarly Neural Operator Forecaster Eng-3927 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11047 | 11179 | No |
| 13045 | Riemannian Scholarly Neural Operator Forecaster Eng-4023 | Topological data analysis / Betti persistence / Stock pairs | 7445 | 7286 | No |
| 13083 | Riemannian Scholarly Neural Operator Forecaster Eng-4119 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7455 | 5242 | No |
| 13197 | Riemannian Scholarly Neural Operator Forecaster Eng-4407 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11056 | 11198 | No |
| 13236 | Riemannian Scholarly Neural Operator Forecaster Eng-4503 | Topological data analysis / Betti persistence / Stock pairs | 7487 | 7318 | No |
| 13274 | Riemannian Scholarly Neural Operator Forecaster Eng-4599 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7497 | 5335 | No |
| 13388 | Riemannian Scholarly Neural Operator Forecaster Eng-4887 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11065 | 11217 | No |
| 13427 | Riemannian Scholarly Neural Operator Forecaster Eng-4983 | Topological data analysis / Betti persistence / Stock pairs | 7529 | 7350 | No |
| 13465 | Riemannian Scholarly Neural Operator Forecaster Eng-5079 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7539 | 5428 | No |
| 13579 | Riemannian Scholarly Neural Operator Forecaster Eng-5367 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11074 | 11236 | No |
| 13618 | Riemannian Scholarly Neural Operator Forecaster Eng-5463 | Topological data analysis / Betti persistence / Stock pairs | 7571 | 7382 | No |
| 13656 | Riemannian Scholarly Neural Operator Forecaster Eng-5559 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7581 | 5521 | No |
| 13770 | Riemannian Scholarly Neural Operator Forecaster Eng-5847 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11083 | 11255 | No |
| 13809 | Riemannian Scholarly Neural Operator Forecaster Eng-5943 | Topological data analysis / Betti persistence / Stock pairs | 7613 | 7414 | No |
| 14100 | Riemannian Scholarly Neural Operator Forecaster Eng-471 | Delay differential equations / Controlled ODEs / Stock execution | 8838 | 4534 | No |
| 14111 | Riemannian Scholarly Neural Operator Forecaster Eng-951 | Delay differential equations / Controlled ODEs / Stock execution | 8874 | 4627 | No |
| 14122 | Riemannian Scholarly Neural Operator Forecaster Eng-1431 | Delay differential equations / Controlled ODEs / Stock execution | 8910 | 4720 | No |
| 14133 | Riemannian Scholarly Neural Operator Forecaster Eng-1911 | Delay differential equations / Controlled ODEs / Stock execution | 8946 | 4813 | No |
| 14144 | Riemannian Scholarly Neural Operator Forecaster Eng-2391 | Delay differential equations / Controlled ODEs / Stock execution | 8982 | 4906 | No |
| 14155 | Riemannian Scholarly Neural Operator Forecaster Eng-2871 | Delay differential equations / Controlled ODEs / Stock execution | 9018 | 4999 | No |
| 14166 | Riemannian Scholarly Neural Operator Forecaster Eng-3351 | Delay differential equations / Controlled ODEs / Stock execution | 9054 | 5092 | No |
| 14177 | Riemannian Scholarly Neural Operator Forecaster Eng-3831 | Delay differential equations / Controlled ODEs / Stock execution | 9090 | 5185 | No |
| 14188 | Riemannian Scholarly Neural Operator Forecaster Eng-4311 | Delay differential equations / Controlled ODEs / Stock execution | 9126 | 5278 | No |
| 14199 | Riemannian Scholarly Neural Operator Forecaster Eng-4791 | Delay differential equations / Controlled ODEs / Stock execution | 9162 | 5371 | No |
| 14210 | Riemannian Scholarly Neural Operator Forecaster Eng-5271 | Delay differential equations / Controlled ODEs / Stock execution | 9198 | 5464 | No |
| 14221 | Riemannian Scholarly Neural Operator Forecaster Eng-5751 | Delay differential equations / Controlled ODEs / Stock execution | 9234 | 5557 | No |
