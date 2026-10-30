# Markov-Switching Vector Error Correction Model (MS-VECM) Arbitrage

**Ledger ID RK131** · rank 131 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Econometric / Regime-switching cointegration |
| Potential effectiveness rank | 131 (1 = strongest) |
| AI implementability rank | 172 (1 = easiest) |
| Retail advantage rank | 19 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** A short-leg basket trade (on crypto coins in the CSV's wording) with no trading study. |
| Implemented in volatility-ai | **Research code** `research.catalog.econometrics`: `fit_vecm`; `research.strategies.regime_models`: `GaussianHMM`. |
| Related ledger entries | RK36, RK102 |

## In one paragraph

Model cointegrated baskets whose cointegrating vector and adjustment
speed change with a Markov regime. Jochmann and Koop give Bayesian
methods in which both the vectors and the number of relations can
switch; the applications found are macroeconomic, not trading.

## Evidence

* **Jochmann & Koop (2015), *Studies in Nonlinear Dynamics &
  Econometrics* 19(1):** Bayesian VECMs with Markov-switching
  cointegrating vectors and rank. (Abstract.)
* **No study found** that tests this combination as a trading strategy.

## Against, and failure modes

* Regime-dependent cointegration multiplies the parameters of an already
  fragile spread model.

## Fit with volatility-ai

A relative-value trade between assets: it needs a short leg and a
universe of related instruments, and the engine trades one leveraged ETF
long-only. Out of scope as a strategy.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Jochmann, M., Koop, G. (2015). Regime-switching cointegration.
  *Studies in Nonlinear Dynamics & Econometrics* 19(1), 35–48. Abstract.
