# Earnings Volatility Crush / Delta-Hedged Event Options

**Ledger ID RK170** · rank 170 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Options / event volatility |
| Potential effectiveness rank | 170 (1 = strongest) |
| AI implementability rank | 169 (1 = easiest) |
| Retail advantage rank | 165 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** Options are outside the instrument rule. |
| Implemented in volatility-ai | **Research code** `research.catalog.options`: `bs_price`. |
| Related ledger entries | V6, RK45 |

## In one paragraph

Buy or sell options around earnings against a forecast of the
announcement move. Gao, Xing and Zhang find at-the-money straddles
bought three days before announcements earned 3.34% to the announcement,
strongest in small, volatile, costly-to-trade firms; implied volatility
then collapses after the event.

## Evidence

* **Gao, Xing & Zhang (2018), *Journal of Financial and Quantitative
  Analysis* 53(6):** pre-announcement straddles earn a significant
  3.34%; limits to arbitrage keep it. (Abstract.)

## Against, and failure modes

* Option strategies pay or collect the volatility premium and need
  option data the warehouse does not hold.

## Fit with volatility-ai

Options are outside the owner's instrument rule (long-only stocks and
ETFs), and the engine has no options data or pricing.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Gao, C., Xing, Y., Zhang, X. (2018). Anticipating Uncertainty:
  Straddles around Earnings Announcements. *JFQA* 53(6), 2587–2617.
  Abstract.
