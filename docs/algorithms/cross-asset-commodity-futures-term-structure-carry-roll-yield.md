# Cross-Asset Commodity Futures Term-Structure Carry & Roll Yield

**Ledger ID RK42** · rank 42 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Macro / commodity carry |
| Potential effectiveness rank | 42 (1 = strongest) |
| AI implementability rank | 160 (1 = easiest) |
| Retail advantage rank | 139 (1 = strongest) |
| Fit with this project | ⛔ (long/short commodity futures, direction hedged) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK32, RK8, RK4 |

## In one paragraph

This is RK32 (commodity roll yield) in its market-neutral form: long the
most backwardated futures, short the most contangoed, so the book earns
the roll-yield spread without a net bet on commodity prices. The
academic version of exactly this spread is the "basis factor" of
Szymanowska et al. One CSV reference (Pynecone, a web-app framework) is
unrelated to the strategy.

## The rule

```
slope_i = log(F_1 / F_2) annualised                    # front vs second contract
monthly: long the top quintile (backwardation), short the bottom quintile (contango),
         equal dollar per leg so the net commodity beta is ~0
roll before first notice; skip contracts near delivery
```

## Evidence

* **Szymanowska et al. (2014):** a high-minus-low basis portfolio
  explains the cross-section of commodity spot premia; basis-sorted
  spot premia 5–14% a year. (Abstract.)
* **Koijen et al. (2018):** commodity carry predicts returns. (Abstract.)
* **Gorton, Hayashi & Rouwenhorst (2013):** inventories drive both the
  basis and the premium. (Abstract.)

## Against, and failure modes

* Liquidity collapses near notice dates; roll logic is where delivery
  risk lives (the CSV's caveat).
* "Direction-hedged" by dollar weights is not hedged by volatility;
  energy legs dominate.

## Fit with volatility-ai

Out of scope: commodity futures and a short leg. Recorded for
completeness next to RK32, whose long-only ETF form is the in-scope one.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Szymanowska, M., de Roon, F., Nijman, T., van den Goorbergh, R. (2014).
  *Journal of Finance* 69(1), 453–482. Abstract.
* Koijen, R. S. J., Moskowitz, T. J., Pedersen, L. H., Vrugt, E. B. (2018).
  "Carry." *Journal of Financial Economics* 127(2), 197–225. Abstract.
* Gorton, G. B., Hayashi, F., Rouwenhorst, K. G. (2013). *Review of
  Finance* 17(1), 35–105. Abstract.
* The CSV's own references: <https://github.com/quantconnect/lean> (a
  backtesting engine); <https://github.com/pynecone-io/pynecone> (a Python
  web framework, unrelated to the strategy).
