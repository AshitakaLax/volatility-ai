# Fractional Differentiation Feature Pipeline

**Ledger ID RK300** · rank 300 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | ML / time-series preprocessing |
| Potential effectiveness rank | 300 (1 = strongest) |
| AI implementability rank | 151 (1 = easiest) |
| Retail advantage rank | 136 (1 = strongest) |
| Fit with this project | 🧪 as a feature transform (C-ML5) |
| Implemented in volatility-ai | **Yes.** Its own strategy id, `rk300_fracdiff`, selectable for backtests: `LibrarySizing` (`research/strategies/library_sizing.py`) with `signal=fracdiff`, component `FracDiffGate`. Tune it with `signal_params`. Unmeasured. Before this change: **Research code.** Fixed-width-window fractional differencing (`ml.info_bars.frac_diff_ffd`, ledger C-ML5). |
| Related ledger entries | C-ML5, RK213, RK271 |

## In one paragraph

Ordinary differencing (returns) makes prices stationary but throws away
their memory; levels keep the memory but are not stationary. Fractional
differencing with an order d between 0 and 1 finds the smallest d that
passes a unit-root test, keeping as much memory as possible. López de
Prado popularised it for ML features; the mathematics goes back to
Hosking (1981). It is a preprocessing step and, as the CSV says, creates
no alpha on its own.

## The rule

```text
weights w_0 = 1, w_k = -w_(k-1) (d - k + 1) / k; truncate when |w_k| < tau (fixed-width window)
x~_t = sum_k w_k x_(t-k); choose the smallest d with ADF p < 0.05 on the training fold only
```

## Evidence

* **López de Prado (2018), *Advances in Financial Machine Learning*, ch.
  5:** fixed-width-window fractional differencing; most financial series
  become stationary at d well below 1 while staying highly correlated
  with the original. (Standard reference; not re-opened.)
* **Hosking (1981), *Biometrika*:** fractional differencing. (Standard
  reference.)
* No study found isolating its contribution to trading returns.

## Against, and failure modes

* Tune d inside training folds only (the CSV's caveat); a d chosen on
  the full sample leaks.

## Fit with volatility-ai

Built. A candidate transform for the ML feature set (ml_plan.md's 22
bar-local features use plain returns); worth a feature-ablation run once
the held-out ML test exists, not before.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* López de Prado, M. (2018). *Advances in Financial Machine Learning*.
  Wiley. Standard reference; chapters as cited, not re-opened here.
* Hosking, J. R. M. (1981). "Fractional differencing." *Biometrika*
  68(1). Standard reference.
* This repository: `research/ml/info_bars.py` (`frac_diff_ffd`), ledger
  C-ML5.
