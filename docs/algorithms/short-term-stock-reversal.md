# Short-Term Stock Reversal

**Ledger ID RK151** · rank 151 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Mean reversion / cross-sectional |
| Potential effectiveness rank | 151 (1 = strongest) |
| AI implementability rank | 12 (1 = easiest) |
| Retail advantage rank | 62 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** A cross-sectional stock trade with a short leg; its returns are payment for liquidity provision, which a single ETF cannot collect. |
| Implemented in volatility-ai | **Research code** `research.strategies.mean_reversion`: `contrarian_weights`, `decayed_reversal_scores`. |
| Related ledger entries | C-MR1, RK90 |

## In one paragraph

Buy last week's or month's losers and sell the winners. Short-term
reversal is one of the oldest anomalies (Jegadeesh 1990; Lehmann 1990),
and Nagel shows its returns behave like the returns to liquidity
provision, spiking when liquidity evaporates in turmoil.

## Evidence

* **Nagel (2012), *Review of Financial Studies* 25(7):** reversal
  returns proxy for liquidity-provision returns; expected returns and
  Sharpe ratios spike in market turmoil. (Abstract.)
* **This repository:** `mean_reversion.contrarian_weights` (C-MR1).

## Against, and failure modes

* High turnover in small stocks; profits concentrate in illiquid names
  and crises.

## Fit with volatility-ai

A cross-sectional stock-selection model; this project trades one
leveraged index ETF and has no stock universe, fundamentals or relation
data. The grid's buying into weakness is the single-asset echo of the
same liquidity-provision trade.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Nagel, S. (2012). Evaporating Liquidity. *Review of Financial Studies*
  25(7), 2005–2039. Abstract.
* Jegadeesh, N. (1990), Lehmann, B. (1990). Cited via secondary sources.
