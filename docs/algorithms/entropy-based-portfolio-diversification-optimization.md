# Entropy-Based Portfolio Diversification Optimization

**Ledger ID RK107** · rank 107 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Information Theory / Portfolio Construction |
| Potential effectiveness rank | 107 (1 = strongest) |
| AI implementability rank | 63 (1 = easiest) |
| Retail advantage rank | 76 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** A multi-asset weighting rule; this book holds one instrument. |
| Implemented in volatility-ai | **Research code** `research.catalog.allocation`: `maxent_weights`. |
| Related ledger entries | RK222, RK117 |

## In one paragraph

Maximise the Shannon entropy of weights or risk contributions so the
portfolio is as diversified as its constraints allow. Bera and Park's
maximum-entropy diversification is the usual source; the CSV's DOI could
not be resolved by search.

## Evidence

* **Bera & Park (2008), *Econometric Reviews* 27:** maximum-entropy
  weights subject to mean-variance constraints reduce concentration
  relative to Markowitz portfolios (see RK222).
* **This repository:** `allocation.maxent_weights` implements it.

## Against, and failure modes

* Entropy rewards spreading weight, not spreading risk; with correlated
  assets maximum entropy can be no more diversified than 1/N.

## Fit with volatility-ai

A portfolio-construction rule for a multi-asset book. The engine trades
one symbol and the multi-asset allocator in ledger §11 is not built; it
becomes relevant only if a multi-ETF book is added (as X2/X3 explore).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Bera, A. K., Park, S. Y. (2008). Optimal portfolio diversification
  using the maximum entropy principle. *Econometric Reviews* 27(4–6),
  484–512. Not re-checked.
* The CSV's DOI (10.1016/j.jbankfin.2008.06.002) did not resolve in
  search.
