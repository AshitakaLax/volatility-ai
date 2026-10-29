# Commodity Futures Roll Yield

**Ledger ID RK32** · rank 32 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Carry / macro (commodities) |
| Potential effectiveness rank | 32 (1 = strongest) |
| AI implementability rank | 67 (1 = easiest) |
| Retail advantage rank | 120 (1 = strongest) |
| Fit with this project | ⛔ as a long/short futures strategy · ⏳ long-only via a roll-optimised commodity ETF |
| Implemented in volatility-ai | **Research code** in `research.catalog.carry_rates`: `roll_yield`, `basis_factor`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK8, RK42, RK4 |

## In one paragraph

Rank commodity futures by the slope of their curve and hold those in
backwardation (rolling into a cheaper contract earns a positive roll
yield), avoiding or shorting those in steep contango. It is the
commodity leg of carry (RK4). The best explanation is the theory of
storage: backwardation signals scarce inventories, which go with high
risk premia. Erb and Harvey's warning applies: the average individual
commodity future has earned about nothing; returns came from
diversification, rebalancing and term-structure selection.

## The rule

```
roll yield_i = log(F_near / F_next) x (12 / months between contracts)
monthly: long the top third by roll yield, short the bottom third; or long-only top third
```

## Evidence

* **Erb & Harvey (2006), *Financial Analysts Journal* 62(2):** the
  average individual commodity future's excess return has been about
  zero; rebalanced portfolios can be equity-like; term-structure
  characteristics have been rewarded; tactical strategies beat long-only
  exposure. (Abstract.)
* **Gorton, Hayashi & Rouwenhorst (2013):** risk premia track inventory
  levels; the basis signals inventory states. (Abstract.)
* **Szymanowska, de Roon, Nijman & van den Goorbergh (2014), *Journal of
  Finance* 69(1), 453–482:** basis-sorted portfolios earn spot premia of
  5–14% a year and term premia of 1–3%; one high-minus-low basis factor
  explains spot premia. (Abstract.)

## Against, and failure modes

* Backwardation or contango alone does not guarantee returns; curve
  definitions and roll schedules vary (the CSV's caveat).
* Long-only commodity funds were a poor holding for most of 2011–2020.

## Fit with volatility-ai

Futures and shorts are out. A roll-optimised long-only commodity ETF
(funds that pick the contract with the best roll yield) is an in-scope
holding, as a candidate inflation hedge (RK41), not as a TQQQ diversifier
in crashes (commodities fell in 2008 and March 2020).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Erb, C. B., Harvey, C. R. (2006). "The Strategic and Tactical Value of
  Commodity Futures." *Financial Analysts Journal* 62(2). NBER w11222.
  Abstract.
* Gorton, G. B., Hayashi, F., Rouwenhorst, K. G. (2013). *Review of
  Finance* 17(1), 35–105. Abstract.
* Szymanowska, M., de Roon, F., Nijman, T., van den Goorbergh, R.
  (2014). "An Anatomy of Commodity Futures Risk Premia." *Journal of
  Finance* 69(1), 453–482. Abstract.
* The CSV's own references: QuantConnect strategy library; MOP (2012).
