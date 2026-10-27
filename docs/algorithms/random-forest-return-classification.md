# Random Forest Return Classification

**Ledger ID RK290** · rank 290 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Machine learning |
| Potential effectiveness rank | 290 (1 = strongest) |
| AI implementability rank | 312 (1 = easiest) |
| Retail advantage rank | 53 (1 = strongest) |
| Fit with this project | ⏳ as a sizing or gating model · ⛔ long-short stock selection |
| Implemented in volatility-ai | **No.** The ML models here are LightGBM (V13, V14). |
| Related ledger entries | RK291, RK214, RK292 |

## In one paragraph

Train an ensemble of decision trees to classify the next period's return
(up or down, or top versus bottom of the cross-section) from engineered
features. On S&P 500 constituents the random forest was the strongest
single model in one comparison (about 0.43% a day before costs,
1992–2015), with profits fading after the early 2000s.

## The rule

```text
features x_t (returns over several lags, volatility, ...) -> P(r_(t+1) > median) by random forest
each day long the top k and short the bottom k by probability; walk-forward refits
```

## Evidence

* **Krauss, Do & Huck (2017), *European Journal of Operational Research*
  259(2), 689–702:** deep nets, gradient-boosted trees and random
  forests on S&P 500 constituents, 1992–2015, daily long-short of the
  top and bottom 10; an equal-weighted ensemble earned over 0.45% a day
  before costs, with profits declining in recent years. (Abstract.) A
  later paper reports the random forest alone at 0.43% a day.
  (Secondary.)
* **In this repository** (`docs/ml_plan.md`, Phase 0): a purged
  five-fold walk-forward of LightGBM models predicting whether a 0.5%
  target is reached within a session gave AUCs of 0.52–0.63 on RSP, COWZ
  and SPYD; adding macro features helped only COWZ (+0.046), one hit in
  six comparisons, and none of it is yet connected to P&L.

## Against, and failure modes

* Leakage, nonstationarity, class imbalance and repeated model selection
  invalidate naive backtests (the CSV's caveat).
* Daily long-short turnover; results before costs.

## Fit with volatility-ai

The repository chose gradient boosting (LightGBM) for its sizing models;
a random forest is an interchangeable learner there and would not change
the weak AUCs measured so far. Not worth a separate build.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Krauss, C., Do, X. A., Huck, N. (2017). "Deep neural networks,
  gradient-boosted trees, random forests: Statistical arbitrage on the
  S&P 500." *European Journal of Operational Research* 259(2), 689–702.
  <https://ideas.repec.org/a/eee/ejores/v259y2017i2p689-702.html>.
  Abstract.
* This repository: `docs/ml_plan.md`, `tools/evaluate_ml_features.py`.
