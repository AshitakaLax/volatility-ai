# VIX Futures Term-Structure Strategy

**Ledger ID RK168** · rank 168 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Options / volatility |
| Potential effectiveness rank | 168 (1 = strongest) |
| AI implementability rank | 92 (1 = easiest) |
| Retail advantage rank | 265 (1 = strongest) |
| Fit with this project | ⏳ worth testing |
| Useful for volatility-ai | **Worth testing.** Trading VIX futures is excluded, but the term structure itself is a candidate regime input; the research code exists. |
| Implemented in volatility-ai | **Partly.** `research.catalog.leads`: `vix_term_structure_regime`. |
| Related ledger entries | RK56, V17, N5 |

## In one paragraph

Short VIX futures in contango and buy them in backwardation, hedged with
equity futures. Simon and Campasano find the basis forecasts VIX futures
returns (not spot VIX), and the hedged strategy profitable after costs.
The futures trade is out of scope; the information in the term structure
(stress when it inverts) is not.

## Evidence

* **Simon & Campasano (2014), "The VIX Futures Basis: Evidence and
  Trading Strategies":** the basis predicts VIX futures returns, not
  spot VIX changes; hedged roll strategies were profitable and robust to
  costs, 2006–2011. (Summaries.)
* **This repository:** `leads.vix_term_structure_regime` and `vix_bands`
  (VIX levels as a regime) are research code.

## Against, and failure modes

* Short VIX futures lose catastrophically in volatility spikes (February
  2018).

## Fit with volatility-ai

Keep the signal, drop the trade: a VIX/VIX3M inversion is a stress flag
that could pause new lots or trigger the regime exit. Compare it with
the NATR regime.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Simon, D. P., Campasano, J. (2014). The VIX Futures Basis: Evidence
  and Trading Strategies. *Journal of Derivatives* 21(3). Summaries.
