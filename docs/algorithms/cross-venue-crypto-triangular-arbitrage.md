# Cross-Venue Crypto Triangular Arbitrage

**Ledger ID RK278** · rank 278 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Arbitrage / Crypto microstructure |
| Potential effectiveness rank | 278 (1 = strongest) |
| AI implementability rank | 365 (1 = easiest) |
| Retail advantage rank | 1,807 (1 = strongest) |
| Fit with this project | ❌ (crypto) |
| Implemented in volatility-ai | **Research code.** Bellman–Ford negative-cycle search over conversion rates (`crypto.find_arbitrage_cycle`, ledger A7). |
| Related ledger entries | A7, RK83, RK279 |

## In one paragraph

Trade a cycle of three pairs (BTC/USD → ETH/BTC → ETH/USD) when the
product of executable rates exceeds one after fees, within one venue or
across venues. Crypto markets have shown large and persistent
cross-exchange price gaps, mostly across countries where capital
controls block arbitrage capital; within a venue, the triangle closes as
fast as in FX (RK83).

## The rule

```text
rates r_ij from executable bid/ask net of taker fees; find a cycle with sum(-log r) < 0 (Bellman-Ford)
trade all legs at once; across venues add withdrawal fees and transfer time
```

## Evidence

* **Makarov & Schoar (2020), "Trading and arbitrage in cryptocurrency
  markets," *Journal of Financial Economics* 135(2), 293–319:** trade
  data from 34 exchanges in 19 countries; large, recurring bitcoin price
  gaps across exchanges that persist for hours to weeks, much larger
  across countries than within them (capital controls), widening in
  rallies. (Abstract.)
* **Fenn et al. (2009):** in spot FX, triangular opportunities exist but
  are small, brief and too contested to exploit (RK83).

## Against, and failure modes

* Taker and withdrawal fees and WebSocket latency (the CSV's caveat).

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
