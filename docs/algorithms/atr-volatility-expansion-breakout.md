# ATR Volatility-Expansion Breakout

**Ledger ID RK77** · rank 77 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Trend / volatility breakout |
| Potential effectiveness rank | 77 (1 = strongest) |
| AI implementability rank | 14 (1 = easiest) |
| Retail advantage rank | 91 (1 = strongest) |
| Fit with this project | ⛔ as a breakout trade (stops) · the volatility half is already this project's regime |
| Implemented in volatility-ai | **Research code** in `research.catalog.technical_ml`: `volatility_expansion_breakout`, `williams_breakout`; tested on synthetic data, not wired into the engine. Not traded as a breakout. Its downside break is the N1 Dual Thrust gate; its "volatility is expanding" measure is the NATR regime of the Ultimate design. |
| Related ledger entries | N1, RK68, RK43, RK44, L1, L6 |

## In one paragraph

Enter when price breaks a recent range while ATR or realised volatility
is expanding, on the idea that compression gives way to directional
moves. Larry Williams' volatility breakout (buy at the open plus a
fraction of the prior day's range) is the best-known form, and Dual
Thrust (RK68) is a close cousin. I found no academic test. For this
project the interesting half is the volatility measure, which runs the
other way: a NATR spike is the signal to stop holding leveraged lots,
not to buy a breakout.

## The rule

```
range = N-day high/low channel (or the prior day's range for Williams)
expansion = ATR(n) / ATR(m) > threshold (or realised vol above its median)
long when close > channel high and expansion holds; short on the mirror
Williams form: buy stop at open + k x (prior high - prior low), k around 0.5-1.0
```

## Evidence

* **Larry Williams' volatility breakout**, used by him from the 1980s
  and published in *Long-Term Secrets to Short-Term Trading* (1999).
  (Secondary sources; exact dating varies by account.)
* **No academic study found** of an ATR-confirmed breakout. Channel
  breakouts in commodity futures have support (Szakmary et al. 2010,
  RK43); the volatility confirmation is untested in that literature.
* **In this repository:** the volatility side, a causal NATR(10) regime
  against its 100-session median, is the strongest regime measured
  (CAGR/max DD 1.30–1.40; L1, L6). It is used to step *out* of TQQQ in
  high volatility, the opposite of this algorithm.

## Against, and failure modes

* False breaks at scheduled news and across overnight gaps (the CSV's
  caveat); the stop that limits them realises losses.
* Expansion often follows the break, so the filter delays entry.

## Fit with volatility-ai

As a breakout trade, out. Its parts are already here with the signs this
project's evidence supports: the downside break is the N1 gate, and
volatility expansion is the turbulent regime that moves the book to
cash or QQQ.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Williams, L. (1999). *Long-Term Secrets to Short-Term Trading*. Wiley.
  Via secondary descriptions.
* Szakmary, A. C., Shen, Q., Sharma, S. C. (2010). *Journal of Banking &
  Finance* 34(2), 409–426. Abstract.
* This repository: `research/strategies/entry_gates.py`,
  `research/strategies/natr_regime.py`, `docs/research/ultimate-algorithm.md`
  (L1, L6).
