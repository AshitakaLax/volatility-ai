# Hierarchical Equal Risk Contribution (HERC)

**Ledger ID RK119** · rank 119 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Portfolio optimization / clustering |
| Potential effectiveness rank | 119 (1 = strongest) |
| AI implementability rank | 7 (1 = easiest) |
| Retail advantage rank | 44 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** A multi-asset allocator; HRP (A5) is already the built hierarchical method. |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | A5, RK21 |

## In one paragraph

Cluster assets hierarchically, then split risk equally across clusters
and within them (Raffinot). It extends HRP with a chosen number of
clusters and downside risk measures. The out-of-sample claims are the
author's; an independent comparison found it the best performer in one
30-stock test but with high concentration and turnover.

## Evidence

* **Raffinot (2018):** HERC portfolios are diversified and outperform
  out of sample, especially with CDaR as the risk measure; the author's
  claims. (Quoted summary.)
* **This repository:** `hrp.hrp_weights` (A5) is the built hierarchical
  allocator.

## Against, and failure modes

* Cluster count and linkage are free choices that change the weights.

## Fit with volatility-ai

A portfolio-construction rule for a multi-asset book. The engine trades
one symbol and the multi-asset allocator in ledger §11 is not built; it
becomes relevant only if a multi-ETF book is added (as X2/X3 explore).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Raffinot, T. (2018). The Hierarchical Equal Risk Contribution
  Portfolio. SSRN 3237540. Quoted summary (Hudson & Thames).
