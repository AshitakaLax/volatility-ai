# Same-Calendar-Month Seasonality

**Ledger ID RK152** · rank 152 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Seasonality / event |
| Potential effectiveness rank | 152 (1 = strongest) |
| AI implementability rank | 36 (1 = easiest) |
| Retail advantage rank | 119 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** The documented effect is cross-sectional across stocks; there is no single-index version with evidence. |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK153, RK7 |

## In one paragraph

Rank stocks by their average return in the same calendar month of past
years. Heston and Sadka found individual stocks' relative returns recur
in the same month each year, independent of size, industry and earnings;
the effect holds abroad in advanced markets.

## Evidence

* **Heston & Sadka (2008), *Journal of Financial Economics* 87:**
  same-month returns recur across NYSE/AMEX stocks, 1963–2002; about 13%
  a year in a later update through 2011. (Abstract and secondary
  sources.)

## Against, and failure modes

* A long-short decile spread across thousands of stocks; nothing at the
  level of one index ETF.

## Fit with volatility-ai

A cross-sectional stock-selection model; this project trades one
leveraged index ETF and has no stock universe, fundamentals or relation
data.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Heston, S. L., Sadka, R. (2008). Seasonality in the cross-section of
  stock returns. *Journal of Financial Economics* 87(2), 418–445.
  Abstract.
