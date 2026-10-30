# Stochastic Oscillator Reversal

**Ledger ID RK162** · rank 162 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Mean reversion |
| Potential effectiveness rank | 162 (1 = strongest) |
| AI implementability rank | 85 (1 = easiest) |
| Retail advantage rank | 80 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** No specific evidence; available as an indicator but redundant with RSI and Bollinger gates. |
| Implemented in volatility-ai | **Partly.** `research.strategies.indicator_library`. |
| Related ledger entries | V15, RK148 |

## In one paragraph

Trade %K/%D crossovers in overbought and oversold zones. It is a
range-position oscillator like Williams %R (RK148); I found no study
specific to it beyond the general technical analysis literature.

## Evidence

* **Park & Irwin (2007):** mixed evidence for technical rules in stocks.
  (Abstract.)
* **This repository:** the indicator library (V15) exposes TA-Lib's
  STOCH.

## Against, and failure modes

* Crossovers inside the zones whipsaw in trends.

## Fit with volatility-ai

Redundant with the gates already researched.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Park, C.-H., Irwin, S. H. (2007). *Journal of Economic Surveys* 21(4).
  Abstract.
