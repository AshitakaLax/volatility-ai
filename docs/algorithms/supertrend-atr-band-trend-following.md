# Supertrend ATR-Band Trend Following

**Ledger ID RK44** · rank 44 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Trend / technical |
| Potential effectiveness rank | 44 (1 = strongest) |
| AI implementability rank | 49 (1 = easiest) |
| Retail advantage rank | 4 (1 = strongest) |
| Fit with this project | ⏳ as a long-or-cash regime · ⛔ as a stop-and-reverse trade |
| Implemented in volatility-ai | **Research code** in `research.catalog.technical_ml`: `supertrend`, `atr`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK70 (PSAR), RK38, V15 |

## In one paragraph

Draw a band at the bar's midpoint plus and minus a multiple of ATR
(commonly 3 × ATR(10)); the band ratchets with price, and the trend
flips when the close crosses the active band. It is a volatility-scaled
trailing level, close in spirit to Wilder's Parabolic SAR and the
chandelier exit. It is credited to Olivier Seban and is everywhere in
retail charting, which explains its #4 retail-advantage rank; I found no
peer-reviewed evaluation of it.

## The rule

```
mid = (high + low) / 2
upper = mid + k x ATR(n); lower = mid - k x ATR(n)                       # common: n = 10, k = 3 (also 7/3)
final lower band ratchets up while in an uptrend; final upper band ratchets down in a downtrend
trend = up when close > final upper band; down when close < final lower band
```

## Evidence

* Attributed to Olivier Seban (TradingView's documentation); later coded
  for MetaTrader by Jason Robinson. (Summaries.) Seban's book *Tout le
  monde mérite d'être riche* exists (cited by the owner-supplied Gemini
  answer), but no source confirms that it describes Supertrend.
* **No academic study found.** The only performance figures are vendor
  examples (one SMA + Supertrend backtest reporting 14.36% in a year),
  which are not evidence.
* The general record of technical rules applies (Park & Irwin 2007: 56
  of 95 modern studies positive, profits at least through the early
  1990s, most studies exposed to data snooping).

## Against, and failure modes

* Same as every trailing-level trend rule: whipsaw in ranges, lag at
  turns; defaults differ by platform (10/3 vs 7/3).
* Its ATR scaling widens the band after volatility spikes, which delays
  re-entry after a crash bottom.

## Fit with volatility-ai

A long-or-cash regime fits. Expect it to behave like PSAR, which as a
causal regime gating the TQQQ grid measured 0.06–0.17 CAGR/max DD
against NATR's 1.30–1.40 (L1).

## How to test it here

If tested: `supertrend_risk_on(daily, n=10, k=3)` in `trend_regimes.py`,
run in `tools/leverage_stepdown.py` beside `psar`, causal, with and
without `--min-hold 5`, one parameter set fixed in advance.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* TradingView support documentation (Supertrend; attribution to Olivier
  Seban) and practitioner descriptions found by search. No primary
  publication by Seban located.
* Seban, O. *Tout le monde mérite d'être riche* (Dunod; 3rd edition).
  A personal-finance book; its link to Supertrend is unconfirmed.
* Park, C.-H., Irwin, S. H. (2007). *Journal of Economic Surveys* 21(4),
  786–826. Abstract.
