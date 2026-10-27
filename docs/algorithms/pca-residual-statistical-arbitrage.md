# PCA Residual Statistical Arbitrage

**Ledger ID RK76** · rank 76 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Statistical arbitrage |
| Potential effectiveness rank | 76 (1 = strongest) |
| AI implementability rank | 194 (1 = easiest) |
| Retail advantage rank | 264 (1 = strongest) |
| Fit with this project | ⛔ (stock universe, short leg) |
| Implemented in volatility-ai | **Partial.** The s-score is built on sector-ETF residuals (C-MR2); the PCA factor variant is not. |
| Related ledger entries | C-MR2, RK33, RK96 |

## In one paragraph

The PCA form of RK33. Estimate common factors as the principal
components of a stock universe's return correlation matrix, regress each
stock on them, and trade the residual's mean reversion. In Avellaneda
and Lee's study the PCA form was the stronger one: Sharpe 1.44 after
costs over 1997–2007, falling to 0.9 over 2003–2007. It needs a large
point-in-time stock universe, which this project's warehouse does not
have.

## The rule

```
correlation matrix of standardised returns (rolling 252 days); keep the top m eigenvectors (or enough to explain ~55%)
factor returns = eigenportfolio returns; regress each stock on them (60 days); OU s-score on the residual (see RK33)
```

## Evidence

* **Avellaneda & Lee (2010), *Quantitative Finance* 10(7), 761–782:**
  PCA strategies, Sharpe 1.44 after costs over 1997–2007 and 0.9 over
  2003–2007. (Abstract.)

## Against, and failure modes

* Sensitive to universe construction, estimation windows, costs and
  crowding (the CSV's caveat); eigenvectors rotate in crises.

## Fit with volatility-ai

Out of scope: a market-neutral stock book.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Avellaneda, M., Lee, J.-H. (2010). "Statistical arbitrage in the US
  equities market." *Quantitative Finance* 10(7), 761–782. Abstract.
* This repository: `research/strategies/mean_reversion.py`, ledger C-MR2.
