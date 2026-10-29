# Multi-Agent Mean-Field Game Optimal Execution Routing

**Ledger ID RK369** · rank 369 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Mean-field games / Execution routing / Optimal execution |
| Potential effectiveness rank | 369 (1 = strongest) |
| AI implementability rank | 692 (1 = easiest) |
| Retail advantage rank | 7,427 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **Research code** in `research.catalog.execution`: `mfg_venue_split`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK368, RK358 |

## In one paragraph

Route child orders across venues using a mean-field game of many routing
agents. Mean-field liquidation has theory (RK368); I found no routing
study, and the CSV's reference, arXiv 2005.02345, could not be
identified.

## Evidence

* **Cardaliaguet & Lehalle (2018), "Mean field game of controls and an
  application to trade crowding," *Mathematics and Financial Economics*
  12, 335–363 (arXiv 1610.09904):** liquidation when many similar
  traders' flows move prices permanently; closed-form solution,
  heterogeneous risk aversion, and learning the crowd's state day by
  day; follow the crowd, but not too fast. (Abstract.)
* **No mean-field routing study found.**

## Against, and failure modes

* Venue fees, latencies and fill probabilities are what routing turns
  on; a mean-field crowd is a weak model of them.

## Fit with volatility-ai

The grid's orders are small against TQQQ's daily volume, price-triggered
and single-venue; there is no parent order to schedule and no impact
worth modelling. Alpaca routes orders itself; there is no venue choice.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Cardaliaguet, P., Lehalle, C.-A. (2018). *Mathematics and Financial
  Economics* 12, 335–363. <https://arxiv.org/abs/1610.09904>. Abstract.
