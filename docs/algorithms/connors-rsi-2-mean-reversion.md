# Connors RSI-2 Mean Reversion

**Ledger ID RK146** · rank 146 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Mean reversion |
| Potential effectiveness rank | 146 (1 = strongest) |
| AI implementability rank | 11 (1 = easiest) |
| Retail advantage rank | 116 (1 = strongest) |
| Fit with this project | ⏳ worth testing |
| Useful for volatility-ai | **Worth testing.** A long-only, single-index dip-buying rule, aligned with the grid; cheap to test as a buy gate, but its evidence is in-sample only. |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | V3, Q10, RK160 |

## In one paragraph

Buy when the 2-period RSI is deeply oversold while price is above its
200-day average, and sell on a bounce. It is the best-known short-term
mean-reversion rule for index ETFs. The original tests (1995–2007) apply
no out-of-sample split or data-mining correction; later write-ups and
informal replications on SPY report high win rates and drawdowns near a
third.

## Evidence

* **Connors & Alvarez, *Short Term Trading Strategies That Work*
  (2008):** daily stock and index data, 1995–2007; CXO Advisory notes no
  correction for data mining and no out-of-sample test. (Review.)
* **Secondary SPY backtests:** about 75% winners and 0.5% a trade, with
  drawdowns near 34% and sensitivity to parameters; in-sample and
  informal.

## Against, and failure modes

* Win rates hide the size of losing trades; on a 3x ETF a stopless dip
  buy can wait through a long decline, as the grid does.

## Fit with volatility-ai

It fits the owner's rules (long-only index ETF, no stops needed) and the
grid's logic: buy short-term weakness in an uptrend. The useful test is
RSI-2 as a gate on the grid's buys, or as a lot-size boost when
oversold, walk-forward on TQQQ with costs. Treat its published numbers
as in-sample.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Connors, L., Alvarez, C. (2008). *Short Term Trading Strategies That
  Work*. TradingMarkets. Reviewed via CXO Advisory.
