# Neural-network-based approach to delay-aware portfolio allocation

**Concept page** · shared by **10** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,730) ·
researched 2026-10-30

| | |
|---|---|
| Task | Delay-aware portfolio allocation |
| Method | Neural networks |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of neural networks improving allocation through lagged dynamics, and the book trades one symbol. |
| Implemented in volatility-ai | Nothing; the closest is the top-K dropout turnover rule (RK216). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK216, RK366 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Neural Scholarly Delay
Differential Allocator Ref-85") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Model delayed or lagged relationships in market variables and use the
estimated dynamics to adjust portfolio weights. The neural-network
version fits a neural network to the task. I found no study of this
method on this task.

## The CSV's description

Proposed neural-network-based approach to delay-aware portfolio
allocation: Model delayed or lagged relationships in market variables
and use the estimated dynamics to adjust portfolio weights; the state
equations and decision rules require specification. This is a
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
* Neural forecasts on one index have not reliably beaten simple rules;
  an LSTM's stock picks were largely short-term reversal (Fischer &
  Krauss 2018, RK292).

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
| 1730 | Neural Scholarly Delay Differential Allocator Ref-85 | Rough path theory / Tensor signatures / Stock trend forecasting | 6497 | 3032 | No |
| 1785 | Neural Scholarly Delay Differential Allocator Ref-565 | Rough path theory / Tensor signatures / Stock trend forecasting | 6540 | 3149 | No |
| 3856 | Neural Scholarly Delay Differential Allocator Ref-469 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8274 | 3126 | No |
| 3942 | Neural Scholarly Delay Differential Allocator Ref-949 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8315 | 3243 | No |
| 6214 | Neural Scholarly Delay Differential Allocator Ref-277 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10051 | 11307 | No |
| 6260 | Neural Scholarly Delay Differential Allocator Ref-757 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10061 | 11328 | No |
| 8747 | Neural Scholarly Delay Differential Allocator Ref-181 | Graph attention / Sector contagion / Stock baskets | 708 | 1019 | No |
| 8824 | Neural Scholarly Delay Differential Allocator Ref-373 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7793 | 5977 | No |
| 8938 | Neural Scholarly Delay Differential Allocator Ref-661 | Graph attention / Sector contagion / Stock baskets | 724 | 1054 | No |
| 9015 | Neural Scholarly Delay Differential Allocator Ref-853 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7810 | 5997 | No |
