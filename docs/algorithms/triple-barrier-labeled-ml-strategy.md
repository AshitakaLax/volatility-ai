# Triple-Barrier Labeled ML Strategy

**Ledger ID RK294** · rank 294 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Machine learning / event-based labels |
| Potential effectiveness rank | 294 (1 = strongest) |
| AI implementability rank | 150 (1 = easiest) |
| Retail advantage rank | 135 (1 = strongest) |
| Fit with this project | 🧪 as labels for lot outcomes (C-ML1) |
| Implemented in volatility-ai | **Partial.** `ml.barrier_labels.triple_barrier_labels` (ledger C-ML1); no classifier is trained on the labels. |
| Related ledger entries | C-ML1, RK213, RK271, V13 |

## In one paragraph

Label each candidate trade by which barrier it touches first: a profit
target, a stop (or lower barrier) or a time limit; then train a
classifier on those labels, often as a meta-model deciding whether to
take a primary signal's trade and how large. López de Prado's method
maps unusually well onto this project: a grid lot is a trade with a
fixed profit target, a regime-exit level and a maximum hold.

## The rule

```text
for each event t0: upper = p0 x (1 + target), lower = p0 x (1 - stop), vertical = t0 + max_hold
label = +1 / -1 / 0 by the first barrier touched; train a (meta-)classifier on features known at t0
```

## Evidence

* **López de Prado (2018), *Advances in Financial Machine Learning*, ch.
  3:** the triple-barrier method and meta-labelling. (Standard
  reference; not re-opened.)
* **In this repository** (`docs/ml_plan.md`, Phase 0): a purged
  five-fold walk-forward of LightGBM models predicting whether a 0.5%
  target is reached within a session gave AUCs of 0.52–0.63 on RSP, COWZ
  and SPYD; adding macro features helped only COWZ (+0.046), one hit in
  six comparisons, and none of it is yet connected to P&L. Its `reached`
  label is a two-barrier form of the same idea (target within a
  horizon).

## Against, and failure modes

* A labelling method, not a strategy; labels overlap and validation must
  respect that (the CSV's caveat).

## Fit with volatility-ai

The barriers map one to one onto a lot (target, regime-exit level,
maximum hold), and V13's reachability label is already a two-barrier
form. The labels are built; the missing piece is the meta-model trained
on them, which is ml_plan.md's next step in substance.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* López de Prado, M. (2018). *Advances in Financial Machine Learning*.
  Wiley. Standard reference; chapters as cited, not re-opened here.
* This repository: `research/ml/barrier_labels.py` (C-ML1),
  `research/ml/labels.py`, `docs/ml_plan.md`.
