# POV / Percent-of-Volume Execution

**Ledger ID RK365** · rank 365 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Execution / market microstructure |
| Potential effectiveness rank | 365 (1 = strongest) |
| AI implementability rank | 339 (1 = easiest) |
| Retail advantage rank | 5,929 (1 = strongest) |
| Fit with this project | ⛔ (not needed) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK364, RK363 |

## In one paragraph

Trade a fixed fraction of the market's realised volume (say 10%) until
the order is done, so the order speeds up when the market is active and
slows when it is quiet. Completion time is uncertain, and in a falling,
high-volume market a sell program sells faster into the decline.

## Evidence

* **BIS Markets Committee (2020), "FX execution algorithms and market
  functioning" (the CSV's reference):** execution algorithms (TWAP,
  VWAP, POV, implementation shortfall) improve market functioning but
  shift execution risk to end users. (Summary; see RK244.)
* **Almgren & Chriss (2001), "Optimal execution of portfolio
  transactions," *Journal of Risk* 3(2), 5–39:** with linear impact, the
  mean-variance optimal liquidation path is x_j = X sinh(κ(T − t_j)) /
  sinh(κT); with zero risk aversion it is a straight line, TWAP. The
  efficient frontier trades expected cost against timing risk. (The
  CSV's reference; standard.)

## Against, and failure modes

* Uncertain completion; feeds momentum in a one-sided market.

## Fit with volatility-ai

The grid's orders are small against TQQQ's daily volume, price-triggered
and single-venue; there is no parent order to schedule and no impact
worth modelling.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* BIS Markets Committee (2020). "FX execution algorithms and market
  functioning." <https://www.bis.org/publ/mktc13.htm>. Summary.
* Almgren, R., Chriss, N. (2001). "Optimal execution of portfolio
  transactions." *Journal of Risk* 3(2), 5–39. Standard reference.
