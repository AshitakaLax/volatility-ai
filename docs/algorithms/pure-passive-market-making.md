# Pure Passive Market Making

**Ledger ID RK245** · rank 245 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Market microstructure / market making |
| Potential effectiveness rank | 245 (1 = strongest) |
| AI implementability rank | 304 (1 = easiest) |
| Retail advantage rank | 2,118 (1 = strongest) |
| Fit with this project | ⛔ two-sided quoting (asks without inventory, sales below cost) · the grid is the buy-side relative |
| Implemented in volatility-ai | **Research code.** Quote models (`inventory_control.as_quotes`, `glft_quotes`; ledger C-MM1, C-MM2). |
| Related ledger entries | C-MM1, C-MM2, RK246, RK274, V5 |

## In one paragraph

Rest a bid and an ask at set distances from the mid-price and refresh
them on a timer or price move, earning the spread when both sides fill.
Without inventory control and protection from informed flow, the spread
is given back on positions: one large HFT market maker earned €1.55 a
trade on the spread and lost €0.68 on its positions.

## The rule

```text
every refresh: bid = mid x (1 - d_bid), ask = mid x (1 + d_ask); cancel and replace on a timer or a price move
optional: stop quoting the side that would grow inventory past a limit
```

## Evidence

* **Menkveld (2013), "High frequency trading and the new market makers,"
  *Journal of Financial Markets* 16(4), 712–740:** a large HFT market
  maker's inventory losses are offset by spread profits, and its Sharpe
  ratio is very sensitive to the cost of capital. A working-paper
  version gives €1.55 per trade earned on the spread net of fees against
  a €0.68 loss on positions. (Abstract; per-trade figures from the
  working paper.)
* Hummingbot's pure-market-making strategy documents the rule (the CSV's
  reference). (Documentation.)

## Against, and failure modes

* Without inventory and adverse-selection controls, spread capture can
  be negative after toxic fills and trends (the CSV's caveat).
* Queue priority and latency decide fills. The warehouse holds minute
  bars only; no historical quotes, trades or depth.

## Fit with volatility-ai

The grid is the buy-side, long-only relative of market making: resting
buys below the price and a sale of each lot at its own target above
cost. It cannot quote an ask without inventory, and the no-loss guard
forbids skewing a sale below cost. The quote models are research code
for that buy side.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Menkveld, A. J. (2013). "High frequency trading and the new market
  makers." *Journal of Financial Markets* 16(4), 712–740. Abstract and
  working paper.
* Hummingbot, pure market making documentation (the CSV's reference).
* This repository: `research/strategies/inventory_control.py`, ledger
  C-MM1, C-MM2.
