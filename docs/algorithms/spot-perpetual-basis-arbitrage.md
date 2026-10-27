# Spot-Perpetual Basis Arbitrage

**Ledger ID RK85** · rank 85 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Crypto / basis |
| Potential effectiveness rank | 85 (1 = strongest) |
| AI implementability rank | 56 (1 = easiest) |
| Retail advantage rank | 132 (1 = strongest) |
| Fit with this project | ❌ (crypto, short leg) |
| Implemented in volatility-ai | **Partial.** `crypto.funding_carry_positions` (ledger C-RJ2) holds long spot / short perpetual on a *funding* threshold: in once annualised funding reaches `entry_apr`, out when it drops below `exit_apr`. It never reads the basis, so the basis entry and convergence exit described here are not built; `funding_carry_pnl` only books the basis move as P&L. |
| Related ledger entries | C-RJ2, RK84 |

## In one paragraph

The entry-timing variant of RK84: open a long-spot, short-perpetual
position when the price gap between the perpetual and spot, plus the
expected funding, exceeds fees, funding costs and a risk buffer. Close
it when the gap closes. Perpetuals have no expiry to force convergence,
so the arbitrage is "random-maturity": it relies on the funding
mechanism pulling prices together. The evidence and risks are those of
RK84.

## The rule

```
basis = perp / spot - 1; edge = basis + expected funding over the hold - fees - buffer
edge > 0: long spot, short perp; close when the basis returns inside the cost band (or reverse for negative basis)
```

## Evidence

* **He, Manela, Ross & von Wachter (arXiv 2212.06888):** perpetual
  prices deviate from no-arbitrage values by large, co-moving amounts
  that shrink over time; trading the deviation beats a carry benchmark.
  (Abstract and summaries.)
* **Schmeling, Schrimpf & Todorov (2023), BIS WP 1087:** large,
  time-varying carry and crash-prone cash-and-carry. (Abstract.)

## Against, and failure modes

* The basis can widen, funding can flip, and venues fail independently;
  forced liquidation and transfer constraints (the CSV's caveat).

## Fit with volatility-ai

Rejected: crypto (ledger C-RJ2).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* He, S., Manela, A., Ross, O., von Wachter, V. "Fundamentals of
  Perpetual Futures." <https://arxiv.org/abs/2212.06888>. Abstract.
* Schmeling, M., Schrimpf, A., Todorov, K. (2023). BIS Working Paper
  1087. Abstract.
* This repository: `research/catalog/crypto.py`, ledger C-RJ2.
