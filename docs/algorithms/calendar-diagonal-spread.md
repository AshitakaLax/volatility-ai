# Calendar / Diagonal Spread

**Ledger ID RK166** · rank 166 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Options / volatility |
| Potential effectiveness rank | 166 (1 = strongest) |
| AI implementability rank | 201 (1 = easiest) |
| Retail advantage rank | 253 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** Options are outside the instrument rule. |
| Implemented in volatility-ai | **Research code** `research.catalog.options`: `bs_price`. |
| Related ledger entries | RK167, RK168 |

## In one paragraph

Sell a near expiry and buy a far one (diagonals also change strike) to
trade the term structure, time decay or direction. Vasquez finds the
slope of the implied-volatility term structure predicts option returns;
calendar spreads themselves have only practitioner coverage.

## Evidence

* **Vasquez (2017), *Journal of Financial and Quantitative Analysis*
  52(6):** the term-structure slope predicts option returns across five
  option strategies; bid-ask costs cut a straddle long-short from 19.6%
  to 5.5%. (Abstract and summary.)

## Against, and failure modes

* Option strategies pay or collect the volatility premium and need
  option data the warehouse does not hold.

## Fit with volatility-ai

Options are outside the owner's instrument rule (long-only stocks and
ETFs), and the engine has no options data or pricing.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Vasquez, A. (2017). Equity Volatility Term Structures and the Cross
  Section of Option Returns. *JFQA* 52(6), 2727–2754. Abstract.
