# Fractional Kelly Position Sizing

**Ledger ID RK134** · rank 134 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Position sizing |
| Potential effectiveness rank | 134 (1 = strongest) |
| AI implementability rank | 47 (1 = easiest) |
| Retail advantage rank | 70 (1 = strongest) |
| Fit with this project | ⏳ worth testing |
| Useful for volatility-ai | **Worth testing.** A principled cap on lot size or total exposure; the research code exists (C-S2). |
| Implemented in volatility-ai | **Research code** `research.strategies.position_sizing`: `kelly_portfolio`, `kelly_leverage`. |
| Related ledger entries | C-S2, V1, RK194 |

## In one paragraph

Size bets to the Kelly growth-optimal fraction, scaled down (half Kelly,
say) to limit the damage from estimation error. MacLean, Thorp and
Ziemba lay out the trade-off: full Kelly maximises long-run growth but
is very risky in the short run; fractional Kelly blends it with cash,
trading growth for safety.

## Evidence

* **MacLean, Thorp & Ziemba (2010), *Quantitative Finance* 10(7):**
  Kelly maximises the limiting growth rate but its bets can be very
  large; fractional Kelly reduces risk at the cost of growth, and its
  optimality fails outside lognormal markets. (Abstract and excerpts.)
* **This repository:** `position_sizing.kelly_portfolio` and
  `kelly_leverage` (C-S2).

## Against, and failure modes

* The edge estimate drives the size; overestimating it is the usual way
  Kelly bettors ruin themselves. TQQQ already carries 3x leverage.

## Fit with volatility-ai

Useful as a ceiling, not a target: the Kelly leverage implied by TQQQ's
estimated edge and variance bounds how much of the book the grid should
commit. Test half-Kelly caps on total exposure walk-forward.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* MacLean, L. C., Thorp, E. O., Ziemba, W. T. (2010). Long-term capital
  growth: the good and bad properties of the Kelly and fractional Kelly
  capital growth criteria. *Quantitative Finance* 10(7), 681–687.
  Abstract and excerpts.
