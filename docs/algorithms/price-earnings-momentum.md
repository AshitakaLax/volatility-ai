# Price + Earnings Momentum

**Ledger ID RK29** · rank 29 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Factor / event-driven |
| Potential effectiveness rank | 29 (1 = strongest) |
| AI implementability rank | 112 (1 = easiest) |
| Retail advantage rank | 20 (1 = strongest) |
| Fit with this project | ⏳ long-only stock basket (needs earnings data) · ⛔ long/short |
| Implemented in volatility-ai | **Research code** in `research.catalog.factors`: `price_earnings_momentum`, `sue`; tested on synthetic data, not wired into the engine. The earnings calendar exists only to size grid lots on top-holding earnings days (V6). |
| Related ledger entries | RK6, RK40, RK45, V6 |

## In one paragraph

Combine price momentum with earnings momentum (a standardised earnings
surprise, or upward analyst revisions) and buy stocks strong on both.
Chan, Jegadeesh and Lakonishok found each predicts future returns after
controlling for the other, with little later reversal, and that
analysts' forecasts themselves adjust slowly: the market takes time to
absorb news. Intersecting the two signals concentrates on stocks where
the news and the price agree.

## The rule

```
monthly, for each stock:
    price momentum  = return over t-12..t-2 (RK6)
    earnings momentum = SUE (latest earnings surprise / its volatility, RK45)
                        or the 6-month change in consensus forecasts / price (RK40)
rank on each, combine (average rank or double sort), long the top group
```

## Evidence

* **Chan, Jegadeesh & Lakonishok (1996):** past return and past earnings
  surprise each predict large drifts after controlling for the other;
  little evidence of reversal for stocks with high price and earnings
  momentum; market risk, size and book-to-market do not explain them;
  analysts' forecasts respond sluggishly, especially for the worst past
  performers. NYSE, AMEX and Nasdaq stocks, 1977–1993. (Abstract and
  CFA Digest summary.)

## Against, and failure modes

* **Data timing.** Earnings and estimate data must be point-in-time
  (as known on the announcement date); restated fundamentals make
  backtests look better than live trading.
* **Crowding and valuation risk**, the CSV's caveat: high-momentum,
  high-revision stocks are often expensive and fall together.
* Same crash exposure as price momentum in rebounds.

## Fit with volatility-ai

A long-only stock book fits the instrument rule; the data (earnings
history with announcement dates, I/B/E/S-style estimates) is not in the
repository. `tools/build_earnings_calendar.py` builds release dates for
the TQQQ basket's top holdings, which is a start on timing but not on
surprises or revisions.

## What it would take

Point-in-time EPS and consensus estimates for a stock universe, then a
monthly long-only basket outside the single-symbol engine. Until then
this is a reference entry; RK45 (PEAD) is the narrower event version.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Chan, L. K. C., Jegadeesh, N., Lakonishok, J. (1996). "Momentum
  Strategies." *Journal of Finance* 51(5), 1681–1713.
  <https://ideas.repec.org/a/bla/jfinan/v51y1996i5p1681-1713.html>.
  Abstract and CFA Digest summary.
