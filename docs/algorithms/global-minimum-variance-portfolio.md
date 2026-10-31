# Global Minimum-Variance Portfolio

**Ledger ID RK60** · rank 60 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Portfolio construction |
| Potential effectiveness rank | 60 (1 = strongest) |
| AI implementability rank | 44 (1 = easiest) |
| Retail advantage rank | 69 (1 = strongest) |
| Fit with this project | ⏳ long-only weights for a multi-ETF book |
| Implemented in volatility-ai | **Yes, as a backtest book.** Selectable as `--allocator global_min_variance` in the portfolio book (`python -m tools.portfolio_book`; `research/strategies/allocator_library.py`), which routes every sale through the no-loss guard. Trading it live needs a multi-asset deployment ([engine/roadmap.md](../../engine/roadmap.md) item 1). Unmeasured. Before this change: **Research code.** `je_suis_tm_projects.markowitz_weights` returns long-only, fully invested min-variance weights (Q13's notebook); not wired into a harness. |
| Related ledger entries | Q13, A5, RK18, RK56 |

## In one paragraph

Pick the weights with the lowest estimated portfolio variance. It is the
one point on the efficient frontier that needs no expected-return
forecasts, only a covariance matrix, which is why it survives where
mean-variance fails. In US stocks since 1968 the long-only version had
about three-quarters of the market's risk with higher average returns.
It is also the parent of minimum-volatility ETFs (USMV), which this
project already holds as a defensive candidate.

## The rule

```
minimise w' Sigma w  subject to  sum w = 1, w >= 0 (long-only), optional caps per asset
Sigma: shrunk sample covariance (Ledoit-Wolf) over 1-5 years; rebalance monthly or quarterly
```

## Evidence

* **Clarke, de Silva & Thorley (2006), *Journal of Portfolio Management*
  33(1), 10–24:** the long-only minimum-variance portfolio of US stocks
  since 1968 had about three-fourths the realised risk of the
  cap-weighted market with higher average returns. (Abstract.)
* **DeMiguel, Garlappi & Uppal (2009), *Review of Financial Studies*
  22(5), 1915–1953:** of 14 optimisers on seven datasets none
  consistently beat 1/N; minimum variance is among the better ones.
  (Abstract and a citing summary.)

## Against, and failure modes

* Concentrates in historically low-volatility or highly correlated
  assets; estimated risk can shift fast (the CSV's caveat).
* Unconstrained, it piles into whatever had the lowest variance in the
  window (long bonds before 2022).

## Fit with volatility-ai

Long-only ETF weights fit the constraints. As for every allocator, the
project lacks a multi-instrument engine; the rotation harness's
additive account is the testing ground.

## How to test it here

Wire `markowitz_weights(...)["min_variance"]` as a `--mode minvar` beside
`--mode hrp` in `tools/rotation.py` (weights fitted on the warm-up only,
as HRP's are) and compare both with equal weights.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Clarke, R., de Silva, H., Thorley, S. (2006). "Minimum-Variance
  Portfolios in the U.S. Equity Market." *Journal of Portfolio
  Management* 33(1), 10–24. Abstract.
* DeMiguel, V., Garlappi, L., Uppal, R. (2009). "Optimal Versus Naive
  Diversification." *Review of Financial Studies* 22(5), 1915–1953.
  <https://econpapers.repec.org/RePEc:oup:rfinst:v:22:y:2009:i:5:p:1915-1953>.
  Abstract.
* This repository: `research/catalog/je_suis_tm_projects.py`
  (`markowitz_weights`), ledger Q13.
