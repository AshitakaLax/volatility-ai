# Conformal Prediction Uncertainty Wrapper (CP-MAPIE)

**Ledger ID RK295** · rank 295 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Uncertainty quantification / Machine learning filter |
| Potential effectiveness rank | 295 (1 = strongest) |
| AI implementability rank | 155 (1 = easiest) |
| Retail advantage rank | 74 (1 = strongest) |
| Fit with this project | 🧪 as uncertainty-aware lot sizing |
| Implemented in volatility-ai | **Yes.** Its own strategy id, `rk295_conformal`, selectable for backtests: `LibrarySizing` (`research/strategies/library_sizing.py`) with `signal=conformal`, component `ConformalSizer`. Tune it with `signal_params`. Unmeasured. Before this change: **Research code.** Split-conformal intervals and a long-only sizing rule (`position_sizing.split_conformal_interval`, `conformal_long_size`, catalog S5). |
| Related ledger entries | V13, RK99, S5 |

## In one paragraph

Wrap any forecasting model in conformal prediction: calibrate the
model's errors on held-out data and turn each new prediction into an
interval with guaranteed coverage, provided past and future errors are
exchangeable. Used as a filter, it skips or shrinks trades whose
interval includes a loss. Markets are not exchangeable, so adaptive
versions that recalibrate under drift are the practical form.

## The rule

```text
calibration residuals e_i = |y_i - f(x_i)|; q = the ceil((n+1)(1-alpha))/n quantile of e
interval for a new x: [f(x) - q, f(x) + q]; trade (or size up) only if the lower bound clears the cost or target
```

## Evidence

* **Vovk, Gammerman & Shafer (2005), *Algorithmic Learning in a Random
  World*:** the conformal framework and its finite-sample coverage
  guarantee under exchangeability. (Standard reference.)
* **Kato (2024), arXiv 2410.16333:** conformal intervals around
  predicted portfolio returns; maximising the lower bound did best on US
  and Japanese stocks. (Abstract; see RK99.)
* **Gibbs & Candès (2021):** adaptive conformal inference under
  distribution shift. (Not verified here; see RK99.)

## Against, and failure modes

* Coverage holds only under exchangeability, or approximately with
  adaptive extensions (the CSV's caveat).
* An interval is only as useful as the model inside it; the models here
  are weak (AUC 0.52–0.63).

## Fit with volatility-ai

Built as research code for sizing. Wrapping the V13 reachability model
in a conformal interval is the natural pairing, and would size lots down
when the model is unsure. It inherits the weakness of the underlying
model.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Vovk, V., Gammerman, A., Shafer, G. (2005). *Algorithmic Learning in a
  Random World*. Springer.
* Kato, M. (2024). "Conformal Predictive Portfolio Selection." arXiv
  2410.16333. Abstract.
* This repository: `research/strategies/position_sizing.py`
  (`split_conformal_interval`, `conformal_long_size`).
