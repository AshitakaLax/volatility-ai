# Williams %R Reversal

**Ledger ID RK148** · rank 148 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Mean reversion |
| Potential effectiveness rank | 148 (1 = strongest) |
| AI implementability rank | 86 (1 = easiest) |
| Retail advantage rank | 16 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** An oscillator with no specific evidence; available via the indicator library but not worth a dedicated test. |
| Implemented in volatility-ai | **Partly.** `research.strategies.indicator_library`. |
| Related ledger entries | V15, RK162 |

## In one paragraph

Trade reversals when the close sits near the top or bottom of its recent
range. It is the stochastic oscillator inverted. Park and Irwin's review
finds technical-rule evidence mixed in stocks and plagued by data
snooping; I found no study specific to %R.

## Evidence

* **Park & Irwin (2007), *Journal of Economic Surveys* 21(4):** of 95
  modern studies, 56 positive, 20 negative, 19 mixed; most suffer from
  data snooping and ex-post rule selection. (Abstract.)
* **This repository:** the indicator library (V15) exposes TA-Lib's
  WILLR.

## Against, and failure modes

* Range-position oscillators flag "oversold" all the way down a trend.

## Fit with volatility-ai

Redundant with the RSI and Bollinger gates; no reason to prefer it.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Park, C.-H., Irwin, S. H. (2007). What Do We Know About the
  Profitability of Technical Analysis? *Journal of Economic Surveys*
  21(4), 786–826. Abstract.
