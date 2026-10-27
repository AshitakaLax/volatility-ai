# Avellaneda–Stoikov Market Making

**Ledger ID RK274** · rank 274 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Market making |
| Potential effectiveness rank | 274 (1 = strongest) |
| AI implementability rank | 302 (1 = easiest) |
| Retail advantage rank | 5,930 (1 = strongest) |
| Fit with this project | ✅ buy-side reservation price (C-MM1) · ⛔ two-sided quoting |
| Implemented in volatility-ai | **Research code.** `inventory_control.as_reservation_price`, `as_optimal_spread`, `as_quotes` (ledger C-MM1); buy-side use only. |
| Related ledger entries | C-MM1, RK246, RK245, C-G2 |

## In one paragraph

The standard market-making model: quote around a reservation price that
sits below mid when long and above when short, with a spread set by risk
aversion, volatility, time left and how quickly fill probability decays
with distance. It is a model, not a production strategy; latency,
adverse selection, fees and inventory limits decide real results.

## The rule

```text
r = s - q gamma sigma^2 (T - t); total spread = gamma sigma^2 (T - t) + (2 / gamma) ln(1 + gamma / k)
bid = r - spread/2; ask = r + spread/2
```

## Evidence

* **Avellaneda & Stoikov (2008), "High-frequency trading in a limit
  order book," *Quantitative Finance* 8(3), 217–224:** quotes around a
  reservation price r = s − qγσ²(T − t) with spread γσ²(T − t) + (2/γ)
  ln(1 + γ/k), trading off inventory risk against order arrival
  intensity. (Standard reference; the CSV's own reference.)
* **Menkveld (2013), "High frequency trading and the new market makers,"
  *Journal of Financial Markets* 16(4), 712–740:** a large HFT market
  maker's inventory losses are offset by spread profits, and its Sharpe
  ratio is very sensitive to the cost of capital. A working-paper
  version gives €1.55 per trade earned on the spread net of fees against
  a €0.68 loss on positions. (Abstract; per-trade figures from the
  working paper.)

## Against, and failure modes

* Model reference, not production strategy (the CSV's caveat).

## Fit with volatility-ai

Only the bid side applies: the reservation price is a principled way to
lower the next grid buy as inventory builds, which is C-G2's skew. The
ask side would sell below cost or short.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Avellaneda, M., Stoikov, S. (2008). "High-frequency trading in a limit
  order book." *Quantitative Finance* 8(3), 217–224.
  <https://math.nyu.edu/inmemoriam/avellaneda/HighFrequencyTrading.pdf>.
* Menkveld, A. J. (2013). "High frequency trading and the new market
  makers." *Journal of Financial Markets* 16(4), 712–740. Abstract and
  working paper.
* This repository: `research/strategies/inventory_control.py`, ledger
  C-MM1.
