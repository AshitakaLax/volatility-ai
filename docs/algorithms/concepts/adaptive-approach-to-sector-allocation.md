# Adaptive approach to sector allocation

**Concept page** · shared by **2** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #3,658) ·
researched 2026-10-30

| | |
|---|---|
| Task | Sector allocation |
| Method | Adaptive (time-varying parameters or thresholds) |
| Fit with this project | ⏳ reference only · background, nothing to build now |
| Useful for volatility-ai | **Reference only.** An adaptive rule could weight a sector sleeve, but no study shows it beating plain sector momentum; background until X3 is measured. |
| Implemented in volatility-ai | `tools/rotation.py --mode relative_strength` (X3) rotates across a small ETF universe, including sector momentum (RK19), with an HRP mode (A5). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | X3, RK19, RK3, RK7, A5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Adaptive Scholarly Sector
ETF Allocator MK-29") combine a method word, "Scholarly", a task and a
serial number, and the rows' references are software libraries or papers
the CSV's own review calls unrelated. There is no specific algorithm
behind each name to research, so this page researches what the members
share: the task, done with the method.

## In one paragraph

Compare sector-level return, trend or risk signals and periodically
re-weight among sector funds, controlling concentration and turnover.
The adaptive version lets its parameters or thresholds move with recent
data. I found no study of this method on this task.

## The CSV's description

Proposed adaptive approach to sector allocation: Compare sector-level
return, trend, or risk signals and periodically adjust weights among
sector funds; concentration and turnover need to be controlled. This is
a concept-level interpretation of the title, not a complete trading
specification: the exact model inputs/target, calibration, entry/exit or
rebalance rules, and position sizing are not fully defined here.

## Evidence

* **Moskowitz & Grinblatt (1999), "Do Industries Explain Momentum?"
  *Journal of Finance* 54(4), 1249–1290:** industry momentum is highly
  profitable after controls and accounts for much of stock momentum.
  (Abstract.)

## Against, and failure modes

* Sector rotation adds turnover and taxes; the long-only half keeps only
  part of the long-short industry-momentum premium.
* Parameters re-fitted often chase the recent past unless the adaptation
  itself is tested out of sample.

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
| 3658 | Adaptive Scholarly Sector ETF Allocator MK-29 | Geometric deep learning / Riemannian optimization / Risk parity | 6438 | 8380 | No |
| 3668 | Adaptive Scholarly Sector ETF Allocator MK-89 | Geometric deep learning / Riemannian optimization / Risk parity | 6443 | 8383 | No |
