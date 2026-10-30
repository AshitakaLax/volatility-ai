# Adaptive Range-Breakout with Volatility Filter

**Ledger ID RK105** · rank 105 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Trend / breakout |
| Potential effectiveness rank | 105 (1 = strongest) |
| AI implementability rank | 17 (1 = easiest) |
| Retail advantage rank | 85 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** A breakout entry is the opposite of the grid's buy-the-drop entry, and its volatility filter is already the NATR regime. |
| Implemented in volatility-ai | **Research code** `research.catalog.technical_ml`: `volatility_expansion_breakout`. |
| Related ledger entries | RK38, RK68, RK77, N1 |

## In one paragraph

Buy (or sell) a break of a rolling range only when volatility, liquidity
and trend filters agree. It is a filtered relative of Donchian and Dual
Thrust breakouts. I found no study of this filtered form; breakout
evidence is the trend-following literature's.

## Evidence

* **Breakout rules** are covered by RK38 (Donchian) and RK68 (Dual
  Thrust), whose evidence is mixed after costs for single indices.
* **This repository:** `technical_ml.volatility_expansion_breakout` and
  `williams_breakout` implement the filtered form (RK77); the N1 Dual
  Thrust gate uses the downside break as a buy gate.
* **No study found** that tests this combination as a trading strategy.

## Against, and failure modes

* Each added filter is a parameter fitted to the same history; breakouts
  on a 3x ETF whipsaw at the range edges.

## Fit with volatility-ai

The grid buys falls and sells rises; buying a breakout above a range
contradicts it. The useful half, a volatility filter, is the NATR regime
already.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* The CSV's references are je-suis-tm/quant-trading and QuantConnect's
  strategy library.
