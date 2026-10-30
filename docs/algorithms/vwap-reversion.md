# VWAP Reversion

**Ledger ID RK150** · rank 150 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Mean reversion / intraday |
| Potential effectiveness rank | 150 (1 = strongest) |
| AI implementability rank | 222 (1 = easiest) |
| Retail advantage rank | 424 (1 = strongest) |
| Fit with this project | 🧪 reference only |
| Useful for volatility-ai | **Reference only.** Session VWAP is already researched as a buy gate (C-MS3); there is no academic evidence for VWAP fades as a strategy. |
| Implemented in volatility-ai | **Research code** `research.strategies.intraday_gates`: `VwapGate`, `session_vwap`. |
| Related ledger entries | C-MS3, RK364 |

## In one paragraph

Fade intraday deviations from the session VWAP back toward it when order
flow is not strongly directional. VWAP's academic role is as an
execution benchmark (Berkowitz, Logue and Noser 1988); I found no
peer-reviewed test of VWAP reversion, only vendor code and blogs.

## Evidence

* **No peer-reviewed study found**; vendor samples and blogs report
  backtests without out-of-sample evidence.
* **This repository:** `intraday_gates.session_vwap` and `VwapGate`
  (C-MS3) gate buys below VWAP.

## Against, and failure modes

* Intraday edges this small are consumed by costs and slippage.

## Fit with volatility-ai

As a gate it is researched; as a stand-alone intraday strategy it
contradicts the grid's hold-to-target lots.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Berkowitz, S. A., Logue, D. E., Noser, E. A. (1988). The Total Cost of
  Transactions on the NYSE. *Journal of Finance* 43(1). Standard
  reference.
