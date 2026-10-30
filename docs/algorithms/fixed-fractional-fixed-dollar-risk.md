# Fixed Fractional / Fixed Dollar Risk

**Ledger ID RK194** · rank 194 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Position sizing |
| Potential effectiveness rank | 194 (1 = strongest) |
| AI implementability rank | 93 (1 = easiest) |
| Retail advantage rank | 254 (1 = strongest) |
| Fit with this project | ✅ in use |
| Useful for volatility-ai | **In use.** Fixed-fraction sizing is the grid's base sizing (V1); stop-distance sizing does not apply, since the grid uses no stops. |
| Implemented in volatility-ai | **Yes.** `research.strategies.size_calculators`: `FixedPortfolioPercentage`. |
| Related ledger entries | V1, V11, S4, RK134 |

## In one paragraph

Risk a fixed fraction of equity, or a fixed dollar amount, per trade,
sizing by the stop distance. It is the standard position-sizing rule of
trading texts (Vince's fixed fraction). Its fixed-fraction half is the
grid's FixedPortfolioPercentage sizing; its stop-distance half needs a
stop, which the no-loss rule replaces with lot targets and the regime
exit.

## Evidence

* **Practitioner standard** (Vince 1990; fixed-fractional sizing in
  trading texts); no evidence is needed for an accounting rule.
* **This repository:** `FixedPortfolioPercentage` (V1) is a registered
  sizing strategy; riskkit's drawdown ladder is reviewed under V11/S4.

## Against, and failure modes

* A fixed fraction of equity grows bets after wins and shrinks them
  after losses, which on a grid means smaller lots near the bottom.

## Fit with volatility-ai

In use as V1. Nothing further to build.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Vince, R. (1990). *Portfolio Management Formulas*. Wiley. Standard
  reference.
