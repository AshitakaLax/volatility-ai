# Heikin-Ashi Trend Filter

**Ledger ID RK71** · rank 71 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Trend / breakout (smoothed candles) |
| Potential effectiveness rank | 71 (1 = strongest) |
| AI implementability rank | 84 (1 = easiest) |
| Retail advantage rank | 3 (1 = strongest) |
| Fit with this project | 🔬 as a regime (built, measured, worst of six) · ⛔ as a trade with stops |
| Implemented in volatility-ai | **Yes.** `--regime heikin_ashi` on `tools/leverage_stepdown.py` and `tools/rotation.py` (`trend_regimes.heikin_ashi_risk_on`, Q3); quant-trading's trade script as research code (`je_suis_tm.heikin_ashi_trades`). |
| Related ledger entries | Q3, RK46, RK70, L1 |

## In one paragraph

Heikin-Ashi ("average bar") candles replace each bar with a smoothed
synthetic one: the close is the bar's OHLC average and the open is the
midpoint of the previous synthetic candle. Runs of same-coloured candles
then mark a trend, and a colour change marks a possible turn. Dan Valcu
introduced it to Western traders in 2004. It is the third-most
retail-friendly algorithm on the list, and as a regime gating the TQQQ
grid it measured worst of the six regimes this project tried.

## The rule

```
HA_close = (open + high + low + close) / 4
HA_open  = (HA_open[t-1] + HA_close[t-1]) / 2
HA_high  = max(high, HA_open, HA_close); HA_low = min(low, HA_open, HA_close)
regime (this project): risk-on after `confirm` consecutive bullish HA candles, off after as many bearish
```

## Evidence

* **Valcu (2004), "Using the Heikin-Ashi Technique," *Technical
  Analysis of Stocks & Commodities* 22(2):** the formulas above.
  (Secondary sources.)
* **No academic study found.**
* **In this repository:** as a causal regime gating the TQQQ grid,
  CAGR/max DD −0.09–0.11, the worst of the six regimes, against NATR's
  1.30–1.40 (ultimate-algorithm.md L1).

## Against, and failure modes

* The candles are synthetic: an HA price is not a fill price (the CSV's
  caveat). A backtest that fills at HA_close is lookahead and fiction.
* Smoothing adds lag, so colour changes come after the turn.

## Fit with volatility-ai

Built and measured; it lost. Nothing further to build.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Valcu, D. (2004). "Using the Heikin-Ashi Technique." *Technical
  Analysis of Stocks & Commodities* 22(2). Formulas via secondary sources.
* This repository: `research/strategies/trend_regimes.py`,
  `research/catalog/je_suis_tm.py`, `docs/research/ultimate-algorithm.md` (L1).
