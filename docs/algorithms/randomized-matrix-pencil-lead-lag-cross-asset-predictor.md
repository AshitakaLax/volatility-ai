# Randomized Matrix Pencil Lead-Lag Cross-Asset Predictor

**Ledger ID RK196** · rank 196 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Signal processing / Matrix pencil / Lead-lag arbitrage |
| Potential effectiveness rank | 196 (1 = strongest) |
| AI implementability rank | 229 (1 = easiest) |
| Retail advantage rank | 2,829 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** No finance study of the method, and lead-lag trading needs a second traded asset and speed. |
| Implemented in volatility-ai | **Research code** `research.catalog.leads`: `hy_lead_lag`. |
| Related ledger entries | RK204, RK221 |

## In one paragraph

Extract damped exponentials from cross-asset price series with a
randomised matrix pencil and read lead-lag relations from them. Lead-lag
detection has several finance methods (thermal optimal path,
multireference alignment, Hayashi–Yoshida); I found none using the
matrix pencil, and the CSV's reference, arXiv 2101.05432, could not be
identified.

## Evidence

* **Lead-lag methods with finance evidence:** the thermal optimal path
  (Zhou & Sornette) and multireference alignment for lagged factor
  models (arXiv 2305.06704). (Abstracts.)
* **This repository:** `leads.hy_lead_lag` and
  `lagged_cross_correlation` (RK204).
* **No study found** that tests this combination as a trading strategy.

## Against, and failure modes

* Prices are not sums of damped exponentials; the pencil fits noise.

## Fit with volatility-ai

Lead-lag trading (RK204) has a cost problem already; a new estimator
does not fix it.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Robust Detection of Lead-Lag Relationships in Lagged Multi-Factor
  Models. <https://arxiv.org/abs/2305.06704>. Abstract.
* The CSV's reference, arXiv 2101.05432 (not identified).
