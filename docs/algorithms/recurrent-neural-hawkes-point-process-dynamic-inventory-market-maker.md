# Recurrent Neural Hawkes Point Process Dynamic Inventory Market Maker

**Ledger ID RK356** · rank 356 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Point processes / Recurrent neural networks / Market making |
| Potential effectiveness rank | 356 (1 = strongest) |
| AI implementability rank | 1,880 (1 = easiest) |
| Retail advantage rank | 10,340 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK304, RK274, RK246 |

## In one paragraph

Forecast buy and sell order arrivals with a neural Hawkes process and
widen or skew quotes against inventory as the predicted flow turns
one-sided. Hawkes order arrivals have been built into market-making
models; the neural version has no market-making study, and the CSV's
reference, arXiv 2104.09876, is a heat-pump health-monitoring paper,
unrelated to trading.

## Evidence

* **Mei & Eisner (2017):** the neural Hawkes process (see RK304).
* **Bacry, Mastromatteo & Muzy (2015):** Hawkes models of order flow
  (see RK248).

## Against, and failure modes

* Needs event data; inventory control has closed-form answers (C-MM1,
  C-MM2).

## Fit with volatility-ai

The warehouse holds minute bars only; no historical quotes, trades or
depth. The grid is the buy-side, long-only relative of market making:
resting buys below the price and a sale of each lot at its own target
above cost. It cannot quote an ask without inventory, and the no-loss
guard forbids skewing a sale below cost.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Mei, H., Eisner, J. (2017). NeurIPS 30.
  <https://arxiv.org/abs/1612.09328>.
* Bacry, E., Mastromatteo, I., Muzy, J.-F. (2015).
  <https://arxiv.org/abs/1502.04592>.
