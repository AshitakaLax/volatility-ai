# Markowitz Mean-Variance Optimization

**Ledger ID RK116** · rank 116 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Portfolio construction |
| Potential effectiveness rank | 116 (1 = strongest) |
| AI implementability rank | 42 (1 = easiest) |
| Retail advantage rank | 66 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** A multi-asset rule whose estimation error beats its benefit out of sample. |
| Implemented in volatility-ai | **Research code** `research.catalog.je_suis_tm_projects`: `markowitz_weights`. |
| Related ledger entries | Q13, RK117, RK63 |

## In one paragraph

Choose weights for the best return per unit of variance. It is the
foundation of portfolio theory and, with sample estimates, a poor
practical rule: DeMiguel, Garlappi and Uppal found nothing in 14 models
consistently beat equal weights out of sample.

## Evidence

* **DeMiguel, Garlappi & Uppal (2009), *Review of Financial Studies*
  22(5):** across 14 models and seven datasets none consistently beat
  1/N out of sample on Sharpe ratio, certainty-equivalent return or
  turnover; sample mean-variance needs roughly 3,000 months of data to
  beat 1/N for 25 assets. (Abstract.)
* **This repository:** `markowitz_weights` (Q13) and
  `allocation.mean_variance_weights`.

## Against, and failure modes

* Weights chase noisy mean estimates; turnover is high.

## Fit with volatility-ai

A portfolio-construction rule for a multi-asset book. The engine trades
one symbol and the multi-asset allocator in ledger §11 is not built; it
becomes relevant only if a multi-ETF book is added (as X2/X3 explore).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* DeMiguel, V., Garlappi, L., Uppal, R. (2009). Optimal Versus Naive
  Diversification. *Review of Financial Studies* 22(5), 1915–1953.
  Abstract.
