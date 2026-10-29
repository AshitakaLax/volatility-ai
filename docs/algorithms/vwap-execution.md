# VWAP Execution

**Ledger ID RK364** · rank 364 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Execution / market microstructure |
| Potential effectiveness rank | 364 (1 = strongest) |
| AI implementability rank | 329 (1 = easiest) |
| Retail advantage rank | 10,281 (1 = strongest) |
| Fit with this project | ⛔ (not needed; the VWAP is used as a gate instead, C-MS3) |
| Implemented in volatility-ai | **No** VWAP execution. The session VWAP is computed as a gate (`intraday_gates.session_vwap`, C-MS3). |
| Related ledger entries | RK251, RK363, C-MS3 |

## In one paragraph

Slice a parent order in proportion to the market's expected intraday
volume curve so the average fill tracks the volume-weighted average
price, the most common institutional benchmark. Better volume forecasts
track it more closely (RK251). For a small order, VWAP tracking is no
better than a single well-placed order.

## Evidence

* **Berkowitz, Logue & Noser (1988), "The total cost of transactions on
  the NYSE," *Journal of Finance* 43(1):** introduced the VWAP benchmark
  for execution cost. (Standard reference; not re-checked here.)
* **Białkowski, Darolles & Le Fol (2008):** dynamic volume models
  improve VWAP tracking (see RK251).
* **BIS Markets Committee (2020), "FX execution algorithms and market
  functioning" (the CSV's reference):** execution algorithms (TWAP,
  VWAP, POV, implementation shortfall) improve market functioning but
  shift execution risk to end users. (Summary; see RK244.)

## Against, and failure modes

* A benchmark, not alpha: tracking VWAP well can still buy at a bad
  price.

## Fit with volatility-ai

The grid's orders are small against TQQQ's daily volume, price-triggered
and single-venue; there is no parent order to schedule and no impact
worth modelling. The VWAP itself is already used as a buy gate (C-MS3).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Berkowitz, S. A., Logue, D. E., Noser, E. A. (1988). *Journal of
  Finance* 43(1). Not re-checked.
* BIS Markets Committee (2020). "FX execution algorithms and market
  functioning." <https://www.bis.org/publ/mktc13.htm>. Summary.
