# Model for sector allocation

**Concept page** · shared by **13** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(2 of them in ranks 426–700; best-ranked member #587) ·
researched 2026-10-29

| | |
|---|---|
| Task | Sector allocation |
| Method | Unspecified model |
| Fit with this project | 🧪 relative-strength rotation is built (X3) · unmeasured |
| Implemented in volatility-ai | `tools/rotation.py --mode relative_strength` (X3) rotates across a small ETF universe; HRP mode (A5). |
| Evidence | Evidence found (for the task; see the page for the method) |
| Related ledger entries | X3, RK7, RK3, A5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Manifold-Valued Scholarly
Sector ETF Allocator MK-14") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Allocate across sector ETFs by forecast returns or risk. The
best-documented signal is industry momentum: buying past winning
industries and selling losers was highly profitable, and it explains
much of individual-stock momentum. Long-only, it becomes sector
rotation, which this repository builds as relative-strength rotation.

## The CSV's description

Proposed model for sector allocation: Compare sector-level return,
trend, or risk signals and periodically adjust weights among sector
funds; concentration and turnover need to be controlled. This is a
concept-level interpretation of the title, not a complete trading
specification: the exact model inputs/target, calibration, entry/exit or
rebalance rules, and position sizing are not fully defined here.

## Evidence

* **Moskowitz & Grinblatt (1999), "Do Industries Explain Momentum?"
  *Journal of Finance* 54(4), 1249–1290:** industry momentum is highly
  profitable after controls and accounts for much of stock momentum.
  (Abstract.)
* **Moskowitz, Ooi & Pedersen (2012), "Time series momentum," *Journal
  of Financial Economics* 104(2):** a security's own past 12-month
  return predicts its next month across 58 futures and forwards (see
  RK1). (Standard reference.)

## Against, and failure modes

* Sector rotation adds turnover and taxes; the long-only half keeps only
  part of the long-short premium.

## Fit with volatility-ai

Built as X3 (relative-strength rotation across a small ETF universe),
not yet measured. A sector-rotation sleeve would sit beside the grid,
not inside it.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Moskowitz, T. J., Grinblatt, M. (1999). *Journal of Finance* 54(4),
  1249–1290. doi:10.1111/0022-1082.00146. Abstract.
* Moskowitz, T. J., Ooi, Y. H., Pedersen, L. H. (2012). "Time series
  momentum." *Journal of Financial Economics* 104(2). Standard
  reference.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 587 | Manifold-Valued Scholarly Sector ETF Allocator MK-14 | Vine copulas / Regularization / Multi-factor equity allocation | 9257 | 7560 | No |
| 589 | Manifold-Valued Scholarly Sector ETF Allocator MK-74 | Vine copulas / Regularization / Multi-factor equity allocation | 9260 | 7562 | No |
| 8428 | Cross-Sectional Scholarly Sector ETF Allocator Ver-32 | Persistence landscapes / Topological data analysis / Equity index | 2057 | 2859 | No |
| 8434 | Dynamic Scholarly Sector ETF Allocator Ver-52 | Persistence landscapes / Topological data analysis / Equity index | 9891 | 12501 | No |
| 8444 | Convolutional Scholarly Sector ETF Allocator Ver-92 | Persistence landscapes / Topological data analysis / Equity index | 2063 | 2871 | No |
| 8457 | Cross-Sectional Scholarly Sector ETF Allocator Ver-132 | Persistence landscapes / Topological data analysis / Equity index | 2070 | 2880 | No |
| 8463 | Dynamic Scholarly Sector ETF Allocator Ver-152 | Persistence landscapes / Topological data analysis / Equity index | 2071 | 2884 | No |
| 8473 | Convolutional Scholarly Sector ETF Allocator Ver-192 | Persistence landscapes / Topological data analysis / Equity index | 2078 | 2895 | No |
| 8490 | Wasserstein Scholarly Sector Allocation Strategy Alpha-41 | Graph neural networks / Sector contagion / Equity baskets | 13903 | 13694 | No |
| 8530 | Wasserstein Scholarly Sector Allocation Strategy Alpha-141 | Graph neural networks / Sector contagion / Equity baskets | 8194 | 2930 | No |
| 8570 | Wasserstein Scholarly Sector Allocation Strategy Alpha-241 | Graph neural networks / Sector contagion / Equity baskets | 8207 | 2950 | No |
| 8610 | Wasserstein Scholarly Sector Allocation Strategy Alpha-341 | Graph neural networks / Sector contagion / Equity baskets | 13909 | 13705 | No |
| 8650 | Wasserstein Scholarly Sector Allocation Strategy Alpha-441 | Graph neural networks / Sector contagion / Equity baskets | 8227 | 2998 | No |
