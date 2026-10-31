# Sequential Bootstrapping Sample Weights

**Ledger ID RK271** · rank 271 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | ML / training data sampling |
| Potential effectiveness rank | 271 (1 = strongest) |
| AI implementability rank | 153 (1 = easiest) |
| Retail advantage rank | 138 (1 = strongest) |
| Fit with this project | ⏳ for training the ML sizing models |
| Implemented in volatility-ai | **Yes.** Its own strategy id, `rk271_rf_seqboot`, selectable for backtests: `LibrarySizing` (`research/strategies/library_sizing.py`) with `signal=rf_seqboot`, component `RandomForestGate`. Tune it with `signal_params`. Unmeasured. Before this change: **Research code** in `research.catalog.technical_ml`: `sequential_bootstrap`, `average_uniqueness`, `indicator_matrix`; tested on synthetic data, not wired into the engine. Purged k-fold and combinatorial purged CV also exist (C-ML3). |
| Related ledger entries | C-ML3, RK213, RK294, V13, V14 |

## In one paragraph

Financial labels overlap in time (a label spanning ten bars shares
information with its neighbours), so ordinary bootstrapping over-samples
redundant observations. López de Prado's sequential bootstrap draws
samples with probability proportional to their average uniqueness given
what has already been drawn, so each bagged tree sees
closer-to-independent data. It is a training hygiene step, not a
strategy.

## The rule

```text
c_t = number of labels spanning bar t; uniqueness_i = mean over label i's span of 1 / c_t
draw sequentially: P(i) proportional to i's average uniqueness given the draws so far; bag models on the draws
```

## Evidence

* **López de Prado (2018), *Advances in Financial Machine Learning*, ch.
  4:** average uniqueness, sample weights and the sequential bootstrap,
  with Monte Carlo evidence that it raises the uniqueness of the
  bootstrap sample. (Standard reference; not re-opened.)
* No independent study found of its effect on trading performance.

## Against, and failure modes

* It improves data handling but removes neither leakage nor overfitting;
  apply only inside training folds (the CSV's caveat).

## Fit with volatility-ai

The LightGBM sizing models (V13, V14) train on overlapping
session-horizon labels; uniqueness weights are a cheap addition to their
training. Low priority: their measured AUCs are weak for reasons
sampling will not fix.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* López de Prado, M. (2018). *Advances in Financial Machine Learning*.
  Wiley. Standard reference; chapters as cited, not re-opened here.
* This repository: `research/optimization/purged_cv.py` (C-ML3);
  `docs/ml_plan.md`.
