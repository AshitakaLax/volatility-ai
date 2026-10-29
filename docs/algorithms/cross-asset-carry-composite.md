# Cross-Asset Carry Composite

**Ledger ID RK4** · rank 4 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Macro / carry |
| Potential effectiveness rank | 4 (1 = strongest) |
| AI implementability rank | 68 (1 = easiest) |
| Retail advantage rank | 131 (1 = strongest) |
| Fit with this project | ⛔ (futures, forwards and short legs across asset classes) |
| Implemented in volatility-ai | **Research code** in `research.catalog.carry_rates`: `carry_composite`, `fx_carry`, `roll_yield`, `bond_carry_rolldown`, `rank_weights`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK28, RK30, RK32, RK42 |

## In one paragraph

"Carry" is the return an asset earns if its price does not move: the
interest-rate differential for a currency, the roll yield for a
commodity future, yield plus roll-down for a bond, the dividend yield
minus financing for an equity-index future. Koijen, Moskowitz, Pedersen
and Vrugt measured it the same way in every asset class and found it
predicts returns in all of them, and that a diversified carry portfolio
is not explained by the usual factors. The catch is in the same paper:
carry strategies everywhere tend to fail together, in global recessions.

## The rule

```
carry_i = (spot_i - futures_i) / futures_i        # one definition for every futures market
          (FX: rate differential; bonds: yield + roll-down - financing; commodities: roll yield)
within each asset class: long the high-carry markets, short the low-carry ones, risk-weighted
diversify across asset classes, equal risk per class
```

## Evidence

* **Koijen, Moskowitz, Pedersen & Vrugt (2018), *Journal of Financial
  Economics* 127(2), 197–225:** carry predicts returns in the
  cross-section and time series of global equities, global bonds,
  commodities, US Treasuries, credit and options; it is not explained by
  known predictors and captures many of them; carry strategies across
  asset classes can all do poorly at once, in global recessions.
  (Abstract.)

## Against, and failure modes

* **Carry is crash-risk compensation** (the CSV's caveat): currency carry
  is negatively skewed (Brunnermeier, Nagel & Pedersen 2008, RK30); the
  diversified version loses in recessions, the same time a leveraged
  equity book does.
* Needs futures, forwards and short positions, with careful roll and
  financing data.

## Fit with volatility-ai

Out of scope: futures, FX forwards and short legs, and its bad states
coincide with this project's. Its long-only shadows (holding a bond ETF
for its yield, a roll-optimised commodity ETF) are covered as RK28 and
RK32. Carry is still a useful *concept* here: the engine already credits
idle cash with a historical cash yield, the simplest carry there is.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Koijen, R. S. J., Moskowitz, T. J., Pedersen, L. H., Vrugt, E. B.
  (2018). "Carry." *Journal of Financial Economics* 127(2), 197–225.
  <https://econpapers.repec.org/RePEc:eee:jfinec:v:127:y:2018:i:2:p:197-225>.
  Abstract.
* Brunnermeier, M., Nagel, S., Pedersen, L. H. (2008). "Carry Trades and
  Currency Crashes." *NBER Macroeconomics Annual* 23. NBER w14473.
  Abstract.
* The CSV's own references: AQR research; QuantConnect strategy library.
