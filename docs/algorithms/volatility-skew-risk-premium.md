# Volatility Skew Risk Premium

**Ledger ID RK169** · rank 169 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Options / volatility risk premium |
| Potential effectiveness rank | 169 (1 = strongest) |
| AI implementability rank | 99 (1 = easiest) |
| Retail advantage rank | 39 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** Options are outside the instrument rule. |
| Implemented in volatility-ai | **Research code** `research.catalog.options`: `bs_price`. |
| Related ledger entries | RK114 |

## In one paragraph

Trade the richness of downside against upside implied volatility with
risk reversals, put spreads or delta-hedged options. Kozhan, Neuberger
and Schneider find the skew premium is the variance premium in another
form: hedge one and the other earns nothing.

## Evidence

* **Kozhan, Neuberger & Schneider (2013), *Review of Financial Studies*
  26(9):** the skew premium explains over 40% of the S&P 500
  implied-volatility slope and reflects the same risk as the variance
  premium. (Abstract.)

## Against, and failure modes

* Option strategies pay or collect the volatility premium and need
  option data the warehouse does not hold.

## Fit with volatility-ai

Options are outside the owner's instrument rule (long-only stocks and
ETFs), and the engine has no options data or pricing.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Kozhan, R., Neuberger, A., Schneider, P. (2013). The Skew Risk Premium
  in the Equity Index Market. *RFS* 26(9), 2174–2203. Abstract.
