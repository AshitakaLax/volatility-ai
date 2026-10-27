# Fractional Brownian Motion Multi-Scale Trend Scanning Strategy

**Ledger ID RK202** · rank 202 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Fractional calculus / Trend scanning / Technical alpha |
| Potential effectiveness rank | 202 (1 = strongest) |
| AI implementability rank | 317 (1 = easiest) |
| Retail advantage rank | 304 (1 = strongest) |
| Fit with this project | ⛔ (no evidence for the combination) |
| Implemented in volatility-ai | **No.** Trend-scanning labels (RK213) and Hurst/variance-ratio diagnostics (C-MR4) exist separately. |
| Related ledger entries | RK213, RK297, C-MR4 |

## In one paragraph

Combine fractional-Brownian-motion style tests (variance ratios, Hurst
exponents) with trend-scanning across horizons to find statistically
significant trends. Each part is standard. The evidence on long memory
in stock returns is weak once short-range dependence is accounted for,
and I found no study of the combination as a strategy.

## Evidence

* **Lo & MacKinlay (1988), *Review of Financial Studies* 1(1):** the
  variance-ratio test; weekly returns of US stocks reject the random
  walk. (Standard reference; not re-checked here.)
* **Lo (1991), *Econometrica* 59(5):** the modified rescaled-range
  statistic finds little evidence of long-term memory in stock returns.
  (Standard reference; not re-checked.)
* **No study found** of the combined strategy.

## Against, and failure modes

* Multiple testing across horizons; Hurst estimates are noisy on short
  windows.

## Fit with volatility-ai

Both diagnostics exist here (C-MR4's variance ratio and Hurst exponent,
C-ML1's trend scanning). As a regime they would be a direction signal,
the kind L1 found costs more than it saves.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Lo, A. W., MacKinlay, A. C. (1988). *Review of Financial Studies*
  1(1). Not re-checked.
* Lo, A. W. (1991). "Long-Term Memory in Stock Market Prices."
  *Econometrica* 59(5). Not re-checked.
* This repository: `research/strategies/mean_reversion.py`
  (`variance_ratio`, `hurst_exponent`), `research/ml/barrier_labels.py`.
