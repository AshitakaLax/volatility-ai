# Gradient-Boosted Trees Return Prediction

**Ledger ID RK291** · rank 291 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Machine learning |
| Potential effectiveness rank | 291 (1 = strongest) |
| AI implementability rank | 275 (1 = easiest) |
| Retail advantage rank | 103 (1 = strongest) |
| Fit with this project | ✅ as lot sizing (V13, V14) · ⛔ as a return-direction trade |
| Implemented in volatility-ai | **Yes.** LightGBM models size grid lots: `ml_reachability_*` (V13) scores whether a lot's target is reachable, `ml_regime_*` (V14) scores crash risk. Neither predicts returns. |
| Related ledger entries | V13, V14, RK290, RK214 |

## In one paragraph

Boosted decision trees predict returns, probabilities or ranks from
technical, fundamental or macro features. They are among the best
cross-sectional forecasters in the academic comparisons. This repository
uses them differently: to size grid lots by the estimated chance of
reaching a lot's target or of a crash. Measured, the models' AUCs are
weak (0.52–0.63) and not yet connected to money.

## Evidence

* **Gu, Kelly & Xiu (2020), "Empirical Asset Pricing via Machine
  Learning," *Review of Financial Studies* 33(5), 2223–2273:** trees and
  neural networks forecast the cross-section best, through nonlinear
  interactions among predictors; the dominant signals are momentum,
  liquidity and volatility variants; economic gains in some cases double
  leading regression-based strategies. (Abstract.)
* **Krauss, Do & Huck (2017), *European Journal of Operational Research*
  259(2), 689–702:** deep nets, gradient-boosted trees and random
  forests on S&P 500 constituents, 1992–2015, daily long-short of the
  top and bottom 10; an equal-weighted ensemble earned over 0.45% a day
  before costs, with profits declining in recent years. (Abstract.)
* **In this repository** (`docs/ml_plan.md`, Phase 0): a purged
  five-fold walk-forward of LightGBM models predicting whether a 0.5%
  target is reached within a session gave AUCs of 0.52–0.63 on RSP, COWZ
  and SPYD; adding macro features helped only COWZ (+0.046), one hit in
  six comparisons, and none of it is yet connected to P&L.

## Against, and failure modes

* Forecast accuracy is not trade profitability; optimise after costs
  with leakage-safe walk-forward tests (the CSV's caveat).
* One reproducible lift in six comparisons is close to chance
  (ml_plan.md's own reading).

## Fit with volatility-ai

Built and wired as sizing levers. The open work is ml_plan.md's:
pre-register the COWZ result, test it on held-out 2025–2026 data, and
require any model to beat `hf_local_reference` through the
`SizingStrategy` interface rather than on AUC.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Gu, S., Kelly, B., Xiu, D. (2020). "Empirical Asset Pricing via
  Machine Learning." *Review of Financial Studies* 33(5), 2223–2273.
  Abstract.
* Krauss, C., Do, X. A., Huck, N. (2017). "Deep neural networks,
  gradient-boosted trees, random forests: Statistical arbitrage on the
  S&P 500." *European Journal of Operational Research* 259(2), 689–702.
  <https://ideas.repec.org/a/eee/ejores/v259y2017i2p689-702.html>.
  Abstract.
* This repository: `research/ml/reachability_sizing.py`,
  `research/ml/regime_scaled_sizing.py`, `docs/ml_plan.md`, ledger V13,
  V14.
