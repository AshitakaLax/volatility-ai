# Fixed-Income Carry and Roll-Down

**Ledger ID RK28** · rank 28 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Fixed income / relative value |
| Potential effectiveness rank | 28 (1 = strongest) |
| AI implementability rank | 168 (1 = easiest) |
| Retail advantage rank | 30 (1 = strongest) |
| Fit with this project | ⛔ as a levered curve trade · ⏳ long-only: choosing a bond ETF's maturity by carry + roll-down |
| Implemented in volatility-ai | **Research code** in `research.catalog.carry_rates`: `bond_carry_rolldown`; tested on synthetic data, not wired into the engine. Idle cash earns a historical money-market yield (`research/optimization/money_market_yield.py`); no bond holdings. |
| Related ledger entries | RK4, RK20, RK86, X5 |

## In one paragraph

A bond earns its yield, and if the curve is upward-sloping and does not
move, it also gains as it ages into a shorter, lower-yielding maturity
(roll-down). Carry plus roll-down is the return you get if nothing
happens. Holding the maturities with the highest expected carry-plus-
roll, net of financing, is a classic fixed-income allocation; Koijen et
al. show bond carry predicts returns. It is compensation for rate,
credit and liquidity risk, and it reverses violently in rate shocks
like 2022.

## The rule

```
for each maturity bucket (or bond ETF):
    carry     = yield - financing rate (repo / T-bill)
    roll-down = (y(T) - y(T - h)) x duration(T - h)        # gain if the curve is unchanged over horizon h
    expected  = carry + roll-down
long-only form: hold the bucket with the best expected return per unit of duration
academic form: long high-carry, short low-carry, duration-neutral
```

## Evidence

* **Koijen, Moskowitz, Pedersen & Vrugt (2018):** carry predicts returns
  in global bonds and US Treasuries, as in other asset classes. (Abstract.)
* The level/slope/curvature decomposition (Litterman & Scheinkman 1991)
  underlies roll-down: most yield variation is a level shift, which is
  exactly the risk carry earns a premium for.

## Against, and failure modes

* Rate shocks: 2022 repriced the whole curve and erased years of carry;
  long Treasuries fell with stocks (ledger X5).
* Needs financing, roll and convexity assumptions (the CSV's caveat).

## Fit with volatility-ai

The levered, duration-neutral curve trade is out of scope (shorts,
futures, financing). A long-only choice of Treasury-ETF maturity by
carry-plus-roll is in scope but is a bond-allocation decision for idle
capital, which the project currently parks in cash at the money-market
yield. That cash leg has no duration risk, which is why it has been the
safer choice for this book.

## How to test it here

If bonds are ever considered as the defensive leg (X2), compare holding
SHY, IEF and TLT by carry-plus-roll (yields from FRED's constant-maturity
series via `research/ml/sources.fetch_fred`, lagged a day) against plain
cash at the engine's yield, scored on 2020 and 2022.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Koijen, R. S. J., Moskowitz, T. J., Pedersen, L. H., Vrugt, E. B.
  (2018). "Carry." *Journal of Financial Economics* 127(2), 197–225.
  Abstract.
* Litterman, R., Scheinkman, J. (1991). "Common Factors Affecting Bond
  Returns." *Journal of Fixed Income* 1(1), 54–61. Summaries.
* The CSV's own references: CME education; AQR research.
