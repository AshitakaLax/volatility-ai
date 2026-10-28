# Lead-Lag Cross-Asset Predictive Trading

**Ledger ID RK204** · rank 204 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Cross-asset / statistical |
| Potential effectiveness rank | 204 (1 = strongest) |
| AI implementability rank | 139 (1 = easiest) |
| Retail advantage rank | 105 (1 = strongest) |
| Fit with this project | 🧪 the estimator · ⏳ as an entry-timing input (Nasdaq-100 futures leading TQQQ) · ⛔ as a latency trade |
| Implemented in volatility-ai | **Research code.** `leads.lagged_cross_correlation` and `leads.hy_lead_lag` (the Hayashi–Yoshida covariance with the Hoffmann–Rosenbaum–Yoshida lead estimate), a gap-analysis lead for Nasdaq-100 futures leading the ETF; no trading rule. |
| Related ledger entries | RK100, RK221, RK257 |

## In one paragraph

When one market absorbs news before a related one, the leader's last
move forecasts the follower's next. At tick level the effect is well
documented: liquid assets lead illiquid ones and index futures lead
their stocks, and the leader's past predicts the lagger's next mid-quote
move about 60% of the time. But the predicted move is smaller than the
bid/ask spread, so a strategy that takes liquidity cannot profit; the
edge belongs to market makers and co-located traders.

## The rule

```text
lead time: theta* = argmax_theta |HY-corr(x_t, y_(t+theta))| on asynchronous ticks (Hoffmann-Rosenbaum-Yoshida)
signal: sign(leader return over the last theta*) = expected sign of the follower's next move
trade only if the expected move exceeds half the spread plus fees
```

## Evidence

* **Huth & Abergel, "High frequency lead/lag relationships — Empirical
  facts" (arXiv 1111.7103):** tick data and the Hayashi–Yoshida
  estimator; strongly asymmetric cross-correlations, above all futures
  leading stocks; the most liquid assets lead; intraday seasonality,
  with shifts around macro announcements and the US open; about 60%
  accuracy forecasting the lagger's next mid-quote move, yet no profit
  for a market-order strategy after the spread. (Abstract.)
* **Lo & MacKinlay (1990), *Review of Financial Studies* 3(2):**
  large-stock returns lead small-stock returns at weekly horizons, one
  source of contrarian profits. (Standard reference; not re-checked
  here.)
* **Stübinger (2019)**, lead-lag causal paths on minute S&P 500 data, is
  on RK100.

## Against, and failure modes

* Timestamp leakage, latency, stale quotes and venue fees (the CSV's
  caveat); the effect is competed away as participants adapt.
* At bar frequencies the lead usually sits inside one bar and vanishes.

## Fit with volatility-ai

TQQQ is priced off the Nasdaq-100, and Nasdaq-100 futures trade nearly
around the clock, so a lead exists in principle. It would not be a trade
here; at most an entry-timing input for the grid (do not buy TQQQ if
futures have already fallen since its last print). The estimator is
already written.

## How to test it here

Run `leads.hy_lead_lag` on Nasdaq-100 futures (or QQQ) against TQQQ
one-minute bars for a sample of sessions. If the best shift is under one
bar, the lead is invisible to a one-minute grid and there is nothing to
build.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Huth, N., Abergel, F. "High frequency lead/lag relationships —
  Empirical facts." <https://arxiv.org/abs/1111.7103>. Abstract.
* Lo, A. W., MacKinlay, A. C. (1990). "When Are Contrarian Profits Due
  to Stock Market Overreaction?" *Review of Financial Studies* 3(2). Not
  re-checked.
* This repository: `research/catalog/leads.py`
  (`lagged_cross_correlation`, `hayashi_yoshida`, `hy_lead_lag`).
