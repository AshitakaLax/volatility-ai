# Topology-aware approach to delay-aware portfolio allocation

**Concept page** · shared by **5** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #8,488) ·
researched 2026-10-30

| | |
|---|---|
| Task | Delay-aware portfolio allocation |
| Method | Topological data analysis (persistent homology) |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of topological data analysis improving allocation through lagged dynamics, and the book trades one symbol. |
| Implemented in volatility-ai | Nothing; the closest is the top-K dropout turnover rule (RK216). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK216, RK366 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Topological Scholarly Delay
Differential Allocator Alpha-33") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Model delayed or lagged relationships in market variables and use the
estimated dynamics to adjust portfolio weights. The topology-aware
version derives persistent-homology features (Betti numbers, persistence
landscapes) from sliding windows of returns. I found no study of this
method on this task.

## The CSV's description

Proposed topology-aware approach to delay-aware portfolio allocation:
Model delayed or lagged relationships in market variables and use the
estimated dynamics to adjust portfolio weights; the state equations and
decision rules require specification. This is a concept-level
interpretation of the title, not a complete trading specification: the
exact model inputs/target, calibration, entry/exit or rebalance rules,
and position sizing are not fully defined here.

## Evidence

* **Gârleanu & Pedersen (2013), "Dynamic Trading with Predictable
  Returns and Transaction Costs," *Journal of Finance* 68(6),
  2309–2340:** with costs, aim in front of the target and trade only
  partway toward the aim; slower-decaying signals get more weight. Net
  of costs it beat naive rules on commodity futures. (Abstract.)

## Against, and failure modes

* The title's delay-differential dynamics are unspecified; lagged
  relations between liquid ETFs are small and quickly arbitraged.
* The best-known topological crash study is in sample (Gidea & Katz
  2018), and the features depend on window and scale choices.

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
| 8488 | Topological Scholarly Delay Differential Allocator Alpha-33 | Quantum computing / QAOA combinatorial / Stock index rebalancing | 7764 | 7572 | No |
| 8528 | Topological Scholarly Delay Differential Allocator Alpha-133 | Quantum computing / QAOA combinatorial / Stock index rebalancing | 7767 | 5945 | No |
| 8568 | Topological Scholarly Delay Differential Allocator Alpha-233 | Quantum computing / QAOA combinatorial / Stock index rebalancing | 13756 | 12787 | No |
| 8608 | Topological Scholarly Delay Differential Allocator Alpha-333 | Quantum computing / QAOA combinatorial / Stock index rebalancing | 7774 | 7581 | No |
| 8648 | Topological Scholarly Delay Differential Allocator Alpha-433 | Quantum computing / QAOA combinatorial / Stock index rebalancing | 7777 | 5958 | No |
