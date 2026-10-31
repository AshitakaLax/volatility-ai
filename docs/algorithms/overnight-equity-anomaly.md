# Overnight Equity Anomaly

**Ledger ID RK154** · rank 154 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Seasonality / intraday |
| Potential effectiveness rank | 154 (1 = strongest) |
| AI implementability rank | 91 (1 = easiest) |
| Retail advantage rank | 160 (1 = strongest) |
| Fit with this project | 🧪 reference only |
| Useful for volatility-ai | **Reference only.** The overnight/intraday split is already measured (leads.overnight_intraday); as a close-to-open strategy it conflicts with the grid's hold-to-target lots. |
| Implemented in volatility-ai | **Yes.** Its own strategy id, `rk154_overnight`, selectable for backtests: `LibrarySizing` (`research/strategies/library_sizing.py`) with `signal=overnight`, component `OvernightGate`. Tune it with `signal_params`. Unmeasured. Before this change: **Research code** `research.catalog.leads`: `overnight_intraday`. |
| Related ledger entries | RK69 |

## In one paragraph

Hold from the close to the next open, isolating overnight returns. US
equity returns since the 1990s have accrued largely overnight, and Lou,
Polk and Skouras show a "tug of war": momentum profits accrue overnight,
most other anomaly profits intraday, usually with opposite signs in the
other half of the day.

## Evidence

* **Lou, Polk & Skouras (2019), *Journal of Financial Economics* 134:**
  across 14 strategies, profits are earned entirely overnight or
  entirely intraday, typically with opposite signs; momentum's are
  overnight. (Abstract.)
* **arXiv 2507.04481 (2025):** cumulative overnight returns of S&P 500
  stocks far exceeded intraday returns over 2000–2021. (Abstract.)
* **This repository:** `leads.overnight_intraday` splits returns.

## Against, and failure modes

* Two trades a day; costs and the opening auction eat much of the
  overnight return; for a 3x ETF, overnight gaps are also where the
  largest losses arrive.

## Fit with volatility-ai

Useful as measurement: whether TQQQ's grid profits come from overnight
gaps or intraday swings tells where lots should be placed. A
close-to-open rotation would fight the grid's per-lot targets.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Lou, D., Polk, C., Skouras, S. (2019). A tug of war: Overnight versus
  intraday expected returns. *Journal of Financial Economics* 134(1),
  192–213. Abstract.
* arXiv 2507.04481 (2025). Abstract.
