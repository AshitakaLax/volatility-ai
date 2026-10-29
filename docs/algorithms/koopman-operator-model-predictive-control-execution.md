# Koopman Operator Model Predictive Control Execution

**Ledger ID RK362** · rank 362 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Operator theory / Model predictive control / Execution |
| Potential effectiveness rank | 362 (1 = strongest) |
| AI implementability rank | 345 (1 = easiest) |
| Retail advantage rank | 7,426 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK201, RK366 |

## In one paragraph

Linearise price and order-flow dynamics with a Koopman dictionary and
plan child orders with model predictive control. The Koopman/MPC entries
elsewhere in the list have no trading evidence (RK201, RK206); I found
none for execution, and the CSV's reference, arXiv 2004.05678, is a
mathematical-physics paper ("Stable polynomials and crystalline
measures"), unrelated to trading.

## Evidence

* **Mann & Kutz (2016):** DMD trading with windows tuned in sample (see
  RK219).
* **Almgren & Chriss (2001), "Optimal execution of portfolio
  transactions," *Journal of Risk* 3(2), 5–39:** with linear impact, the
  mean-variance optimal liquidation path is x_j = X sinh(κ(T − t_j)) /
  sinh(κT); with zero risk aversion it is a straight line, TWAP. The
  efficient frontier trades expected cost against timing risk. (The
  CSV's reference; standard.)

## Against, and failure modes

* MPC is only as good as its model; impact models are already the hard
  part.

## Fit with volatility-ai

The grid's orders are small against TQQQ's daily volume, price-triggered
and single-venue; there is no parent order to schedule and no impact
worth modelling.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Almgren, R., Chriss, N. (2001). "Optimal execution of portfolio
  transactions." *Journal of Risk* 3(2), 5–39. Standard reference.
