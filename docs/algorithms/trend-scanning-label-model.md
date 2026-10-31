# Trend-Scanning Label Model

**Ledger ID RK213** · rank 213 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | ML / event labeling |
| Potential effectiveness rank | 213 (1 = strongest) |
| AI implementability rank | 152 (1 = easiest) |
| Retail advantage rank | 137 (1 = strongest) |
| Fit with this project | 🧪 as a labelling tool (C-ML1) · not a strategy |
| Implemented in volatility-ai | **Yes.** Its own strategy id, `rk213_trend_scan`, selectable for backtests: `LibrarySizing` (`research/strategies/library_sizing.py`) with `signal=trend_scan`, component `TrendScanGate`. Tune it with `signal_params`. Unmeasured. Before this change: **Research code.** `ml.barrier_labels.trend_scanning_labels` (ledger C-ML1); no model is trained on the labels. |
| Related ledger entries | C-ML1, RK294, RK271, C-ML3 |

## In one paragraph

For each bar, fit linear trends over several forward windows and keep
the window whose slope has the largest t-value; the label is that
t-value's sign, and its size is the confidence. López de Prado
introduced it as a way to label training data for a classifier, or to
split history into up-, down- and no-trend regimes. It uses the future
by construction, so it is a target, never a feature, and it is not a
strategy on its own.

## The rule

```text
for L in spans: fit close[t .. t+L-1] = a + b x i; t_L = b / se(b)
L* = argmax_L |t_L|; label_t = sign(t_L*); weight_t = |t_L*|; label end t1 = t + L* - 1
```

## Evidence

* **López de Prado (2020), *Machine Learning for Asset Managers*,
  Cambridge Elements, ch. 5 (Financial Labels):** the method, earlier in
  his AFML lecture slides. (Book listing and secondary descriptions.)
* No study found of trading performance attributable to trend-scanning
  labels as such; the label's value depends on the model trained on it.

## Against, and failure modes

* Future-derived: labels must never leak into features; overlapping
  label windows need purging and embargo (the CSV's caveat).

## Fit with volatility-ai

Built as research code. Its natural use here is labelling regimes for
the learned regime sizing (V14) or validating the NATR regime against
trend states. Nothing further to build until a model is trained on it.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* López de Prado, M. (2020). *Machine Learning for Asset Managers*.
  Cambridge University Press, Elements in Quantitative Finance. Listing
  and secondary descriptions.
* This repository: `research/ml/barrier_labels.py`, ledger C-ML1; purged
  CV is C-ML3.
