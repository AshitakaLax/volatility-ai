# Graph-based approach to trade-execution optimization

**Concept page** · shared by **61** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #2,048) ·
researched 2026-10-30

| | |
|---|---|
| Task | Trade-execution optimisation |
| Method | Graph / network models |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** The book's orders are too small for impact to matter; execution optimisation solves a problem it does not have. |
| Implemented in volatility-ai | Schedules and execution agents are research code (`execution`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK363, RK366, RK244 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Graph Scholarly Execution
Trajectory Planner Mod-85") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Plan order timing and slicing over a horizon to balance slippage,
impact, completion risk and liquidity. The graph-based version
represents assets as a network of correlation or causality links and
acts on its structure. I found no study of this method on this task.

## The CSV's description

Proposed graph-based approach to trade-execution optimization: Plan
order timing and slicing over an execution horizon to balance expected
slippage, market impact, completion risk, and liquidity. This is a
concept-level interpretation of the title, not a complete trading
specification: the exact model inputs/target, calibration, entry/exit or
rebalance rules, and position sizing are not fully defined here.

## Evidence

* **Almgren & Chriss (2001), "Optimal execution of portfolio
  transactions," *Journal of Risk* 3(2):** the mean-variance trade-off
  between impact and timing risk for a large order (see RK366).
  (Standard reference.)
* **Frazzini, Israel & Moskowitz (2018), "Trading Costs" (SSRN
  3229719):** on $1.7 trillion of live institutional trades, market
  impact averaged under 9 bp for orders completed within a day, an order
  of magnitude below earlier estimates. (Abstract and summaries.)

## Against, and failure modes

* Execution schedules address impact, which is a few basis points even
  for institutional orders (Frazzini, Israel & Moskowitz).
* Networks estimated from correlations are noisy and change with the
  window.

## Fit with volatility-ai

The engine's orders are small against TQQQ's volume; slicing schedules
solve a problem this book does not have (RK363, RK366). A spread gate
(RK244) covers what matters.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Almgren, R., Chriss, N. (2001). *Journal of Risk* 3(2), 5–39. Standard
  reference.
* Frazzini, A., Israel, R., Moskowitz, T. J. (2018). "Trading Costs."
  SSRN 3229719. Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 2048 | Graph Scholarly Execution Trajectory Planner Mod-85 | Rough path theory / Tensor signatures / Stock trend forecasting | 6750 | 3667 | No |
| 2101 | Graph Scholarly Execution Trajectory Planner Mod-565 | Rough path theory / Tensor signatures / Stock trend forecasting | 6792 | 3762 | No |
| 2154 | Graph Scholarly Execution Trajectory Planner Mod-1045 | Rough path theory / Tensor signatures / Stock trend forecasting | 6834 | 3857 | No |
| 2207 | Graph Scholarly Execution Trajectory Planner Mod-1525 | Rough path theory / Tensor signatures / Stock trend forecasting | 6876 | 3952 | No |
| 2260 | Graph Scholarly Execution Trajectory Planner Mod-2005 | Rough path theory / Tensor signatures / Stock trend forecasting | 6918 | 4047 | No |
| 2313 | Graph Scholarly Execution Trajectory Planner Mod-2485 | Rough path theory / Tensor signatures / Stock trend forecasting | 6960 | 4142 | No |
| 2366 | Graph Scholarly Execution Trajectory Planner Mod-2965 | Rough path theory / Tensor signatures / Stock trend forecasting | 7002 | 4237 | No |
| 2419 | Graph Scholarly Execution Trajectory Planner Mod-3445 | Rough path theory / Tensor signatures / Stock trend forecasting | 7044 | 4332 | No |
| 2472 | Graph Scholarly Execution Trajectory Planner Mod-3925 | Rough path theory / Tensor signatures / Stock trend forecasting | 7086 | 4427 | No |
| 6479 | Graph Scholarly Execution Trajectory Planner Mod-277 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10119 | 11388 | No |
| 6524 | Graph Scholarly Execution Trajectory Planner Mod-757 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10131 | 11402 | No |
| 6569 | Graph Scholarly Execution Trajectory Planner Mod-1237 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10143 | 11416 | No |
| 6614 | Graph Scholarly Execution Trajectory Planner Mod-1717 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10155 | 11430 | No |
| 6659 | Graph Scholarly Execution Trajectory Planner Mod-2197 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10167 | 11444 | No |
| 6704 | Graph Scholarly Execution Trajectory Planner Mod-2677 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10179 | 11458 | No |
| 6749 | Graph Scholarly Execution Trajectory Planner Mod-3157 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10191 | 11472 | No |
| 6794 | Graph Scholarly Execution Trajectory Planner Mod-3637 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10203 | 11486 | No |
| 7551 | Graph Scholarly Execution Trajectory Planner Sys-475 | Neural SDEs / Adversarial robustness / Stock options hedging | 9752 | 5653 | No |
| 7582 | Graph Scholarly Execution Trajectory Planner Sys-955 | Neural SDEs / Adversarial robustness / Stock options hedging | 9756 | 5670 | No |
| 7613 | Graph Scholarly Execution Trajectory Planner Sys-1435 | Neural SDEs / Adversarial robustness / Stock options hedging | 9760 | 5687 | No |
| 7644 | Graph Scholarly Execution Trajectory Planner Sys-1915 | Neural SDEs / Adversarial robustness / Stock options hedging | 9764 | 5704 | No |
| 7680 | Graph Scholarly Execution Trajectory Planner Mod-469 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8523 | 3745 | No |
| 7712 | Graph Scholarly Execution Trajectory Planner Mod-949 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8561 | 3840 | No |
| 7744 | Graph Scholarly Execution Trajectory Planner Mod-1429 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8599 | 3935 | No |
| 7776 | Graph Scholarly Execution Trajectory Planner Mod-1909 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8637 | 4030 | No |
| 7808 | Graph Scholarly Execution Trajectory Planner Mod-2389 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8675 | 4125 | No |
| 7840 | Graph Scholarly Execution Trajectory Planner Mod-2869 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8713 | 4220 | No |
| 7872 | Graph Scholarly Execution Trajectory Planner Mod-3349 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8751 | 4315 | No |
| 7904 | Graph Scholarly Execution Trajectory Planner Mod-3829 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8789 | 4410 | No |
| 9109 | Graph Scholarly Execution Trajectory Planner Sys-91 | Delay differential equations / Controlled ODEs / Stock execution | 3924 | 1084 | No |
| 9222 | Graph Scholarly Execution Trajectory Planner Sys-379 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 8353 | 3331 | No |
| 9296 | Graph Scholarly Execution Trajectory Planner Sys-571 | Delay differential equations / Controlled ODEs / Stock execution | 3953 | 1108 | No |
| 9409 | Graph Scholarly Execution Trajectory Planner Sys-859 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 8393 | 3426 | No |
| 9483 | Graph Scholarly Execution Trajectory Planner Sys-1051 | Delay differential equations / Controlled ODEs / Stock execution | 3982 | 1132 | No |
| 9596 | Graph Scholarly Execution Trajectory Planner Sys-1339 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 8433 | 3521 | No |
| 9670 | Graph Scholarly Execution Trajectory Planner Sys-1531 | Delay differential equations / Controlled ODEs / Stock execution | 4011 | 1156 | No |
| 9783 | Graph Scholarly Execution Trajectory Planner Sys-1819 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 8473 | 3616 | No |
| 9921 | Graph Scholarly Execution Trajectory Planner Mod-181 | Graph attention / Sector contagion / Stock baskets | 756 | 1189 | No |
| 10112 | Graph Scholarly Execution Trajectory Planner Mod-661 | Graph attention / Sector contagion / Stock baskets | 766 | 1213 | No |
| 10303 | Graph Scholarly Execution Trajectory Planner Mod-1141 | Graph attention / Sector contagion / Stock baskets | 776 | 1237 | No |
| 10494 | Graph Scholarly Execution Trajectory Planner Mod-1621 | Graph attention / Sector contagion / Stock baskets | 786 | 1261 | No |
| 10685 | Graph Scholarly Execution Trajectory Planner Mod-2101 | Graph attention / Sector contagion / Stock baskets | 796 | 1285 | No |
| 10876 | Graph Scholarly Execution Trajectory Planner Mod-2581 | Graph attention / Sector contagion / Stock baskets | 806 | 1309 | No |
| 11067 | Graph Scholarly Execution Trajectory Planner Mod-3061 | Graph attention / Sector contagion / Stock baskets | 816 | 1333 | No |
| 11258 | Graph Scholarly Execution Trajectory Planner Mod-3541 | Graph attention / Sector contagion / Stock baskets | 826 | 1357 | No |
| 13904 | Graph Scholarly Execution Trajectory Planner Sys-187 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12545 | 12565 | No |
| 13907 | Graph Scholarly Execution Trajectory Planner Sys-283 | Topological data analysis / Betti persistence / Stock pairs | 2220 | 3313 | No |
| 13922 | Graph Scholarly Execution Trajectory Planner Sys-667 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12552 | 12577 | No |
| 13925 | Graph Scholarly Execution Trajectory Planner Sys-763 | Topological data analysis / Betti persistence / Stock pairs | 2267 | 3408 | No |
| 13940 | Graph Scholarly Execution Trajectory Planner Sys-1147 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12559 | 12589 | No |
| 13943 | Graph Scholarly Execution Trajectory Planner Sys-1243 | Topological data analysis / Betti persistence / Stock pairs | 2314 | 3503 | No |
| 13958 | Graph Scholarly Execution Trajectory Planner Sys-1627 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12566 | 12601 | No |
| 13961 | Graph Scholarly Execution Trajectory Planner Sys-1723 | Topological data analysis / Betti persistence / Stock pairs | 2361 | 3598 | No |
| 13982 | Graph Scholarly Execution Trajectory Planner Mod-373 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7848 | 6081 | No |
| 13996 | Graph Scholarly Execution Trajectory Planner Mod-853 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7862 | 6098 | No |
| 14010 | Graph Scholarly Execution Trajectory Planner Mod-1333 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7876 | 6115 | No |
| 14024 | Graph Scholarly Execution Trajectory Planner Mod-1813 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7890 | 6132 | No |
| 14038 | Graph Scholarly Execution Trajectory Planner Mod-2293 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7904 | 6149 | No |
| 14052 | Graph Scholarly Execution Trajectory Planner Mod-2773 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7918 | 6166 | No |
| 14066 | Graph Scholarly Execution Trajectory Planner Mod-3253 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7932 | 6183 | No |
| 14080 | Graph Scholarly Execution Trajectory Planner Mod-3733 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7946 | 6200 | No |
