# Copula-Based Pairs Trading

**Ledger ID RK74** · rank 74 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Statistical arbitrage |
| Potential effectiveness rank | 74 (1 = strongest) |
| AI implementability rank | 193 (1 = easiest) |
| Retail advantage rank | 427 (1 = strongest) |
| Fit with this project | ⛔ (short leg) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK37, RK72, RK94 |

## In one paragraph

Fit the two assets' marginal return distributions separately, join them
with a copula (Gaussian, Student-t, Clayton, Gumbel, or a vine for more
than two), and trade when one asset's conditional probability given the
other is extreme (say below 5% or above 95%). It captures nonlinear and
tail dependence that a correlation or a linear spread misses. The large
comparative study finds it the weakest of the three classic methods
after costs, though vine copulas on many stocks have done better.

## The rule

```
u = F_x(r_x), v = F_y(r_y) (fitted marginals); fit copula C(u, v)
h(u | v) = dC/dv; long x / short y when h(u|v) < 0.05 and h(v|u) > 0.95; reverse at the mirror; exit when both near 0.5
```

## Evidence

* **Liew & Wu (2013), "Pairs trading: A copula approach," *Journal of
  Derivatives & Hedge Funds* 19(1), 12–30:** copula strategy compared with
  two conventional strategies; described as a powerful alternative.
  (Abstract.)
* **Rad, Low & Faff (2016):** US equities 1962–2014; copula 43 bp a
  month before costs and 5 bp after (against 91/38 for distance and
  85/33 for cointegration), but better on unconverged trades. (Abstract.)
* **Stübinger, Mangold & Krauss (2018), "Statistical arbitrage with vine
  copulas," *Quantitative Finance* 18(11), 1831–1849:** S&P 500,
  1992–2015; 9.25% a year after costs, Sharpe 1.12, maximum drawdown
  6.57%; better than Gaussian and t versions. (Abstract.)

## Against, and failure modes

* Model selection and tail estimation need long samples; dependence
  changes in crises (the CSV's caveat).
* Short leg.

## Fit with volatility-ai

Out of scope.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Liew, R. Q., Wu, Y. (2013). *Journal of Derivatives & Hedge Funds*
  19(1), 12–30. <https://doi.org/10.1057/jdhf.2013.1>. Abstract.
* Rad, H., Low, R. K. Y., Faff, R. (2016). *Quantitative Finance*
  16(10), 1541–1558. Abstract.
* Stübinger, J., Mangold, B., Krauss, C. (2018). *Quantitative Finance*
  18(11), 1831–1849.
  <https://econpapers.repec.org/RePEc:taf:quantf:v:18:y:2018:i:11:p:1831-1849>.
  Abstract.
