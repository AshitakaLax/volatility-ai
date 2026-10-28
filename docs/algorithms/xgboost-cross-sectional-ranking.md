# XGBoost Cross-Sectional Ranking

**Ledger ID RK214** · rank 214 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | ML / cross-sectional selection |
| Potential effectiveness rank | 214 (1 = strongest) |
| AI implementability rank | 113 (1 = easiest) |
| Retail advantage rank | 23 (1 = strongest) |
| Fit with this project | ⏳ long-only top-k over an ETF or stock universe · ⛔ long-short |
| Implemented in volatility-ai | **No.** The repository's LightGBM models size grid lots (V13, V14); none ranks assets. |
| Related ledger entries | RK291, RK216, RK7 |

## In one paragraph

Train a gradient-boosted tree model (XGBoost, LightGBM) to predict
relative returns, or with a ranking loss, and hold the top of the
ranking. In the largest academic comparison, trees and neural networks
were the best cross-sectional forecasters, through nonlinear
interactions of momentum, liquidity and volatility signals. Evidence is
long-short and before costs; rank turnover is the practical enemy.

## The rule

```text
features x_i,t (momentum, volatility, liquidity, ...); target = next-period return rank (or LambdaRank loss)
fit on rolling training windows with purged validation; each period hold the top k by predicted score
```

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

## Against, and failure modes

* Rank IC and net returns must be evaluated out of sample; feature
  importance is not causality; turnover can be excessive (the CSV's
  caveat).
* Most reported gains are long-short, equal-weighted and before costs.

## Fit with volatility-ai

A long-only top-k over a small ETF universe is the relative-strength
rotation (X3) with a learned score instead of trailing return; over
stocks it is a separate book. Given that X3 itself is unmeasured, a
learned ranker is not the next step.

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
* Chen, T., Guestrin, C. (2016). "XGBoost: A Scalable Tree Boosting
  System." KDD 2016. Standard reference.
