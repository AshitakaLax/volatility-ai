# Delta-Hedged Volatility Arbitrage

**Ledger ID RK167** · rank 167 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Options / volatility |
| Potential effectiveness rank | 167 (1 = strongest) |
| AI implementability rank | 328 (1 = easiest) |
| Retail advantage rank | 6,473 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** Options are outside the instrument rule. |
| Implemented in volatility-ai | **Research code** `research.catalog.options`: `bs_price`. |
| Related ledger entries | RK309, RK166 |

## In one paragraph

Buy options whose implied volatility is low against a forecast of
realised volatility and sell those where it is high, delta-hedging in
the underlying. Goyal and Saretto's sort on historical minus implied
volatility earned large monthly returns on US equity options; later work
finds costs remove much of it.

## Evidence

* **Goyal & Saretto (2009), *Journal of Financial Economics* 94(2):**
  long-short straddles and delta-hedged options sorted on historical
  minus implied volatility, 1996–2006, robust to risk factors.
  (Abstract.)
* **Do, Foster & Gray (2016):** returns largely removed by costs in
  Australian options. (Secondary.)

## Against, and failure modes

* Option strategies pay or collect the volatility premium and need
  option data the warehouse does not hold.

## Fit with volatility-ai

Options are outside the owner's instrument rule (long-only stocks and
ETFs), and the engine has no options data or pricing.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Goyal, A., Saretto, A. (2009). Cross-section of option returns and
  volatility. *JFE* 94(2), 310–326. Abstract.
