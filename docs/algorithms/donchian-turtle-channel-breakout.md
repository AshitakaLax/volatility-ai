# Donchian / Turtle Channel Breakout

**Ledger ID RK43** · rank 43 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Trend / breakout |
| Potential effectiveness rank | 43 (1 = strongest) |
| AI implementability rank | 107 (1 = easiest) |
| Retail advantage rank | 261 (1 = strongest) |
| Fit with this project | ⛔ as published (2N stops, short side) · 🧪 the scale-in pyramid (C-G5) |
| Implemented in volatility-ai | **Research code.** The full Turtle trade with stops (`trend_following.turtle_original_trades`, `letianzj_turtle_trades`) and the in-scope scale-in (`position_sizing.TurtlePyramid`); ledger C-G5. |
| Related ledger entries | C-G5, C-RJ5, RK67, RK1 |

## In one paragraph

Buy when price breaks above its N-day high, sell (or short) when it
breaks below its M-day low: Richard Donchian's channel rule, made famous
by the Turtle traders (20-day entry, 10-day exit; 55/20 for the slow
system), with ATR-based units and pyramiding. Channel breakouts are the
other classic trend rule besides moving averages, and in commodity
futures they have one of the better academic records: positive net of
costs in at least 22 of 28 markets over 48 years. Equity indices are a
weaker fit, and the stops and shorts are out of scope here.

## The rule

```
entry long:  close > highest high of the last 20 days (system 1) or 55 days (system 2)
exit long:   close < lowest low of the last 10 (or 20) days, or a 2N stop below entry (N = 20-day ATR)
size:        units of 1% equity / N; add a unit every +0.5 N, up to 4 units
(short side mirrors it)
```

## Evidence

* **Szakmary, Shen & Sharma (2010), *Journal of Banking & Finance*
  34(2), 409–426:** monthly data, 48 years, 28 commodity futures; every
  parameterisation of channel and dual-moving-average rules earned
  positive mean excess returns net of costs in at least 22 of 28
  markets, and pooled returns were hugely significant across most
  subperiods, robust to data-mining adjustments and costs. (Abstract.)
* **Faith (2003), "The Original Turtle Trading Rules":** the rule set
  above. (Transcribed in `research/catalog/trend_following.py`.)
* **Park & Irwin (2007):** of 95 modern studies of technical trading, 56
  positive, 20 negative, 19 mixed; early studies found profits in FX and
  futures but not stocks, modern ones across markets at least through
  the early 1990s; most suffer from data snooping and ex-post rule
  selection. (Abstract.)

## Against, and failure modes

* Long flat periods and whipsaw between trends; the Turtles' reported
  edge has faded since the 1980s, a common pattern for published rules.
* The 2N stop realises losses (excluded here); the short side is
  essential in futures.
* **Source quirk in this repo:** letianzj's `turtle.py` computes its
  "10-day low" exit as the max of the highs (`textbook_exit=True` fixes
  it; ledger §8B).

## Fit with volatility-ai

As published, out of scope. The part kept is C-G5's scale-in: rebuild
TQQQ inventory on strength after a regime exit, buying confirmation
instead of the low. A long-or-cash Donchian regime (in after a 55-day
high, out after a 20-day low) would be a direction regime like RK17 and
RK62, with the same expected result here (L1).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Szakmary, A. C., Shen, Q., Sharma, S. C. (2010). "Trend-Following
  Trading Strategies in Commodity Futures: A Re-examination." *Journal
  of Banking & Finance* 34(2), 409–426.
  <https://econpapers.repec.org/RePEc:eee:jbfina:v:34:y:2010:i:2:p:409-426>.
  Abstract.
* Park, C.-H., Irwin, S. H. (2007). "What Do We Know About the
  Profitability of Technical Analysis?" *Journal of Economic Surveys*
  21(4), 786–826. Abstract.
* Faith, C. (2003). "The Original Turtle Trading Rules" (the CSV's
  reference, via its ATR-sizing row). As transcribed in this repository.
* This repository: `research/catalog/trend_following.py`,
  `research/strategies/position_sizing.py`, ledger C-G5.
