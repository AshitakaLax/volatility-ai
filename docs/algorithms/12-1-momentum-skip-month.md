# 12–1 Momentum (Skip-Month)

**Ledger ID RK6** · rank 6 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Trend / momentum (cross-sectional, stocks) |
| Potential effectiveness rank | 6 (1 = strongest) |
| AI implementability rank | 19 (1 = easiest) |
| Retail advantage rank | 11 (1 = strongest) |
| Fit with this project | ⏳ long-only top-decile basket (needs a stock universe) · ⛔ long/short |
| Implemented in volatility-ai | **Research code** in `research.catalog.factors`: `momentum_12_1`, `quantile_weights`; tested on synthetic data, not wired into the engine. The nearest code ranks a few ETFs by a 63-session return with no skip month (X3, `tools/rotation.py`). |
| Related ledger entries | X3, RK3, RK7, RK14, RK16 |

## In one paragraph

Each month, rank stocks by their return over the past twelve months
*excluding the most recent month*, buy the winners (and, in the academic
form, short the losers), and hold for a month. Skipping the last month
removes the one-month reversal that would otherwise contaminate the
signal. It is the standard definition of the equity momentum factor and
one of the best-documented anomalies there is. Here it is a stock-picking
book, which the platform does not run and has no data for; the realistic
routes are a momentum ETF as a rotation candidate, or research on the
published factor returns.

## The rule

```
every month end t:
    score_i = P_i(t-1) / P_i(t-12) - 1          # skip month t-1 to t
    long  = top decile by score (value- or equal-weighted)
    short = bottom decile (academic form only)
    hold one month, rebalance
```

Ken French's data library publishes the US momentum factor built from
prior (2–12) month returns, the same window, which makes a research test
possible without a stock database.

## Evidence

* **Jegadeesh & Titman (1993):** buying past 3–12-month winners and
  selling losers earns significant returns over 3–12-month holding
  periods, not explained by systematic risk; part of the first year's
  gain dissipates over the following two years. (Abstract.)
* **Novy-Marx (2012):** the effect comes mainly from returns 12 to 7
  months before formation rather than the most recent months, in US
  stocks and in international indices, commodities and currencies.
  (Abstract.) This is why the most recent month is skipped and why
  short lookbacks are weaker.
* **Asness, Moskowitz & Pedersen (2013):** momentum premia appear in
  eight markets and asset classes, and are negatively correlated with
  value. (Abstract.)

## Against, and failure modes

* **Crashes in rebounds.** Daniel & Moskowitz (2016): momentum crashes
  follow market declines in high-volatility "panic" states and coincide
  with the rebound. In March–May 2009 the past-loser decile rose by
  about 163% against about 8% for past winners. The crash is driven by
  the short leg; a long-only version is hit less, but still holds
  last year's winners into a rotation.
* **Turnover and costs.** Monthly decile rebalancing turns over a large
  part of the book; small-cap winners are expensive to trade.
* **Data.** A survivorship-free, point-in-time universe with delisting
  returns is required; anything less inflates the result.

## Fit with volatility-ai

* The long-only top-decile basket fits the instrument rule (standard
  stocks), but it is a cross-sectional stock book, not the TQQQ grid,
  and the warehouse holds bars for a handful of ETFs, not a stock
  universe.
* The short leg, where the crash risk and much of the academic spread
  live, is out of scope.
* The repository's evidence that matters: its volatility regime (N5,
  NATR) is calm or turbulent by exactly the "panic state" measure
  Daniel & Moskowitz use to predict crashes.

## How to test it here

1. **Research only, no new data pipeline:** download the Ken French
   momentum factor and momentum decile portfolios (monthly), and check
   whether the project's causal NATR regime on QQQ, lagged one month,
   separates momentum's good and crash months. This tests a
   transferable idea (the regime as a crash predictor), not the trade.
2. **ETF route:** add a momentum-factor ETF to `tools/rotation.py`'s
   `--universe` and let X3's relative-strength rule decide when to hold
   it. Set `--rs-days 252` to approximate a 12-month signal (the harness
   has no skip-month option yet).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Jegadeesh, N., Titman, S. (1993). "Returns to Buying Winners and
  Selling Losers: Implications for Stock Market Efficiency." *Journal
  of Finance* 48(1), 65–91.
  <https://ideas.repec.org/a/bla/jfinan/v48y1993i1p65-91.html>. Abstract.
* Novy-Marx, R. (2012). "Is Momentum Really Momentum?" *Journal of
  Financial Economics* 103(3), 429–453.
  <https://econpapers.repec.org/RePEc:eee:jfinec:v:103:y:2012:i:3:p:429-453>.
  Abstract.
* Asness, C., Moskowitz, T., Pedersen, L. H. (2013). "Value and Momentum
  Everywhere." *Journal of Finance* 68(3), 929–985.
  <https://pages.stern.nyu.edu/~lpederse/papers/ValMomEverywhere.pdf>.
  Abstract.
* Daniel, K., Moskowitz, T. (2016). "Momentum Crashes." *Journal of
  Financial Economics* 122(2), 221–247.
  <https://www.nber.org/papers/w20439>. Abstract; the 2009 figures are
  from the working paper as summarised in search results.
* Kenneth R. French data library (momentum factor, prior 2–12 returns).
  <https://mba.tuck.dartmouth.edu/pages/faculty/Ken.French/data_library.html>.
  The CSV's own reference.
