# Turn-of-the-Month Effect

**Ledger ID RK153** · rank 153 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Seasonality / event |
| Potential effectiveness rank | 153 (1 = strongest) |
| AI implementability rank | 37 (1 = easiest) |
| Retail advantage rank | 65 (1 = strongest) |
| Fit with this project | ⏳ worth testing |
| Useful for volatility-ai | **Worth testing.** An index-level, long-only calendar effect with long-run evidence; a cheap test as a lot-size boost or buy gate on TQQQ. |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | V6, RK152 |

## In one paragraph

Hold more equity from the last trading day of a month through the first
three of the next. McConnell and Xu found that over 1926–2005 US
investors earned essentially no market premium outside these four days;
the effect was not explained by risk, size or fund flows. Later studies
disagree on whether it persists, some finding it has shifted earlier or
faded.

## Evidence

* **McConnell & Xu (2008), *Financial Analysts Journal* 64(2):** average
  turn-of-month daily returns of 0.15% (value-weighted) and 0.22%
  (equal-weighted) over 1926–2005; no reward for market risk outside
  them; not explained by volume or flows. (Abstract.)
* **Later work:** an S&P 500 study (2001–2011) finds the effect earlier
  in the month; a 2025 paper is titled "The disappearing turn-of-month
  effect". (Secondary sources.)

## Against, and failure modes

* Calendar effects weaken once published; four days a month is few
  trades a year to confirm it out of sample.

## Fit with volatility-ai

One of the few entries that fits as is: long-only, index-level and
daily. The grid already boosts lots on event days (V6); a turn-of-month
boost or buy gate on TQQQ is a one-flag test. Judge it on post-2008 data
only, since that is where the doubt is.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* McConnell, J. J., Xu, W. (2008). Equity Returns at the Turn of the
  Month. *Financial Analysts Journal* 64(2), 49–64. Abstract.
* The disappearing turn-of-month effect (2025). Title only.
