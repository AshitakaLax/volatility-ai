# Distance-Based Pairs Trading

**Ledger ID RK72** · rank 72 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Statistical arbitrage |
| Potential effectiveness rank | 72 (1 = strongest) |
| AI implementability rank | 134 (1 = easiest) |
| Retail advantage rank | 220 (1 = strongest) |
| Fit with this project | ⛔ (short leg) |
| Implemented in volatility-ai | **Research code** in `research.catalog.stat_arb`: `ggr_pairs`, `ggr_positions`; tested on synthetic data, not wired into the engine. The cointegration form and a long-only spread signal are research code (RK37). |
| Related ledger entries | Q2, RK37, RK73, RK74 |

## In one paragraph

Gatev, Goetzmann and Rouwenhorst's rule. Over a 12-month formation
period, pair each stock with the one whose normalised price path is
closest (minimum sum of squared differences). Over the next six months,
open a pair when the two diverge by two historical standard deviations,
and close it when they cross. It is the benchmark of the pairs
literature, and its decline is well documented: the top-20-pairs
portfolio earned 0.86% a month over 1962–1988, 0.37% over 1989–2002
and 0.24% over 2003–2009, before costs.

## The rule

```
formation (12 months): normalise prices to 1; pair = argmin sum((p_i - p_j)^2)
trading (6 months): open when |p_i - p_j| > 2 x formation std; long the loser, short the winner
close when the normalised prices cross, or at the end of the trading period
```

## Evidence

* **Gatev, Goetzmann & Rouwenhorst (2006), "Pairs Trading: Performance
  of a Relative-Value Arbitrage Rule," *Review of Financial Studies*
  19(3), 797–827:** US stocks 1962–2002; annualised excess returns of up
  to about 11% for self-financing portfolios of top pairs. (Recalled
  from the abstract; not re-checked in this pass.)
* **Do & Faff (2010), "Does Simple Pairs Trading Still Work?" *Financial
  Analysts Journal* 66(4), 83–95:** to June 2009; the top-20 mean excess
  return fell from 0.86% a month (1962–1988) to 0.37% (1989–2002) and
  0.24% (2003–2009); the strategy is strong in prolonged turbulence,
  including 2007–2009. (Abstract.)
* **Rad, Low & Faff (2016):** 91 bp a month before costs, 38 bp after,
  1962–2014. (Abstract.)

## Against, and failure modes

* Correlation is not a reason to converge (the CSV's caveat); structural
  breaks; legging and slippage.
* Costs take most of the remaining edge.

## Fit with volatility-ai

Out of scope (short leg). Its long-only remainder is the relative-value
rotation (X3).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Gatev, E., Goetzmann, W. N., Rouwenhorst, K. G. (2006). *Review of
  Financial Studies* 19(3), 797–827. Not re-checked in this pass.
* Do, B., Faff, R. (2010). *Financial Analysts Journal* 66(4), 83–95.
  <https://econpapers.repec.org/RePEc:taf:ufajxx:v:66:y:2010:i:4:p:83-95>.
  Abstract.
* Rad, H., Low, R. K. Y., Faff, R. (2016). *Quantitative Finance*
  16(10), 1541–1558. Abstract.
