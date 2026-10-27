# Commodity Momentum + Term Structure

**Ledger ID RK8** · rank 8 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Trend / carry (commodities) |
| Potential effectiveness rank | 8 (1 = strongest) |
| AI implementability rank | 25 (1 = easiest) |
| Retail advantage rank | 14 (1 = strongest) |
| Fit with this project | ⛔ (long/short commodity futures) |
| Implemented in volatility-ai | **No.** GLD is the only commodity holding considered (X9). |
| Related ledger entries | RK1, RK32, RK42, X9 |

## In one paragraph

Among commodity futures, buy those that are both rising (momentum) and
in backwardation (futures below spot, so rolling earns a positive yield),
and short those falling and in contango. Each signal works alone; the
double sort works better. The economics come from the theory of storage:
low inventories produce backwardation, high risk premia and, often,
rising prices. It is a futures long/short strategy, out of scope here.

## The rule

```
monthly, across ~25-30 commodity futures:
    momentum   = trailing 12-month return (or 1-12)
    term slope = log(F_near / F_next) annualised          # > 0: backwardation
double sort: within the top momentum third, long the most backwardated;
             within the bottom third, short the most contangoed
hold one month, roll before notice dates
```

## Evidence

* **Fuertes, Miffre & Rallis (2010), *Journal of Banking & Finance*
  34(10), 2530–2548:** momentum and term-structure strategies earn
  annualised alphas of 10.14% and 12.66% alone; the double sort earns
  21.02%, not explained by liquidity, data mining or transaction costs.
  (Abstract.)
* **Gorton, Hayashi & Rouwenhorst (2013), *Review of Finance* 17(1),
  35–105:** commodity risk premia vary with physical inventories; the
  basis and prior returns reflect inventory states; momentum and
  backwardation returns stem partly from selecting commodities with low
  inventories. (Abstract.)
* **Moskowitz, Ooi & Pedersen (2012)** include 24 commodity futures in
  time-series momentum (RK1; the CSV's reference).

## Against, and failure modes

* **Roll and contract construction** change the result materially (the
  CSV's caveat).
* Commodity markets are thin and event-driven (weather, OPEC, delivery
  squeezes); the short leg is essential to the published alpha.

## Fit with volatility-ai

Out of scope: commodity futures and short positions. The only commodity
the project considers holding is gold via GLD, as a defensive candidate
(X9), where a simple momentum gate (RK1's long-or-cash form) is the
in-scope piece.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Fuertes, A.-M., Miffre, J., Rallis, G. (2010). "Tactical Allocation in
  Commodity Futures Markets: Combining Momentum and Term Structure
  Signals." *Journal of Banking & Finance* 34(10), 2530–2548.
  <https://openaccess.city.ac.uk/id/eprint/6416/>. Abstract.
* Gorton, G. B., Hayashi, F., Rouwenhorst, K. G. (2013). "The
  Fundamentals of Commodity Futures Returns." *Review of Finance* 17(1),
  35–105. NBER w13249. Abstract.
* Moskowitz, T., Ooi, Y. H., Pedersen, L. H. (2012).
  <https://doi.org/10.1016/j.jfineco.2011.11.003> (the CSV's reference).
