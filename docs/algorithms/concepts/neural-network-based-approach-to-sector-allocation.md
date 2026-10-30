# Neural-network-based approach to sector allocation

**Concept page** · shared by **11** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,768) ·
researched 2026-10-30

| | |
|---|---|
| Task | Sector allocation |
| Method | Neural networks |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of neural networks improving sector allocation; industry momentum (RK19, X3) is the documented signal. |
| Implemented in volatility-ai | `tools/rotation.py --mode relative_strength` (X3) rotates across a small ETF universe, including sector momentum (RK19), with an HRP mode (A5). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | X3, RK19, RK3, RK7, A5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Neural Scholarly Sector
Allocation Strategy Ref-405") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Compare sector-level return, trend or risk signals and periodically
re-weight among sector funds, controlling concentration and turnover.
The neural-network version fits a neural network to the task. I found no
study of this method on this task.

## The CSV's description

Proposed neural-network-based approach to sector allocation: Compare
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
* Neural forecasts on one index have not reliably beaten simple rules;
  an LSTM's stock picks were largely short-term reversal (Fischer &
  Krauss 2018, RK292).

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
| 1768 | Neural Scholarly Sector Allocation Strategy Ref-405 | Rough path theory / Tensor signatures / Stock trend forecasting | 5608 | 2168 | No |
| 1823 | Neural Scholarly Sector Allocation Strategy Ref-885 | Rough path theory / Tensor signatures / Stock trend forecasting | 5616 | 2193 | No |
| 3824 | Neural Scholarly Sector Allocation Strategy Ref-309 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6516 | 3086 | No |
| 3910 | Neural Scholarly Sector Allocation Strategy Ref-789 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6559 | 3203 | No |
| 6199 | Neural Scholarly Sector Allocation Strategy Ref-117 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 399 | 1846 | No |
| 6245 | Neural Scholarly Sector Allocation Strategy Ref-597 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 411 | 1858 | No |
| 8683 | Neural Scholarly Sector Allocation Strategy Ref-21 | Graph attention / Sector contagion / Stock baskets | 703 | 1009 | No |
| 8759 | Neural Scholarly Sector Allocation Strategy Ref-213 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7788 | 7597 | No |
| 8874 | Neural Scholarly Sector Allocation Strategy Ref-501 | Graph attention / Sector contagion / Stock baskets | 719 | 1044 | No |
| 8950 | Neural Scholarly Sector Allocation Strategy Ref-693 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7805 | 7621 | No |
| 9065 | Neural Scholarly Sector Allocation Strategy Ref-981 | Graph attention / Sector contagion / Stock baskets | 735 | 1079 | No |
