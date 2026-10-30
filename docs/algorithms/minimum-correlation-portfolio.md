# Minimum-Correlation Portfolio

**Ledger ID RK118** · rank 118 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Portfolio optimization |
| Potential effectiveness rank | 118 (1 = strongest) |
| AI implementability rank | 6 (1 = easiest) |
| Retail advantage rank | 43 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** A multi-asset heuristic with only its authors' backtests behind it. |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK66, RK61 |

## In one paragraph

Weight assets by how little they correlate with the rest, after
equalising volatility (Varadi, Kapler, Bee and Rittenhouse's minimum
correlation algorithm). It was presented as a practical alternative to
risk parity and maximum diversification, tested by its authors on
portfolios back to 1980.

## Evidence

* **Varadi, Kapler, Bee & Rittenhouse (2012), "The Minimum Correlation
  Algorithm":** two heuristics weighting assets by low average
  correlation; the authors' tests go back to 1980. Results not seen.
  (Secondary summaries.)

## Against, and failure modes

* Correlations estimated on 60 days are noisy and jump together in
  crises, when diversification is needed.

## Fit with volatility-ai

A portfolio-construction rule for a multi-asset book. The engine trades
one symbol and the multi-asset allocator in ledger §11 is not built; it
becomes relevant only if a multi-ETF book is added (as X2/X3 explore).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Varadi, D., Kapler, M., Bee, H., Rittenhouse, C. (2012). The Minimum
  Correlation Algorithm: A Practical Diversification Tool. CSS
  Analytics. Secondary summaries.
