# Liquidity Factor

**Ledger ID RK59** · rank 59 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Factor / systematic equity |
| Potential effectiveness rank | 59 (1 = strongest) |
| AI implementability rank | 2 (1 = easiest) |
| Retail advantage rank | 82 (1 = strongest) |
| Fit with this project | ⛔ as an illiquidity premium (illiquid stocks, capacity) · 🧪 the measures, as data |
| Implemented in volatility-ai | **Partial.** Amihud illiquidity and other bar-based liquidity measures exist as research code (`microstructure.amihud_illiquidity`, `kyle_lambda`, `roll_spread`; ledger C-MS5); there is no liquidity-sorted portfolio. |
| Related ledger entries | C-MS5, RK58 |

## In one paragraph

Two different ideas share the name. The *level* version: illiquid stocks
earn a premium for being costly to trade (Amihud 2002). The *risk*
version: stocks whose returns fall when market-wide liquidity dries up
earn a premium for that exposure (Pástor & Stambaugh 2003: 7.5% a year
between high and low sensitivity, 1966–1999, after market, size, value
and momentum). The CSV notes a third use, liquidity as a tradability
screen. For this project the measures matter more than the premium:
they describe how much it costs the grid to trade.

## The rule

```
Amihud illiquidity_i = mean over days of |return_d| / dollar volume_d       # monthly or annual
level strategy: long the most illiquid group, short the most liquid (capacity-limited)
risk strategy (Pástor-Stambaugh): beta of returns on innovations in aggregate liquidity; long high, short low
```

## Evidence

* **Amihud (2002), *Journal of Financial Markets* 5(1), 31–56:**
  illiquidity is priced in the cross-section, and expected market
  illiquidity raises expected excess returns over time. (Abstract.)
* **Pástor & Stambaugh (2003), *Journal of Political Economy* 111(3),
  642–685:** sensitivity to aggregate liquidity is priced; high-minus-low
  sensitivity earned 7.5% a year after adjusting for market, size, value
  and momentum, 1966–1999. (Abstract.)

## Against, and failure modes

* The illiquidity premium is largely eaten by the costs of trading
  illiquid stocks (the CSV's caveat: "not free alpha").
* Liquidity-risk premia pay off badly exactly in liquidity crises.

## Fit with volatility-ai

Trading illiquid stocks for a premium is out of character for a
minute-bar grid on large ETFs (and is a capacity strategy). The
measures are already here as research code (C-MS5) and are useful as
data: an Amihud reading on TQQQ or QQQ rising is a cost and
fill-quality warning for the grid in fast markets.

## How to test it here

Compute the daily Amihud measure on QQQ from the warehouse bars and
check whether high-illiquidity days line up with the N8 booking problems
(fills booked outside the bar) and with turbulent NATR sessions. That is
a measurement question for the engine's fill model, not a strategy.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Amihud, Y. (2002). "Illiquidity and Stock Returns: Cross-Section and
  Time-Series Effects." *Journal of Financial Markets* 5(1), 31–56.
  Abstract.
* Pástor, Ľ., Stambaugh, R. F. (2003). "Liquidity Risk and Expected
  Stock Returns." *Journal of Political Economy* 111(3), 642–685.
  <https://econpapers.repec.org/RePEc:ucp:jpolec:v:111:y:2003:i:3:p:642-685>.
  Abstract.
* This repository: `research/strategies/microstructure.py` (C-MS5).
