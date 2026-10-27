# Capital Structure Arbitrage

**Ledger ID RK81** · rank 81 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Relative value / credit-equity |
| Potential effectiveness rank | 81 (1 = strongest) |
| AI implementability rank | 205 (1 = easiest) |
| Retail advantage rank | 130 (1 = strongest) |
| Fit with this project | ⛔ (CDS, bonds, short legs) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK80 |

## In one paragraph

Use a structural credit model (CreditGrades is the usual one) to infer
a firm's fair credit spread from its equity price and volatility. When
the market CDS spread is far from that value, trade the CDS against the
stock and bet on convergence. Single trades can lose heavily because CDS
and equity move only loosely together. An equal-weighted portfolio of
all trades has historically looked like other fixed-income arbitrage: a
modest Sharpe ratio with crash risk.

## The rule

```
model spread = CreditGrades(equity price, equity vol, debt per share, recovery)
market CDS >> model: sell protection, sell stock (hedge); market CDS << model: buy protection, buy stock
exit on convergence or after a holding limit
```

## Evidence

* **Yu (2006), "How Profitable Is Capital Structure Arbitrage?"
  *Financial Analysts Journal* 62(5), 47–62:** CreditGrades, 135,759
  daily CDS spreads on 261 North American obligors. Individual trades
  can lose heavily. An equal-weighted portfolio of all trades has Sharpe
  ratios similar to other fixed-income arbitrage strategies and hedge
  fund benchmarks. (Abstract.)
* **Duarte, Longstaff & Yu (2007), "Risk and Return in Fixed-Income
  Arbitrage: Nickels in Front of a Steamroller?" *Review of Financial
  Studies*:** capital structure arbitrage among the strategies studied.
  (Title and listing only.)

## Against, and failure modes

* Model risk (seniority, recovery, debt definition), liquidity and
  basis risk: legs may never converge (the CSV's caveat).

## Fit with volatility-ai

Out of scope.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Yu, F. (2006). *Financial Analysts Journal* 62(5), 47–62.
  <https://econpapers.repec.org/RePEc:taf:ufajxx:v:62:y:2006:i:5:p:47-62>.
  Abstract.
* Duarte, J., Longstaff, F. A., Yu, F. (2007). *Review of Financial
  Studies*. Listing only.
