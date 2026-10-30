# Nonlinear approach to neural-operator forecasting

**Concept page** · shared by **63** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #5,047) ·
researched 2026-10-30

| | |
|---|---|
| Task | Neural-operator forecasting |
| Method | Nonlinear models |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Neural operators have no trading evidence and need far more data than this book has. |
| Implemented in volatility-ai | Nothing. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK291 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Non-Linear Scholarly Neural
Operator Forecaster Eng-135") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Learn a map from market-state histories or feature fields to a forecast
or allocation. The nonlinear version replaces linear rules with
nonlinear regressions or filters. I found no study of this method on
this task.

## The CSV's description

Proposed nonlinear approach to neural-operator forecasting: Learn a
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
* Nonlinear fits on a few thousand daily bars overfit easily; gains over
  linear rules are usually small out of sample.

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
| 5047 | Non-Linear Scholarly Neural Operator Forecaster Eng-135 | Neural SDEs / Adversarial robustness / Stock options hedging | 8815 | 7987 | No |
| 5133 | Non-Linear Scholarly Neural Operator Forecaster Eng-615 | Neural SDEs / Adversarial robustness / Stock options hedging | 8851 | 8019 | No |
| 5219 | Non-Linear Scholarly Neural Operator Forecaster Eng-1095 | Neural SDEs / Adversarial robustness / Stock options hedging | 8887 | 8051 | No |
| 5305 | Non-Linear Scholarly Neural Operator Forecaster Eng-1575 | Neural SDEs / Adversarial robustness / Stock options hedging | 8923 | 8083 | No |
| 5391 | Non-Linear Scholarly Neural Operator Forecaster Eng-2055 | Neural SDEs / Adversarial robustness / Stock options hedging | 8959 | 8115 | No |
| 5477 | Non-Linear Scholarly Neural Operator Forecaster Eng-2535 | Neural SDEs / Adversarial robustness / Stock options hedging | 8995 | 8147 | No |
| 5563 | Non-Linear Scholarly Neural Operator Forecaster Eng-3015 | Neural SDEs / Adversarial robustness / Stock options hedging | 9031 | 8179 | No |
| 5649 | Non-Linear Scholarly Neural Operator Forecaster Eng-3495 | Neural SDEs / Adversarial robustness / Stock options hedging | 9067 | 8211 | No |
| 5735 | Non-Linear Scholarly Neural Operator Forecaster Eng-3975 | Neural SDEs / Adversarial robustness / Stock options hedging | 9103 | 8243 | No |
| 5821 | Non-Linear Scholarly Neural Operator Forecaster Eng-4455 | Neural SDEs / Adversarial robustness / Stock options hedging | 9139 | 8275 | No |
| 5907 | Non-Linear Scholarly Neural Operator Forecaster Eng-4935 | Neural SDEs / Adversarial robustness / Stock options hedging | 9175 | 8307 | No |
| 5993 | Non-Linear Scholarly Neural Operator Forecaster Eng-5415 | Neural SDEs / Adversarial robustness / Stock options hedging | 9211 | 8339 | No |
| 6079 | Non-Linear Scholarly Neural Operator Forecaster Eng-5895 | Neural SDEs / Adversarial robustness / Stock options hedging | 9247 | 8371 | No |
| 11459 | Non-Linear Scholarly Neural Operator Forecaster Eng-39 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7098 | 4451 | No |
| 11570 | Non-Linear Scholarly Neural Operator Forecaster Eng-327 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9540 | 11036 | No |
| 11612 | Non-Linear Scholarly Neural Operator Forecaster Eng-423 | Topological data analysis / Betti persistence / Stock pairs | 7132 | 7046 | No |
| 11650 | Non-Linear Scholarly Neural Operator Forecaster Eng-519 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7140 | 4544 | No |
| 11761 | Non-Linear Scholarly Neural Operator Forecaster Eng-807 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9556 | 11055 | No |
| 11803 | Non-Linear Scholarly Neural Operator Forecaster Eng-903 | Topological data analysis / Betti persistence / Stock pairs | 7174 | 7078 | No |
| 11841 | Non-Linear Scholarly Neural Operator Forecaster Eng-999 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7182 | 4637 | No |
| 11952 | Non-Linear Scholarly Neural Operator Forecaster Eng-1287 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9572 | 11074 | No |
| 11994 | Non-Linear Scholarly Neural Operator Forecaster Eng-1383 | Topological data analysis / Betti persistence / Stock pairs | 7216 | 7110 | No |
| 12032 | Non-Linear Scholarly Neural Operator Forecaster Eng-1479 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7224 | 4730 | No |
| 12143 | Non-Linear Scholarly Neural Operator Forecaster Eng-1767 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9588 | 11093 | No |
| 12185 | Non-Linear Scholarly Neural Operator Forecaster Eng-1863 | Topological data analysis / Betti persistence / Stock pairs | 7258 | 7142 | No |
| 12223 | Non-Linear Scholarly Neural Operator Forecaster Eng-1959 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7266 | 4823 | No |
| 12334 | Non-Linear Scholarly Neural Operator Forecaster Eng-2247 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9604 | 11112 | No |
| 12376 | Non-Linear Scholarly Neural Operator Forecaster Eng-2343 | Topological data analysis / Betti persistence / Stock pairs | 7300 | 7174 | No |
| 12414 | Non-Linear Scholarly Neural Operator Forecaster Eng-2439 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7308 | 4916 | No |
| 12525 | Non-Linear Scholarly Neural Operator Forecaster Eng-2727 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9620 | 11131 | No |
| 12567 | Non-Linear Scholarly Neural Operator Forecaster Eng-2823 | Topological data analysis / Betti persistence / Stock pairs | 7342 | 7206 | No |
| 12605 | Non-Linear Scholarly Neural Operator Forecaster Eng-2919 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7350 | 5009 | No |
| 12716 | Non-Linear Scholarly Neural Operator Forecaster Eng-3207 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9636 | 11150 | No |
| 12758 | Non-Linear Scholarly Neural Operator Forecaster Eng-3303 | Topological data analysis / Betti persistence / Stock pairs | 7384 | 7238 | No |
| 12796 | Non-Linear Scholarly Neural Operator Forecaster Eng-3399 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7392 | 5102 | No |
| 12907 | Non-Linear Scholarly Neural Operator Forecaster Eng-3687 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9652 | 11169 | No |
| 12949 | Non-Linear Scholarly Neural Operator Forecaster Eng-3783 | Topological data analysis / Betti persistence / Stock pairs | 7426 | 7270 | No |
| 12987 | Non-Linear Scholarly Neural Operator Forecaster Eng-3879 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7434 | 5195 | No |
| 13098 | Non-Linear Scholarly Neural Operator Forecaster Eng-4167 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9668 | 11188 | No |
| 13140 | Non-Linear Scholarly Neural Operator Forecaster Eng-4263 | Topological data analysis / Betti persistence / Stock pairs | 7468 | 7302 | No |
| 13178 | Non-Linear Scholarly Neural Operator Forecaster Eng-4359 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7476 | 5288 | No |
| 13289 | Non-Linear Scholarly Neural Operator Forecaster Eng-4647 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9684 | 11207 | No |
| 13331 | Non-Linear Scholarly Neural Operator Forecaster Eng-4743 | Topological data analysis / Betti persistence / Stock pairs | 7510 | 7334 | No |
| 13369 | Non-Linear Scholarly Neural Operator Forecaster Eng-4839 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7518 | 5381 | No |
| 13480 | Non-Linear Scholarly Neural Operator Forecaster Eng-5127 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9700 | 11226 | No |
| 13522 | Non-Linear Scholarly Neural Operator Forecaster Eng-5223 | Topological data analysis / Betti persistence / Stock pairs | 7552 | 7366 | No |
| 13560 | Non-Linear Scholarly Neural Operator Forecaster Eng-5319 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7560 | 5474 | No |
| 13671 | Non-Linear Scholarly Neural Operator Forecaster Eng-5607 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9716 | 11245 | No |
| 13713 | Non-Linear Scholarly Neural Operator Forecaster Eng-5703 | Topological data analysis / Betti persistence / Stock pairs | 7594 | 7398 | No |
| 13751 | Non-Linear Scholarly Neural Operator Forecaster Eng-5799 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7602 | 5567 | No |
| 14093 | Non-Linear Scholarly Neural Operator Forecaster Eng-231 | Delay differential equations / Controlled ODEs / Stock execution | 8822 | 4487 | No |
| 14104 | Non-Linear Scholarly Neural Operator Forecaster Eng-711 | Delay differential equations / Controlled ODEs / Stock execution | 8858 | 4580 | No |
| 14115 | Non-Linear Scholarly Neural Operator Forecaster Eng-1191 | Delay differential equations / Controlled ODEs / Stock execution | 8894 | 4673 | No |
| 14126 | Non-Linear Scholarly Neural Operator Forecaster Eng-1671 | Delay differential equations / Controlled ODEs / Stock execution | 8930 | 4766 | No |
| 14137 | Non-Linear Scholarly Neural Operator Forecaster Eng-2151 | Delay differential equations / Controlled ODEs / Stock execution | 8966 | 4859 | No |
| 14148 | Non-Linear Scholarly Neural Operator Forecaster Eng-2631 | Delay differential equations / Controlled ODEs / Stock execution | 9002 | 4952 | No |
| 14159 | Non-Linear Scholarly Neural Operator Forecaster Eng-3111 | Delay differential equations / Controlled ODEs / Stock execution | 9038 | 5045 | No |
| 14170 | Non-Linear Scholarly Neural Operator Forecaster Eng-3591 | Delay differential equations / Controlled ODEs / Stock execution | 9074 | 5138 | No |
| 14181 | Non-Linear Scholarly Neural Operator Forecaster Eng-4071 | Delay differential equations / Controlled ODEs / Stock execution | 9110 | 5231 | No |
| 14192 | Non-Linear Scholarly Neural Operator Forecaster Eng-4551 | Delay differential equations / Controlled ODEs / Stock execution | 9146 | 5324 | No |
| 14203 | Non-Linear Scholarly Neural Operator Forecaster Eng-5031 | Delay differential equations / Controlled ODEs / Stock execution | 9182 | 5417 | No |
| 14214 | Non-Linear Scholarly Neural Operator Forecaster Eng-5511 | Delay differential equations / Controlled ODEs / Stock execution | 9218 | 5510 | No |
| 14225 | Non-Linear Scholarly Neural Operator Forecaster Eng-5991 | Delay differential equations / Controlled ODEs / Stock execution | 9254 | 5603 | No |
