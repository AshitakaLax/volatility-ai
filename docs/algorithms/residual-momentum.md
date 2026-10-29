# Residual Momentum

**Ledger ID RK16** · rank 16 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Factor / systematic equity |
| Potential effectiveness rank | 16 (1 = strongest) |
| AI implementability rank | 34 (1 = easiest) |
| Retail advantage rank | 29 (1 = strongest) |
| Fit with this project | ⏳ long-only stock basket (needs stocks and factor returns) · ⛔ long/short |
| Implemented in volatility-ai | **Research code** in `research.catalog.factors`: `residual_momentum`; tested on synthetic data, not wired into the engine. The closest code computes ETF-residual s-scores for mean reversion (C-MR2), the opposite sign of trade. |
| Related ledger entries | RK6, C-MR2 |

## In one paragraph

Instead of ranking stocks on their total return, regress each stock on
the Fama-French factors and rank on the trailing return of the
*residual*. Total-return momentum loads heavily on whatever factor just
won, so it inherits that factor's reversals; residual momentum strips
that out. Blitz, Huij and Martens report roughly twice the risk-adjusted
profit of ordinary momentum, more consistent over time, and the result
has held up out of sample.

## The rule

```
for each stock i, monthly:
    regress r_i on (MKT, SMB, HML) over the prior 36 months -> residuals e_i
    score_i = sum of e_i over months t-12 .. t-2, divided by std(e_i) over the same window
long the top decile, short the bottom decile (academic form); hold one month
```

## Evidence

* **Blitz, Huij & Martens (2011):** residual momentum's risk-adjusted
  profits are about twice those of total-return momentum, more
  consistent over time and less concentrated in the extremes; results do
  not support a priced-risk or microstructure explanation. (Abstract.)
  Residuals come from 36-month three-factor regressions; ranking uses
  months t−12 to t−2. (Summary.)
* A later study by Huij & Lansdorp (2017) reports the findings robust
  across global universes and out-of-sample periods. (Search-result
  summary.)

## Against, and failure modes

* **Model dependence.** The result depends on the factor model and the
  regression window; a different model gives different residuals.
* **Estimation noise** for young or thinly traded stocks; 36 months of
  history is a hard filter on the universe.
* Still a momentum strategy: rebounds after panics hurt it, though less
  than total-return momentum.

## Fit with volatility-ai

A cross-sectional stock book with the same data gap as RK6, plus a need
for factor returns (Ken French's library supplies them for research).
Nothing in the grid or regime machinery uses it.

## What it would take

A point-in-time US stock universe with delisting returns, monthly
three-factor regressions, and a long-only top-decile book outside the
grid engine (the engine is single-symbol). Until then this is a
reference entry.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Blitz, D., Huij, J., Martens, M. (2011). "Residual Momentum." *Journal
  of Empirical Finance* 18(3), 506–521.
  <https://repub.eur.nl/pub/22252>. Abstract and summary.
* Huij, J., Lansdorp, S. (2017). Residual momentum revisited. Search-result
  summary only; not opened.
