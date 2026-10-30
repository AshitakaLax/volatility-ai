# Protective Put / Collar

**Ledger ID RK133** · rank 133 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Options / hedging |
| Potential effectiveness rank | 133 (1 = strongest) |
| AI implementability rank | 252 (1 = easiest) |
| Retail advantage rank | 121 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** Options are excluded, and the evidence says holding less equity protects better per unit of return. |
| Implemented in volatility-ai | **Research code** `research.catalog.options`: `tail_hedge_slice_budget`, `tail_hedge_harvest`. |
| Related ledger entries | S1, V17, RK130 |

## In one paragraph

Buy puts to floor losses, optionally selling calls to pay for them.
Israelov finds that put protection usually gives worse drawdowns than
simply holding less equity for the same average return, because puts
carry the volatility risk premium; collars pay it too.

## Evidence

* **Israelov (2019), "Pathetic Protection," *Journal of Alternative
  Investments*:** protective puts more often than not lead to worse
  drawdowns than divesting to match the average return. (Secondary
  summaries.)
* **Israelov & Klein (2016):** index collars are not an optimal risk
  mitigation strategy because of the volatility premium they pay.
  (Secondary summary.)
* **This repository:** tail-hedge helpers are research code (S1).

## Against, and failure modes

* Protection costs the premium every month to pay off in a few.

## Fit with volatility-ai

Options are outside the owner's instrument rule (long-only stocks and
ETFs), and the engine has no options data or pricing. The project's
protection is the regime exit, which holds less equity when volatility
rises: the cheaper alternative the evidence favours.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Israelov, R. (2019). Pathetic Protection: The Elusive Benefits of
  Protective Puts. *Journal of Alternative Investments*. Secondary
  summaries.
* Israelov, R., Klein, M. (2016). Risk and Return of Equity Index
  Collars. Secondary summary.
