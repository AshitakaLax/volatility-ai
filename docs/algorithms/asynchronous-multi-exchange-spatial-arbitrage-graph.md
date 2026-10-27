# Asynchronous Multi-Exchange Spatial Arbitrage Graph

**Ledger ID RK279** · rank 279 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Arbitrage / Market microstructure |
| Potential effectiveness rank | 279 (1 = strongest) |
| AI implementability rank | 366 (1 = easiest) |
| Retail advantage rank | 1,808 (1 = strongest) |
| Fit with this project | ❌ (crypto) |
| Implemented in volatility-ai | **Research code.** Cross-venue spread capture and cycle detection (`crypto.depth_arbitrage`, `find_arbitrage_cycle`; ledger A7); no minimum-cost-flow solver. |
| Related ledger entries | A7, RK278, RK83 |

## In one paragraph

Model fragmented venues as a directed graph of prices, fees and transfer
limits and solve a minimum-cost flow to route multi-hop arbitrage. The
opportunity it targets is documented in crypto: large, recurring
cross-exchange gaps, much larger across countries than within them. The
obstacles are the ones that created the gaps: capital controls,
withdrawal freezes and transfer delays.

## Evidence

* **Makarov & Schoar (2020), "Trading and arbitrage in cryptocurrency
  markets," *Journal of Financial Economics* 135(2), 293–319:** trade
  data from 34 exchanges in 19 countries; large, recurring bitcoin price
  gaps across exchanges that persist for hours to weeks, much larger
  across countries than within them (capital controls), widening in
  rallies. (Abstract.)

## Against, and failure modes

* Latency, withdrawal freezes and API rate limits (the CSV's caveat).

## Fit with volatility-ai

Rejected: crypto is outside the instrument rules (ledger A7).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Makarov, I., Schoar, A. (2020). "Trading and arbitrage in
  cryptocurrency markets." *Journal of Financial Economics* 135(2),
  293–319.
  <https://econpapers.repec.org/RePEc:eee:jfinec:v:135:y:2020:i:2:p:293-319>.
  Abstract.
* This repository: `research/catalog/crypto.py`, ledger A7.
