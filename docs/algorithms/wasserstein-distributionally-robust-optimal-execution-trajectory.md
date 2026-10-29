# Wasserstein Distributionally Robust Optimal Execution Trajectory

**Ledger ID RK370** · rank 370 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Robust statistics / Optimal execution / Institutional execution |
| Potential effectiveness rank | 370 (1 = strongest) |
| AI implementability rank | 348 (1 = easiest) |
| Retail advantage rank | 10,164 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK366, RK371, RK225 |

## In one paragraph

Choose the liquidation path that minimises cost under the worst
price-impact and volatility model in a Wasserstein ball around the
estimated one. Robust execution with model uncertainty has a literature,
and Wasserstein robustness has portfolio results (RK225); I found no
Wasserstein-robust execution study, and the CSV's reference, arXiv
1908.01234, looks like a placeholder ID (sequential digits, like arXiv
1908.01234 on RK97) and could not be identified.

## Evidence

* **Almgren & Chriss (2001), "Optimal execution of portfolio
  transactions," *Journal of Risk* 3(2), 5–39:** with linear impact, the
  mean-variance optimal liquidation path is x_j = X sinh(κ(T − t_j)) /
  sinh(κT); with zero risk aversion it is a straight line, TWAP. The
  efficient frontier trades expected cost against timing risk. (The
  CSV's reference; standard.)
* **Blanchet, Chen & Zhou (2022):** Wasserstein-robust mean-variance
  portfolios (see RK225).
* **No Wasserstein-robust execution study found.**

## Against, and failure modes

* The ambiguity radius drives the schedule; a robust schedule mostly
  trades faster, as a higher risk aversion would.

## Fit with volatility-ai

The grid's orders are small against TQQQ's daily volume, price-triggered
and single-venue; there is no parent order to schedule and no impact
worth modelling.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Almgren, R., Chriss, N. (2001). "Optimal execution of portfolio
  transactions." *Journal of Risk* 3(2), 5–39. Standard reference.
