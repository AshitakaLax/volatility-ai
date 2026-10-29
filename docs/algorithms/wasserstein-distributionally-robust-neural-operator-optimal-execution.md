# Wasserstein Distributionally Robust Neural Operator Optimal Execution

**Ledger ID RK410** · rank 410 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-29

| | |
|---|---|
| Family | Robust statistics / Neural operators / Optimal execution |
| Potential effectiveness rank | 410 (1 = strongest) |
| AI implementability rank | 377 (1 = easiest) |
| Retail advantage rank | 7,430 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK370, RK326 |

## In one paragraph

Solve execution control in function space with a neural operator,
against the worst market-impact curve in a Wasserstein ball. Wasserstein
robustness has portfolio results (RK225); I found no robust execution
study of this form. The CSV's reference, arXiv 2010.08895, is the
Fourier neural operator paper, a general PDE method.

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
