# Meta-Labeling Primary Signals

**Ledger ID RK317** · rank 317 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Machine learning / signal filtering |
| Potential effectiveness rank | 317 (1 = strongest) |
| AI implementability rank | 253 (1 = easiest) |
| Retail advantage rank | 107 (1 = strongest) |
| Fit with this project | ✅ (V13: a model scales grid buys by the chance the lot reaches its target) |
| Implemented in volatility-ai | **Yes.** `research/ml/reachability_sizing.py` (ledger V13) is meta-labelling applied to the grid: the grid trigger is the primary signal and a LightGBM model of P(target reached) shrinks the size of each buy. Per-ticker models exist for COWZ, RSP and SPYD, not TQQQ. |
| Related ledger entries | V13, C-ML1, V14, RK213 |

## In one paragraph

Meta-labelling separates side from size. A primary model or rule decides
when and which way to trade; a secondary classifier, trained on whether
the primary signal's trades reached their profit target (triple-barrier
labels), predicts the chance this one will, and that probability filters
or sizes the trade. It turns a high-recall signal into a
higher-precision one. López de Prado introduced it; Joubert's framework
paper tests its components in a controlled experiment.

## The rule

```text
primary: the grid's buy trigger (side is always long)
label each past trigger: 1 if the lot reached its profit target before the barrier, else 0
secondary: p = P(label = 1 | features at the trigger)       # LightGBM here
size = base_size x f(p), with f mapping [0, 1] to [confidence_floor, 1]   # can only shrink
```

## Evidence

* **López de Prado (2018), *Advances in Financial Machine Learning*, ch.
  3:** the method, with triple-barrier labels. (Standard reference; not
  re-checked here.)
* **Joubert (2022), "Meta-Labeling: Theory and Framework," *Journal of
  Financial Data Science* 4(3), 31–44:** splits meta-labelling into
  three components and shows their effects on strategy metrics in a
  controlled experiment. (Abstract.)
* **Meyer, Barziy & Joubert (2023), "Meta-Labeling: Calibration and
  Position Sizing," *JFDS* 5(2), 23–40:** calibration improves fixed
  position-sizing methods but gives no significant benefit to sizing
  methods that are themselves fitted on training data. (Abstract.)
* In this repository the reachability models' held-out AUCs are about
  0.57–0.60, weakly informative (`reachability_sizing.py` docstring;
  docs/ml_plan.md).

## Against, and failure modes

* Its value is bounded by the secondary model's skill, which is weak
  here.
* Sizing down good trades costs return; the effect on corrections is
  unmeasured (V13).

## Fit with volatility-ai

This is the one way ML can touch the grid without breaking its rules: it
never decides whether to buy, never moves a target and never sells, so
it cannot strand a lot or realise a loss. The missing piece is a TQQQ
model; the existing ones cover COWZ, RSP and SPYD.

## What to measure next

Train the reachability model on TQQQ triggers with the purged
walk-forward split (C-ML3), and compare the champion with and without
the sizing over the 2020 and 2022 drawdowns, ranking by total return and
Calmar.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* López de Prado, M. (2018). *Advances in Financial Machine Learning*.
  Wiley. Ch. 3. Not re-checked.
* Joubert, J. F. (2022). "Meta-Labeling: Theory and Framework." *Journal
  of Financial Data Science* 4(3), 31–44. Abstract.
* Meyer, M., Barziy, I., Joubert, J. F. (2023). "Meta-Labeling:
  Calibration and Position Sizing." *Journal of Financial Data Science*
  5(2), 23–40. Abstract.
* This repository: `research/ml/reachability_sizing.py` (V13),
  `research/ml/barrier_labels.py` (C-ML1), docs/ml_plan.md.
