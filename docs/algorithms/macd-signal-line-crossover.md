# MACD Signal-Line Crossover

**Ledger ID RK46** · rank 46 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Trend / momentum |
| Potential effectiveness rank | 46 (1 = strongest) |
| AI implementability rank | 80 (1 = easiest) |
| Retail advantage rank | 10 (1 = strongest) |
| Fit with this project | 🔬 as a regime (built, measured) · ⛔ as a long/short trade |
| Implemented in volatility-ai | **Yes.** `--regime macd` (MACD line above its 9-period signal line, EMA 12/26) on `tools/leverage_stepdown.py` and `tools/rotation.py` (`trend_regimes.macd_risk_on`, ledger Q1); quant-trading's script as a trade is research code. |
| Related ledger entries | Q1, Q5, RK62, L1 |

## In one paragraph

MACD is the gap between a 12- and a 26-period EMA; its signal line is a
9-period EMA of that gap. Long when MACD crosses above the signal line,
out (or short) when it crosses below, sometimes only when MACD is above
zero. Gerald Appel created it in the 1970s; academic tests find its
profitability depends on the market and the parameters, not that it
reliably beats holding. This project built it as a causal regime and
measured it on the TQQQ grid: one of the weaker regimes it tried.

## The rule

```
macd = EMA(close, 12) - EMA(close, 26); signal = EMA(macd, 9)
risk-on while macd > signal (optional: and macd > 0); act at the next session
```

## Evidence

* **Origin:** Gerald Appel, 1970s (accounts give 1970, around 1977, or
  the 1960s); the 12/26/9 default is a convention, and one paper notes
  Appel suggested 8/17/9 for buys and 12/25/9 for sells. (Summaries.)
* **Academic tests are mixed:** on Italian stocks a 12/26/0 variant beat
  buy-and-hold while 12/26/9 did not; a simulation of 19,456 MACD models
  on Nikkei 225 futures (*JRFM* 2021) found filters helped mostly for
  optimised parameters. (Summaries.)
* **In this repository:** as a causal regime gating the TQQQ grid,
  CAGR/max DD 0.12–0.26 against 1.30–1.40 for the NATR volatility regime
  (ultimate-algorithm.md L1).

## Against, and failure modes

* A transformation of price, not independent information (the CSV's
  caveat); it lags at turns and whipsaws in ranges.
* On this book, every risk-off flip liquidates grid lots (N10's debounce
  exists for this).

## Fit with volatility-ai

Built and measured; it fits as a regime and lost to the volatility
regime. Unless a new use appears (for example as a tie-breaker inside
the turbulent regime), there is nothing further to build.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Appel, G. Attribution and parameter history via secondary sources.
* "Filtering rules for MACD" study on Nikkei 225 futures, *Journal of
  Risk and Financial Management* 14(1), 2021
  (<https://doi.org/10.3390/jrfm14010037>). Summary.
* This repository: `research/strategies/trend_regimes.py`,
  `research/catalog/je_suis_tm.py`, `docs/research/ultimate-algorithm.md`.
* The CSV's own references: je-suis-tm/quant-trading; QuantConnect
  indicators.
