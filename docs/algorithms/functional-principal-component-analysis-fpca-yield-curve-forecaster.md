# Functional Principal Component Analysis (FPCA) Yield Curve Forecaster

**Ledger ID RK226** · rank 226 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Functional data analysis / Fixed income |
| Potential effectiveness rank | 226 (1 = strongest) |
| AI implementability rank | 79 (1 = easiest) |
| Retail advantage rank | 48 (1 = strongest) |
| Fit with this project | ⛔ (rates forecasting; no direct use here) |
| Implemented in volatility-ai | **Research code** in `research.catalog.carry_rates`: `fpca`, `fpca_forecast`, `dns_forecast`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK86, RK28, RK224 |

## In one paragraph

Treat each day's yield curve as a smooth function of maturity, extract
its principal component functions, and forecast their scores. A
functional dynamic factor model of this kind forecast actual yields
well, especially in a trading exercise. The standard baseline is the
dynamic Nelson–Siegel model; most yield forecasting struggles to beat a
random walk at short horizons.

## Evidence

* **Hays, Shen & Huang (2012), "Functional dynamic factor models with
  application to yield curve forecasting," *Annals of Applied
  Statistics* 6(3), 870–894:** factor loading curves estimated by EM;
  good forecasts of actual yields, particularly in a trading exercise,
  with economically interpretable factors. (Abstract.)
* **Diebold & Li (2006), *Journal of Econometrics* 130(2):** dynamic
  Nelson–Siegel forecasting. (Standard reference; not re-checked here.)

## Against, and failure modes

* Bond trades need duration-neutral construction (RK86); forecasts
  degrade out of sample (RK86's Thornton & Valente).

## Fit with volatility-ai

Rates forecasting has no direct use for this book. Reference entry.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Hays, S., Shen, H., Huang, J. Z. (2012). *Annals of Applied
  Statistics* 6(3), 870–894. <https://arxiv.org/abs/1209.6172>.
  Abstract.
* Diebold, F. X., Li, C. (2006). *Journal of Econometrics* 130(2). Not
  re-checked.
