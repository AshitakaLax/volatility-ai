# Multi-scale approach to trade-execution optimization

**Concept page** · shared by **70** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #2,075) ·
researched 2026-10-30

| | |
|---|---|
| Task | Trade-execution optimisation |
| Method | Multi-scale (several horizons combined) |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** The book's orders are too small for impact to matter; execution optimisation solves a problem it does not have. |
| Implemented in volatility-ai | Schedules and execution agents are research code (`execution`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK363, RK366, RK244 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Multi-Scale Scholarly
Execution Trajectory Planner Mod-325") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Plan order timing and slicing over a horizon to balance slippage,
impact, completion risk and liquidity. The multi-scale version combines
signals or estimates measured over several horizons. I found no study of
this method on this task.

## The CSV's description

Proposed multi-scale approach to trade-execution optimization: Plan
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
* More horizons mean more weights to choose, and the blend can be
  overfitted.

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
| 2075 | Multi-Scale Scholarly Execution Trajectory Planner Mod-325 | Rough path theory / Tensor signatures / Stock trend forecasting | 6771 | 3717 | No |
| 2128 | Multi-Scale Scholarly Execution Trajectory Planner Mod-805 | Rough path theory / Tensor signatures / Stock trend forecasting | 6813 | 3812 | No |
| 2181 | Multi-Scale Scholarly Execution Trajectory Planner Mod-1285 | Rough path theory / Tensor signatures / Stock trend forecasting | 6855 | 3907 | No |
| 2234 | Multi-Scale Scholarly Execution Trajectory Planner Mod-1765 | Rough path theory / Tensor signatures / Stock trend forecasting | 6897 | 4002 | No |
| 2287 | Multi-Scale Scholarly Execution Trajectory Planner Mod-2245 | Rough path theory / Tensor signatures / Stock trend forecasting | 6939 | 4097 | No |
| 2340 | Multi-Scale Scholarly Execution Trajectory Planner Mod-2725 | Rough path theory / Tensor signatures / Stock trend forecasting | 6981 | 4192 | No |
| 2393 | Multi-Scale Scholarly Execution Trajectory Planner Mod-3205 | Rough path theory / Tensor signatures / Stock trend forecasting | 7023 | 4287 | No |
| 2446 | Multi-Scale Scholarly Execution Trajectory Planner Mod-3685 | Rough path theory / Tensor signatures / Stock trend forecasting | 7065 | 4382 | No |
| 6137 | Multi-Scale Scholarly Execution Trajectory Planner Alpha-17 | Wavelets / Multi-resolution / Statistical arbitrage stocks | 6461 | 6499 | No |
| 6147 | Multi-Scale Scholarly Execution Trajectory Planner Alpha-117 | Wavelets / Multi-resolution / Statistical arbitrage stocks | 392 | 1829 | No |
| 6157 | Multi-Scale Scholarly Execution Trajectory Planner Alpha-217 | Wavelets / Multi-resolution / Statistical arbitrage stocks | 10035 | 11291 | No |
| 6167 | Multi-Scale Scholarly Execution Trajectory Planner Alpha-317 | Wavelets / Multi-resolution / Statistical arbitrage stocks | 6479 | 6518 | No |
| 6177 | Multi-Scale Scholarly Execution Trajectory Planner Alpha-417 | Wavelets / Multi-resolution / Statistical arbitrage stocks | 395 | 1840 | No |
| 6457 | Multi-Scale Scholarly Execution Trajectory Planner Mod-37 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10114 | 11381 | No |
| 6502 | Multi-Scale Scholarly Execution Trajectory Planner Mod-517 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10126 | 11395 | No |
| 6547 | Multi-Scale Scholarly Execution Trajectory Planner Mod-997 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10138 | 11409 | No |
| 6592 | Multi-Scale Scholarly Execution Trajectory Planner Mod-1477 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10150 | 11423 | No |
| 6637 | Multi-Scale Scholarly Execution Trajectory Planner Mod-1957 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10162 | 11437 | No |
| 6682 | Multi-Scale Scholarly Execution Trajectory Planner Mod-2437 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10174 | 11451 | No |
| 6727 | Multi-Scale Scholarly Execution Trajectory Planner Mod-2917 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10186 | 11465 | No |
| 6772 | Multi-Scale Scholarly Execution Trajectory Planner Mod-3397 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10198 | 11479 | No |
| 6817 | Multi-Scale Scholarly Execution Trajectory Planner Mod-3877 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10210 | 11493 | No |
| 7537 | Multi-Scale Scholarly Execution Trajectory Planner Sys-235 | Neural SDEs / Adversarial robustness / Stock options hedging | 9750 | 5645 | No |
| 7568 | Multi-Scale Scholarly Execution Trajectory Planner Sys-715 | Neural SDEs / Adversarial robustness / Stock options hedging | 9754 | 5662 | No |
| 7599 | Multi-Scale Scholarly Execution Trajectory Planner Sys-1195 | Neural SDEs / Adversarial robustness / Stock options hedging | 9758 | 5679 | No |
| 7630 | Multi-Scale Scholarly Execution Trajectory Planner Sys-1675 | Neural SDEs / Adversarial robustness / Stock options hedging | 9762 | 5696 | No |
| 7664 | Multi-Scale Scholarly Execution Trajectory Planner Mod-229 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8504 | 3698 | No |
| 7696 | Multi-Scale Scholarly Execution Trajectory Planner Mod-709 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8542 | 3793 | No |
| 7728 | Multi-Scale Scholarly Execution Trajectory Planner Mod-1189 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8580 | 3888 | No |
| 7760 | Multi-Scale Scholarly Execution Trajectory Planner Mod-1669 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8618 | 3983 | No |
| 7792 | Multi-Scale Scholarly Execution Trajectory Planner Mod-2149 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8656 | 4078 | No |
| 7824 | Multi-Scale Scholarly Execution Trajectory Planner Mod-2629 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8694 | 4173 | No |
| 7856 | Multi-Scale Scholarly Execution Trajectory Planner Mod-3109 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8732 | 4268 | No |
| 7888 | Multi-Scale Scholarly Execution Trajectory Planner Mod-3589 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8770 | 4363 | No |
| 8398 | Multi-Scale Scholarly Execution Trajectory Optimizer MK-38 | Attention networks / Hawkes point processes / Stock alpha | 13565 | 11858 | No |
| 8416 | Multi-Scale Scholarly Execution Trajectory Optimizer MK-98 | Attention networks / Hawkes point processes / Stock alpha | 13567 | 11860 | No |
| 9126 | Multi-Scale Scholarly Execution Trajectory Planner Sys-139 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 8331 | 3282 | No |
| 9205 | Multi-Scale Scholarly Execution Trajectory Planner Sys-331 | Delay differential equations / Controlled ODEs / Stock execution | 3938 | 1096 | No |
| 9313 | Multi-Scale Scholarly Execution Trajectory Planner Sys-619 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 8371 | 3377 | No |
| 9392 | Multi-Scale Scholarly Execution Trajectory Planner Sys-811 | Delay differential equations / Controlled ODEs / Stock execution | 3967 | 1120 | No |
| 9500 | Multi-Scale Scholarly Execution Trajectory Planner Sys-1099 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 8411 | 3472 | No |
| 9579 | Multi-Scale Scholarly Execution Trajectory Planner Sys-1291 | Delay differential equations / Controlled ODEs / Stock execution | 3996 | 1144 | No |
| 9687 | Multi-Scale Scholarly Execution Trajectory Planner Sys-1579 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 8451 | 3567 | No |
| 9766 | Multi-Scale Scholarly Execution Trajectory Planner Sys-1771 | Delay differential equations / Controlled ODEs / Stock execution | 4025 | 1168 | No |
| 10020 | Multi-Scale Scholarly Execution Trajectory Planner Mod-421 | Graph attention / Sector contagion / Stock baskets | 760 | 1199 | No |
| 10211 | Multi-Scale Scholarly Execution Trajectory Planner Mod-901 | Graph attention / Sector contagion / Stock baskets | 770 | 1223 | No |
| 10402 | Multi-Scale Scholarly Execution Trajectory Planner Mod-1381 | Graph attention / Sector contagion / Stock baskets | 780 | 1247 | No |
| 10593 | Multi-Scale Scholarly Execution Trajectory Planner Mod-1861 | Graph attention / Sector contagion / Stock baskets | 790 | 1271 | No |
| 10784 | Multi-Scale Scholarly Execution Trajectory Planner Mod-2341 | Graph attention / Sector contagion / Stock baskets | 800 | 1295 | No |
| 10975 | Multi-Scale Scholarly Execution Trajectory Planner Mod-2821 | Graph attention / Sector contagion / Stock baskets | 810 | 1319 | No |
| 11166 | Multi-Scale Scholarly Execution Trajectory Planner Mod-3301 | Graph attention / Sector contagion / Stock baskets | 820 | 1343 | No |
| 11357 | Multi-Scale Scholarly Execution Trajectory Planner Mod-3781 | Graph attention / Sector contagion / Stock baskets | 830 | 1367 | No |
| 13899 | Multi-Scale Scholarly Execution Trajectory Planner Sys-43 | Topological data analysis / Betti persistence / Stock pairs | 2197 | 3264 | No |
| 13913 | Multi-Scale Scholarly Execution Trajectory Planner Sys-427 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12549 | 12570 | No |
| 13917 | Multi-Scale Scholarly Execution Trajectory Planner Sys-523 | Topological data analysis / Betti persistence / Stock pairs | 2244 | 3359 | No |
| 13931 | Multi-Scale Scholarly Execution Trajectory Planner Sys-907 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12556 | 12582 | No |
| 13935 | Multi-Scale Scholarly Execution Trajectory Planner Sys-1003 | Topological data analysis / Betti persistence / Stock pairs | 2291 | 3454 | No |
| 13949 | Multi-Scale Scholarly Execution Trajectory Planner Sys-1387 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12563 | 12594 | No |
| 13953 | Multi-Scale Scholarly Execution Trajectory Planner Sys-1483 | Topological data analysis / Betti persistence / Stock pairs | 2338 | 3549 | No |
| 13967 | Multi-Scale Scholarly Execution Trajectory Planner Sys-1867 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12570 | 12606 | No |
| 13971 | Multi-Scale Scholarly Execution Trajectory Planner Sys-1963 | Topological data analysis / Betti persistence / Stock pairs | 2385 | 3644 | No |
| 13977 | Multi-Scale Scholarly Execution Trajectory Planner Mod-133 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7839 | 6073 | No |
| 13991 | Multi-Scale Scholarly Execution Trajectory Planner Mod-613 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7853 | 6090 | No |
| 14005 | Multi-Scale Scholarly Execution Trajectory Planner Mod-1093 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7867 | 6107 | No |
| 14019 | Multi-Scale Scholarly Execution Trajectory Planner Mod-1573 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7881 | 6124 | No |
| 14033 | Multi-Scale Scholarly Execution Trajectory Planner Mod-2053 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7895 | 6141 | No |
| 14047 | Multi-Scale Scholarly Execution Trajectory Planner Mod-2533 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7909 | 6158 | No |
| 14061 | Multi-Scale Scholarly Execution Trajectory Planner Mod-3013 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7923 | 6175 | No |
| 14075 | Multi-Scale Scholarly Execution Trajectory Planner Mod-3493 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7937 | 6192 | No |
| 14089 | Multi-Scale Scholarly Execution Trajectory Planner Mod-3973 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7951 | 6209 | No |
