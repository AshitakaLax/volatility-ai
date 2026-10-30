# Koopman-operator-based approach to leveraged-ETF exposure rebalancing

**Concept page** · shared by **63** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,858) ·
researched 2026-10-30

| | |
|---|---|
| Task | Leveraged-ETF exposure rebalancing |
| Method | Koopman operators (DMD / EDMD) |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of Koopman operators improving leveraged-ETF exposure; the sibling pages' volatility rules (V18, N7) are the ones to test. |
| Implemented in volatility-ai | The project's exposure levers are built: volatility targeting (V18), the TQQQ/QQQ leverage step-down (N7) and the SMA leverage switch (V16). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | V16, N7, V18, C-MS6, RK22 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Koopman Scholarly Leveraged
ETF Rebalancer Sys-225") combine a method word, "Scholarly", a task and
a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Hold a target exposure through a leveraged ETF, rebalancing as the daily
reset and the path of returns pull the realised leverage away from
target, net of costs. The Koopman version linearises the dynamics in a
lifted feature space and forecasts with the linear operator. I found no
study of this method on this task.

## The CSV's description

Proposed Koopman-operator-based approach to leveraged-ETF exposure
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
* The Koopman entries in the list have no peer-reviewed trading evidence
  (RK206).

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
| 1858 | Koopman Scholarly Leveraged ETF Rebalancer Sys-225 | Rough path theory / Tensor signatures / Stock trend forecasting | 5619 | 6011 | No |
| 1907 | Koopman Scholarly Leveraged ETF Rebalancer Sys-705 | Rough path theory / Tensor signatures / Stock trend forecasting | 5623 | 6026 | No |
| 1956 | Koopman Scholarly Leveraged ETF Rebalancer Sys-1185 | Rough path theory / Tensor signatures / Stock trend forecasting | 5627 | 6041 | No |
| 2005 | Koopman Scholarly Leveraged ETF Rebalancer Sys-1665 | Rough path theory / Tensor signatures / Stock trend forecasting | 5631 | 6056 | No |
| 3973 | Koopman Scholarly Leveraged ETF Rebalancer Sys-129 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6590 | 7456 | No |
| 4059 | Koopman Scholarly Leveraged ETF Rebalancer Sys-609 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6629 | 7460 | No |
| 4145 | Koopman Scholarly Leveraged ETF Rebalancer Sys-1089 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6668 | 7464 | No |
| 4231 | Koopman Scholarly Leveraged ETF Rebalancer Sys-1569 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6707 | 7468 | No |
| 4315 | Koopman Scholarly Leveraged ETF Rebalancer Mod-15 | Neural SDEs / Adversarial robustness / Stock options hedging | 8489 | 6737 | No |
| 4400 | Koopman Scholarly Leveraged ETF Rebalancer Mod-495 | Neural SDEs / Adversarial robustness / Stock options hedging | 8527 | 6771 | No |
| 4485 | Koopman Scholarly Leveraged ETF Rebalancer Mod-975 | Neural SDEs / Adversarial robustness / Stock options hedging | 8565 | 6805 | No |
| 4570 | Koopman Scholarly Leveraged ETF Rebalancer Mod-1455 | Neural SDEs / Adversarial robustness / Stock options hedging | 8603 | 6839 | No |
| 4655 | Koopman Scholarly Leveraged ETF Rebalancer Mod-1935 | Neural SDEs / Adversarial robustness / Stock options hedging | 8641 | 6873 | No |
| 4740 | Koopman Scholarly Leveraged ETF Rebalancer Mod-2415 | Neural SDEs / Adversarial robustness / Stock options hedging | 8679 | 6907 | No |
| 4825 | Koopman Scholarly Leveraged ETF Rebalancer Mod-2895 | Neural SDEs / Adversarial robustness / Stock options hedging | 8717 | 6941 | No |
| 4910 | Koopman Scholarly Leveraged ETF Rebalancer Mod-3375 | Neural SDEs / Adversarial robustness / Stock options hedging | 8755 | 6975 | No |
| 4995 | Koopman Scholarly Leveraged ETF Rebalancer Mod-3855 | Neural SDEs / Adversarial robustness / Stock options hedging | 8793 | 7009 | No |
| 6319 | Koopman Scholarly Leveraged ETF Rebalancer Sys-417 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 429 | 5651 | No |
| 6360 | Koopman Scholarly Leveraged ETF Rebalancer Sys-897 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 437 | 5668 | No |
| 6401 | Koopman Scholarly Leveraged ETF Rebalancer Sys-1377 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 445 | 5685 | No |
| 6442 | Koopman Scholarly Leveraged ETF Rebalancer Sys-1857 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 453 | 5702 | No |
| 9086 | Koopman Scholarly Leveraged ETF Rebalancer Sys-33 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7816 | 10175 | No |
| 9199 | Koopman Scholarly Leveraged ETF Rebalancer Sys-321 | Graph attention / Sector contagion / Stock baskets | 738 | 2212 | No |
| 9273 | Koopman Scholarly Leveraged ETF Rebalancer Sys-513 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7821 | 10185 | No |
| 9386 | Koopman Scholarly Leveraged ETF Rebalancer Sys-801 | Graph attention / Sector contagion / Stock baskets | 742 | 2231 | No |
| 9460 | Koopman Scholarly Leveraged ETF Rebalancer Sys-993 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7826 | 10195 | No |
| 9573 | Koopman Scholarly Leveraged ETF Rebalancer Sys-1281 | Graph attention / Sector contagion / Stock baskets | 746 | 2250 | No |
| 9647 | Koopman Scholarly Leveraged ETF Rebalancer Sys-1473 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7831 | 10205 | No |
| 9760 | Koopman Scholarly Leveraged ETF Rebalancer Sys-1761 | Graph attention / Sector contagion / Stock baskets | 750 | 2269 | No |
| 9834 | Koopman Scholarly Leveraged ETF Rebalancer Sys-1953 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7836 | 10215 | No |
| 9934 | Koopman Scholarly Leveraged ETF Rebalancer Mod-207 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4843 | 11763 | No |
| 9971 | Koopman Scholarly Leveraged ETF Rebalancer Mod-303 | Topological data analysis / Betti persistence / Stock pairs | 2412 | 9437 | No |
| 10011 | Koopman Scholarly Leveraged ETF Rebalancer Mod-399 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2420 | 7475 | No |
| 10125 | Koopman Scholarly Leveraged ETF Rebalancer Mod-687 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4870 | 11767 | No |
| 10162 | Koopman Scholarly Leveraged ETF Rebalancer Mod-783 | Topological data analysis / Betti persistence / Stock pairs | 2451 | 9453 | No |
| 10202 | Koopman Scholarly Leveraged ETF Rebalancer Mod-879 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2459 | 7479 | No |
| 10316 | Koopman Scholarly Leveraged ETF Rebalancer Mod-1167 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4897 | 11771 | No |
| 10353 | Koopman Scholarly Leveraged ETF Rebalancer Mod-1263 | Topological data analysis / Betti persistence / Stock pairs | 2490 | 9469 | No |
| 10393 | Koopman Scholarly Leveraged ETF Rebalancer Mod-1359 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2498 | 7483 | No |
| 10507 | Koopman Scholarly Leveraged ETF Rebalancer Mod-1647 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4924 | 11775 | No |
| 10544 | Koopman Scholarly Leveraged ETF Rebalancer Mod-1743 | Topological data analysis / Betti persistence / Stock pairs | 2529 | 9485 | No |
| 10584 | Koopman Scholarly Leveraged ETF Rebalancer Mod-1839 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2537 | 7487 | No |
| 10698 | Koopman Scholarly Leveraged ETF Rebalancer Mod-2127 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4951 | 11779 | No |
| 10735 | Koopman Scholarly Leveraged ETF Rebalancer Mod-2223 | Topological data analysis / Betti persistence / Stock pairs | 2568 | 9501 | No |
| 10775 | Koopman Scholarly Leveraged ETF Rebalancer Mod-2319 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2576 | 7491 | No |
| 10889 | Koopman Scholarly Leveraged ETF Rebalancer Mod-2607 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4978 | 11783 | No |
| 10926 | Koopman Scholarly Leveraged ETF Rebalancer Mod-2703 | Topological data analysis / Betti persistence / Stock pairs | 2607 | 9517 | No |
| 10966 | Koopman Scholarly Leveraged ETF Rebalancer Mod-2799 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2615 | 7495 | No |
| 11080 | Koopman Scholarly Leveraged ETF Rebalancer Mod-3087 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5005 | 11787 | No |
| 11117 | Koopman Scholarly Leveraged ETF Rebalancer Mod-3183 | Topological data analysis / Betti persistence / Stock pairs | 2646 | 9533 | No |
| 11157 | Koopman Scholarly Leveraged ETF Rebalancer Mod-3279 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2654 | 7499 | No |
| 11271 | Koopman Scholarly Leveraged ETF Rebalancer Mod-3567 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5032 | 11791 | No |
| 11308 | Koopman Scholarly Leveraged ETF Rebalancer Mod-3663 | Topological data analysis / Betti persistence / Stock pairs | 2685 | 9549 | No |
| 11348 | Koopman Scholarly Leveraged ETF Rebalancer Mod-3759 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2693 | 7503 | No |
| 13975 | Koopman Scholarly Leveraged ETF Rebalancer Mod-111 | Delay differential equations / Controlled ODEs / Stock execution | 4044 | 2284 | No |
| 13989 | Koopman Scholarly Leveraged ETF Rebalancer Mod-591 | Delay differential equations / Controlled ODEs / Stock execution | 4070 | 2307 | No |
| 14003 | Koopman Scholarly Leveraged ETF Rebalancer Mod-1071 | Delay differential equations / Controlled ODEs / Stock execution | 4096 | 2330 | No |
| 14017 | Koopman Scholarly Leveraged ETF Rebalancer Mod-1551 | Delay differential equations / Controlled ODEs / Stock execution | 4122 | 2353 | No |
| 14031 | Koopman Scholarly Leveraged ETF Rebalancer Mod-2031 | Delay differential equations / Controlled ODEs / Stock execution | 4148 | 2376 | No |
| 14045 | Koopman Scholarly Leveraged ETF Rebalancer Mod-2511 | Delay differential equations / Controlled ODEs / Stock execution | 4174 | 2399 | No |
| 14059 | Koopman Scholarly Leveraged ETF Rebalancer Mod-2991 | Delay differential equations / Controlled ODEs / Stock execution | 4200 | 2422 | No |
| 14073 | Koopman Scholarly Leveraged ETF Rebalancer Mod-3471 | Delay differential equations / Controlled ODEs / Stock execution | 4226 | 2445 | No |
| 14087 | Koopman Scholarly Leveraged ETF Rebalancer Mod-3951 | Delay differential equations / Controlled ODEs / Stock execution | 4252 | 2468 | No |
