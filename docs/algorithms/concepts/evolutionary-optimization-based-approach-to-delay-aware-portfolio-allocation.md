# Evolutionary-optimization-based approach to delay-aware portfolio allocation

**Concept page** · shared by **16** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,204) ·
researched 2026-10-30

| | |
|---|---|
| Task | Delay-aware portfolio allocation |
| Method | Evolutionary / genetic optimisation |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of a genetic search improving allocation through lagged dynamics, and the book trades one symbol. |
| Implemented in volatility-ai | Nothing; the closest is the top-K dropout turnover rule (RK216). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK216, RK366 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Evolutionary Scholarly
Delay Differential Allocator Ref-325") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Model delayed or lagged relationships in market variables and use the
estimated dynamics to adjust portfolio weights. The evolutionary version
searches parameters or weights with genetic algorithms. I found no study
of this method on this task.

## The CSV's description

Proposed evolutionary-optimization-based approach to delay-aware
portfolio allocation: Model delayed or lagged relationships in market
variables and use the estimated dynamics to adjust portfolio weights;
the state equations and decision rules require specification. This is a
concept-level interpretation of the title, not a complete trading
specification: the exact model inputs/target, calibration, entry/exit or
rebalance rules, and position sizing are not fully defined here.

## Evidence

* **Gârleanu & Pedersen (2013), "Dynamic Trading with Predictable
  Returns and Transaction Costs," *Journal of Finance* 68(6),
  2309–2340:** with costs, aim in front of the target and trade only
  partway toward the aim; slower-decaying signals get more weight. Net
  of costs it beat naive rules on commodity futures. (Abstract.)

## Against, and failure modes

* The title's delay-differential dynamics are unspecified; lagged
  relations between liquid ETFs are small and quickly arbitraged.
* A genetic search over a backtest is a large multiple-testing exercise
  that finds the noise that fits best.

## Fit with volatility-ai

Trading partway toward a moving target matters for a multi-asset book
turned over at cost. The engine trades one symbol in lots, which is
already a form of partial trading.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Gârleanu, N., Pedersen, L. H. (2013). *Journal of Finance* 68(6),
  2309–2340. doi:10.1111/jofi.12080. Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 1204 | Evolutionary Scholarly Delay Differential Allocator Ref-325 | Rough path theory / Tensor signatures / Stock trend forecasting | 6518 | 3090 | No |
| 1215 | Evolutionary Scholarly Delay Differential Allocator Ref-805 | Rough path theory / Tensor signatures / Stock trend forecasting | 6561 | 3207 | No |
| 3177 | Evolutionary Scholarly Delay Differential Allocator Ref-37 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10046 | 11297 | No |
| 3193 | Evolutionary Scholarly Delay Differential Allocator Ref-517 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10056 | 11318 | No |
| 3209 | Evolutionary Scholarly Delay Differential Allocator Ref-997 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10066 | 11339 | No |
| 3811 | Evolutionary Scholarly Delay Differential Allocator Ref-229 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8253 | 3067 | No |
| 3897 | Evolutionary Scholarly Delay Differential Allocator Ref-709 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8294 | 3184 | No |
| 7482 | Evolutionary Scholarly Delay Differential Allocator Ref-421 | Graph attention / Sector contagion / Stock baskets | 716 | 1036 | No |
| 7516 | Evolutionary Scholarly Delay Differential Allocator Ref-901 | Graph attention / Sector contagion / Stock baskets | 732 | 1071 | No |
| 8513 | Evolutionary Scholarly Delay Differential Allocator Alpha-93 | Quantum computing / QAOA combinatorial / Stock index rebalancing | 7766 | 7573 | No |
| 8553 | Evolutionary Scholarly Delay Differential Allocator Alpha-193 | Quantum computing / QAOA combinatorial / Stock index rebalancing | 7769 | 5947 | No |
| 8593 | Evolutionary Scholarly Delay Differential Allocator Alpha-293 | Quantum computing / QAOA combinatorial / Stock index rebalancing | 13757 | 12788 | No |
| 8633 | Evolutionary Scholarly Delay Differential Allocator Alpha-393 | Quantum computing / QAOA combinatorial / Stock index rebalancing | 7776 | 7582 | No |
| 8673 | Evolutionary Scholarly Delay Differential Allocator Alpha-493 | Quantum computing / QAOA combinatorial / Stock index rebalancing | 7779 | 5960 | No |
| 8729 | Evolutionary Scholarly Delay Differential Allocator Ref-133 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7784 | 5967 | No |
| 8920 | Evolutionary Scholarly Delay Differential Allocator Ref-613 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7801 | 5987 | No |
