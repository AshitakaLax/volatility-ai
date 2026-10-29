# Convertible Bond Arbitrage

**Ledger ID RK80** · rank 80 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Capital structure / relative value |
| Potential effectiveness rank | 80 (1 = strongest) |
| AI implementability rank | 204 (1 = easiest) |
| Retail advantage rank | 281 (1 = strongest) |
| Fit with this project | ⛔ (convertible bonds, short stock) |
| Implemented in volatility-ai | **Research code** in `research.catalog.stat_arb`: `convertible_price`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK81 |

## In one paragraph

Buy a convertible bond and short the issuer's stock to hedge the
embedded option's equity delta, earning the bond's coupon, the short
rebate and the option's cheapness while rebalancing the hedge. Much of
the hedge-fund return in this strategy is explained by a simple
"buy convertibles, hedge only the equity" factor, which is to say it
is paid for providing liquidity and bearing credit and supply risk.
It is a specialist institutional trade.

## The rule

```
long convertible; short delta x conversion ratio shares; rebalance as delta changes
optional: hedge credit (CDS) and rates; exit on cheapening reversal, call or maturity
```

## Evidence

* **Agarwal, Fung, Loon & Naik (2011), "Risk and return in convertible
  arbitrage: Evidence from the convertible bond market," *Journal of
  Empirical Finance* 18(2), 175–194 (the CSV's reference):** a
  buy-and-hedge factor explains a substantial share of convertible-
  arbitrage fund returns; extreme market events and convertible supply
  matter; larger funds short more actively. (Abstract.)
* Mitchell, Pedersen & Pulvino (2007, "Slow Moving Capital") on the 2005
  redemption-driven cheapening is the standard reference for its crash
  risk. (Not re-checked in this pass.)

## Against, and failure modes

* Borrow recalls, issuer credit deterioration, jumps and forced
  deleveraging dominate the modelled edge (the CSV's caveat).

## Fit with volatility-ai

Out of scope.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Agarwal, V., Fung, W. H., Loon, Y. C., Naik, N. Y. (2011). *Journal of
  Empirical Finance* 18(2), 175–194.
  <https://doi.org/10.1016/j.jempfin.2010.11.008>. Abstract.
* Mitchell, M., Pedersen, L. H., Pulvino, T. (2007). "Slow Moving
  Capital." *American Economic Review* 97(2). Not re-checked.
