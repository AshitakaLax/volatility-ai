# Put Debit Spread Momentum

**Ledger ID RK174** · rank 174 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Options / directional risk-defined |
| Potential effectiveness rank | 174 (1 = strongest) |
| AI implementability rank | 101 (1 = easiest) |
| Retail advantage rank | 40 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** Options are outside the instrument rule. |
| Implemented in volatility-ai | **Research code** `research.catalog.options`: `bs_price`. |
| Related ledger entries | RK14 |

## In one paragraph

Buy a put and sell a lower-strike put to bet on downside momentum with
defined risk. It is a bearish trade with a capped payoff; I found no
study of it as a momentum strategy.

## Evidence

* **No study found** of put spreads as a momentum strategy.

## Against, and failure modes

* Option strategies pay or collect the volatility premium and need
  option data the warehouse does not hold.

## Fit with volatility-ai

Options are outside the owner's instrument rule (long-only stocks and
ETFs), and the engine has no options data or pricing.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* The CSV's references are optopsy and Cboe insights.
