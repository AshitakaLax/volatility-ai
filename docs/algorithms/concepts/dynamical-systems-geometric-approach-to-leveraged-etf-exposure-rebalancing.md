# Dynamical-systems/geometric approach to leveraged-ETF exposure rebalancing

**Concept page** · shared by **62** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,233) ·
researched 2026-10-30

| | |
|---|---|
| Task | Leveraged-ETF exposure rebalancing |
| Method | Dynamical-systems / geometric (e.g. Hamiltonian) models |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of imposed dynamical-systems models improving leveraged-ETF exposure; the sibling pages' volatility rules (V18, N7) are the ones to test. |
| Implemented in volatility-ai | The project's exposure levers are built: volatility targeting (V18), the TQQQ/QQQ leverage step-down (N7) and the SMA leverage switch (V16). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | V16, N7, V18, C-MS6, RK22 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Hamiltonian Scholarly
Leveraged ETF Rebalancer Sys-345") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Hold a target exposure through a leveraged ETF, rebalancing as the daily
reset and the path of returns pull the realised leverage away from
target, net of costs. The dynamical-systems version models the market as
a Hamiltonian or delay-differential system and acts on its fitted state.
I found no study of this method on this task.

## The CSV's description

Proposed dynamical-systems/geometric approach to leveraged-ETF exposure
rebalancing: Adjust exposure to maintain a specified leveraged-ETF
allocation or target exposure, while accounting for daily-reset effects,
path dependency, and transaction costs. This is a concept-level
interpretation of the title, not a complete trading specification: the
exact model inputs/target, calibration, entry/exit or rebalance rules,
and position sizing are not fully defined here.

## Evidence

* **Avellaneda & Zhang (2010), "Path-Dependence of Leveraged ETF
  Returns," *SIAM Journal on Financial Mathematics* 1, 586–603:** the
  gap between a leveraged ETF and a static leveraged position is driven
  mainly by the underlying's realised variance; fees and funding are
  predictable. (Abstract and author slides.)
* **Cheng & Madhavan (2009), "The Dynamics of Leveraged and Inverse
  ETFs," *Journal of Investment Management*:** daily rebalancing makes
  leveraged ETFs path-dependent and creates end-of-day rebalancing flows
  in the direction of the day's move (see C-MS6). (Paper; cited in the
  ledger.)
* **Gayed & Bilello (2016), "Leverage for the Long Run":** hold leverage
  above the index's 200-day average and T-bills below it; volatility,
  which erodes daily-reset leverage, clusters below the average. The
  repository's measurement of the same switch carries a same-session
  lookahead (V16, R1). (Paper summary in
  `docs/research/correction-strategies.md`.)

## Against, and failure modes

* Volatility decay is a property of the path, not a forecastable edge:
  rebalancing toward a target chooses how much leverage to hold, it does
  not remove the decay.
* A target-exposure rule and a lot-harvesting grid pull in different
  directions; every sale still has to pass the no-loss guard.
* The physics is imposed, not estimated from evidence; no trading study
  found.

## Fit with volatility-ai

This is the project's home ground. The engine trades TQQQ and already
varies its exposure three ways: volatility targeting (V18), the leverage
step-down between TQQQ and QQQ (N7) and the SMA leverage switch (V16).
An exposure rule here is a sizing lever on the grid, not a separate
strategy.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Avellaneda, M., Zhang, S. (2010). "Path-Dependence of Leveraged ETF
  Returns." *SIAM Journal on Financial Mathematics* 1, 586–603.
  doi:10.1137/090760805. Abstract.
* Cheng, M., Madhavan, A. (2009). "The Dynamics of Leveraged and Inverse
  ETFs." *Journal of Investment Management*. Cited in the ledger
  (C-MS6).
* Gayed, M. A., Bilello, C. (2016). "Leverage for the Long Run."
  Practitioner paper; see `docs/research/correction-strategies.md` R1.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 1233 | Hamiltonian Scholarly Leveraged ETF Rebalancer Sys-345 | Rough path theory / Tensor signatures / Stock trend forecasting | 5620 | 6014 | No |
| 1250 | Hamiltonian Scholarly Leveraged ETF Rebalancer Sys-825 | Rough path theory / Tensor signatures / Stock trend forecasting | 5624 | 6029 | No |
| 1267 | Hamiltonian Scholarly Leveraged ETF Rebalancer Sys-1305 | Rough path theory / Tensor signatures / Stock trend forecasting | 5628 | 6044 | No |
| 1284 | Hamiltonian Scholarly Leveraged ETF Rebalancer Sys-1785 | Rough path theory / Tensor signatures / Stock trend forecasting | 5632 | 6059 | No |
| 3212 | Hamiltonian Scholarly Leveraged ETF Rebalancer Sys-57 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 423 | 5638 | No |
| 3234 | Hamiltonian Scholarly Leveraged ETF Rebalancer Sys-537 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 431 | 5655 | No |
| 3256 | Hamiltonian Scholarly Leveraged ETF Rebalancer Sys-1017 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 439 | 5672 | No |
| 3278 | Hamiltonian Scholarly Leveraged ETF Rebalancer Sys-1497 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 447 | 5689 | No |
| 3300 | Hamiltonian Scholarly Leveraged ETF Rebalancer Sys-1977 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 455 | 5706 | No |
| 3995 | Hamiltonian Scholarly Leveraged ETF Rebalancer Sys-249 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6601 | 7457 | No |
| 4081 | Hamiltonian Scholarly Leveraged ETF Rebalancer Sys-729 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6640 | 7461 | No |
| 4167 | Hamiltonian Scholarly Leveraged ETF Rebalancer Sys-1209 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6679 | 7465 | No |
| 4253 | Hamiltonian Scholarly Leveraged ETF Rebalancer Sys-1689 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6718 | 7469 | No |
| 4379 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-375 | Neural SDEs / Adversarial robustness / Stock options hedging | 8517 | 6762 | No |
| 4464 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-855 | Neural SDEs / Adversarial robustness / Stock options hedging | 8555 | 6796 | No |
| 4549 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-1335 | Neural SDEs / Adversarial robustness / Stock options hedging | 8593 | 6830 | No |
| 4634 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-1815 | Neural SDEs / Adversarial robustness / Stock options hedging | 8631 | 6864 | No |
| 4719 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-2295 | Neural SDEs / Adversarial robustness / Stock options hedging | 8669 | 6898 | No |
| 4804 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-2775 | Neural SDEs / Adversarial robustness / Stock options hedging | 8707 | 6932 | No |
| 4889 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-3255 | Neural SDEs / Adversarial robustness / Stock options hedging | 8745 | 6966 | No |
| 4974 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-3735 | Neural SDEs / Adversarial robustness / Stock options hedging | 8783 | 7000 | No |
| 7548 | Hamiltonian Scholarly Leveraged ETF Rebalancer Sys-441 | Graph attention / Sector contagion / Stock baskets | 739 | 2217 | No |
| 7579 | Hamiltonian Scholarly Leveraged ETF Rebalancer Sys-921 | Graph attention / Sector contagion / Stock baskets | 743 | 2236 | No |
| 7610 | Hamiltonian Scholarly Leveraged ETF Rebalancer Sys-1401 | Graph attention / Sector contagion / Stock baskets | 747 | 2255 | No |
| 7641 | Hamiltonian Scholarly Leveraged ETF Rebalancer Sys-1881 | Graph attention / Sector contagion / Stock baskets | 751 | 2274 | No |
| 7668 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-279 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2409 | 7474 | No |
| 7700 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-759 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2448 | 7478 | No |
| 7732 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-1239 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2487 | 7482 | No |
| 7764 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-1719 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2526 | 7486 | No |
| 7796 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-2199 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2565 | 7490 | No |
| 7828 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-2679 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2604 | 7494 | No |
| 7860 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-3159 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2643 | 7498 | No |
| 7892 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-3639 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2682 | 7502 | No |
| 9132 | Hamiltonian Scholarly Leveraged ETF Rebalancer Sys-153 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7817 | 10178 | No |
| 9319 | Hamiltonian Scholarly Leveraged ETF Rebalancer Sys-633 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7822 | 10188 | No |
| 9506 | Hamiltonian Scholarly Leveraged ETF Rebalancer Sys-1113 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7827 | 10198 | No |
| 9693 | Hamiltonian Scholarly Leveraged ETF Rebalancer Sys-1593 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7832 | 10208 | No |
| 9886 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-87 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4836 | 11762 | No |
| 9922 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-183 | Topological data analysis / Betti persistence / Stock pairs | 2402 | 9433 | No |
| 10040 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-471 | Delay differential equations / Controlled ODEs / Stock execution | 4065 | 2301 | No |
| 10077 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-567 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4863 | 11766 | No |
| 10113 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-663 | Topological data analysis / Betti persistence / Stock pairs | 2441 | 9449 | No |
| 10231 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-951 | Delay differential equations / Controlled ODEs / Stock execution | 4091 | 2324 | No |
| 10268 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-1047 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4890 | 11770 | No |
| 10304 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-1143 | Topological data analysis / Betti persistence / Stock pairs | 2480 | 9465 | No |
| 10422 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-1431 | Delay differential equations / Controlled ODEs / Stock execution | 4117 | 2347 | No |
| 10459 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-1527 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4917 | 11774 | No |
| 10495 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-1623 | Topological data analysis / Betti persistence / Stock pairs | 2519 | 9481 | No |
| 10613 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-1911 | Delay differential equations / Controlled ODEs / Stock execution | 4143 | 2370 | No |
| 10650 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-2007 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4944 | 11778 | No |
| 10686 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-2103 | Topological data analysis / Betti persistence / Stock pairs | 2558 | 9497 | No |
| 10804 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-2391 | Delay differential equations / Controlled ODEs / Stock execution | 4169 | 2393 | No |
| 10841 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-2487 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4971 | 11782 | No |
| 10877 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-2583 | Topological data analysis / Betti persistence / Stock pairs | 2597 | 9513 | No |
| 10995 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-2871 | Delay differential equations / Controlled ODEs / Stock execution | 4195 | 2416 | No |
| 11032 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-2967 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4998 | 11786 | No |
| 11068 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-3063 | Topological data analysis / Betti persistence / Stock pairs | 2636 | 9529 | No |
| 11186 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-3351 | Delay differential equations / Controlled ODEs / Stock execution | 4221 | 2439 | No |
| 11223 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-3447 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5025 | 11790 | No |
| 11259 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-3543 | Topological data analysis / Betti persistence / Stock pairs | 2675 | 9545 | No |
| 11377 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-3831 | Delay differential equations / Controlled ODEs / Stock execution | 4247 | 2462 | No |
| 11414 | Hamiltonian Scholarly Leveraged ETF Rebalancer Mod-3927 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5052 | 11794 | No |
