# Evolutionary-optimization-based approach to neural-operator forecasting

**Concept page** · shared by **62** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,868) ·
researched 2026-10-30

| | |
|---|---|
| Task | Neural-operator forecasting |
| Method | Evolutionary / genetic optimisation |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Neural operators have no trading evidence and need far more data than this book has. |
| Implemented in volatility-ai | Nothing. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK291 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Evolutionary Scholarly
Neural Operator Forecaster Sys-285") combine a method word, "Scholarly",
a task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Learn a map from market-state histories or feature fields to a forecast
or allocation. The evolutionary version searches parameters or weights
with genetic algorithms. I found no study of this method on this task.

## The CSV's description

Proposed evolutionary-optimization-based approach to neural-operator
forecasting: Learn a mapping from market-state histories or feature
fields to a forecast or allocation output; the predicted variable,
forecast horizon, and validation protocol must be defined. This is a
concept-level interpretation of the title, not a complete trading
specification: the exact model inputs/target, calibration, entry/exit or
rebalance rules, and position sizing are not fully defined here.

## Evidence

* **Li et al. (2021), "Fourier Neural Operator for Parametric Partial
  Differential Equations," ICLR:** neural operators learn solution maps
  of PDE families (Burgers, Darcy, Navier-Stokes); the paper has no
  financial experiment, and I found no trading study. (Abstract.)

## Against, and failure modes

* Neural operators are built for smooth PDE solution maps, not noisy
  return series.
* A genetic search over a backtest is a large multiple-testing exercise
  that finds the noise that fits best.

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
| 1868 | Evolutionary Scholarly Neural Operator Forecaster Sys-285 | Rough path theory / Tensor signatures / Stock trend forecasting | 9906 | 2211 | No |
| 1917 | Evolutionary Scholarly Neural Operator Forecaster Sys-765 | Rough path theory / Tensor signatures / Stock trend forecasting | 9917 | 2230 | No |
| 1966 | Evolutionary Scholarly Neural Operator Forecaster Sys-1245 | Rough path theory / Tensor signatures / Stock trend forecasting | 9928 | 2249 | No |
| 2015 | Evolutionary Scholarly Neural Operator Forecaster Sys-1725 | Rough path theory / Tensor signatures / Stock trend forecasting | 9939 | 2268 | No |
| 3986 | Evolutionary Scholarly Neural Operator Forecaster Sys-189 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6595 | 3293 | No |
| 4072 | Evolutionary Scholarly Neural Operator Forecaster Sys-669 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6634 | 3388 | No |
| 4158 | Evolutionary Scholarly Neural Operator Forecaster Sys-1149 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6673 | 3483 | No |
| 4244 | Evolutionary Scholarly Neural Operator Forecaster Sys-1629 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6712 | 3578 | No |
| 4388 | Evolutionary Scholarly Neural Operator Forecaster Mod-435 | Neural SDEs / Adversarial robustness / Stock options hedging | 8520 | 7756 | No |
| 4473 | Evolutionary Scholarly Neural Operator Forecaster Mod-915 | Neural SDEs / Adversarial robustness / Stock options hedging | 8558 | 7786 | No |
| 4558 | Evolutionary Scholarly Neural Operator Forecaster Mod-1395 | Neural SDEs / Adversarial robustness / Stock options hedging | 8596 | 7816 | No |
| 4643 | Evolutionary Scholarly Neural Operator Forecaster Mod-1875 | Neural SDEs / Adversarial robustness / Stock options hedging | 8634 | 7846 | No |
| 4728 | Evolutionary Scholarly Neural Operator Forecaster Mod-2355 | Neural SDEs / Adversarial robustness / Stock options hedging | 8672 | 7876 | No |
| 4813 | Evolutionary Scholarly Neural Operator Forecaster Mod-2835 | Neural SDEs / Adversarial robustness / Stock options hedging | 8710 | 7906 | No |
| 4898 | Evolutionary Scholarly Neural Operator Forecaster Mod-3315 | Neural SDEs / Adversarial robustness / Stock options hedging | 8748 | 7936 | No |
| 4983 | Evolutionary Scholarly Neural Operator Forecaster Mod-3795 | Neural SDEs / Adversarial robustness / Stock options hedging | 8786 | 7966 | No |
| 6322 | Evolutionary Scholarly Neural Operator Forecaster Sys-477 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 3265 | 6620 | No |
| 6363 | Evolutionary Scholarly Neural Operator Forecaster Sys-957 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 3289 | 6656 | No |
| 6404 | Evolutionary Scholarly Neural Operator Forecaster Sys-1437 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 3313 | 6692 | No |
| 6445 | Evolutionary Scholarly Neural Operator Forecaster Sys-1917 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 3337 | 6728 | No |
| 9111 | Evolutionary Scholarly Neural Operator Forecaster Sys-93 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 10745 | 10248 | No |
| 9223 | Evolutionary Scholarly Neural Operator Forecaster Sys-381 | Graph attention / Sector contagion / Stock baskets | 4725 | 3332 | No |
| 9298 | Evolutionary Scholarly Neural Operator Forecaster Sys-573 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 10753 | 10252 | No |
| 9410 | Evolutionary Scholarly Neural Operator Forecaster Sys-861 | Graph attention / Sector contagion / Stock baskets | 4756 | 3427 | No |
| 9485 | Evolutionary Scholarly Neural Operator Forecaster Sys-1053 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 10761 | 10256 | No |
| 9597 | Evolutionary Scholarly Neural Operator Forecaster Sys-1341 | Graph attention / Sector contagion / Stock baskets | 4787 | 3522 | No |
| 9672 | Evolutionary Scholarly Neural Operator Forecaster Sys-1533 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 10769 | 10260 | No |
| 9784 | Evolutionary Scholarly Neural Operator Forecaster Sys-1821 | Graph attention / Sector contagion / Stock baskets | 4818 | 3617 | No |
| 9908 | Evolutionary Scholarly Neural Operator Forecaster Mod-147 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9394 | 10872 | No |
| 9950 | Evolutionary Scholarly Neural Operator Forecaster Mod-243 | Topological data analysis / Betti persistence / Stock pairs | 6764 | 6752 | No |
| 9990 | Evolutionary Scholarly Neural Operator Forecaster Mod-339 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6773 | 3720 | No |
| 10099 | Evolutionary Scholarly Neural Operator Forecaster Mod-627 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9411 | 10891 | No |
| 10141 | Evolutionary Scholarly Neural Operator Forecaster Mod-723 | Topological data analysis / Betti persistence / Stock pairs | 6806 | 6786 | No |
| 10181 | Evolutionary Scholarly Neural Operator Forecaster Mod-819 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6815 | 3815 | No |
| 10290 | Evolutionary Scholarly Neural Operator Forecaster Mod-1107 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9428 | 10910 | No |
| 10332 | Evolutionary Scholarly Neural Operator Forecaster Mod-1203 | Topological data analysis / Betti persistence / Stock pairs | 6848 | 6820 | No |
| 10372 | Evolutionary Scholarly Neural Operator Forecaster Mod-1299 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6857 | 3910 | No |
| 10481 | Evolutionary Scholarly Neural Operator Forecaster Mod-1587 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9445 | 10929 | No |
| 10523 | Evolutionary Scholarly Neural Operator Forecaster Mod-1683 | Topological data analysis / Betti persistence / Stock pairs | 6890 | 6854 | No |
| 10563 | Evolutionary Scholarly Neural Operator Forecaster Mod-1779 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6899 | 4005 | No |
| 10672 | Evolutionary Scholarly Neural Operator Forecaster Mod-2067 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9462 | 10948 | No |
| 10714 | Evolutionary Scholarly Neural Operator Forecaster Mod-2163 | Topological data analysis / Betti persistence / Stock pairs | 6932 | 6888 | No |
| 10754 | Evolutionary Scholarly Neural Operator Forecaster Mod-2259 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6941 | 4100 | No |
| 10863 | Evolutionary Scholarly Neural Operator Forecaster Mod-2547 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9479 | 10967 | No |
| 10905 | Evolutionary Scholarly Neural Operator Forecaster Mod-2643 | Topological data analysis / Betti persistence / Stock pairs | 6974 | 6922 | No |
| 10945 | Evolutionary Scholarly Neural Operator Forecaster Mod-2739 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6983 | 4195 | No |
| 11054 | Evolutionary Scholarly Neural Operator Forecaster Mod-3027 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9496 | 10986 | No |
| 11096 | Evolutionary Scholarly Neural Operator Forecaster Mod-3123 | Topological data analysis / Betti persistence / Stock pairs | 7016 | 6956 | No |
| 11136 | Evolutionary Scholarly Neural Operator Forecaster Mod-3219 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7025 | 4290 | No |
| 11245 | Evolutionary Scholarly Neural Operator Forecaster Mod-3507 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9513 | 11005 | No |
| 11287 | Evolutionary Scholarly Neural Operator Forecaster Mod-3603 | Topological data analysis / Betti persistence / Stock pairs | 7058 | 6990 | No |
| 11327 | Evolutionary Scholarly Neural Operator Forecaster Mod-3699 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7067 | 4385 | No |
| 11436 | Evolutionary Scholarly Neural Operator Forecaster Mod-3987 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9530 | 11024 | No |
| 13974 | Evolutionary Scholarly Neural Operator Forecaster Mod-51 | Delay differential equations / Controlled ODEs / Stock execution | 8491 | 3660 | No |
| 13988 | Evolutionary Scholarly Neural Operator Forecaster Mod-531 | Delay differential equations / Controlled ODEs / Stock execution | 8529 | 3755 | No |
| 14002 | Evolutionary Scholarly Neural Operator Forecaster Mod-1011 | Delay differential equations / Controlled ODEs / Stock execution | 8567 | 3850 | No |
| 14016 | Evolutionary Scholarly Neural Operator Forecaster Mod-1491 | Delay differential equations / Controlled ODEs / Stock execution | 8605 | 3945 | No |
| 14030 | Evolutionary Scholarly Neural Operator Forecaster Mod-1971 | Delay differential equations / Controlled ODEs / Stock execution | 8643 | 4040 | No |
| 14044 | Evolutionary Scholarly Neural Operator Forecaster Mod-2451 | Delay differential equations / Controlled ODEs / Stock execution | 8681 | 4135 | No |
| 14058 | Evolutionary Scholarly Neural Operator Forecaster Mod-2931 | Delay differential equations / Controlled ODEs / Stock execution | 8719 | 4230 | No |
| 14072 | Evolutionary Scholarly Neural Operator Forecaster Mod-3411 | Delay differential equations / Controlled ODEs / Stock execution | 8757 | 4325 | No |
| 14086 | Evolutionary Scholarly Neural Operator Forecaster Mod-3891 | Delay differential equations / Controlled ODEs / Stock execution | 8795 | 4420 | No |
