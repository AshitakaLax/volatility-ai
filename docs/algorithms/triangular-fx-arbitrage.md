# Triangular FX Arbitrage

**Ledger ID RK83** · rank 83 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Cross-market arbitrage |
| Potential effectiveness rank | 83 (1 = strongest) |
| AI implementability rank | 55 (1 = easiest) |
| Retail advantage rank | 94 (1 = strongest) |
| Fit with this project | ⛔ (FX, latency) |
| Implemented in volatility-ai | **Research code.** A Bellman–Ford negative-cycle search over conversion rates, `crypto.find_arbitrage_cycle` and `conversion_rates` (written for crypto venues; ledger A7). |
| Related ledger entries | A7, RK84, RK85 |

## In one paragraph

If EUR/USD × USD/JPY differs from EUR/JPY by more than the spreads,
converting around the triangle locks in a profit. Opportunities do
exist in executable prices, but they are small and short-lived, and a
trader would have to beat other arbitrageurs to an implausibly large
share of them. They became rarer once algorithms connected directly to
the interbank platforms in the mid-2000s. It is a latency race, not a
strategy for a daily or minute-bar system.

## The rule

```
for every triangle A->B->C->A: product of executable rates (bid/ask, fees) > 1 + threshold -> trade all three legs at once
general form: a negative cycle in -log(rate) (Bellman-Ford)
```

## Evidence

* **Fenn, Howison, McDonald, Williams & Johnson (2009), "The Mirage of
  Triangular Arbitrage in the Spot Foreign Exchange Market,"
  *International Journal of Theoretical and Applied Finance* 12(8),
  1105–1123:** executable prices; opportunities exist but are mostly
  short and small, more numerous and shorter in liquid hours, and
  declining; profiting would need an unfeasibly large share of them.
  (Abstract.)
* **Kozhan & Tham, "How Riskless Is 'Riskless' Arbitrage?":**
  execution risk from competing arbitrageurs limits it. (Working paper
  abstract.)
* **Ito, Yamada, Takayasu & Takayasu (2020), NBER WP 26706:** exploitable
  before the mid-2000s on EBS even after costs; much rarer after
  algorithmic access. (Abstract.)

## Against, and failure modes

* Legging risk, rejects, credit limits; the displayed opportunity is
  gone before execution (the CSV's caveat).

## Fit with volatility-ai

Out of scope.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Fenn, D. J., Howison, S. D., McDonald, M., Williams, S., Johnson, N. F.
  (2009). *IJTAF* 12(8), 1105–1123. <https://arxiv.org/abs/0812.0913>.
  Abstract.
* Kozhan, R., Tham, W. W. "How Riskless Is 'Riskless' Arbitrage?" New
  York Fed conference paper (2010). Abstract.
* Ito, T., Yamada, K., Takayasu, M., Takayasu, H. (2020). NBER Working
  Paper 26706. Abstract.
* This repository: `research/catalog/crypto.py`, ledger A7.
