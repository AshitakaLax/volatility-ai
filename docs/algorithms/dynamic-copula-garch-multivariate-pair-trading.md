# Dynamic Copula-GARCH Multivariate Pair Trading

**Ledger ID RK94** · rank 94 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Statistical arbitrage / econometrics |
| Potential effectiveness rank | 94 (1 = strongest) |
| AI implementability rank | 291 (1 = easiest) |
| Retail advantage rank | 9,358 (1 = strongest) |
| Fit with this project | ⛔ (short leg) |
| Implemented in volatility-ai | **Research code** in `research.catalog.stat_arb`: `copula_garch_positions`; tested on synthetic data, not wired into the engine. GARCH, DCC and the copula tools it uses are in `research.catalog.econometrics`. |
| Related ledger entries | RK74 |

## In one paragraph

RK74 with two upgrades. GARCH models give each asset's marginal
distribution a time-varying volatility. A time-varying copula (Clayton
or Gumbel for asymmetric tails) lets the dependence change through
stress. The trade still fires on extreme conditional probabilities.
Vine copulas with time-varying dependence have a published S&P 500
result, but I found no study of this exact copula-GARCH pairs design.

## The rule

```
r_i,t = mu_i + sigma_i,t z_i,t with GARCH(1,1) sigma; u_i,t = F(z_i,t)
dynamic copula C_t(u_1, u_2; theta_t) (e.g. Patton-style time-varying parameter)
trade as in RK74 on h(u_1 | u_2) at the 5%/95% levels
```

## Evidence

* **Stübinger, Mangold & Krauss (2018), *Quantitative Finance* 18(11),
  1831–1849:** vine-copula stat arb on the S&P 500, 9.25% a year after
  costs, Sharpe 1.12, 1992–2015. (Abstract.)
* **Rad, Low & Faff (2016):** static copula pairs earned 5 bp a month
  after costs. (Abstract.)
* **No copula-GARCH pairs study verified.** The owner-supplied Gemini
  answer cites Cherubini, Luciano & Vecchiato (2004), *Copula Methods in
  Finance*, a methods book, and unnamed JSE bank studies that could not
  be found. The nearest found: a GARCH-adaptive cointegration system on
  the JSE (North-West University thesis, 2017), which did not beat
  classical pairs there.

## Against, and failure modes

* Heavy estimation (two layers of models, rolling); results depend on
  window and copula family (the CSV's caveat).

## Fit with volatility-ai

Out of scope.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Stübinger, J., Mangold, B., Krauss, C. (2018). "Statistical arbitrage
  with vine copulas." *Quantitative Finance* 18(11), 1831–1849. Abstract.
* Rad, H., Low, R. K. Y., Faff, R. (2016). *Quantitative Finance* 16(10),
  1541–1558. Abstract.
* Cherubini, U., Luciano, E., Vecchiato, W. (2004). *Copula Methods in
  Finance*. Wiley. Methods only.
* The CSV's references: the `arch` and `copulas` Python libraries.
