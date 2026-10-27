# Kalman-Filter Dynamic-Hedge Pairs

**Ledger ID RK73** · rank 73 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Statistical arbitrage |
| Potential effectiveness rank | 73 (1 = strongest) |
| AI implementability rank | 192 (1 = easiest) |
| Retail advantage rank | 263 (1 = strongest) |
| Fit with this project | ⛔ (short leg) · 🧪 the long-only spread signal |
| Implemented in volatility-ai | **Research code.** `pairs.KalmanHedgeRatio` (a time-varying hedge ratio) and `pairs.spread_long_signal` (catalog MR3 variant). |
| Related ledger entries | Q2, RK37, RK75 |

## In one paragraph

Instead of a fixed regression hedge ratio, let the hedge ratio (and
intercept) follow a random walk and estimate it bar by bar with a
Kalman filter; the filter's forecast error, scaled by its own variance,
is the trading signal. The state-space view of pairs trading goes back
to Elliott, van der Hoek and Malcolm (2005), who model the spread as a
mean-reverting process observed with noise. It adapts to slow drift;
the risk is that it adapts to noise as readily.

## The rule

```
state beta_t = beta_{t-1} + w_t (process noise delta); observation y_t = beta_t' [1, x_t] + v_t
filter -> forecast error e_t and its variance Q_t
long the spread when e_t < -sqrt(Q_t), short when e_t > sqrt(Q_t); exit near zero
long-only form (this repository): buy the cheap leg only
```

## Evidence

* **Elliott, van der Hoek & Malcolm (2005), "Pairs trading,"
  *Quantitative Finance* 5(3), 271–276:** spread as a mean-reverting
  Gaussian Markov chain observed in noise; Kalman filtering and EM
  estimation; trade when the observation departs from the filtered
  value. (Secondary summaries.)
* No study found that compares out-of-sample returns of the
  Kalman-hedge form with the static form on a common sample; the general
  pairs record applies (RK37, RK72).

## Against, and failure modes

* The noise ratio (delta) decides how fast beta moves: too fast, and the
  filter tracks noise and the spread never looks wide (the CSV's caveat).

## Fit with volatility-ai

Out of scope as a pair. The filter is reusable (for example, a drifting
beta of TQQQ to QQQ), but no use for it is planned.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Elliott, R. J., van der Hoek, J., Malcolm, W. P. (2005). "Pairs
  trading." *Quantitative Finance* 5(3), 271–276.
  <https://econpapers.repec.org/RePEc:taf:quantf:v:5:y:2005:i:3:p:271-276>.
  Secondary summaries.
* This repository: `research/strategies/pairs.py`.
