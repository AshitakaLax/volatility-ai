# Fractional Order Cointegration Vector AutoRegressive (VAR) Strategy

**Ledger ID RK135** · rank 135 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Statistical arbitrage / Fractional time series / Econometrics |
| Potential effectiveness rank | 135 (1 = strongest) |
| AI implementability rank | 178 (1 = easiest) |
| Retail advantage rank | 285 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** A short-leg spread trade with no tested evidence for the fractional variant. |
| Implemented in volatility-ai | **Research code** `research.catalog.allocation`: `fractional_var_allocation`. |
| Related ledger entries | RK239, RK340, RK36 |

## In one paragraph

Fit a VAR to fractionally differenced cointegrated baskets and trade the
long-memory spread. Fractional cointegration itself is established
econometrics; I found no study trading it in this form, and it inherits
the short leg and the parameter fragility of any spread trade.

## Evidence

* **Fractionally cointegrated VAR (Johansen & Nielsen 2012):** an
  established model in which the equilibrium error has long memory; the
  applications found are econometric (term-structure persistence, metals
  price discovery, a commodity high-low range working paper), not tested
  trading strategies (see RK239).
* **No study found** that tests this combination as a trading strategy.

## Against, and failure modes

* Long-memory parameters are estimated with wide error bands on a few
  years of data; a spread that is fractionally rather than fully
  mean-reverting can drift for months.

## Fit with volatility-ai

A relative-value trade between assets: it needs a short leg and a
universe of related instruments, and the engine trades one leveraged ETF
long-only. Out of scope as a strategy.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Johansen, S., Nielsen, M. Ø. (2012). Likelihood inference for a
  fractionally cointegrated vector autoregressive model. *Econometrica*
  80(6), 2667–2732. Standard reference.
