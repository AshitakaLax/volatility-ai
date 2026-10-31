# Cross-Sectional Momentum

**Ledger ID RK7** · rank 7 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Trend / momentum (relative) |
| Potential effectiveness rank | 7 (1 = strongest) |
| AI implementability rank | 81 (1 = easiest) |
| Retail advantage rank | 51 (1 = strongest) |
| Fit with this project | 🧪 long-only over an ETF universe (X3) · ⛔ long/short |
| Implemented in volatility-ai | **Yes, as a backtest book.** `research/strategies/allocators.py` `cross_sectional_momentum`, run by the portfolio book (`python -m tools.portfolio_book --allocator cross_sectional_momentum`), which routes every sale through the no-loss guard. Trading it live needs a multi-asset deployment ([engine/roadmap.md](../../engine/roadmap.md) item 1). Unmeasured. Before this change: **Partial.** X3 (`tools/rotation.py --mode relative_strength`) holds the single best of a small ETF universe by trailing return; no top-k basket, no short leg. Unmeasured. |
| Related ledger entries | X3, RK3, RK6, RK19, RK65 |

## In one paragraph

Rank a set of assets by trailing return and hold the leaders, optionally
shorting the laggards. It is the general form of which 12–1 stock
momentum (RK6), sector rotation (RK19) and factor momentum (RK65) are
instances. The academic premium is a long/short spread across many
assets; the long-only, few-asset version this project can run keeps the
"own what is leading" half and is closer to a tactical rotation than to
the factor.

## The rule

```
universe U, lookback k (3–12 months), skip s (0–1 month), top-k count n
every rebalance t:
    score_i = P_i(t-s) / P_i(t-k) - 1
    hold the n highest scores (equal or inverse-volatility weights)
    [academic form: short the n lowest]
```

Choices that matter more than they look: the universe (survivorship-free,
fixed in advance), the skip month, the rebalance date, and whether the
leaders are equal- or risk-weighted.

## Evidence

* **Jegadeesh & Titman (1993)** for US stocks: 3–12-month winners beat
  losers over 3–12-month holding periods. (Abstract.)
* **Asness, Moskowitz & Pedersen (2013):** the same premium in eight
  markets and asset classes (stocks in four regions, country indices,
  bonds, currencies, commodities), negatively correlated with value.
  (Abstract.)
* **Moskowitz & Grinblatt (1999):** much of individual-stock momentum is
  industry momentum (RK19).

## Against, and failure modes

* **Crashes after panics** (Daniel & Moskowitz 2016), concentrated in the
  short leg's rebound.
* **Few assets, little premium.** The documented spread comes from
  breadth; ranking four ETFs is a rotation bet whose result depends on
  which four (the same point ReSolve makes about dual momentum, RK3).
* **Whipsaw and rebalance timing** in narrow universes.

## Fit with volatility-ai

Long-only ranking of ETFs fits the constraints and is built as X3. Each
switch out of an ETF liquidates that sleeve's grid lots through the
regime-exit path, so the number of switches is a cost here in a way it
is not for the published index-holding version.

## How to test it here

* Run X3 with the defaults, then with `--rs-days 126` and `252`, over a
  universe chosen in advance (for example QQQ, RSP, XLP, USMV, GLD),
  and report switches alongside CAGR and drawdown.
* Add a top-2 option (hold the two leaders, half each) to see whether
  breadth reduces the switch cost; it would be a small change to
  `assign_relative_strength`.
* Score the family together with the deflated Sharpe ratio and PBO
  (ledger C-ML4).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Jegadeesh, N., Titman, S. (1993). *Journal of Finance* 48(1), 65–91.
  <https://ideas.repec.org/a/bla/jfinan/v48y1993i1p65-91.html>. Abstract.
* Asness, C., Moskowitz, T., Pedersen, L. H. (2013). "Value and Momentum
  Everywhere." *Journal of Finance* 68(3), 929–985.
  <https://econpapers.repec.org/RePEc:bla:jfinan:v:68:y:2013:i:3:p:929-985>.
  Abstract.
* Moskowitz, T., Grinblatt, M. (1999). "Do Industries Explain
  Momentum?" *Journal of Finance* 54(4), 1249–1290.
  <https://ideas.repec.org/a/bla/jfinan/v54y1999i4p1249-1290.html>.
  Abstract.
* Daniel, K., Moskowitz, T. (2016). "Momentum Crashes." *Journal of
  Financial Economics* 122(2), 221–247.
  <https://www.nber.org/papers/w20439>. Abstract.
