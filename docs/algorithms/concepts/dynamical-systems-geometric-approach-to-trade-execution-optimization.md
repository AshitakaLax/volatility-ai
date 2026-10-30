# Dynamical-systems/geometric approach to trade-execution optimization

**Concept page** · shared by **62** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #2,509) ·
researched 2026-10-30

| | |
|---|---|
| Task | Trade-execution optimisation |
| Method | Dynamical-systems / geometric (e.g. Hamiltonian) models |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** The book's orders are too small for impact to matter; execution optimisation solves a problem it does not have. |
| Implemented in volatility-ai | Schedules and execution agents are research code (`execution`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK363, RK366, RK244 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Hamiltonian Scholarly
Execution Trajectory Planner Eng-265") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Plan order timing and slicing over a horizon to balance slippage,
impact, completion risk and liquidity. The dynamical-systems version
models the market as a Hamiltonian or delay-differential system and acts
on its fitted state. I found no study of this method on this task.

## The CSV's description

Proposed dynamical-systems/geometric approach to trade-execution
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
* The physics is imposed, not estimated from evidence; no trading study
  found.

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
| 2509 | Hamiltonian Scholarly Execution Trajectory Planner Eng-265 | Rough path theory / Tensor signatures / Stock trend forecasting | 7116 | 4493 | No |
| 2564 | Hamiltonian Scholarly Execution Trajectory Planner Eng-745 | Rough path theory / Tensor signatures / Stock trend forecasting | 7158 | 4586 | No |
| 2619 | Hamiltonian Scholarly Execution Trajectory Planner Eng-1225 | Rough path theory / Tensor signatures / Stock trend forecasting | 7200 | 4679 | No |
| 2674 | Hamiltonian Scholarly Execution Trajectory Planner Eng-1705 | Rough path theory / Tensor signatures / Stock trend forecasting | 7242 | 4772 | No |
| 2729 | Hamiltonian Scholarly Execution Trajectory Planner Eng-2185 | Rough path theory / Tensor signatures / Stock trend forecasting | 7284 | 4865 | No |
| 2784 | Hamiltonian Scholarly Execution Trajectory Planner Eng-2665 | Rough path theory / Tensor signatures / Stock trend forecasting | 7326 | 4958 | No |
| 2839 | Hamiltonian Scholarly Execution Trajectory Planner Eng-3145 | Rough path theory / Tensor signatures / Stock trend forecasting | 7368 | 5051 | No |
| 2894 | Hamiltonian Scholarly Execution Trajectory Planner Eng-3625 | Rough path theory / Tensor signatures / Stock trend forecasting | 7410 | 5144 | No |
| 2949 | Hamiltonian Scholarly Execution Trajectory Planner Eng-4105 | Rough path theory / Tensor signatures / Stock trend forecasting | 7452 | 5237 | No |
| 3004 | Hamiltonian Scholarly Execution Trajectory Planner Eng-4585 | Rough path theory / Tensor signatures / Stock trend forecasting | 7494 | 5330 | No |
| 3059 | Hamiltonian Scholarly Execution Trajectory Planner Eng-5065 | Rough path theory / Tensor signatures / Stock trend forecasting | 7536 | 5423 | No |
| 3114 | Hamiltonian Scholarly Execution Trajectory Planner Eng-5545 | Rough path theory / Tensor signatures / Stock trend forecasting | 7578 | 5516 | No |
| 6871 | Hamiltonian Scholarly Execution Trajectory Planner Eng-457 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10224 | 11509 | No |
| 6917 | Hamiltonian Scholarly Execution Trajectory Planner Eng-937 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10237 | 11523 | No |
| 6963 | Hamiltonian Scholarly Execution Trajectory Planner Eng-1417 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10250 | 11537 | No |
| 7009 | Hamiltonian Scholarly Execution Trajectory Planner Eng-1897 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10263 | 11551 | No |
| 7055 | Hamiltonian Scholarly Execution Trajectory Planner Eng-2377 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10276 | 11565 | No |
| 7101 | Hamiltonian Scholarly Execution Trajectory Planner Eng-2857 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10289 | 11579 | No |
| 7147 | Hamiltonian Scholarly Execution Trajectory Planner Eng-3337 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10302 | 11593 | No |
| 7193 | Hamiltonian Scholarly Execution Trajectory Planner Eng-3817 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10315 | 11607 | No |
| 7239 | Hamiltonian Scholarly Execution Trajectory Planner Eng-4297 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10328 | 11621 | No |
| 7285 | Hamiltonian Scholarly Execution Trajectory Planner Eng-4777 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10341 | 11635 | No |
| 7331 | Hamiltonian Scholarly Execution Trajectory Planner Eng-5257 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10354 | 11649 | No |
| 7377 | Hamiltonian Scholarly Execution Trajectory Planner Eng-5737 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10367 | 11663 | No |
| 7927 | Hamiltonian Scholarly Execution Trajectory Planner Eng-169 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8818 | 4478 | No |
| 7961 | Hamiltonian Scholarly Execution Trajectory Planner Eng-649 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8854 | 4571 | No |
| 7995 | Hamiltonian Scholarly Execution Trajectory Planner Eng-1129 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8890 | 4664 | No |
| 8029 | Hamiltonian Scholarly Execution Trajectory Planner Eng-1609 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8926 | 4757 | No |
| 8063 | Hamiltonian Scholarly Execution Trajectory Planner Eng-2089 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8962 | 4850 | No |
| 8097 | Hamiltonian Scholarly Execution Trajectory Planner Eng-2569 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8998 | 4943 | No |
| 8131 | Hamiltonian Scholarly Execution Trajectory Planner Eng-3049 | Geometric deep learning / Riemannian metrics / Stock risk parity | 9034 | 5036 | No |
| 8165 | Hamiltonian Scholarly Execution Trajectory Planner Eng-3529 | Geometric deep learning / Riemannian metrics / Stock risk parity | 9070 | 5129 | No |
| 8199 | Hamiltonian Scholarly Execution Trajectory Planner Eng-4009 | Geometric deep learning / Riemannian metrics / Stock risk parity | 9106 | 5222 | No |
| 8233 | Hamiltonian Scholarly Execution Trajectory Planner Eng-4489 | Geometric deep learning / Riemannian metrics / Stock risk parity | 9142 | 5315 | No |
| 8267 | Hamiltonian Scholarly Execution Trajectory Planner Eng-4969 | Geometric deep learning / Riemannian metrics / Stock risk parity | 9178 | 5408 | No |
| 8301 | Hamiltonian Scholarly Execution Trajectory Planner Eng-5449 | Geometric deep learning / Riemannian metrics / Stock risk parity | 9214 | 5501 | No |
| 8335 | Hamiltonian Scholarly Execution Trajectory Planner Eng-5929 | Geometric deep learning / Riemannian metrics / Stock risk parity | 9250 | 5594 | No |
| 11583 | Hamiltonian Scholarly Execution Trajectory Planner Eng-361 | Graph attention / Sector contagion / Stock baskets | 845 | 1401 | No |
| 11774 | Hamiltonian Scholarly Execution Trajectory Planner Eng-841 | Graph attention / Sector contagion / Stock baskets | 857 | 1427 | No |
| 11965 | Hamiltonian Scholarly Execution Trajectory Planner Eng-1321 | Graph attention / Sector contagion / Stock baskets | 869 | 1453 | No |
| 12156 | Hamiltonian Scholarly Execution Trajectory Planner Eng-1801 | Graph attention / Sector contagion / Stock baskets | 881 | 1479 | No |
| 12347 | Hamiltonian Scholarly Execution Trajectory Planner Eng-2281 | Graph attention / Sector contagion / Stock baskets | 893 | 1505 | No |
| 12538 | Hamiltonian Scholarly Execution Trajectory Planner Eng-2761 | Graph attention / Sector contagion / Stock baskets | 905 | 1531 | No |
| 12729 | Hamiltonian Scholarly Execution Trajectory Planner Eng-3241 | Graph attention / Sector contagion / Stock baskets | 917 | 1557 | No |
| 12920 | Hamiltonian Scholarly Execution Trajectory Planner Eng-3721 | Graph attention / Sector contagion / Stock baskets | 929 | 1583 | No |
| 13111 | Hamiltonian Scholarly Execution Trajectory Planner Eng-4201 | Graph attention / Sector contagion / Stock baskets | 941 | 1609 | No |
| 13302 | Hamiltonian Scholarly Execution Trajectory Planner Eng-4681 | Graph attention / Sector contagion / Stock baskets | 953 | 1635 | No |
| 13493 | Hamiltonian Scholarly Execution Trajectory Planner Eng-5161 | Graph attention / Sector contagion / Stock baskets | 965 | 1661 | No |
| 13684 | Hamiltonian Scholarly Execution Trajectory Planner Eng-5641 | Graph attention / Sector contagion / Stock baskets | 977 | 1687 | No |
| 14090 | Hamiltonian Scholarly Execution Trajectory Planner Eng-73 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7955 | 6214 | No |
| 14101 | Hamiltonian Scholarly Execution Trajectory Planner Eng-553 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7972 | 6235 | No |
| 14112 | Hamiltonian Scholarly Execution Trajectory Planner Eng-1033 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7989 | 6256 | No |
| 14123 | Hamiltonian Scholarly Execution Trajectory Planner Eng-1513 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8006 | 6277 | No |
| 14134 | Hamiltonian Scholarly Execution Trajectory Planner Eng-1993 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8023 | 6298 | No |
| 14145 | Hamiltonian Scholarly Execution Trajectory Planner Eng-2473 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8040 | 6319 | No |
| 14156 | Hamiltonian Scholarly Execution Trajectory Planner Eng-2953 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8057 | 6340 | No |
| 14167 | Hamiltonian Scholarly Execution Trajectory Planner Eng-3433 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8074 | 6361 | No |
| 14178 | Hamiltonian Scholarly Execution Trajectory Planner Eng-3913 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8091 | 6382 | No |
| 14189 | Hamiltonian Scholarly Execution Trajectory Planner Eng-4393 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8108 | 6403 | No |
| 14200 | Hamiltonian Scholarly Execution Trajectory Planner Eng-4873 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8125 | 6424 | No |
| 14211 | Hamiltonian Scholarly Execution Trajectory Planner Eng-5353 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8142 | 6445 | No |
| 14222 | Hamiltonian Scholarly Execution Trajectory Planner Eng-5833 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 8159 | 6466 | No |
