# Graph-based approach to leveraged-ETF exposure rebalancing

**Concept page** · shared by **67** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #5,036) ·
researched 2026-10-30

| | |
|---|---|
| Task | Leveraged-ETF exposure rebalancing |
| Method | Graph / network models |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** One leveraged ETF is a network of one node; a graph model has nothing to propagate. |
| Implemented in volatility-ai | The project's exposure levers are built: volatility targeting (V18), the TQQQ/QQQ leverage step-down (N7) and the SMA leverage switch (V16). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | V16, N7, V18, C-MS6, RK22 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Graph Scholarly Leveraged
ETF Rebalancer Eng-75") combine a method word, "Scholarly", a task and a
serial number, and the rows' references are software libraries or papers
the CSV's own review calls unrelated. There is no specific algorithm
behind each name to research, so this page researches what the members
share: the task, done with the method.

## In one paragraph

Hold a target exposure through a leveraged ETF, rebalancing as the daily
reset and the path of returns pull the realised leverage away from
target, net of costs. The graph-based version represents assets as a
network of correlation or causality links and acts on its structure. I
found no study of this method on this task.

## The CSV's description

Proposed graph-based approach to leveraged-ETF exposure rebalancing:
Adjust exposure to maintain a specified leveraged-ETF allocation or
target exposure, while accounting for daily-reset effects, path
dependency, and transaction costs. This is a concept-level
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
* Networks estimated from correlations are noisy and change with the
  window.

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
| 5036 | Graph Scholarly Leveraged ETF Rebalancer Eng-75 | Neural SDEs / Adversarial robustness / Stock options hedging | 8810 | 7023 | No |
| 5122 | Graph Scholarly Leveraged ETF Rebalancer Eng-555 | Neural SDEs / Adversarial robustness / Stock options hedging | 8846 | 7055 | No |
| 5208 | Graph Scholarly Leveraged ETF Rebalancer Eng-1035 | Neural SDEs / Adversarial robustness / Stock options hedging | 8882 | 7087 | No |
| 5294 | Graph Scholarly Leveraged ETF Rebalancer Eng-1515 | Neural SDEs / Adversarial robustness / Stock options hedging | 8918 | 7119 | No |
| 5380 | Graph Scholarly Leveraged ETF Rebalancer Eng-1995 | Neural SDEs / Adversarial robustness / Stock options hedging | 8954 | 7151 | No |
| 5466 | Graph Scholarly Leveraged ETF Rebalancer Eng-2475 | Neural SDEs / Adversarial robustness / Stock options hedging | 8990 | 7183 | No |
| 5552 | Graph Scholarly Leveraged ETF Rebalancer Eng-2955 | Neural SDEs / Adversarial robustness / Stock options hedging | 9026 | 7215 | No |
| 5638 | Graph Scholarly Leveraged ETF Rebalancer Eng-3435 | Neural SDEs / Adversarial robustness / Stock options hedging | 9062 | 7247 | No |
| 5724 | Graph Scholarly Leveraged ETF Rebalancer Eng-3915 | Neural SDEs / Adversarial robustness / Stock options hedging | 9098 | 7279 | No |
| 5810 | Graph Scholarly Leveraged ETF Rebalancer Eng-4395 | Neural SDEs / Adversarial robustness / Stock options hedging | 9134 | 7311 | No |
| 5896 | Graph Scholarly Leveraged ETF Rebalancer Eng-4875 | Neural SDEs / Adversarial robustness / Stock options hedging | 9170 | 7343 | No |
| 5982 | Graph Scholarly Leveraged ETF Rebalancer Eng-5355 | Neural SDEs / Adversarial robustness / Stock options hedging | 9206 | 7375 | No |
| 6068 | Graph Scholarly Leveraged ETF Rebalancer Eng-5835 | Neural SDEs / Adversarial robustness / Stock options hedging | 9242 | 7407 | No |
| 7950 | Graph Scholarly Leveraged ETF Rebalancer Eng-459 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2749 | 7509 | No |
| 7984 | Graph Scholarly Leveraged ETF Rebalancer Eng-939 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2787 | 7513 | No |
| 8018 | Graph Scholarly Leveraged ETF Rebalancer Eng-1419 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2825 | 7517 | No |
| 8052 | Graph Scholarly Leveraged ETF Rebalancer Eng-1899 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2863 | 7521 | No |
| 8086 | Graph Scholarly Leveraged ETF Rebalancer Eng-2379 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2901 | 7525 | No |
| 8120 | Graph Scholarly Leveraged ETF Rebalancer Eng-2859 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2939 | 7529 | No |
| 8154 | Graph Scholarly Leveraged ETF Rebalancer Eng-3339 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2977 | 7533 | No |
| 8188 | Graph Scholarly Leveraged ETF Rebalancer Eng-3819 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 3015 | 7537 | No |
| 8222 | Graph Scholarly Leveraged ETF Rebalancer Eng-4299 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 3053 | 7541 | No |
| 8256 | Graph Scholarly Leveraged ETF Rebalancer Eng-4779 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 3091 | 7545 | No |
| 8290 | Graph Scholarly Leveraged ETF Rebalancer Eng-5259 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 3129 | 7549 | No |
| 8324 | Graph Scholarly Leveraged ETF Rebalancer Eng-5739 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 3167 | 7553 | No |
| 8476 | Graph Scholarly Leveraged ETF Rebalancer Alpha-3 | Topological data analysis / Persistent homology / Stock pairs | 2079 | 9371 | No |
| 8516 | Graph Scholarly Leveraged ETF Rebalancer Alpha-103 | Topological data analysis / Persistent homology / Stock pairs | 2089 | 7435 | No |
| 8556 | Graph Scholarly Leveraged ETF Rebalancer Alpha-203 | Topological data analysis / Persistent homology / Stock pairs | 11271 | 13109 | No |
| 8596 | Graph Scholarly Leveraged ETF Rebalancer Alpha-303 | Topological data analysis / Persistent homology / Stock pairs | 2109 | 9377 | No |
| 8636 | Graph Scholarly Leveraged ETF Rebalancer Alpha-403 | Topological data analysis / Persistent homology / Stock pairs | 2119 | 7440 | No |
| 11514 | Graph Scholarly Leveraged ETF Rebalancer Eng-171 | Delay differential equations / Controlled ODEs / Stock execution | 4267 | 2480 | No |
| 11550 | Graph Scholarly Leveraged ETF Rebalancer Eng-267 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5070 | 11797 | No |
| 11584 | Graph Scholarly Leveraged ETF Rebalancer Eng-363 | Topological data analysis / Betti persistence / Stock pairs | 2741 | 9574 | No |
| 11705 | Graph Scholarly Leveraged ETF Rebalancer Eng-651 | Delay differential equations / Controlled ODEs / Stock execution | 4293 | 2503 | No |
| 11741 | Graph Scholarly Leveraged ETF Rebalancer Eng-747 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5095 | 11801 | No |
| 11775 | Graph Scholarly Leveraged ETF Rebalancer Eng-843 | Topological data analysis / Betti persistence / Stock pairs | 2779 | 9594 | No |
| 11896 | Graph Scholarly Leveraged ETF Rebalancer Eng-1131 | Delay differential equations / Controlled ODEs / Stock execution | 4319 | 2526 | No |
| 11932 | Graph Scholarly Leveraged ETF Rebalancer Eng-1227 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5120 | 11805 | No |
| 11966 | Graph Scholarly Leveraged ETF Rebalancer Eng-1323 | Topological data analysis / Betti persistence / Stock pairs | 2817 | 9614 | No |
| 12087 | Graph Scholarly Leveraged ETF Rebalancer Eng-1611 | Delay differential equations / Controlled ODEs / Stock execution | 4345 | 2549 | No |
| 12123 | Graph Scholarly Leveraged ETF Rebalancer Eng-1707 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5145 | 11809 | No |
| 12157 | Graph Scholarly Leveraged ETF Rebalancer Eng-1803 | Topological data analysis / Betti persistence / Stock pairs | 2855 | 9634 | No |
| 12278 | Graph Scholarly Leveraged ETF Rebalancer Eng-2091 | Delay differential equations / Controlled ODEs / Stock execution | 4371 | 2572 | No |
| 12314 | Graph Scholarly Leveraged ETF Rebalancer Eng-2187 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5170 | 11813 | No |
| 12348 | Graph Scholarly Leveraged ETF Rebalancer Eng-2283 | Topological data analysis / Betti persistence / Stock pairs | 2893 | 9654 | No |
| 12469 | Graph Scholarly Leveraged ETF Rebalancer Eng-2571 | Delay differential equations / Controlled ODEs / Stock execution | 4397 | 2595 | No |
| 12505 | Graph Scholarly Leveraged ETF Rebalancer Eng-2667 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5195 | 11817 | No |
| 12539 | Graph Scholarly Leveraged ETF Rebalancer Eng-2763 | Topological data analysis / Betti persistence / Stock pairs | 2931 | 9674 | No |
| 12660 | Graph Scholarly Leveraged ETF Rebalancer Eng-3051 | Delay differential equations / Controlled ODEs / Stock execution | 4423 | 2618 | No |
| 12696 | Graph Scholarly Leveraged ETF Rebalancer Eng-3147 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5220 | 11821 | No |
| 12730 | Graph Scholarly Leveraged ETF Rebalancer Eng-3243 | Topological data analysis / Betti persistence / Stock pairs | 2969 | 9694 | No |
| 12851 | Graph Scholarly Leveraged ETF Rebalancer Eng-3531 | Delay differential equations / Controlled ODEs / Stock execution | 4449 | 2641 | No |
| 12887 | Graph Scholarly Leveraged ETF Rebalancer Eng-3627 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5245 | 11825 | No |
| 12921 | Graph Scholarly Leveraged ETF Rebalancer Eng-3723 | Topological data analysis / Betti persistence / Stock pairs | 3007 | 9714 | No |
| 13042 | Graph Scholarly Leveraged ETF Rebalancer Eng-4011 | Delay differential equations / Controlled ODEs / Stock execution | 4475 | 2664 | No |
| 13078 | Graph Scholarly Leveraged ETF Rebalancer Eng-4107 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5270 | 11829 | No |
| 13112 | Graph Scholarly Leveraged ETF Rebalancer Eng-4203 | Topological data analysis / Betti persistence / Stock pairs | 3045 | 9734 | No |
| 13233 | Graph Scholarly Leveraged ETF Rebalancer Eng-4491 | Delay differential equations / Controlled ODEs / Stock execution | 4501 | 2687 | No |
| 13269 | Graph Scholarly Leveraged ETF Rebalancer Eng-4587 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5295 | 11833 | No |
| 13303 | Graph Scholarly Leveraged ETF Rebalancer Eng-4683 | Topological data analysis / Betti persistence / Stock pairs | 3083 | 9754 | No |
| 13424 | Graph Scholarly Leveraged ETF Rebalancer Eng-4971 | Delay differential equations / Controlled ODEs / Stock execution | 4527 | 2710 | No |
| 13460 | Graph Scholarly Leveraged ETF Rebalancer Eng-5067 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5320 | 11837 | No |
| 13494 | Graph Scholarly Leveraged ETF Rebalancer Eng-5163 | Topological data analysis / Betti persistence / Stock pairs | 3121 | 9774 | No |
| 13615 | Graph Scholarly Leveraged ETF Rebalancer Eng-5451 | Delay differential equations / Controlled ODEs / Stock execution | 4553 | 2733 | No |
| 13651 | Graph Scholarly Leveraged ETF Rebalancer Eng-5547 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5345 | 11841 | No |
| 13685 | Graph Scholarly Leveraged ETF Rebalancer Eng-5643 | Topological data analysis / Betti persistence / Stock pairs | 3159 | 9794 | No |
| 13806 | Graph Scholarly Leveraged ETF Rebalancer Eng-5931 | Delay differential equations / Controlled ODEs / Stock execution | 4579 | 2756 | No |
