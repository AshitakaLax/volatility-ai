# Public Activist-Filing Event Strategy

**Ledger ID RK47** · rank 47 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Event-driven / public filings / shareholder activism |
| Potential effectiveness rank | 47 (1 = strongest) |
| AI implementability rank | 62 (1 = easiest) |
| Retail advantage rank | 90 (1 = strongest) |
| Fit with this project | ⏳ (long-only event basket; a separate book) |
| Implemented in volatility-ai | **Research code** in `research.catalog.factors`: `activist_score`, `market_model_car`, `event_drift_trades`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK39 |

## In one paragraph

Watch SEC EDGAR for Schedule 13D filings, which an investor must file
after crossing 5% ownership with intent to influence the company. Parse
the filer, stake and stated demands, and buy the targets that remain
liquid and have not already repriced. Hedge-fund activism announcements
carried about a 7% abnormal return that did not reverse over the
following year. As the CSV warns, much of that move happens at or
before disclosure, so the return available after the filing is smaller
and unmeasured.

## The rule

```
on each new SC 13D (not 13D/A unless the purpose changes): parse filer, target, stake, Item 4 purpose
filter: known activist, liquid target, post-filing reaction not already large (e.g. < +5% from the prior close)
buy at the next open after the filing time stamp; hold 6-12 months or until the campaign resolves
```

## Evidence

* **Brav, Jiang, Partnoy & Thomas (2008), "The Returns to Hedge Fund
  Activism," *Financial Analysts Journal* 64(6), 45–61 (the CSV's
  reference):** 2001–2006, hand-collected; about 7% abnormal return
  around the announcement with no reversal over the next year; activists
  succeed fully or partly in two-thirds of cases; median holding about a
  year. (Abstract.)
* The SEC shortened the initial 13D deadline from 10 calendar days to 5
  business days (rules adopted in 2023), which narrows the pre-filing
  window. (Recalled; verify the effective dates.)

## Against, and failure modes

* Announcement returns are not a post-filing strategy return; separate
  the filing time from the trade date; overnight gaps and spreads (the
  CSV's caveat).
* Event flow is lumpy; small-cap targets are thin.

## Fit with volatility-ai

A long-only stock event book would pass the instrument rule, and EDGAR is
free, but it is a separate strategy with no link to the TQQQ grid.

## What it would take

An EDGAR full-text poller for SC 13D, point-in-time prices for the
targets, and a backtest that enters only after the filing's acceptance
time stamp.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Brav, A., Jiang, W., Partnoy, F., Thomas, R. S. (2008). *Financial
  Analysts Journal* 64(6), 45–61. <https://doi.org/10.2469/faj.v64.n6.7>.
  Abstract.
* ECGI working paper, "Value creation in shareholder activism" (the
  CSV's second reference). Not opened.
* SEC EDGAR full-text search (the CSV's third reference).
