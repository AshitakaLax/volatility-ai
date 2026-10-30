# Path-signature-based approach to neural-operator forecasting

**Concept page** · shared by **63** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,881) ·
researched 2026-10-30

| | |
|---|---|
| Task | Neural-operator forecasting |
| Method | Path signatures |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Neural operators have no trading evidence and need far more data than this book has. |
| Implemented in volatility-ai | Nothing. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK291 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Signature Scholarly Neural
Operator Forecaster Sys-405") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Learn a map from market-state histories or feature fields to a forecast
or allocation. The path-signature version describes price paths by their
iterated-integral signatures and fits on those features. I found no
study of this method on this task.

## The CSV's description

Proposed path-signature-based approach to neural-operator forecasting:
Learn a mapping from market-state histories or feature fields to a
forecast or allocation output; the predicted variable, forecast horizon,
and validation protocol must be defined. This is a concept-level
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
* Signature features multiply with depth and dimension; no out-of-sample
  trading evidence found (RK328).

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
| 1881 | Signature Scholarly Neural Operator Forecaster Sys-405 | Rough path theory / Tensor signatures / Stock trend forecasting | 9909 | 2215 | No |
| 1930 | Signature Scholarly Neural Operator Forecaster Sys-885 | Rough path theory / Tensor signatures / Stock trend forecasting | 9920 | 2234 | No |
| 1979 | Signature Scholarly Neural Operator Forecaster Sys-1365 | Rough path theory / Tensor signatures / Stock trend forecasting | 9931 | 2253 | No |
| 2028 | Signature Scholarly Neural Operator Forecaster Sys-1845 | Rough path theory / Tensor signatures / Stock trend forecasting | 9942 | 2272 | No |
| 4007 | Signature Scholarly Neural Operator Forecaster Sys-309 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6606 | 3318 | No |
| 4093 | Signature Scholarly Neural Operator Forecaster Sys-789 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6645 | 3413 | No |
| 4179 | Signature Scholarly Neural Operator Forecaster Sys-1269 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6684 | 3508 | No |
| 4265 | Signature Scholarly Neural Operator Forecaster Sys-1749 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6723 | 3603 | No |
| 4367 | Signature Scholarly Neural Operator Forecaster Mod-315 | Neural SDEs / Adversarial robustness / Stock options hedging | 8511 | 7749 | No |
| 4452 | Signature Scholarly Neural Operator Forecaster Mod-795 | Neural SDEs / Adversarial robustness / Stock options hedging | 8549 | 7779 | No |
| 4537 | Signature Scholarly Neural Operator Forecaster Mod-1275 | Neural SDEs / Adversarial robustness / Stock options hedging | 8587 | 7809 | No |
| 4622 | Signature Scholarly Neural Operator Forecaster Mod-1755 | Neural SDEs / Adversarial robustness / Stock options hedging | 8625 | 7839 | No |
| 4707 | Signature Scholarly Neural Operator Forecaster Mod-2235 | Neural SDEs / Adversarial robustness / Stock options hedging | 8663 | 7869 | No |
| 4792 | Signature Scholarly Neural Operator Forecaster Mod-2715 | Neural SDEs / Adversarial robustness / Stock options hedging | 8701 | 7899 | No |
| 4877 | Signature Scholarly Neural Operator Forecaster Mod-3195 | Neural SDEs / Adversarial robustness / Stock options hedging | 8739 | 7929 | No |
| 4962 | Signature Scholarly Neural Operator Forecaster Mod-3675 | Neural SDEs / Adversarial robustness / Stock options hedging | 8777 | 7959 | No |
| 6291 | Signature Scholarly Neural Operator Forecaster Sys-117 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 3247 | 6593 | No |
| 6332 | Signature Scholarly Neural Operator Forecaster Sys-597 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 3271 | 6629 | No |
| 6373 | Signature Scholarly Neural Operator Forecaster Sys-1077 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 3295 | 6665 | No |
| 6414 | Signature Scholarly Neural Operator Forecaster Sys-1557 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 3319 | 6701 | No |
| 9081 | Signature Scholarly Neural Operator Forecaster Sys-21 | Graph attention / Sector contagion / Stock baskets | 4703 | 3259 | No |
| 9158 | Signature Scholarly Neural Operator Forecaster Sys-213 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 10748 | 10249 | No |
| 9268 | Signature Scholarly Neural Operator Forecaster Sys-501 | Graph attention / Sector contagion / Stock baskets | 4734 | 3354 | No |
| 9345 | Signature Scholarly Neural Operator Forecaster Sys-693 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 10756 | 10253 | No |
| 9455 | Signature Scholarly Neural Operator Forecaster Sys-981 | Graph attention / Sector contagion / Stock baskets | 4765 | 3449 | No |
| 9532 | Signature Scholarly Neural Operator Forecaster Sys-1173 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 10764 | 10257 | No |
| 9642 | Signature Scholarly Neural Operator Forecaster Sys-1461 | Graph attention / Sector contagion / Stock baskets | 4796 | 3544 | No |
| 9719 | Signature Scholarly Neural Operator Forecaster Sys-1653 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 10772 | 10261 | No |
| 9829 | Signature Scholarly Neural Operator Forecaster Sys-1941 | Graph attention / Sector contagion / Stock baskets | 4827 | 3639 | No |
| 9862 | Signature Scholarly Neural Operator Forecaster Mod-27 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9389 | 10868 | No |
| 9900 | Signature Scholarly Neural Operator Forecaster Mod-123 | Topological data analysis / Betti persistence / Stock pairs | 6754 | 6744 | No |
| 9941 | Signature Scholarly Neural Operator Forecaster Mod-219 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6762 | 3696 | No |
| 10053 | Signature Scholarly Neural Operator Forecaster Mod-507 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9406 | 10887 | No |
| 10091 | Signature Scholarly Neural Operator Forecaster Mod-603 | Topological data analysis / Betti persistence / Stock pairs | 6796 | 6778 | No |
| 10132 | Signature Scholarly Neural Operator Forecaster Mod-699 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6804 | 3791 | No |
| 10244 | Signature Scholarly Neural Operator Forecaster Mod-987 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9423 | 10906 | No |
| 10282 | Signature Scholarly Neural Operator Forecaster Mod-1083 | Topological data analysis / Betti persistence / Stock pairs | 6838 | 6812 | No |
| 10323 | Signature Scholarly Neural Operator Forecaster Mod-1179 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6846 | 3886 | No |
| 10435 | Signature Scholarly Neural Operator Forecaster Mod-1467 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9440 | 10925 | No |
| 10473 | Signature Scholarly Neural Operator Forecaster Mod-1563 | Topological data analysis / Betti persistence / Stock pairs | 6880 | 6846 | No |
| 10514 | Signature Scholarly Neural Operator Forecaster Mod-1659 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6888 | 3981 | No |
| 10626 | Signature Scholarly Neural Operator Forecaster Mod-1947 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9457 | 10944 | No |
| 10664 | Signature Scholarly Neural Operator Forecaster Mod-2043 | Topological data analysis / Betti persistence / Stock pairs | 6922 | 6880 | No |
| 10705 | Signature Scholarly Neural Operator Forecaster Mod-2139 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6930 | 4076 | No |
| 10817 | Signature Scholarly Neural Operator Forecaster Mod-2427 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9474 | 10963 | No |
| 10855 | Signature Scholarly Neural Operator Forecaster Mod-2523 | Topological data analysis / Betti persistence / Stock pairs | 6964 | 6914 | No |
| 10896 | Signature Scholarly Neural Operator Forecaster Mod-2619 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6972 | 4171 | No |
| 11008 | Signature Scholarly Neural Operator Forecaster Mod-2907 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9491 | 10982 | No |
| 11046 | Signature Scholarly Neural Operator Forecaster Mod-3003 | Topological data analysis / Betti persistence / Stock pairs | 7006 | 6948 | No |
| 11087 | Signature Scholarly Neural Operator Forecaster Mod-3099 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7014 | 4266 | No |
| 11199 | Signature Scholarly Neural Operator Forecaster Mod-3387 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9508 | 11001 | No |
| 11237 | Signature Scholarly Neural Operator Forecaster Mod-3483 | Topological data analysis / Betti persistence / Stock pairs | 7048 | 6982 | No |
| 11278 | Signature Scholarly Neural Operator Forecaster Mod-3579 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7056 | 4361 | No |
| 11390 | Signature Scholarly Neural Operator Forecaster Mod-3867 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9525 | 11020 | No |
| 11428 | Signature Scholarly Neural Operator Forecaster Mod-3963 | Topological data analysis / Betti persistence / Stock pairs | 7090 | 7016 | No |
| 13983 | Signature Scholarly Neural Operator Forecaster Mod-411 | Delay differential equations / Controlled ODEs / Stock execution | 8519 | 3734 | No |
| 13997 | Signature Scholarly Neural Operator Forecaster Mod-891 | Delay differential equations / Controlled ODEs / Stock execution | 8557 | 3829 | No |
| 14011 | Signature Scholarly Neural Operator Forecaster Mod-1371 | Delay differential equations / Controlled ODEs / Stock execution | 8595 | 3924 | No |
| 14025 | Signature Scholarly Neural Operator Forecaster Mod-1851 | Delay differential equations / Controlled ODEs / Stock execution | 8633 | 4019 | No |
| 14039 | Signature Scholarly Neural Operator Forecaster Mod-2331 | Delay differential equations / Controlled ODEs / Stock execution | 8671 | 4114 | No |
| 14053 | Signature Scholarly Neural Operator Forecaster Mod-2811 | Delay differential equations / Controlled ODEs / Stock execution | 8709 | 4209 | No |
| 14067 | Signature Scholarly Neural Operator Forecaster Mod-3291 | Delay differential equations / Controlled ODEs / Stock execution | 8747 | 4304 | No |
| 14081 | Signature Scholarly Neural Operator Forecaster Mod-3771 | Delay differential equations / Controlled ODEs / Stock execution | 8785 | 4399 | No |
