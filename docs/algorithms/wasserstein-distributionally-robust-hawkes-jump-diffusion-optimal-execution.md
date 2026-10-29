# Wasserstein Distributionally Robust Hawkes Jump-Diffusion Optimal Execution

**Ledger ID RK424** · rank 424 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-29

| | |
|---|---|
| Family | Robust statistics / Point processes / Optimal execution |
| Potential effectiveness rank | 424 (1 = strongest) |
| AI implementability rank | 992 (1 = easiest) |
| Retail advantage rank | 10,342 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK371, RK367 |

## In one paragraph

Minimise worst-case execution cost over a Wasserstein ball of Hawkes
jump-diffusion order-arrival models. Wasserstein robustness has
portfolio results (RK225); I found no robust execution study of this
form.

## Evidence

* **Almgren & Chriss (2001):** the mean-variance optimal liquidation
  path; TWAP at zero risk aversion (see RK366).
* **Blanchet, Chen & Zhou (2022), *Management Science* 68(9):**
  Wasserstein-robust mean-variance portfolios reduce to regularised
  variance minimisation (see RK225).
* **No study found** of this robust execution form.

## Against, and failure modes

* The ambiguity radius drives the answer; robust schedules mostly behave
  like higher risk aversion.

## Fit with volatility-ai

The grid's orders are small against TQQQ's daily volume, price-triggered
and single-venue; there is no parent order to schedule and no impact
worth modelling.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Almgren, R., Chriss, N. (2001). *Journal of Risk* 3(2), 5–39. Standard
  reference.
* Blanchet, J., Chen, L., Zhou, X. Y. (2022). *Management Science*
  68(9), 6382–6410. Abstract.
