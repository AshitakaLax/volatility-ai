# Evolutionary-optimization-based approach to sector allocation

**Concept page** · shared by **10** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,200) ·
researched 2026-10-30

| | |
|---|---|
| Task | Sector allocation |
| Method | Evolutionary / genetic optimisation |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of a genetic search improving sector allocation; industry momentum (RK19, X3) is the documented signal. |
| Implemented in volatility-ai | `tools/rotation.py --mode relative_strength` (X3) rotates across a small ETF universe, including sector momentum (RK19), with an HRP mode (A5). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | X3, RK19, RK3, RK7, A5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Evolutionary Scholarly
Sector Allocation Strategy Ref-165") combine a method word, "Scholarly",
a task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Compare sector-level return, trend or risk signals and periodically
re-weight among sector funds, controlling concentration and turnover.
The evolutionary version searches parameters or weights with genetic
algorithms. I found no study of this method on this task.

## The CSV's description

Proposed evolutionary-optimization-based approach to sector allocation:
Compare sector-level return, trend, or risk signals and periodically
adjust weights among sector funds; concentration and turnover need to be
controlled. This is a concept-level interpretation of the title, not a
complete trading specification: the exact model inputs/target,
calibration, entry/exit or rebalance rules, and position sizing are not
fully defined here.

## Evidence

* **Moskowitz & Grinblatt (1999), "Do Industries Explain Momentum?"
  *Journal of Finance* 54(4), 1249–1290:** industry momentum is highly
  profitable after controls and accounts for much of stock momentum.
  (Abstract.)

## Against, and failure modes

* Sector rotation adds turnover and taxes; the long-only half keeps only
  part of the long-short industry-momentum premium.
* A genetic search over a backtest is a large multiple-testing exercise
  that finds the noise that fits best.

## Fit with volatility-ai

Built as X3 (relative-strength rotation across a small ETF universe) and
RK19 (sector momentum), neither yet measured. A sector sleeve would sit
beside the grid, not inside it.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Moskowitz, T. J., Grinblatt, M. (1999). *Journal of Finance* 54(4),
  1249–1290. Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 1200 | Evolutionary Scholarly Sector Allocation Strategy Ref-165 | Rough path theory / Tensor signatures / Stock trend forecasting | 5604 | 2157 | No |
| 1211 | Evolutionary Scholarly Sector Allocation Strategy Ref-645 | Rough path theory / Tensor signatures / Stock trend forecasting | 5612 | 2182 | No |
| 3188 | Evolutionary Scholarly Sector Allocation Strategy Ref-357 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 406 | 1852 | No |
| 3204 | Evolutionary Scholarly Sector Allocation Strategy Ref-837 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 418 | 1864 | No |
| 3781 | Evolutionary Scholarly Sector Allocation Strategy Ref-69 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6495 | 3027 | No |
| 3867 | Evolutionary Scholarly Sector Allocation Strategy Ref-549 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6538 | 3144 | No |
| 7470 | Evolutionary Scholarly Sector Allocation Strategy Ref-261 | Graph attention / Sector contagion / Stock baskets | 711 | 1026 | No |
| 7504 | Evolutionary Scholarly Sector Allocation Strategy Ref-741 | Graph attention / Sector contagion / Stock baskets | 727 | 1061 | No |
| 8853 | Evolutionary Scholarly Sector Allocation Strategy Ref-453 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7796 | 7609 | No |
| 9044 | Evolutionary Scholarly Sector Allocation Strategy Ref-933 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7813 | 7633 | No |
