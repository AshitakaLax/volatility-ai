# Implementation-Shortfall / Almgren–Chriss

**Ledger ID RK366** · rank 366 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Execution / market microstructure |
| Potential effectiveness rank | 366 (1 = strongest) |
| AI implementability rank | 224 (1 = easiest) |
| Retail advantage rank | 9,810 (1 = strongest) |
| Fit with this project | 🧪 research code (the trajectory) · ⏳ as a measurement (shortfall of each fill, RK250) |
| Implemented in volatility-ai | **Research code.** `leads.almgren_chriss` and `almgren_chriss_objective` compute the optimal holdings path, expected cost and variance; the live loop does not record shortfall. Deferred: execution scheduling is [engine/roadmap.md](../../engine/roadmap.md) item 2. |
| Related ledger entries | RK250, RK363, RK244 |

## In one paragraph

Implementation shortfall measures execution against the price when the
decision was made, counting impact, delay and the cost of what never
filled (Perold). An implementation-shortfall algorithm minimises
expected shortfall plus a penalty on its variance, which in the
Almgren-Chriss model front-loads trading as risk aversion rises.

## The rule

```text
minimise E[cost] + lambda Var[cost] over holdings x_0 = X, ..., x_N = 0
optimum: x_j = X sinh(kappa (T - t_j)) / sinh(kappa T), cosh(kappa tau) = 1 + tau^2 lambda sigma^2 / (2 eta~)
shortfall of a fill = side x (fill price - decision price) x quantity (+ fees, + missed-fill opportunity cost)
```

## Evidence

* **Perold (1988), "The implementation shortfall: paper versus reality,"
  *Journal of Portfolio Management* 14(3), 4–9:** measures execution by
  the gap between a paper portfolio traded at decision prices and the
  real one, including the opportunity cost of unfilled orders; the Value
  Line paper portfolio returned 26.2% a year (1979–1991) against 16.1%
  for the real fund (a later paper's figures). (Secondary sources.)
* **Almgren & Chriss (2001), "Optimal execution of portfolio
  transactions," *Journal of Risk* 3(2), 5–39:** with linear impact, the
  mean-variance optimal liquidation path is x_j = X sinh(κ(T − t_j)) /
  sinh(κT); with zero risk aversion it is a straight line, TWAP. The
  efficient frontier trades expected cost against timing risk. (The
  CSV's reference; standard.)

## Against, and failure modes

* Linear impact and known volatility are strong assumptions; the
  parameters are hard to estimate for small traders.

## Fit with volatility-ai

The grid's orders are small against TQQQ's daily volume, price-triggered
and single-venue; there is no parent order to schedule and no impact
worth modelling. The measurement is the useful part: logging each live
grid buy's shortfall against the trigger price, as RK250 proposes, would
show what extended-hours limit pricing costs.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Perold, A. F. (1988). "The implementation shortfall: paper versus
  reality." *Journal of Portfolio Management* 14(3), 4–9. Secondary
  sources.
* Almgren, R., Chriss, N. (2001). "Optimal execution of portfolio
  transactions." *Journal of Risk* 3(2), 5–39. Standard reference.
* This repository: `research/catalog/leads.py` (`almgren_chriss`,
  `almgren_chriss_objective`).
