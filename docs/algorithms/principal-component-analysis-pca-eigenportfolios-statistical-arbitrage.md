# Principal Component Analysis (PCA) Eigenportfolios Statistical Arbitrage

**Ledger ID RK96** · rank 96 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Statistical arbitrage / factor modeling |
| Potential effectiveness rank | 96 (1 = strongest) |
| AI implementability rank | 105 (1 = easiest) |
| Retail advantage rank | 269 (1 = strongest) |
| Fit with this project | ⛔ (stock universe, short leg) |
| Implemented in volatility-ai | **Partial.** The s-score on ETF residuals (C-MR2); no eigenportfolios. |
| Related ledger entries | C-MR2, RK33, RK76 |

## In one paragraph

The same strategy as RK76, described through its building block. Each
eigenvector of the correlation matrix, divided by the stocks'
volatilities, defines an "eigenportfolio." The first is close to the
market, and the next few are sector- and style-like. Regress each stock
on the leading eigenportfolios and trade the residual's mean reversion.
Avellaneda and Lee introduced the term in this context; their PCA
results (Sharpe 1.44 over 1997–2007, 0.9 over 2003–2007) are the
evidence.

## The rule

```
eigenportfolio j weights: Q_i^(j) = v_i^(j) / sigma_i (v = j-th eigenvector of the correlation matrix)
F_j = sum_i Q_i^(j) r_i; regress r_i on F_1..F_m; OU s-score on the residual (RK33)
```

## Evidence

* **Avellaneda & Lee (2010), *Quantitative Finance* 10(7), 761–782:**
  eigenportfolio factors, Sharpe 1.44 after costs over 1997–2007, 0.9
  over 2003–2007. (Abstract.)

## Against, and failure modes

* Loadings drift and rotate in crises (the CSV's caveat); m is a free
  parameter.

## Fit with volatility-ai

Out of scope.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Avellaneda, M., Lee, J.-H. (2010). "Statistical arbitrage in the US
  equities market." *Quantitative Finance* 10(7), 761–782. Abstract.
* This repository: `research/strategies/mean_reversion.py`, ledger C-MR2.
