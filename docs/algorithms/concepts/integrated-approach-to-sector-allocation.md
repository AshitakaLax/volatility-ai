# Integrated approach to sector allocation

**Concept page** · shared by **5** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #8,482) ·
researched 2026-10-30

| | |
|---|---|
| Task | Sector allocation |
| Method | Integrated (combined) models |
| Fit with this project | ⏳ reference only · background, nothing to build now |
| Useful for volatility-ai | **Reference only.** An integrated model could weight a sector sleeve, but no study shows it beating plain sector momentum; background until X3 is measured. |
| Implemented in volatility-ai | `tools/rotation.py --mode relative_strength` (X3) rotates across a small ETF universe, including sector momentum (RK19), with an HRP mode (A5). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | X3, RK19, RK3, RK7, A5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Holistic Scholarly Sector
Allocation Strategy Alpha-21") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Compare sector-level return, trend or risk signals and periodically
re-weight among sector funds, controlling concentration and turnover.
The integrated version chains several models or data sources into one
pipeline; the title does not say which. I found no study of this method
on this task.

## The CSV's description

Proposed integrated approach to sector allocation: Compare sector-level
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
* An unspecified combination cannot be tested as stated; each part would
  need its own evidence.

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
| 8482 | Holistic Scholarly Sector Allocation Strategy Alpha-21 | Graph neural networks / Sector contagion / Equity baskets | 4601 | 2903 | No |
| 8522 | Holistic Scholarly Sector Allocation Strategy Alpha-121 | Graph neural networks / Sector contagion / Equity baskets | 4609 | 2924 | No |
| 8562 | Holistic Scholarly Sector Allocation Strategy Alpha-221 | Graph neural networks / Sector contagion / Equity baskets | 13470 | 13701 | No |
| 8602 | Holistic Scholarly Sector Allocation Strategy Alpha-321 | Graph neural networks / Sector contagion / Equity baskets | 4629 | 2971 | No |
| 8642 | Holistic Scholarly Sector Allocation Strategy Alpha-421 | Graph neural networks / Sector contagion / Equity baskets | 4637 | 2992 | No |
