# Standardized Unexpected Earnings (SUE)

**Ledger ID RK207** · rank 207 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Factor / event-driven |
| Potential effectiveness rank | 207 (1 = strongest) |
| AI implementability rank | 111 (1 = easiest) |
| Retail advantage rank | 118 (1 = strongest) |
| Fit with this project | ⏳ long-only event basket · ⛔ with the short side |
| Implemented in volatility-ai | **Yes, as a backtest book.** Selectable as `--allocator standardized_unexpected_earnings` in the portfolio book (`python -m tools.portfolio_book` --data fundamentals=FILE; `research/strategies/allocator_library.py`), which routes every sale through the no-loss guard. Trading it live needs a multi-asset deployment ([engine/roadmap.md](../../engine/roadmap.md) item 1). Unmeasured. Before this change: **Research code** in `research.catalog.factors`: `sue`; tested on synthetic data, not wired into the engine. No earnings or consensus data in the warehouse. |
| Related ledger entries | RK45, RK40, V6 |

## In one paragraph

Standardised unexpected earnings: this quarter's EPS minus a forecast
(the same quarter a year ago, or the analyst consensus), divided by the
standard deviation of past surprises. Buy the highest-SUE stocks after
they report and hold for about a quarter. SUE is the classic measurement
behind the post-earnings drift (RK45), and shares its record: strong for
decades, then much weaker in large stocks since the mid-2000s.

## The rule

```text
SUE = (EPS_q - EPS_(q-4)) / std(last 8 surprises)          # seasonal random walk; or (EPS - consensus) / price
long the top decile at the next open after the announcement; hold ~60 trading days
```

## Evidence

* **Foster, Olsen & Shevlin (1984), *Accounting Review* 59(4):** returns
  drift after announcements in the direction of SUE. (Standard
  reference; not re-checked here.)
* **Bernard & Thomas (1989):** the drift is a delayed price response,
  not a risk premium. (Standard reference; see RK45.)
* **Martineau (2022), *Critical Finance Review*:** prices now absorb
  surprises on the day; no drift in large stocks since 2006. (Abstract;
  see RK45.)
* **Fink (2021), *Journal of Behavioral and Experimental Finance* 29:**
  survey of the drift literature. (Abstract; see RK45.)

## Against, and failure modes

* Point-in-time estimates and exact announcement times are essential
  (the CSV's caveat); consensus data is licensed.
* What remains of the effect is in small, illiquid names.

## Fit with volatility-ai

A long-only stock basket would pass the instrument rule but is unrelated
to the TQQQ grid, and for the mega-caps that drive the Nasdaq-100 the
drift appears to be gone. The champion's earnings-day lever (V6) sizes
on the volatility of reaction sessions, not on the surprise.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Foster, G., Olsen, C., Shevlin, T. (1984). "Earnings Releases,
  Anomalies, and the Behavior of Security Returns." *The Accounting
  Review* 59(4). Not re-checked.
* Martineau, C. (2022). "Rest in Peace Post-Earnings Announcement
  Drift." *Critical Finance Review* 11(3–4), 613–646. Abstract.
* Fink, J. (2021). "A review of the post-earnings-announcement drift."
  *Journal of Behavioral and Experimental Finance* 29, 100446. Abstract.
