# Robust approach to trade-execution optimization

**Concept page** · shared by **65** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #2,523) ·
researched 2026-10-30

| | |
|---|---|
| Task | Trade-execution optimisation |
| Method | Robust (outlier-resistant) estimation |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** The book's orders are too small for impact to matter; execution optimisation solves a problem it does not have. |
| Implemented in volatility-ai | Schedules and execution agents are research code (`execution`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK363, RK366, RK244 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Robust Scholarly Execution
Trajectory Planner Eng-385") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Plan order timing and slicing over a horizon to balance slippage,
impact, completion risk and liquidity. The robust version estimates its
inputs with outlier-resistant statistics, so a few extreme days do not
drive the result. I found no study of this method on this task.

## The CSV's description

Proposed robust approach to trade-execution optimization: Plan order
timing and slicing over an execution horizon to balance expected
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
* Robust estimators trade efficiency for stability; in calm data they
  add little.

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
| 2523 | Robust Scholarly Execution Trajectory Planner Eng-385 | Rough path theory / Tensor signatures / Stock trend forecasting | 7127 | 4518 | No |
| 2578 | Robust Scholarly Execution Trajectory Planner Eng-865 | Rough path theory / Tensor signatures / Stock trend forecasting | 7169 | 4611 | No |
| 2633 | Robust Scholarly Execution Trajectory Planner Eng-1345 | Rough path theory / Tensor signatures / Stock trend forecasting | 7211 | 4704 | No |
| 2688 | Robust Scholarly Execution Trajectory Planner Eng-1825 | Rough path theory / Tensor signatures / Stock trend forecasting | 7253 | 4797 | No |
| 2743 | Robust Scholarly Execution Trajectory Planner Eng-2305 | Rough path theory / Tensor signatures / Stock trend forecasting | 7295 | 4890 | No |
| 2798 | Robust Scholarly Execution Trajectory Planner Eng-2785 | Rough path theory / Tensor signatures / Stock trend forecasting | 7337 | 4983 | No |
| 2853 | Robust Scholarly Execution Trajectory Planner Eng-3265 | Rough path theory / Tensor signatures / Stock trend forecasting | 7379 | 5076 | No |
| 2908 | Robust Scholarly Execution Trajectory Planner Eng-3745 | Rough path theory / Tensor signatures / Stock trend forecasting | 7421 | 5169 | No |
| 2963 | Robust Scholarly Execution Trajectory Planner Eng-4225 | Rough path theory / Tensor signatures / Stock trend forecasting | 7463 | 5262 | No |
| 3018 | Robust Scholarly Execution Trajectory Planner Eng-4705 | Rough path theory / Tensor signatures / Stock trend forecasting | 7505 | 5355 | No |
| 3073 | Robust Scholarly Execution Trajectory Planner Eng-5185 | Rough path theory / Tensor signatures / Stock trend forecasting | 7547 | 5448 | No |
| 3128 | Robust Scholarly Execution Trajectory Planner Eng-5665 | Rough path theory / Tensor signatures / Stock trend forecasting | 7589 | 5541 | No |
| 6838 | Robust Scholarly Execution Trajectory Planner Eng-97 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10214 | 11498 | No |
| 6884 | Robust Scholarly Execution Trajectory Planner Eng-577 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10227 | 11512 | No |
| 6930 | Robust Scholarly Execution Trajectory Planner Eng-1057 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10240 | 11526 | No |
| 6976 | Robust Scholarly Execution Trajectory Planner Eng-1537 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10253 | 11540 | No |
| 7022 | Robust Scholarly Execution Trajectory Planner Eng-2017 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10266 | 11554 | No |
| 7068 | Robust Scholarly Execution Trajectory Planner Eng-2497 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10279 | 11568 | No |
| 7114 | Robust Scholarly Execution Trajectory Planner Eng-2977 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10292 | 11582 | No |
| 7160 | Robust Scholarly Execution Trajectory Planner Eng-3457 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10305 | 11596 | No |
| 7206 | Robust Scholarly Execution Trajectory Planner Eng-3937 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10318 | 11610 | No |
| 7252 | Robust Scholarly Execution Trajectory Planner Eng-4417 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10331 | 11624 | No |
| 7298 | Robust Scholarly Execution Trajectory Planner Eng-4897 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10344 | 11638 | No |
| 7344 | Robust Scholarly Execution Trajectory Planner Eng-5377 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10357 | 11652 | No |
| 7390 | Robust Scholarly Execution Trajectory Planner Eng-5857 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10370 | 11666 | No |
| 7412 | Robust Scholarly Execution Trajectory Optimizer Ver-29 | Geometric deep learning / Riemannian optimization / Stock risk parity | 6445 | 8386 | No |
| 7422 | Robust Scholarly Execution Trajectory Optimizer Ver-129 | Geometric deep learning / Riemannian optimization / Stock risk parity | 6454 | 2879 | No |
| 7937 | Robust Scholarly Execution Trajectory Planner Eng-289 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8827 | 4501 | No |
| 7971 | Robust Scholarly Execution Trajectory Planner Eng-769 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8863 | 4594 | No |
| 8005 | Robust Scholarly Execution Trajectory Planner Eng-1249 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8899 | 4687 | No |
| 8039 | Robust Scholarly Execution Trajectory Planner Eng-1729 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8935 | 4780 | No |
| 8073 | Robust Scholarly Execution Trajectory Planner Eng-2209 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8971 | 4873 | No |
| 8107 | Robust Scholarly Execution Trajectory Planner Eng-2689 | Geometric deep learning / Riemannian metrics / Stock risk parity | 9007 | 4966 | No |
| 8141 | Robust Scholarly Execution Trajectory Planner Eng-3169 | Geometric deep learning / Riemannian metrics / Stock risk parity | 9043 | 5059 | No |
| 8175 | Robust Scholarly Execution Trajectory Planner Eng-3649 | Geometric deep learning / Riemannian metrics / Stock risk parity | 9079 | 5152 | No |
| 8209 | Robust Scholarly Execution Trajectory Planner Eng-4129 | Geometric deep learning / Riemannian metrics / Stock risk parity | 9115 | 5245 | No |
| 8243 | Robust Scholarly Execution Trajectory Planner Eng-4609 | Geometric deep learning / Riemannian metrics / Stock risk parity | 9151 | 5338 | No |
| 8277 | Robust Scholarly Execution Trajectory Planner Eng-5089 | Geometric deep learning / Riemannian metrics / Stock risk parity | 9187 | 5431 | No |
| 8311 | Robust Scholarly Execution Trajectory Planner Eng-5569 | Geometric deep learning / Riemannian metrics / Stock risk parity | 9223 | 5524 | No |
| 11441 | Robust Scholarly Execution Trajectory Planner Eng-1 | Graph attention / Sector contagion / Stock baskets | 836 | 1381 | No |
| 11632 | Robust Scholarly Execution Trajectory Planner Eng-481 | Graph attention / Sector contagion / Stock baskets | 848 | 1407 | No |
| 11823 | Robust Scholarly Execution Trajectory Planner Eng-961 | Graph attention / Sector contagion / Stock baskets | 860 | 1433 | No |
| 12014 | Robust Scholarly Execution Trajectory Planner Eng-1441 | Graph attention / Sector contagion / Stock baskets | 872 | 1459 | No |
| 12205 | Robust Scholarly Execution Trajectory Planner Eng-1921 | Graph attention / Sector contagion / Stock baskets | 884 | 1485 | No |
| 12396 | Robust Scholarly Execution Trajectory Planner Eng-2401 | Graph attention / Sector contagion / Stock baskets | 896 | 1511 | No |
| 12587 | Robust Scholarly Execution Trajectory Planner Eng-2881 | Graph attention / Sector contagion / Stock baskets | 908 | 1537 | No |
| 12778 | Robust Scholarly Execution Trajectory Planner Eng-3361 | Graph attention / Sector contagion / Stock baskets | 920 | 1563 | No |
| 12969 | Robust Scholarly Execution Trajectory Planner Eng-3841 | Graph attention / Sector contagion / Stock baskets | 932 | 1589 | No |
| 13160 | Robust Scholarly Execution Trajectory Planner Eng-4321 | Graph attention / Sector contagion / Stock baskets | 944 | 1615 | No |
| 13351 | Robust Scholarly Execution Trajectory Planner Eng-4801 | Graph attention / Sector contagion / Stock baskets | 956 | 1641 | No |
| 13542 | Robust Scholarly Execution Trajectory Planner Eng-5281 | Graph attention / Sector contagion / Stock baskets | 968 | 1667 | No |
| 13733 | Robust Scholarly Execution Trajectory Planner Eng-5761 | Graph attention / Sector contagion / Stock baskets | 980 | 1693 | No |
| 14092 | Robust Scholarly Execution Trajectory Planner Eng-193 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7960 | 6219 | No |
| 14103 | Robust Scholarly Execution Trajectory Planner Eng-673 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7977 | 6240 | No |
| 14114 | Robust Scholarly Execution Trajectory Planner Eng-1153 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7994 | 6261 | No |
| 14125 | Robust Scholarly Execution Trajectory Planner Eng-1633 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8011 | 6282 | No |
| 14136 | Robust Scholarly Execution Trajectory Planner Eng-2113 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8028 | 6303 | No |
| 14147 | Robust Scholarly Execution Trajectory Planner Eng-2593 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8045 | 6324 | No |
| 14158 | Robust Scholarly Execution Trajectory Planner Eng-3073 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8062 | 6345 | No |
| 14169 | Robust Scholarly Execution Trajectory Planner Eng-3553 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8079 | 6366 | No |
| 14180 | Robust Scholarly Execution Trajectory Planner Eng-4033 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8096 | 6387 | No |
| 14191 | Robust Scholarly Execution Trajectory Planner Eng-4513 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8113 | 6408 | No |
| 14202 | Robust Scholarly Execution Trajectory Planner Eng-4993 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8130 | 6429 | No |
| 14213 | Robust Scholarly Execution Trajectory Planner Eng-5473 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8147 | 6450 | No |
| 14224 | Robust Scholarly Execution Trajectory Planner Eng-5953 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8164 | 6471 | No |
