# Put-Call Parity Conversion / Reversal Arbitrage

**Ledger ID RK171** · rank 171 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Options / no-arbitrage |
| Potential effectiveness rank | 171 (1 = strongest) |
| AI implementability rank | 100 (1 = easiest) |
| Retail advantage rank | 224 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** Options are outside the instrument rule. |
| Implemented in volatility-ai | **Research code** `research.catalog.options`: `bs_price`. |
| Related ledger entries | RK172 |

## In one paragraph

Combine a call, a put, the underlying and financing to capture
deviations from put-call parity. Ofek, Richardson and Whitelaw find the
deviations are asymmetric toward short-sale constraints and grow with
borrowing costs: they are the price of shorting, not free money.

## Evidence

* **Ofek, Richardson & Whitelaw (2004), *Journal of Financial Economics*
  74(2):** parity violations track the cost and difficulty of shorting
  and predict returns. (Abstract.)

## Against, and failure modes

* Option strategies pay or collect the volatility premium and need
  option data the warehouse does not hold.

## Fit with volatility-ai

Options are outside the owner's instrument rule (long-only stocks and
ETFs), and the engine has no options data or pricing.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Ofek, E., Richardson, M., Whitelaw, R. F. (2004). Limited arbitrage
  and short sales restrictions. *JFE* 74(2), 305–342. Abstract.
