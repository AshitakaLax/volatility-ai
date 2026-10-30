# Dynamic Copula-EVT Tail Risk Relative Value Arbitrage

**Ledger ID RK101** · rank 101 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Extreme value theory / Copulas / Relative value |
| Potential effectiveness rank | 101 (1 = strongest) |
| AI implementability rank | 355 (1 = easiest) |
| Retail advantage rank | 10,445 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** An index-options relative-value trade (options are excluded) with no study found. |
| Implemented in volatility-ai | **Research code** `research.catalog.concepts`: `pot_var_es`; `research.catalog.econometrics`: `fit_cvine`. |
| Related ledger entries | RK74, RK94, RK130 |

## In one paragraph

Model index tail dependence with time-varying copulas and the tails
themselves with a generalised Pareto (EVT) fit, and trade the gap
between that model's tail prices and the market's option prices. Both
tools are standard risk-management machinery (McNeil and Frey's
GARCH-EVT is the classic); I found no study trading option tails this
way.

## Evidence

* **McNeil & Frey (2000), *Journal of Empirical Finance* 7:** GARCH
  filtering plus a generalised Pareto tail for the innovations gives
  good VaR and expected-shortfall forecasts; a risk-measurement result,
  not a trading one. (Abstract.)
* **No study found** that tests this combination as a trading strategy.

## Against, and failure modes

* Tail prices are dominated by the few crashes in the sample; a
  model-vs-market gap in deep out-of-the-money options is mostly the
  variance risk premium, not a mispricing.

## Fit with volatility-ai

Options are outside the owner's instrument rule (long-only stocks and
ETFs), and the engine has no options data or pricing.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* McNeil, A. J., Frey, R. (2000). Estimation of tail-related risk
  measures for heteroscedastic financial time series. *Journal of
  Empirical Finance* 7(3–4), 271–300. Abstract.
* The CSV's references are software (arch, copulas).
