# Intraday Volume-Profile Execution

**Ledger ID RK251** · rank 251 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Execution / volume forecasting |
| Potential effectiveness rank | 251 (1 = strongest) |
| AI implementability rank | 102 (1 = easiest) |
| Retail advantage rank | 250 (1 = strongest) |
| Fit with this project | ⛔ (orders are price-triggered, not scheduled) |
| Implemented in volatility-ai | **No.** The intraday *volatility* profile exists (`engine/data/intraday_profile.py`, used by V9); there is no volume-curve scheduler. |
| Related ledger entries | RK256, V9, RK244 |

## In one paragraph

Forecast the day's volume curve and schedule child orders to follow it,
so a large order tracks the day's VWAP. Splitting volume into a
market-wide component and a stock-specific one, updated during the day,
improves VWAP tracking over a static historical curve.

## Evidence

* **Białkowski, Darolles & Le Fol (2008), "Improving VWAP strategies: A
  dynamic volume approach," *Journal of Banking & Finance* 32(9):** CAC
  40 stocks; market and stock-specific volume components (ARMA/SETAR)
  with intraday updating improve end-of-day VWAP tracking. (Abstract.)

## Against, and failure modes

* Volume curves shift on news, auctions and half-days; forecast error
  and participation caps belong in backtests (the CSV's caveat).

## Fit with volatility-ai

This book buys when price reaches a level, not on a schedule, and its
orders are small. The intraday volatility profile already informs sizing
(V9). Nothing to build.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Białkowski, J., Darolles, S., Le Fol, G. (2008). *Journal of Banking &
  Finance* 32(9). <https://doi.org/10.1016/j.jbankfin.2007.09.023>.
  Abstract.
* This repository: `engine/data/intraday_profile.py`, ledger V9.
