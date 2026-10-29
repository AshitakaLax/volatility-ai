# Continuous-Time Mean-Field Control Execution

**Ledger ID RK368** · rank 368 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Optimal execution / Mean-field games |
| Potential effectiveness rank | 368 (1 = strongest) |
| AI implementability rank | 690 (1 = easiest) |
| Retail advantage rank | 2,120 (1 = strongest) |
| Fit with this project | ⛔ (large-order execution theory) |
| Implemented in volatility-ai | **Research code** in `research.catalog.execution`: `mean_field_execution`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK369, RK366 |

## In one paragraph

Treat many traders liquidating similar positions as a mean-field
population: each one's cost depends on the crowd's aggregate trading
through permanent impact, and the equilibrium speed has a closed form.
The finding is to follow the crowd but not too fast. The CSV's
reference, arXiv 2005.02345, could not be identified.

## Evidence

* **Cardaliaguet & Lehalle (2018), "Mean field game of controls and an
  application to trade crowding," *Mathematics and Financial Economics*
  12, 335–363 (arXiv 1610.09904):** liquidation when many similar
  traders' flows move prices permanently; closed-form solution,
  heterogeneous risk aversion, and learning the crowd's state day by
  day; follow the crowd, but not too fast. (Abstract.)

## Against, and failure modes

* Assumes a crowd of similar, rational liquidators; the crowd's state
  must be estimated.

## Fit with volatility-ai

The grid's orders are small against TQQQ's daily volume, price-triggered
and single-venue; there is no parent order to schedule and no impact
worth modelling.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Cardaliaguet, P., Lehalle, C.-A. (2018). *Mathematics and Financial
  Economics* 12, 335–363. <https://arxiv.org/abs/1610.09904>. Abstract.
