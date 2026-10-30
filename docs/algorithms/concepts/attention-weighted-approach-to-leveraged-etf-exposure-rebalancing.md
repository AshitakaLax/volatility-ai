# Attention-weighted approach to leveraged-ETF exposure rebalancing

**Concept page** · shared by **65** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,224) ·
researched 2026-10-30

| | |
|---|---|
| Task | Leveraged-ETF exposure rebalancing |
| Method | Attention networks |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of attention networks improving leveraged-ETF exposure; the sibling pages' volatility rules (V18, N7) are the ones to test. |
| Implemented in volatility-ai | The project's exposure levers are built: volatility targeting (V18), the TQQQ/QQQ leverage step-down (N7) and the SMA leverage switch (V16). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | V16, N7, V18, C-MS6, RK22 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Attentional Scholarly
Leveraged ETF Rebalancer Sys-105") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Hold a target exposure through a leveraged ETF, rebalancing as the daily
reset and the path of returns pull the realised leverage away from
target, net of costs. The attention version weights its inputs with a
learned attention network. I found no study of this method on this task.

## The CSV's description

Proposed attention-weighted approach to leveraged-ETF exposure
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
* Attention networks need far more data than daily bars of a few ETFs
  provide.

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
| 1224 | Attentional Scholarly Leveraged ETF Rebalancer Sys-105 | Rough path theory / Tensor signatures / Stock trend forecasting | 5618 | 6007 | No |
| 1241 | Attentional Scholarly Leveraged ETF Rebalancer Sys-585 | Rough path theory / Tensor signatures / Stock trend forecasting | 5622 | 6022 | No |
| 1258 | Attentional Scholarly Leveraged ETF Rebalancer Sys-1065 | Rough path theory / Tensor signatures / Stock trend forecasting | 5626 | 6037 | No |
| 1275 | Attentional Scholarly Leveraged ETF Rebalancer Sys-1545 | Rough path theory / Tensor signatures / Stock trend forecasting | 5630 | 6052 | No |
| 3224 | Attentional Scholarly Leveraged ETF Rebalancer Sys-297 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 427 | 5647 | No |
| 3246 | Attentional Scholarly Leveraged ETF Rebalancer Sys-777 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 435 | 5664 | No |
| 3268 | Attentional Scholarly Leveraged ETF Rebalancer Sys-1257 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 443 | 5681 | No |
| 3290 | Attentional Scholarly Leveraged ETF Rebalancer Sys-1737 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 451 | 5698 | No |
| 3952 | Attentional Scholarly Leveraged ETF Rebalancer Sys-9 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6580 | 7455 | No |
| 4038 | Attentional Scholarly Leveraged ETF Rebalancer Sys-489 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6619 | 7459 | No |
| 4124 | Attentional Scholarly Leveraged ETF Rebalancer Sys-969 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6658 | 7463 | No |
| 4210 | Attentional Scholarly Leveraged ETF Rebalancer Sys-1449 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6697 | 7467 | No |
| 4296 | Attentional Scholarly Leveraged ETF Rebalancer Sys-1929 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6736 | 7471 | No |
| 4339 | Attentional Scholarly Leveraged ETF Rebalancer Mod-135 | Neural SDEs / Adversarial robustness / Stock options hedging | 8498 | 6745 | No |
| 4424 | Attentional Scholarly Leveraged ETF Rebalancer Mod-615 | Neural SDEs / Adversarial robustness / Stock options hedging | 8536 | 6779 | No |
| 4509 | Attentional Scholarly Leveraged ETF Rebalancer Mod-1095 | Neural SDEs / Adversarial robustness / Stock options hedging | 8574 | 6813 | No |
| 4594 | Attentional Scholarly Leveraged ETF Rebalancer Mod-1575 | Neural SDEs / Adversarial robustness / Stock options hedging | 8612 | 6847 | No |
| 4679 | Attentional Scholarly Leveraged ETF Rebalancer Mod-2055 | Neural SDEs / Adversarial robustness / Stock options hedging | 8650 | 6881 | No |
| 4764 | Attentional Scholarly Leveraged ETF Rebalancer Mod-2535 | Neural SDEs / Adversarial robustness / Stock options hedging | 8688 | 6915 | No |
| 4849 | Attentional Scholarly Leveraged ETF Rebalancer Mod-3015 | Neural SDEs / Adversarial robustness / Stock options hedging | 8726 | 6949 | No |
| 4934 | Attentional Scholarly Leveraged ETF Rebalancer Mod-3495 | Neural SDEs / Adversarial robustness / Stock options hedging | 8764 | 6983 | No |
| 5019 | Attentional Scholarly Leveraged ETF Rebalancer Mod-3975 | Neural SDEs / Adversarial robustness / Stock options hedging | 8802 | 7017 | No |
| 7534 | Attentional Scholarly Leveraged ETF Rebalancer Sys-201 | Graph attention / Sector contagion / Stock baskets | 737 | 2208 | No |
| 7565 | Attentional Scholarly Leveraged ETF Rebalancer Sys-681 | Graph attention / Sector contagion / Stock baskets | 741 | 2227 | No |
| 7596 | Attentional Scholarly Leveraged ETF Rebalancer Sys-1161 | Graph attention / Sector contagion / Stock baskets | 745 | 2246 | No |
| 7627 | Attentional Scholarly Leveraged ETF Rebalancer Sys-1641 | Graph attention / Sector contagion / Stock baskets | 749 | 2265 | No |
| 7652 | Attentional Scholarly Leveraged ETF Rebalancer Mod-39 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2391 | 7472 | No |
| 7684 | Attentional Scholarly Leveraged ETF Rebalancer Mod-519 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2430 | 7476 | No |
| 7716 | Attentional Scholarly Leveraged ETF Rebalancer Mod-999 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2469 | 7480 | No |
| 7748 | Attentional Scholarly Leveraged ETF Rebalancer Mod-1479 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2508 | 7484 | No |
| 7780 | Attentional Scholarly Leveraged ETF Rebalancer Mod-1959 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2547 | 7488 | No |
| 7812 | Attentional Scholarly Leveraged ETF Rebalancer Mod-2439 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2586 | 7492 | No |
| 7844 | Attentional Scholarly Leveraged ETF Rebalancer Mod-2919 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2625 | 7496 | No |
| 7876 | Attentional Scholarly Leveraged ETF Rebalancer Mod-3399 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2664 | 7500 | No |
| 7908 | Attentional Scholarly Leveraged ETF Rebalancer Mod-3879 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2703 | 7504 | No |
| 8443 | Attention-Weighted Scholarly Leveraged ETF Rebalancer Ver-88 | Point processes / Recurrent neural networks / Stock volatility | 5383 | 7432 | No |
| 8472 | Attention-Weighted Scholarly Leveraged ETF Rebalancer Ver-188 | Point processes / Recurrent neural networks / Stock volatility | 13573 | 13105 | No |
| 9228 | Attentional Scholarly Leveraged ETF Rebalancer Sys-393 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7820 | 10182 | No |
| 9415 | Attentional Scholarly Leveraged ETF Rebalancer Sys-873 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7825 | 10192 | No |
| 9602 | Attentional Scholarly Leveraged ETF Rebalancer Sys-1353 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7830 | 10202 | No |
| 9789 | Attentional Scholarly Leveraged ETF Rebalancer Sys-1833 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7835 | 10212 | No |
| 9945 | Attentional Scholarly Leveraged ETF Rebalancer Mod-231 | Delay differential equations / Controlled ODEs / Stock execution | 4052 | 2290 | No |
| 9983 | Attentional Scholarly Leveraged ETF Rebalancer Mod-327 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4851 | 11764 | No |
| 10021 | Attentional Scholarly Leveraged ETF Rebalancer Mod-423 | Topological data analysis / Betti persistence / Stock pairs | 2422 | 9441 | No |
| 10136 | Attentional Scholarly Leveraged ETF Rebalancer Mod-711 | Delay differential equations / Controlled ODEs / Stock execution | 4078 | 2313 | No |
| 10174 | Attentional Scholarly Leveraged ETF Rebalancer Mod-807 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4878 | 11768 | No |
| 10212 | Attentional Scholarly Leveraged ETF Rebalancer Mod-903 | Topological data analysis / Betti persistence / Stock pairs | 2461 | 9457 | No |
| 10327 | Attentional Scholarly Leveraged ETF Rebalancer Mod-1191 | Delay differential equations / Controlled ODEs / Stock execution | 4104 | 2336 | No |
| 10365 | Attentional Scholarly Leveraged ETF Rebalancer Mod-1287 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4905 | 11772 | No |
| 10403 | Attentional Scholarly Leveraged ETF Rebalancer Mod-1383 | Topological data analysis / Betti persistence / Stock pairs | 2500 | 9473 | No |
| 10518 | Attentional Scholarly Leveraged ETF Rebalancer Mod-1671 | Delay differential equations / Controlled ODEs / Stock execution | 4130 | 2359 | No |
| 10556 | Attentional Scholarly Leveraged ETF Rebalancer Mod-1767 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4932 | 11776 | No |
| 10594 | Attentional Scholarly Leveraged ETF Rebalancer Mod-1863 | Topological data analysis / Betti persistence / Stock pairs | 2539 | 9489 | No |
| 10709 | Attentional Scholarly Leveraged ETF Rebalancer Mod-2151 | Delay differential equations / Controlled ODEs / Stock execution | 4156 | 2382 | No |
| 10747 | Attentional Scholarly Leveraged ETF Rebalancer Mod-2247 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4959 | 11780 | No |
| 10785 | Attentional Scholarly Leveraged ETF Rebalancer Mod-2343 | Topological data analysis / Betti persistence / Stock pairs | 2578 | 9505 | No |
| 10900 | Attentional Scholarly Leveraged ETF Rebalancer Mod-2631 | Delay differential equations / Controlled ODEs / Stock execution | 4182 | 2405 | No |
| 10938 | Attentional Scholarly Leveraged ETF Rebalancer Mod-2727 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4986 | 11784 | No |
| 10976 | Attentional Scholarly Leveraged ETF Rebalancer Mod-2823 | Topological data analysis / Betti persistence / Stock pairs | 2617 | 9521 | No |
| 11091 | Attentional Scholarly Leveraged ETF Rebalancer Mod-3111 | Delay differential equations / Controlled ODEs / Stock execution | 4208 | 2428 | No |
| 11129 | Attentional Scholarly Leveraged ETF Rebalancer Mod-3207 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5013 | 11788 | No |
| 11167 | Attentional Scholarly Leveraged ETF Rebalancer Mod-3303 | Topological data analysis / Betti persistence / Stock pairs | 2656 | 9537 | No |
| 11282 | Attentional Scholarly Leveraged ETF Rebalancer Mod-3591 | Delay differential equations / Controlled ODEs / Stock execution | 4234 | 2451 | No |
| 11320 | Attentional Scholarly Leveraged ETF Rebalancer Mod-3687 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5040 | 11792 | No |
| 11358 | Attentional Scholarly Leveraged ETF Rebalancer Mod-3783 | Topological data analysis / Betti persistence / Stock pairs | 2695 | 9553 | No |
