# Koopman-operator-based approach to trade-execution optimization

**Concept page** · shared by **62** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #5,048) ·
researched 2026-10-30

| | |
|---|---|
| Task | Trade-execution optimisation |
| Method | Koopman operators (DMD / EDMD) |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** The book's orders are too small for impact to matter; execution optimisation solves a problem it does not have. |
| Implemented in volatility-ai | Schedules and execution agents are research code (`execution`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK363, RK366, RK244 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Koopman Scholarly Execution
Trajectory Planner Eng-145") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Plan order timing and slicing over a horizon to balance slippage,
impact, completion risk and liquidity. The Koopman version linearises
the dynamics in a lifted feature space and forecasts with the linear
operator. I found no study of this method on this task.

## The CSV's description

Proposed Koopman-operator-based approach to trade-execution
optimization: Plan order timing and slicing over an execution horizon to
balance expected slippage, market impact, completion risk, and
liquidity. This is a concept-level interpretation of the title, not a
complete trading specification: the exact model inputs/target,
calibration, entry/exit or rebalance rules, and position sizing are not
fully defined here.

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
* The Koopman entries in the list have no peer-reviewed trading evidence
  (RK206).

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
| 5048 | Koopman Scholarly Execution Trajectory Planner Eng-145 | Rough path theory / Tensor signatures / Stock trend forecasting | 7105 | 4470 | No |
| 5134 | Koopman Scholarly Execution Trajectory Planner Eng-625 | Rough path theory / Tensor signatures / Stock trend forecasting | 7147 | 4563 | No |
| 5220 | Koopman Scholarly Execution Trajectory Planner Eng-1105 | Rough path theory / Tensor signatures / Stock trend forecasting | 7189 | 4656 | No |
| 5306 | Koopman Scholarly Execution Trajectory Planner Eng-1585 | Rough path theory / Tensor signatures / Stock trend forecasting | 7231 | 4749 | No |
| 5392 | Koopman Scholarly Execution Trajectory Planner Eng-2065 | Rough path theory / Tensor signatures / Stock trend forecasting | 7273 | 4842 | No |
| 5478 | Koopman Scholarly Execution Trajectory Planner Eng-2545 | Rough path theory / Tensor signatures / Stock trend forecasting | 7315 | 4935 | No |
| 5564 | Koopman Scholarly Execution Trajectory Planner Eng-3025 | Rough path theory / Tensor signatures / Stock trend forecasting | 7357 | 5028 | No |
| 5650 | Koopman Scholarly Execution Trajectory Planner Eng-3505 | Rough path theory / Tensor signatures / Stock trend forecasting | 7399 | 5121 | No |
| 5736 | Koopman Scholarly Execution Trajectory Planner Eng-3985 | Rough path theory / Tensor signatures / Stock trend forecasting | 7441 | 5214 | No |
| 5822 | Koopman Scholarly Execution Trajectory Planner Eng-4465 | Rough path theory / Tensor signatures / Stock trend forecasting | 7483 | 5307 | No |
| 5908 | Koopman Scholarly Execution Trajectory Planner Eng-4945 | Rough path theory / Tensor signatures / Stock trend forecasting | 7525 | 5400 | No |
| 5994 | Koopman Scholarly Execution Trajectory Planner Eng-5425 | Rough path theory / Tensor signatures / Stock trend forecasting | 7567 | 5493 | No |
| 6080 | Koopman Scholarly Execution Trajectory Planner Eng-5905 | Rough path theory / Tensor signatures / Stock trend forecasting | 7609 | 5586 | No |
| 7920 | Koopman Scholarly Execution Trajectory Planner Eng-49 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8808 | 4454 | No |
| 7954 | Koopman Scholarly Execution Trajectory Planner Eng-529 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8844 | 4547 | No |
| 7988 | Koopman Scholarly Execution Trajectory Planner Eng-1009 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8880 | 4640 | No |
| 8022 | Koopman Scholarly Execution Trajectory Planner Eng-1489 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8916 | 4733 | No |
| 8056 | Koopman Scholarly Execution Trajectory Planner Eng-1969 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8952 | 4826 | No |
| 8090 | Koopman Scholarly Execution Trajectory Planner Eng-2449 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8988 | 4919 | No |
| 8124 | Koopman Scholarly Execution Trajectory Planner Eng-2929 | Geometric deep learning / Riemannian metrics / Stock risk parity | 9024 | 5012 | No |
| 8158 | Koopman Scholarly Execution Trajectory Planner Eng-3409 | Geometric deep learning / Riemannian metrics / Stock risk parity | 9060 | 5105 | No |
| 8192 | Koopman Scholarly Execution Trajectory Planner Eng-3889 | Geometric deep learning / Riemannian metrics / Stock risk parity | 9096 | 5198 | No |
| 8226 | Koopman Scholarly Execution Trajectory Planner Eng-4369 | Geometric deep learning / Riemannian metrics / Stock risk parity | 9132 | 5291 | No |
| 8260 | Koopman Scholarly Execution Trajectory Planner Eng-4849 | Geometric deep learning / Riemannian metrics / Stock risk parity | 9168 | 5384 | No |
| 8294 | Koopman Scholarly Execution Trajectory Planner Eng-5329 | Geometric deep learning / Riemannian metrics / Stock risk parity | 9204 | 5477 | No |
| 8328 | Koopman Scholarly Execution Trajectory Planner Eng-5809 | Geometric deep learning / Riemannian metrics / Stock risk parity | 9240 | 5570 | No |
| 8363 | Koopman Scholarly Execution Trajectory Planner Eng-337 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10220 | 11505 | No |
| 8365 | Koopman Scholarly Execution Trajectory Planner Eng-817 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10233 | 11519 | No |
| 8367 | Koopman Scholarly Execution Trajectory Planner Eng-1297 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10246 | 11533 | No |
| 8369 | Koopman Scholarly Execution Trajectory Planner Eng-1777 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10259 | 11547 | No |
| 8371 | Koopman Scholarly Execution Trajectory Planner Eng-2257 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10272 | 11561 | No |
| 8373 | Koopman Scholarly Execution Trajectory Planner Eng-2737 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10285 | 11575 | No |
| 8375 | Koopman Scholarly Execution Trajectory Planner Eng-3217 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10298 | 11589 | No |
| 8377 | Koopman Scholarly Execution Trajectory Planner Eng-3697 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10311 | 11603 | No |
| 8379 | Koopman Scholarly Execution Trajectory Planner Eng-4177 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10324 | 11617 | No |
| 8381 | Koopman Scholarly Execution Trajectory Planner Eng-4657 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10337 | 11631 | No |
| 8383 | Koopman Scholarly Execution Trajectory Planner Eng-5137 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10350 | 11645 | No |
| 8385 | Koopman Scholarly Execution Trajectory Planner Eng-5617 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10363 | 11659 | No |
| 14094 | Koopman Scholarly Execution Trajectory Planner Eng-241 | Graph attention / Sector contagion / Stock baskets | 842 | 1395 | No |
| 14098 | Koopman Scholarly Execution Trajectory Planner Eng-433 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7968 | 6229 | No |
| 14105 | Koopman Scholarly Execution Trajectory Planner Eng-721 | Graph attention / Sector contagion / Stock baskets | 854 | 1421 | No |
| 14109 | Koopman Scholarly Execution Trajectory Planner Eng-913 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7985 | 6250 | No |
| 14116 | Koopman Scholarly Execution Trajectory Planner Eng-1201 | Graph attention / Sector contagion / Stock baskets | 866 | 1447 | No |
| 14120 | Koopman Scholarly Execution Trajectory Planner Eng-1393 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8002 | 6271 | No |
| 14127 | Koopman Scholarly Execution Trajectory Planner Eng-1681 | Graph attention / Sector contagion / Stock baskets | 878 | 1473 | No |
| 14131 | Koopman Scholarly Execution Trajectory Planner Eng-1873 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8019 | 6292 | No |
| 14138 | Koopman Scholarly Execution Trajectory Planner Eng-2161 | Graph attention / Sector contagion / Stock baskets | 890 | 1499 | No |
| 14142 | Koopman Scholarly Execution Trajectory Planner Eng-2353 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8036 | 6313 | No |
| 14149 | Koopman Scholarly Execution Trajectory Planner Eng-2641 | Graph attention / Sector contagion / Stock baskets | 902 | 1525 | No |
| 14153 | Koopman Scholarly Execution Trajectory Planner Eng-2833 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8053 | 6334 | No |
| 14160 | Koopman Scholarly Execution Trajectory Planner Eng-3121 | Graph attention / Sector contagion / Stock baskets | 914 | 1551 | No |
| 14164 | Koopman Scholarly Execution Trajectory Planner Eng-3313 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8070 | 6355 | No |
| 14171 | Koopman Scholarly Execution Trajectory Planner Eng-3601 | Graph attention / Sector contagion / Stock baskets | 926 | 1577 | No |
| 14175 | Koopman Scholarly Execution Trajectory Planner Eng-3793 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8087 | 6376 | No |
| 14182 | Koopman Scholarly Execution Trajectory Planner Eng-4081 | Graph attention / Sector contagion / Stock baskets | 938 | 1603 | No |
| 14186 | Koopman Scholarly Execution Trajectory Planner Eng-4273 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8104 | 6397 | No |
| 14193 | Koopman Scholarly Execution Trajectory Planner Eng-4561 | Graph attention / Sector contagion / Stock baskets | 950 | 1629 | No |
| 14197 | Koopman Scholarly Execution Trajectory Planner Eng-4753 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8121 | 6418 | No |
| 14204 | Koopman Scholarly Execution Trajectory Planner Eng-5041 | Graph attention / Sector contagion / Stock baskets | 962 | 1655 | No |
| 14208 | Koopman Scholarly Execution Trajectory Planner Eng-5233 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8138 | 6439 | No |
| 14215 | Koopman Scholarly Execution Trajectory Planner Eng-5521 | Graph attention / Sector contagion / Stock baskets | 974 | 1681 | No |
| 14219 | Koopman Scholarly Execution Trajectory Planner Eng-5713 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8155 | 6460 | No |
