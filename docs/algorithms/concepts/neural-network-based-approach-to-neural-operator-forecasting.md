# Neural-network-based approach to neural-operator forecasting

**Concept page** · shared by **63** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,843) ·
researched 2026-10-30

| | |
|---|---|
| Task | Neural-operator forecasting |
| Method | Neural networks |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Neural operators have no trading evidence and need far more data than this book has. |
| Implemented in volatility-ai | Nothing. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK291 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Neural Scholarly Neural
Operator Forecaster Sys-45") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Learn a map from market-state histories or feature fields to a forecast
or allocation. The neural-network version fits a neural network to the
task. I found no study of this method on this task.

## The CSV's description

Proposed neural-network-based approach to neural-operator forecasting:
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
* Neural forecasts on one index have not reliably beaten simple rules;
  an LSTM's stock picks were largely short-term reversal (Fischer &
  Krauss 2018, RK292).

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
| 1843 | Neural Scholarly Neural Operator Forecaster Sys-45 | Rough path theory / Tensor signatures / Stock trend forecasting | 9901 | 2201 | No |
| 1892 | Neural Scholarly Neural Operator Forecaster Sys-525 | Rough path theory / Tensor signatures / Stock trend forecasting | 9912 | 2220 | No |
| 1941 | Neural Scholarly Neural Operator Forecaster Sys-1005 | Rough path theory / Tensor signatures / Stock trend forecasting | 9923 | 2239 | No |
| 1990 | Neural Scholarly Neural Operator Forecaster Sys-1485 | Rough path theory / Tensor signatures / Stock trend forecasting | 9934 | 2258 | No |
| 2039 | Neural Scholarly Neural Operator Forecaster Sys-1965 | Rough path theory / Tensor signatures / Stock trend forecasting | 9945 | 2277 | No |
| 4027 | Neural Scholarly Neural Operator Forecaster Sys-429 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6615 | 3342 | No |
| 4113 | Neural Scholarly Neural Operator Forecaster Sys-909 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6654 | 3437 | No |
| 4199 | Neural Scholarly Neural Operator Forecaster Sys-1389 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6693 | 3532 | No |
| 4285 | Neural Scholarly Neural Operator Forecaster Sys-1869 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6732 | 3627 | No |
| 4347 | Neural Scholarly Neural Operator Forecaster Mod-195 | Neural SDEs / Adversarial robustness / Stock options hedging | 8501 | 7741 | No |
| 4432 | Neural Scholarly Neural Operator Forecaster Mod-675 | Neural SDEs / Adversarial robustness / Stock options hedging | 8539 | 7771 | No |
| 4517 | Neural Scholarly Neural Operator Forecaster Mod-1155 | Neural SDEs / Adversarial robustness / Stock options hedging | 8577 | 7801 | No |
| 4602 | Neural Scholarly Neural Operator Forecaster Mod-1635 | Neural SDEs / Adversarial robustness / Stock options hedging | 8615 | 7831 | No |
| 4687 | Neural Scholarly Neural Operator Forecaster Mod-2115 | Neural SDEs / Adversarial robustness / Stock options hedging | 8653 | 7861 | No |
| 4772 | Neural Scholarly Neural Operator Forecaster Mod-2595 | Neural SDEs / Adversarial robustness / Stock options hedging | 8691 | 7891 | No |
| 4857 | Neural Scholarly Neural Operator Forecaster Mod-3075 | Neural SDEs / Adversarial robustness / Stock options hedging | 8729 | 7921 | No |
| 4942 | Neural Scholarly Neural Operator Forecaster Mod-3555 | Neural SDEs / Adversarial robustness / Stock options hedging | 8767 | 7951 | No |
| 6299 | Neural Scholarly Neural Operator Forecaster Sys-237 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 3253 | 6602 | No |
| 6340 | Neural Scholarly Neural Operator Forecaster Sys-717 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 3277 | 6638 | No |
| 6381 | Neural Scholarly Neural Operator Forecaster Sys-1197 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 3301 | 6674 | No |
| 6422 | Neural Scholarly Neural Operator Forecaster Sys-1677 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 3325 | 6710 | No |
| 9127 | Neural Scholarly Neural Operator Forecaster Sys-141 | Graph attention / Sector contagion / Stock baskets | 4709 | 3283 | No |
| 9207 | Neural Scholarly Neural Operator Forecaster Sys-333 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 10749 | 10250 | No |
| 9314 | Neural Scholarly Neural Operator Forecaster Sys-621 | Graph attention / Sector contagion / Stock baskets | 4740 | 3378 | No |
| 9394 | Neural Scholarly Neural Operator Forecaster Sys-813 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 10757 | 10254 | No |
| 9501 | Neural Scholarly Neural Operator Forecaster Sys-1101 | Graph attention / Sector contagion / Stock baskets | 4771 | 3473 | No |
| 9581 | Neural Scholarly Neural Operator Forecaster Sys-1293 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 10765 | 10258 | No |
| 9688 | Neural Scholarly Neural Operator Forecaster Sys-1581 | Graph attention / Sector contagion / Stock baskets | 4802 | 3568 | No |
| 9768 | Neural Scholarly Neural Operator Forecaster Sys-1773 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 10773 | 10262 | No |
| 9853 | Neural Scholarly Neural Operator Forecaster Mod-3 | Topological data analysis / Betti persistence / Stock pairs | 6743 | 6736 | No |
| 9893 | Neural Scholarly Neural Operator Forecaster Mod-99 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6752 | 3670 | No |
| 10007 | Neural Scholarly Neural Operator Forecaster Mod-387 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9401 | 10881 | No |
| 10044 | Neural Scholarly Neural Operator Forecaster Mod-483 | Topological data analysis / Betti persistence / Stock pairs | 6785 | 6770 | No |
| 10084 | Neural Scholarly Neural Operator Forecaster Mod-579 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6794 | 3765 | No |
| 10198 | Neural Scholarly Neural Operator Forecaster Mod-867 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9418 | 10900 | No |
| 10235 | Neural Scholarly Neural Operator Forecaster Mod-963 | Topological data analysis / Betti persistence / Stock pairs | 6827 | 6804 | No |
| 10275 | Neural Scholarly Neural Operator Forecaster Mod-1059 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6836 | 3860 | No |
| 10389 | Neural Scholarly Neural Operator Forecaster Mod-1347 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9435 | 10919 | No |
| 10426 | Neural Scholarly Neural Operator Forecaster Mod-1443 | Topological data analysis / Betti persistence / Stock pairs | 6869 | 6838 | No |
| 10466 | Neural Scholarly Neural Operator Forecaster Mod-1539 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6878 | 3955 | No |
| 10580 | Neural Scholarly Neural Operator Forecaster Mod-1827 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9452 | 10938 | No |
| 10617 | Neural Scholarly Neural Operator Forecaster Mod-1923 | Topological data analysis / Betti persistence / Stock pairs | 6911 | 6872 | No |
| 10657 | Neural Scholarly Neural Operator Forecaster Mod-2019 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6920 | 4050 | No |
| 10771 | Neural Scholarly Neural Operator Forecaster Mod-2307 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9469 | 10957 | No |
| 10808 | Neural Scholarly Neural Operator Forecaster Mod-2403 | Topological data analysis / Betti persistence / Stock pairs | 6953 | 6906 | No |
| 10848 | Neural Scholarly Neural Operator Forecaster Mod-2499 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6962 | 4145 | No |
| 10962 | Neural Scholarly Neural Operator Forecaster Mod-2787 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9486 | 10976 | No |
| 10999 | Neural Scholarly Neural Operator Forecaster Mod-2883 | Topological data analysis / Betti persistence / Stock pairs | 6995 | 6940 | No |
| 11039 | Neural Scholarly Neural Operator Forecaster Mod-2979 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7004 | 4240 | No |
| 11153 | Neural Scholarly Neural Operator Forecaster Mod-3267 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9503 | 10995 | No |
| 11190 | Neural Scholarly Neural Operator Forecaster Mod-3363 | Topological data analysis / Betti persistence / Stock pairs | 7037 | 6974 | No |
| 11230 | Neural Scholarly Neural Operator Forecaster Mod-3459 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7046 | 4335 | No |
| 11344 | Neural Scholarly Neural Operator Forecaster Mod-3747 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 9520 | 11014 | No |
| 11381 | Neural Scholarly Neural Operator Forecaster Mod-3843 | Topological data analysis / Betti persistence / Stock pairs | 7079 | 7008 | No |
| 11421 | Neural Scholarly Neural Operator Forecaster Mod-3939 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7088 | 4430 | No |
| 13981 | Neural Scholarly Neural Operator Forecaster Mod-291 | Delay differential equations / Controlled ODEs / Stock execution | 8510 | 3708 | No |
| 13995 | Neural Scholarly Neural Operator Forecaster Mod-771 | Delay differential equations / Controlled ODEs / Stock execution | 8548 | 3803 | No |
| 14009 | Neural Scholarly Neural Operator Forecaster Mod-1251 | Delay differential equations / Controlled ODEs / Stock execution | 8586 | 3898 | No |
| 14023 | Neural Scholarly Neural Operator Forecaster Mod-1731 | Delay differential equations / Controlled ODEs / Stock execution | 8624 | 3993 | No |
| 14037 | Neural Scholarly Neural Operator Forecaster Mod-2211 | Delay differential equations / Controlled ODEs / Stock execution | 8662 | 4088 | No |
| 14051 | Neural Scholarly Neural Operator Forecaster Mod-2691 | Delay differential equations / Controlled ODEs / Stock execution | 8700 | 4183 | No |
| 14065 | Neural Scholarly Neural Operator Forecaster Mod-3171 | Delay differential equations / Controlled ODEs / Stock execution | 8738 | 4278 | No |
| 14079 | Neural Scholarly Neural Operator Forecaster Mod-3651 | Delay differential equations / Controlled ODEs / Stock execution | 8776 | 4373 | No |
