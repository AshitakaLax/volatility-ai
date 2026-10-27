# Multi-Timeframe Trend Agreement

**Ledger ID RK78** · rank 78 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Trend / signal confirmation |
| Potential effectiveness rank | 78 (1 = strongest) |
| AI implementability rank | 16 (1 = easiest) |
| Retail advantage rank | 181 (1 = strongest) |
| Fit with this project | ⏳ as a long-or-cash confirmation layer · ⛔ with a short side |
| Implemented in volatility-ai | **No.** The pieces exist (daily regimes in `trend_regimes.py`, intraday gates in `entry_gates.py`), but nothing requires them to agree. |
| Related ledger entries | RK1, RK2, RK17, L1 |

## In one paragraph

Hold a directional position only when short-, medium- and
long-horizon trend signals agree (Alexander Elder's "Triple Screen" is
the practitioner form: a weekly trend, a daily oscillator against it,
an intraday entry). It trades less and enters later than any single
signal. The academic trend literature usually *averages* horizons
rather than requiring agreement: Hurst, Ooi & Pedersen combine 1-, 3-
and 12-month time-series momentum and find it profitable across a
century. Requiring agreement is the stricter, slower variant, and I
found no study of it.

## The rule

```
signals: s_short, s_medium, s_long in {+1, -1}   # e.g. 1-, 3-, 12-month TSMOM, or weekly/daily/intraday
agreement form: position = +1 only when all three are +1 (long-or-cash); exit when any turns -1
averaging form (the literature's): weight = mean(s_short, s_medium, s_long)
no unfinished higher-timeframe bar may inform a lower-timeframe decision
```

## Evidence

* **Hurst, Ooi & Pedersen (2017), "A Century of Evidence on
  Trend-Following Investing," *Journal of Portfolio Management* 44(1),
  15–29:** 1-, 3- and 12-month TSMOM signals, combined, profitable in
  every decade since 1880 with low correlation to traditional assets.
  (Abstract and summaries; the combination weights were not verified.)
* **Elder, A. (1993), *Trading for a Living*:** the Triple Screen
  system, first published in *Futures* magazine in April 1986.
  (Secondary sources.)
* **No academic study found** of the agreement (all-must-agree) form.

## Against, and failure modes

* Leakage is the CSV's caveat and the usual bug: a weekly bar that has
  not closed must not drive a daily decision.
* Every extra confirmation adds lag; on a book that sells into risk-off,
  later exits mean deeper drawdowns before the switch (L1).

## Fit with volatility-ai

A long-or-cash version fits, as a variant of RK1/RK2's long-or-cash
TSMOM. The project's evidence is that direction regimes lose to the
volatility regime on this book (L1), and agreement makes a direction
regime slower still, so expectations are low.

## How to test it here

If tested: `tools/leverage_stepdown.py` with a regime that is risk-on
only when the 1-, 3- and 12-month QQQ returns are all positive, causal,
lagged one session, beside the averaging version and the 12-month signal
alone. One parameter set fixed in advance.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Hurst, B., Ooi, Y. H., Pedersen, L. H. (2017). "A Century of Evidence
  on Trend-Following Investing." *Journal of Portfolio Management* 44(1),
  15–29. AQR-hosted abstract and summaries.
* Elder, A. (1993). *Trading for a Living*. Wiley. Secondary
  descriptions.
* This repository: `research/strategies/trend_regimes.py`,
  `research/strategies/entry_gates.py`, `docs/research/ultimate-algorithm.md` (L1).
