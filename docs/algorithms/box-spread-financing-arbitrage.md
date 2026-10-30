# Box-Spread Financing Arbitrage

**Ledger ID RK172** · rank 172 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Options / synthetic lending |
| Potential effectiveness rank | 172 (1 = strongest) |
| AI implementability rank | 209 (1 = easiest) |
| Retail advantage rank | 134 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** Options are outside the instrument rule. |
| Implemented in volatility-ai | **Research code** `research.catalog.options`: `bs_price`. |
| Related ledger entries | RK171, RK92 |

## In one paragraph

Build a four-leg box that pays a fixed amount at expiry and compare its
implied rate with Treasury bills. Van Binsbergen, Diamond and Grotteria
use SPX boxes to measure a risk-free rate free of the convenience yield
on Treasuries.

## Evidence

* **van Binsbergen, Diamond & Grotteria (2022), *Journal of Financial
  Economics* 143(1):** box rates from SPX options measure risk-free
  rates without convenience yields; the gap to Treasuries widens in
  stress. (Abstract and secondary.)

## Against, and failure modes

* Option strategies pay or collect the volatility premium and need
  option data the warehouse does not hold.

## Fit with volatility-ai

Options are outside the owner's instrument rule (long-only stocks and
ETFs), and the engine has no options data or pricing.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* van Binsbergen, J. H., Diamond, W. F., Grotteria, M. (2022). Risk-free
  interest rates. *JFE* 143(1), 1–29. Abstract.
