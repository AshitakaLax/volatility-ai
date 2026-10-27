# Cointegration-Based Pairs Trading

**Ledger ID RK37** · rank 37 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Statistical arbitrage |
| Potential effectiveness rank | 37 (1 = strongest) |
| AI implementability rank | 191 (1 = easiest) |
| Retail advantage rank | 262 (1 = strongest) |
| Fit with this project | ⛔ (short leg) · 🧪 the long-only spread signal |
| Implemented in volatility-ai | **Research code.** quant-trading's Engle–Granger pairs (`je_suis_tm.pair_trading_signals`, Q2), the test (`pairs.engle_granger`) and a long-only spread signal (`pairs.spread_long_signal`). |
| Related ledger entries | Q2, X3, RK36, RK72, RK73 |

## In one paragraph

Find two prices whose linear combination is stationary (Engle–Granger:
regress one on the other, test the residual for a unit root), then buy
the spread when it is unusually low and sell it when unusually high.
Across the US equity market from 1962 to 2014 the cointegration method
earned 85 bp a month before costs and 33 bp after, and did best in
turbulent markets. The edge has shrunk over time, and the short leg is
essential.

## The rule

```
y = a + b x + e (rolling formation window); ADF on e below its critical value -> cointegrated
z = e / std(e); long y / short b x at z < -k, reverse at z > k, exit at 0; drop the pair if cointegration fails
long-only form (this repository): buy the cheap leg at z < -entry, exit at z > exit
```

## Evidence

* **Engle & Granger (1987), *Econometrica* 55(2), 251–276:** the
  two-step test.
* **Rad, Low & Faff (2016), "The profitability of pairs trading
  strategies: distance, cointegration and copula methods," *Quantitative
  Finance* 16(10), 1541–1558:** US equities 1962–2014; distance,
  cointegration and copula methods earn 91, 85 and 43 bp a month before
  costs and 38, 33 and 5 bp after; all have significant alphas;
  cointegration is best in turbulent markets. (Abstract.)
* **Krauss (2017):** survey. (Abstract.)

## Against, and failure modes

* Cointegration breaks (the CSV's caveat and quant-trading's README);
  correlations converge in sell-offs.
* Net returns are thin after costs.

## Fit with volatility-ai

As published, out. The long-only form buys the cheap leg; its
relative-value logic lives on as X3's ETF rotation.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Engle, R. F., Granger, C. W. J. (1987). "Co-integration and Error
  Correction." *Econometrica* 55(2), 251–276.
* Rad, H., Low, R. K. Y., Faff, R. (2016). *Quantitative Finance*
  16(10), 1541–1558.
  <https://econpapers.repec.org/RePEc:taf:quantf:v:16:y:2016:i:10:p:1541-1558>.
  Abstract.
* Krauss, C. (2017). *Journal of Economic Surveys* 31(2), 513–545.
  Abstract.
* This repository: ledger Q2, X3; `research/catalog/je_suis_tm.py`;
  `research/strategies/pairs.py`.
