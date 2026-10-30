# Robust approach to leveraged-ETF exposure rebalancing

**Concept page** · shared by **62** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,237) ·
researched 2026-10-30

| | |
|---|---|
| Task | Leveraged-ETF exposure rebalancing |
| Method | Robust (outlier-resistant) estimation |
| Fit with this project | ⏳ reference only · background, nothing to build now |
| Useful for volatility-ai | **Reference only.** Robust estimation is a sound way to set leverage, but no study shows it beating the simple volatility rules already built (V18, N7); background only. |
| Implemented in volatility-ai | The project's exposure levers are built: volatility targeting (V18), the TQQQ/QQQ leverage step-down (N7) and the SMA leverage switch (V16). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | V16, N7, V18, C-MS6, RK22 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Robust Scholarly Leveraged
ETF Rebalancer Sys-465") combine a method word, "Scholarly", a task and
a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Hold a target exposure through a leveraged ETF, rebalancing as the daily
reset and the path of returns pull the realised leverage away from
target, net of costs. The robust version estimates its inputs with
outlier-resistant statistics, so a few extreme days do not drive the
result. I found no study of this method on this task.

## The CSV's description

Proposed robust approach to leveraged-ETF exposure rebalancing: Adjust
exposure to maintain a specified leveraged-ETF allocation or target
exposure, while accounting for daily-reset effects, path dependency, and
transaction costs. This is a concept-level interpretation of the title,
not a complete trading specification: the exact model inputs/target,
calibration, entry/exit or rebalance rules, and position sizing are not
fully defined here.

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
* Robust estimators trade efficiency for stability; in calm data they
  add little.

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
| 1237 | Robust Scholarly Leveraged ETF Rebalancer Sys-465 | Rough path theory / Tensor signatures / Stock trend forecasting | 5621 | 6017 | No |
| 1254 | Robust Scholarly Leveraged ETF Rebalancer Sys-945 | Rough path theory / Tensor signatures / Stock trend forecasting | 5625 | 6032 | No |
| 1271 | Robust Scholarly Leveraged ETF Rebalancer Sys-1425 | Rough path theory / Tensor signatures / Stock trend forecasting | 5629 | 6047 | No |
| 1288 | Robust Scholarly Leveraged ETF Rebalancer Sys-1905 | Rough path theory / Tensor signatures / Stock trend forecasting | 5633 | 6062 | No |
| 3218 | Robust Scholarly Leveraged ETF Rebalancer Sys-177 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 425 | 5643 | No |
| 3240 | Robust Scholarly Leveraged ETF Rebalancer Sys-657 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 433 | 5660 | No |
| 3262 | Robust Scholarly Leveraged ETF Rebalancer Sys-1137 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 441 | 5677 | No |
| 3284 | Robust Scholarly Leveraged ETF Rebalancer Sys-1617 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 449 | 5694 | No |
| 4016 | Robust Scholarly Leveraged ETF Rebalancer Sys-369 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6610 | 7458 | No |
| 4102 | Robust Scholarly Leveraged ETF Rebalancer Sys-849 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6649 | 7462 | No |
| 4188 | Robust Scholarly Leveraged ETF Rebalancer Sys-1329 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6688 | 7466 | No |
| 4274 | Robust Scholarly Leveraged ETF Rebalancer Sys-1809 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6727 | 7470 | No |
| 4360 | Robust Scholarly Leveraged ETF Rebalancer Mod-255 | Neural SDEs / Adversarial robustness / Stock options hedging | 8508 | 6753 | No |
| 4445 | Robust Scholarly Leveraged ETF Rebalancer Mod-735 | Neural SDEs / Adversarial robustness / Stock options hedging | 8546 | 6787 | No |
| 4530 | Robust Scholarly Leveraged ETF Rebalancer Mod-1215 | Neural SDEs / Adversarial robustness / Stock options hedging | 8584 | 6821 | No |
| 4615 | Robust Scholarly Leveraged ETF Rebalancer Mod-1695 | Neural SDEs / Adversarial robustness / Stock options hedging | 8622 | 6855 | No |
| 4700 | Robust Scholarly Leveraged ETF Rebalancer Mod-2175 | Neural SDEs / Adversarial robustness / Stock options hedging | 8660 | 6889 | No |
| 4785 | Robust Scholarly Leveraged ETF Rebalancer Mod-2655 | Neural SDEs / Adversarial robustness / Stock options hedging | 8698 | 6923 | No |
| 4870 | Robust Scholarly Leveraged ETF Rebalancer Mod-3135 | Neural SDEs / Adversarial robustness / Stock options hedging | 8736 | 6957 | No |
| 4955 | Robust Scholarly Leveraged ETF Rebalancer Mod-3615 | Neural SDEs / Adversarial robustness / Stock options hedging | 8774 | 6991 | No |
| 7526 | Robust Scholarly Leveraged ETF Rebalancer Sys-81 | Graph attention / Sector contagion / Stock baskets | 736 | 2203 | No |
| 7557 | Robust Scholarly Leveraged ETF Rebalancer Sys-561 | Graph attention / Sector contagion / Stock baskets | 740 | 2222 | No |
| 7588 | Robust Scholarly Leveraged ETF Rebalancer Sys-1041 | Graph attention / Sector contagion / Stock baskets | 744 | 2241 | No |
| 7619 | Robust Scholarly Leveraged ETF Rebalancer Sys-1521 | Graph attention / Sector contagion / Stock baskets | 748 | 2260 | No |
| 7661 | Robust Scholarly Leveraged ETF Rebalancer Mod-159 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2400 | 7473 | No |
| 7693 | Robust Scholarly Leveraged ETF Rebalancer Mod-639 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2439 | 7477 | No |
| 7725 | Robust Scholarly Leveraged ETF Rebalancer Mod-1119 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2478 | 7481 | No |
| 7757 | Robust Scholarly Leveraged ETF Rebalancer Mod-1599 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2517 | 7485 | No |
| 7789 | Robust Scholarly Leveraged ETF Rebalancer Mod-2079 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2556 | 7489 | No |
| 7821 | Robust Scholarly Leveraged ETF Rebalancer Mod-2559 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2595 | 7493 | No |
| 7853 | Robust Scholarly Leveraged ETF Rebalancer Mod-3039 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2634 | 7497 | No |
| 7885 | Robust Scholarly Leveraged ETF Rebalancer Mod-3519 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2673 | 7501 | No |
| 7917 | Robust Scholarly Leveraged ETF Rebalancer Mod-3999 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2712 | 7505 | No |
| 9181 | Robust Scholarly Leveraged ETF Rebalancer Sys-273 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7819 | 10180 | No |
| 9368 | Robust Scholarly Leveraged ETF Rebalancer Sys-753 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7824 | 10190 | No |
| 9555 | Robust Scholarly Leveraged ETF Rebalancer Sys-1233 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7829 | 10200 | No |
| 9742 | Robust Scholarly Leveraged ETF Rebalancer Sys-1713 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7834 | 10210 | No |
| 9875 | Robust Scholarly Leveraged ETF Rebalancer Mod-63 | Topological data analysis / Betti persistence / Stock pairs | 2393 | 9429 | No |
| 9994 | Robust Scholarly Leveraged ETF Rebalancer Mod-351 | Delay differential equations / Controlled ODEs / Stock execution | 4058 | 2295 | No |
| 10031 | Robust Scholarly Leveraged ETF Rebalancer Mod-447 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4857 | 11765 | No |
| 10066 | Robust Scholarly Leveraged ETF Rebalancer Mod-543 | Topological data analysis / Betti persistence / Stock pairs | 2432 | 9445 | No |
| 10185 | Robust Scholarly Leveraged ETF Rebalancer Mod-831 | Delay differential equations / Controlled ODEs / Stock execution | 4084 | 2318 | No |
| 10222 | Robust Scholarly Leveraged ETF Rebalancer Mod-927 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4884 | 11769 | No |
| 10257 | Robust Scholarly Leveraged ETF Rebalancer Mod-1023 | Topological data analysis / Betti persistence / Stock pairs | 2471 | 9461 | No |
| 10376 | Robust Scholarly Leveraged ETF Rebalancer Mod-1311 | Delay differential equations / Controlled ODEs / Stock execution | 4110 | 2341 | No |
| 10413 | Robust Scholarly Leveraged ETF Rebalancer Mod-1407 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4911 | 11773 | No |
| 10448 | Robust Scholarly Leveraged ETF Rebalancer Mod-1503 | Topological data analysis / Betti persistence / Stock pairs | 2510 | 9477 | No |
| 10567 | Robust Scholarly Leveraged ETF Rebalancer Mod-1791 | Delay differential equations / Controlled ODEs / Stock execution | 4136 | 2364 | No |
| 10604 | Robust Scholarly Leveraged ETF Rebalancer Mod-1887 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4938 | 11777 | No |
| 10639 | Robust Scholarly Leveraged ETF Rebalancer Mod-1983 | Topological data analysis / Betti persistence / Stock pairs | 2549 | 9493 | No |
| 10758 | Robust Scholarly Leveraged ETF Rebalancer Mod-2271 | Delay differential equations / Controlled ODEs / Stock execution | 4162 | 2387 | No |
| 10795 | Robust Scholarly Leveraged ETF Rebalancer Mod-2367 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4965 | 11781 | No |
| 10830 | Robust Scholarly Leveraged ETF Rebalancer Mod-2463 | Topological data analysis / Betti persistence / Stock pairs | 2588 | 9509 | No |
| 10949 | Robust Scholarly Leveraged ETF Rebalancer Mod-2751 | Delay differential equations / Controlled ODEs / Stock execution | 4188 | 2410 | No |
| 10986 | Robust Scholarly Leveraged ETF Rebalancer Mod-2847 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4992 | 11785 | No |
| 11021 | Robust Scholarly Leveraged ETF Rebalancer Mod-2943 | Topological data analysis / Betti persistence / Stock pairs | 2627 | 9525 | No |
| 11140 | Robust Scholarly Leveraged ETF Rebalancer Mod-3231 | Delay differential equations / Controlled ODEs / Stock execution | 4214 | 2433 | No |
| 11177 | Robust Scholarly Leveraged ETF Rebalancer Mod-3327 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5019 | 11789 | No |
| 11212 | Robust Scholarly Leveraged ETF Rebalancer Mod-3423 | Topological data analysis / Betti persistence / Stock pairs | 2666 | 9541 | No |
| 11331 | Robust Scholarly Leveraged ETF Rebalancer Mod-3711 | Delay differential equations / Controlled ODEs / Stock execution | 4240 | 2456 | No |
| 11368 | Robust Scholarly Leveraged ETF Rebalancer Mod-3807 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5046 | 11793 | No |
| 11403 | Robust Scholarly Leveraged ETF Rebalancer Mod-3903 | Topological data analysis / Betti persistence / Stock pairs | 2705 | 9557 | No |
