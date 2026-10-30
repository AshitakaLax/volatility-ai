# FX Mean-Reversion / Momentum Hybrid

**Ledger ID RK163** · rank 163 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Mean reversion / FX |
| Potential effectiveness rank | 163 (1 = strongest) |
| AI implementability rank | 87 (1 = easiest) |
| Retail advantage rank | 63 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** Currencies are outside the instrument rule. |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK30, Q6 |

## In one paragraph

Switch between momentum and reversion in currencies by volatility, trend
strength or market state. Currency momentum earns up to about 10% a year
between winners and losers, distinct from carry and limited by
transaction costs (Menkhoff, Sarno, Schmeling and Schrimpf).

## Evidence

* **Menkhoff, Sarno, Schmeling & Schrimpf (2012), *Journal of Financial
  Economics* 106(3):** a cross-sectional currency momentum spread of up
  to about 10% a year, partly explained by costs and distinct from
  carry. (Abstract.)

## Against, and failure modes

* Switching rules add a state model on top of two noisy signals.

## Fit with volatility-ai

Currencies are outside the owner's instrument rule (long-only stocks and
ETFs).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Menkhoff, L., Sarno, L., Schmeling, M., Schrimpf, A. (2012). Currency
  momentum strategies. *Journal of Financial Economics* 106(3), 660–684.
  Abstract.
