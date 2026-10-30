# Alpha Stacking / Ensemble Portfolio Optimizer

**Ledger ID RK144** · rank 144 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Portfolio construction / ensemble |
| Potential effectiveness rank | 144 (1 = strongest) |
| AI implementability rank | 149 (1 = easiest) |
| Retail advantage rank | 73 (1 = strongest) |
| Fit with this project | 🧪 reference only |
| Useful for volatility-ai | **Reference only.** Forecast combination has real evidence, but the project has one signal family to combine; keep it for when it has several. |
| Implemented in volatility-ai | **Partly.** `research.catalog.forecasting`: `stack_forecasts`. |
| Related ledger entries | C-RJ4, RK127 |

## In one paragraph

Combine several alpha forecasts or strategy return streams with
validation-based weights or a stacking model. Combination is among the
most robust results in forecasting: Rapach, Strauss and Zhou's combined
equity-premium forecasts beat the historical mean out of sample when
single predictors did not.

## Evidence

* **Rapach, Strauss & Zhou (2010), *Review of Financial Studies*
  23(2):** combination forecasts give consistent out-of-sample gains.
  (Abstract.)
* **This repository:** `forecasting.stack_forecasts` (C-RJ4's stacking)
  is research code.

## Against, and failure modes

* Stacking weights fitted on the same validation window as the base
  models over-fit; equal weights are hard to beat.

## Fit with volatility-ai

The grid has one signal family (price drops and volatility regimes).
Equal-weight combination of regime indicators (NATR, HMM, VIX term
structure) is the realistic use.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Rapach, D. E., Strauss, J. K., Zhou, G. (2010). *Review of Financial
  Studies* 23(2), 821–862. Abstract.
