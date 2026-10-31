# TWAP Execution

**Ledger ID RK363** · rank 363 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Execution / market microstructure |
| Potential effectiveness rank | 363 (1 = strongest) |
| AI implementability rank | 301 (1 = easiest) |
| Retail advantage rank | 5,928 (1 = strongest) |
| Fit with this project | 🧪 the schedule is the zero-risk-aversion case of the Almgren-Chriss lead · ⛔ not needed |
| Implemented in volatility-ai | **Research code.** `leads.almgren_chriss` with zero risk aversion returns the straight-line (TWAP) holdings path; nothing slices live orders. Deferred: execution scheduling is [engine/roadmap.md](../../engine/roadmap.md) item 2. |
| Related ledger entries | RK364, RK365, RK366, RK244 |

## In one paragraph

Split a parent order into equal slices at equal intervals over a set
horizon, so the average fill tracks the time-weighted average price. It
is the simplest execution schedule, and the Almgren-Chriss optimum when
the trader is indifferent to timing risk. It is predictable, and
predictable flow can be detected and traded against.

## The rule

```text
slice = Q / N every T / N, for N intervals over horizon T
(each slice may rest as a limit order and convert to market near the interval end)
```

## Evidence

* **Almgren & Chriss (2001), "Optimal execution of portfolio
  transactions," *Journal of Risk* 3(2), 5–39:** with linear impact, the
  mean-variance optimal liquidation path is x_j = X sinh(κ(T − t_j)) /
  sinh(κT); with zero risk aversion it is a straight line, TWAP. The
  efficient frontier trades expected cost against timing risk. (The
  CSV's reference; standard.)
* **BIS Markets Committee (2020), "FX execution algorithms and market
  functioning" (the CSV's reference):** execution algorithms (TWAP,
  VWAP, POV, implementation shortfall) improve market functioning but
  shift execution risk to end users. (Summary; see RK244.)
* **Karpe, Fang, Ma & Wang (2020), "Multi-Agent Reinforcement Learning
  in a Realistic Limit Order Book Market Simulation," ICAIF '20 (arXiv
  2006.05574):** a double-DQN execution agent in a multi-agent ABIDES
  simulation converges toward TWAP in some scenarios. (Abstract.)

## Against, and failure modes

* Predictable timing invites front-running; ignores the intraday volume
  profile.

## Fit with volatility-ai

The grid's orders are small against TQQQ's daily volume, price-triggered
and single-venue; there is no parent order to schedule and no impact
worth modelling.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Almgren, R., Chriss, N. (2001). "Optimal execution of portfolio
  transactions." *Journal of Risk* 3(2), 5–39. Standard reference.
* BIS Markets Committee (2020). "FX execution algorithms and market
  functioning." <https://www.bis.org/publ/mktc13.htm>. Summary.
* Karpe, M., Fang, J., Ma, Z., Wang, C. (2020). ICAIF '20.
  <https://arxiv.org/abs/2006.05574>. Abstract.
* This repository: `research/catalog/leads.py` (`almgren_chriss`).
