# Conformal Prediction Risk-Bounded Alpha Stacking

**Ledger ID RK127** · rank 127 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Conformal prediction / Ensemble modeling / Portfolio construction |
| Potential effectiveness rank | 127 (1 = strongest) |
| AI implementability rank | 217 (1 = easiest) |
| Retail advantage rank | 49 (1 = strongest) |
| Fit with this project | ⏳ worth testing |
| Useful for volatility-ai | **Worth testing.** Conformal sizing is already researched for grid lots (V13); stacking needs several alpha sources the project does not have. |
| Implemented in volatility-ai | **Yes.** Its own strategy id, `rk127_conformal_stack`, selectable for backtests: `LibrarySizing` (`research/strategies/library_sizing.py`) with `signal=conformal_stack`, component `ConformalSizer`. Tune it with `signal_params`. Unmeasured. Before this change: **Research code** `research.strategies.position_sizing`: `conformal_long_size`; `research.catalog.forecasting`: `stack_forecasts`. |
| Related ledger entries | V13, RK132, RK144 |

## In one paragraph

Combine several machine-learning alpha forecasts and wrap the ensemble
in split conformal intervals, so position size is bounded by a coverage
guarantee. Forecast combination has strong evidence (Rapach, Strauss and
Zhou); conformal intervals have finite-sample coverage under
exchangeability, which markets violate. I found no portfolio study of
the combination.

## Evidence

* **Rapach, Strauss & Zhou (2010), *Review of Financial Studies*
  23(2):** combining single-variable equity-premium forecasts gives
  significant out-of-sample gains over the historical mean. (Abstract.)
* **This repository:** `position_sizing.split_conformal_interval` and
  `conformal_long_size` (V13) size grid lots by a conformal bound;
  `forecasting.stack_forecasts` stacks forecasts.

## Against, and failure modes

* Coverage holds under exchangeability; regime shifts break it unless
  intervals adapt (adaptive conformal inference).

## Fit with volatility-ai

The conformal half fits: bound each lot's size by an interval on its
forecast, as V13 researches. The stacking half waits for a second alpha
source.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Rapach, D. E., Strauss, J. K., Zhou, G. (2010). Out-of-Sample Equity
  Premium Prediction. *Review of Financial Studies* 23(2), 821–862.
  Abstract.
* The CSV's references are MAPIE and the awesome-conformal-prediction
  list.
