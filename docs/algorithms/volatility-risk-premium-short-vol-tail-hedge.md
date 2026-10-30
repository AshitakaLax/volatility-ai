# Volatility Risk Premium (Short Vol + Tail Hedge)

**Ledger ID RK114** · rank 114 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Options / volatility |
| Potential effectiveness rank | 114 (1 = strongest) |
| AI implementability rank | 40 (1 = easiest) |
| Retail advantage rank | 246 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** Selling options is outside the instrument rule; the premium is real but so are its crashes. |
| Implemented in volatility-ai | **Research code** `research.catalog.options`: `wheel_select_contract`, `tail_hedge_entry_allowed`. |
| Related ledger entries | S1, RK56, RK285 |

## In one paragraph

Sell index options or straddles when implied volatility exceeds expected
realised volatility, sometimes buying far out-of-the-money protection.
The variance risk premium is one of the best-documented premia (Carr and
Wu), and the short-volatility part of a covered call earned a Sharpe
ratio near 1.0 (Israelov and Nielsen). It loses heavily in crashes.

## Evidence

* **Carr & Wu (2009), *Review of Financial Studies* 22(3):** model-free
  variance risk premiums are strongly negative on five indices and 35
  stocks, driven by an independent variance factor. (Abstract.)
* **Israelov & Nielsen (2015), *Financial Analysts Journal*:** the
  short-volatility exposure in index covered calls had a Sharpe ratio
  near 1.0. (Abstract.)
* **This repository:** option pricing, wheel and tail-hedge helpers are
  research code (S1).

## Against, and failure modes

* Short volatility loses most when the grid also loses (sell-offs),
  compounding drawdowns.

## Fit with volatility-ai

Options are outside the owner's instrument rule (long-only stocks and
ETFs), and the engine has no options data or pricing.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Carr, P., Wu, L. (2009). Variance Risk Premiums. *Review of Financial
  Studies* 22(3), 1311–1341. Abstract.
* Israelov, R., Nielsen, L. N. (2015). Covered Calls Uncovered.
  *Financial Analysts Journal* 71(6). Abstract.
