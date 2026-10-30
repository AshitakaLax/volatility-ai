# Broken-Wing Butterfly

**Ledger ID RK173** · rank 173 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Options / asymmetric convexity |
| Potential effectiveness rank | 173 (1 = strongest) |
| AI implementability rank | 210 (1 = easiest) |
| Retail advantage rank | 225 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** Options are outside the instrument rule. |
| Implemented in volatility-ai | **Research code** `research.catalog.options`: `bs_price`. |
| Related ledger entries | RK286 |

## In one paragraph

Use unequal wing widths in a butterfly to tilt it directionally or
reduce its cost. It is a payoff shape, not a strategy with a premium of
its own, and I found only practitioner coverage.

## Evidence

* **No study found**; practitioner coverage only (optopsy, Cboe
  insights).

## Against, and failure modes

* Option strategies pay or collect the volatility premium and need
  option data the warehouse does not hold.

## Fit with volatility-ai

Options are outside the owner's instrument rule (long-only stocks and
ETFs), and the engine has no options data or pricing.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* The CSV's reference is optopsy (a backtesting library).
