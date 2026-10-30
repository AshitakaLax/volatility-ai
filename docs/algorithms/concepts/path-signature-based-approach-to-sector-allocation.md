# Path-signature-based approach to sector allocation

**Concept page** · shared by **15** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,203) ·
researched 2026-10-30

| | |
|---|---|
| Task | Sector allocation |
| Method | Path signatures |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of path signatures improving sector allocation; industry momentum (RK19, X3) is the documented signal. |
| Implemented in volatility-ai | `tools/rotation.py --mode relative_strength` (X3) rotates across a small ETF universe, including sector momentum (RK19), with an HRP mode (A5). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | X3, RK19, RK3, RK7, A5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Signature Scholarly Sector
Allocation Strategy Ref-285") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Compare sector-level return, trend or risk signals and periodically
re-weight among sector funds, controlling concentration and turnover.
The path-signature version describes price paths by their
iterated-integral signatures and fits on those features. I found no
study of this method on this task.

## The CSV's description

Proposed path-signature-based approach to sector allocation: Compare
sector-level return, trend, or risk signals and periodically adjust
weights among sector funds; concentration and turnover need to be
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
* Signature features multiply with depth and dimension; no out-of-sample
  trading evidence found (RK328).

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
| 1203 | Signature Scholarly Sector Allocation Strategy Ref-285 | Rough path theory / Tensor signatures / Stock trend forecasting | 5606 | 2163 | No |
| 1214 | Signature Scholarly Sector Allocation Strategy Ref-765 | Rough path theory / Tensor signatures / Stock trend forecasting | 5614 | 2188 | No |
| 3192 | Signature Scholarly Sector Allocation Strategy Ref-477 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 408 | 1855 | No |
| 3208 | Signature Scholarly Sector Allocation Strategy Ref-957 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 420 | 1867 | No |
| 3801 | Signature Scholarly Sector Allocation Strategy Ref-189 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6505 | 3057 | No |
| 3887 | Signature Scholarly Sector Allocation Strategy Ref-669 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6548 | 3174 | No |
| 7478 | Signature Scholarly Sector Allocation Strategy Ref-381 | Graph attention / Sector contagion / Stock baskets | 715 | 1035 | No |
| 7512 | Signature Scholarly Sector Allocation Strategy Ref-861 | Graph attention / Sector contagion / Stock baskets | 731 | 1070 | No |
| 8499 | Signature Scholarly Sector Allocation Strategy Alpha-61 | Graph neural networks / Sector contagion / Equity baskets | 4605 | 2909 | No |
| 8539 | Signature Scholarly Sector Allocation Strategy Alpha-161 | Graph neural networks / Sector contagion / Equity baskets | 13468 | 13698 | No |
| 8579 | Signature Scholarly Sector Allocation Strategy Alpha-261 | Graph neural networks / Sector contagion / Equity baskets | 4622 | 2956 | No |
| 8619 | Signature Scholarly Sector Allocation Strategy Alpha-361 | Graph neural networks / Sector contagion / Equity baskets | 4633 | 2977 | No |
| 8659 | Signature Scholarly Sector Allocation Strategy Alpha-461 | Graph neural networks / Sector contagion / Equity baskets | 13474 | 13709 | No |
| 8712 | Signature Scholarly Sector Allocation Strategy Ref-93 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7783 | 7591 | No |
| 8903 | Signature Scholarly Sector Allocation Strategy Ref-573 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7800 | 7615 | No |
