# Inventory-Skewed Market Making

**Ledger ID RK246** · rank 246 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Market microstructure / market making |
| Potential effectiveness rank | 246 (1 = strongest) |
| AI implementability rank | 305 (1 = easiest) |
| Retail advantage rank | 1,815 (1 = strongest) |
| Fit with this project | ✅ buy-side skew (C-G2) · ⛔ sell-side skew below cost |
| Implemented in volatility-ai | **Yes.** Its own strategy id, `rk246_inventory_skew`, selectable for backtests: `LibrarySizing` (`research/strategies/library_sizing.py`) with `signal=inventory_skew`, component `InventorySkewLevel`. Tune it with `signal_params`. Unmeasured. Before this change: **Research code.** `inventory_control.inventory_skewed_level` and `as_reservation_price` (ledger C-G2, C-MM1); buy-side only, because sell rungs cannot move below cost. |
| Related ledger entries | C-G2, C-MM1, RK274, RK245 |

## In one paragraph

Shift quotes against inventory: as a long position grows, lower both the
bid and the ask so that buying slows and selling speeds up. Avellaneda
and Stoikov derive the shift as a reservation price below mid in
proportion to inventory, risk aversion and variance; Guéant, Lehalle and
Fernandez-Tapia give closed-form approximations. For this project only
half of it applies: the next grid buy can move lower as lots accumulate,
but no sale may move below its lot's cost.

## The rule

```text
reservation r = s - q x gamma x sigma^2 x (T - t)            # q = inventory
buy level = r - spread/2; (sell level = r + spread/2 is out of scope below cost)
```

## Evidence

* **Avellaneda & Stoikov (2008), "High-frequency trading in a limit
  order book," *Quantitative Finance* 8(3), 217–224:** quotes around a
  reservation price r = s − qγσ²(T − t) with spread γσ²(T − t) + (2/γ)
  ln(1 + γ/k), trading off inventory risk against order arrival
  intensity. (Standard reference; the CSV's own reference.)
* **Guéant, Lehalle & Fernandez-Tapia (2013):** closed-form
  approximations of the optimal quotes with inventory limits (GLFT).
  (Standard reference; not re-checked here.)

## Against, and failure modes

* Quote skew is model-dependent; inventory limits, adverse selection,
  stale data and queue position are essential (the CSV's caveat).

## Fit with volatility-ai

The buy-side half is exactly the grid's inventory question: how much
lower should the next buy sit when lots are already open? It is built as
research code (C-G2) and is a candidate lever on the champion.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Avellaneda, M., Stoikov, S. (2008). "High-frequency trading in a limit
  order book." *Quantitative Finance* 8(3), 217–224.
  <https://math.nyu.edu/inmemoriam/avellaneda/HighFrequencyTrading.pdf>.
* Guéant, O., Lehalle, C.-A., Fernandez-Tapia, J. (2013). "Dealing with
  the inventory risk: a solution to the market making problem."
  *Mathematics and Financial Economics* 7. Not re-checked.
* This repository: `research/strategies/inventory_control.py`, ledger
  C-G2, C-MM1.
