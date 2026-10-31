# GARCH Volatility Forecasting with Mean-Reversion Channel

**Ledger ID RK195** · rank 195 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Econometric / Volatility modeling |
| Potential effectiveness rank | 195 (1 = strongest) |
| AI implementability rank | 263 (1 = easiest) |
| Retail advantage rank | 6,475 (1 = strongest) |
| Fit with this project | ⏳ worth testing |
| Useful for volatility-ai | **Worth testing.** The grid's step already scales with volatility; GARCH is a candidate forecaster for that step, and it is hard to beat. |
| Implemented in volatility-ai | **Yes.** Its own strategy id, `rk195_garch`, selectable for backtests: `LibrarySizing` (`research/strategies/library_sizing.py`) with `signal=garch`, component `GarchSizer`. Tune it with `signal_params`. Unmeasured. Before this change: **Research code** `research.catalog.econometrics`: `garch11_fit`, `garch11_forecast`. |
| Related ledger entries | C-G2, S4, RK94 |

## In one paragraph

Fit GARCH(1,1) to returns and use its volatility forecast to widen or
narrow mean-reversion bands. Hansen and Lunde found little consistently
beats GARCH(1,1) as a volatility forecaster (with leverage-effect models
better for stocks). The grid already sets its step from realised
volatility, so GARCH is a drop-in forecaster to compare.

## Evidence

* **Hansen & Lunde (2005), *Journal of Applied Econometrics* 20(7):**
  across 330 ARCH-type models, nothing beat GARCH(1,1) for exchange
  rates; models with a leverage effect beat it for IBM. (Abstract.)
* **This repository:** `econometrics.garch11_fit` and
  `garch11_forecast`; the grid's volatility-scaled step
  (`grid_spacing.VolatilityScaledStep`).

## Against, and failure modes

* A one-day-ahead GARCH forecast and a recent realised range differ
  little at the grid's horizon; the leverage effect matters more for a
  falling 3x ETF.

## Fit with volatility-ai

Long-only and in scope: replace (or blend) the realised-volatility input
to the grid's step with a GARCH or GJR-GARCH forecast and compare
walk-forward. Expect a small difference.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Hansen, P. R., Lunde, A. (2005). A forecast comparison of volatility
  models: does anything beat a GARCH(1,1)? *Journal of Applied
  Econometrics* 20(7), 873–889. Abstract.
