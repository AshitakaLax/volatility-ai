# Futures Calendar-Spread Mean Reversion

**Ledger ID RK34** · rank 34 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Relative value / futures |
| Potential effectiveness rank | 34 (1 = strongest) |
| AI implementability rank | 54 (1 = easiest) |
| Retail advantage rank | 83 (1 = strongest) |
| Fit with this project | ⛔ (futures, a short leg in every spread) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK8, RK32, RK42 |

## In one paragraph

Trade the price difference between two expiries of the same future (for
example, July against December corn) when it leaves a range implied by
carry, storage or seasonality, expecting it to come back. The evidence
is mixed. Simple seasonal spread rules have failed out-of-sample tests.
One study reports mean-reverting spreads with dynamic hedge ratios
earning Sharpe ratios above 2. Another argues that earlier
calendar-spread profits came partly from roll yield that could not be
realised.

## The rule

```
spread = F(near) - F(far) (or a ratio); fair range from carry, storage and seasonal history
spread below range: buy near, sell far; above: the reverse; exit at the mean
```

## Evidence

* **Cole, Kastens, Hampel & Gow (1999):** seasonal rolling-average rules
  on four processing spreads (heating oil, gasoline, soybean crush,
  cattle) earned no out-of-sample profits significantly different from
  zero. (Summary.)
* **Lubnau & Todorova (2015), "Trading on mean-reversion in energy
  futures markets," *Energy Economics* 51, 312–319:** calendar-spread
  portfolios with dynamic hedge ratios and Bollinger Band signals in WTI,
  natural gas, gasoline and heating oil, 1992–2013, with costs and a
  bootstrap test against random orders. Most front/second-month
  combinations were profitable, with Sharpe ratios above 2 for most WTI
  and natural-gas combinations. (Abstract.)
* **Shang, Serra & Garcia (2023), "Ride the trend: Is there spread
  momentum profit in the US commodity markets?" *Journal of Agricultural
  Economics* 74(1), 24–47:** calendar-spread time-series momentum in 22
  US commodity futures over 30+ years. Predictability is very weak once
  earlier studies' problems are corrected, returns are no better than a
  long-only benchmark (both near zero or negative), and earlier profits
  came from roll yield that cannot be realised. This is spread
  *momentum*, the opposite bet to this page's reversion. (Abstract.)

## Against, and failure modes

* Spread risk is not outright risk: delivery, roll and margin effects,
  and continuous-contract construction (the CSV's caveat).
* Seasonal patterns are well known and thin after costs.

## Fit with volatility-ai

Out of scope: futures, with a short leg by construction.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Cole, C., Kastens, T., Hampel, F., Gow, L. (1999). Seasonal processing
  spreads, NCCC-134 conference proceedings. Abstract via AgEcon Search.
* Lubnau, T., Todorova, N. (2015). "Trading on mean-reversion in energy
  futures markets." *Energy Economics* 51, 312–319.
  <https://doi.org/10.1016/j.eneco.2015.06.018>. Abstract.
* Shang, Q., Serra, T., Garcia, P. (2023). "Ride the trend: Is there
  spread momentum profit in the US commodity markets?" *Journal of
  Agricultural Economics* 74(1), 24–47.
  <https://doi.org/10.1111/1477-9552.12485>. Abstract.
