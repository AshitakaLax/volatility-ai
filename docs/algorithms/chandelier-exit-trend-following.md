# Chandelier Exit Trend Following

**Ledger ID RK38** · rank 38 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Trend / risk management |
| Potential effectiveness rank | 38 (1 = strongest) |
| AI implementability rank | 50 (1 = easiest) |
| Retail advantage rank | 55 (1 = strongest) |
| Fit with this project | ⛔ as a stop (sells below cost) · ⏳ as a profit-only trailing exit for lots already past target |
| Implemented in volatility-ai | **Partial.** The profit-only trailing exits exist: V10's trailing profit target and a profit-only Parabolic SAR exit (`grid_lifecycle.psar_profit_exits`); no ATR chandelier. |
| Related ledger entries | V10, Q8, C-X2 (catalog X3), RK43, RK70 |

## In one paragraph

A volatility-scaled trailing stop: for a long position, exit when price
falls a multiple of ATR (commonly 3 × the 22-period ATR) below the
highest high since entry. It "hangs" from the high like a chandelier
from a ceiling. Credited to Chuck LeBeau and popularised by Alexander
Elder, it is an exit rule rather than a strategy; there is no published
study of its performance. Here the stop form is excluded by the loss
policy, but the same trail applied only to lots already above their
target is a profit-only exit, which the project already has in two
forms.

## The rule

```
long stop_t = max over the trade (HighestHigh(22) - 3 x ATR(22))     # ratchet: never lowered
exit when close < stop_t
profit-only variant (this project): apply only to a lot whose price is above its profit target;
the stop is then floored at the target, so the exit cannot sell below it
```

## Evidence

* Attribution to LeBeau (System Traders Club; possibly *Computer
  Analysis of the Futures Markets*, 1992, with Lucas) and to Elder's
  2002 book is consistent across secondary sources; the 22/3.0 defaults
  are a modern convention, not confirmed in LeBeau's text. (Summaries.)
* **No performance study found**, here or by a second search (the
  owner-supplied Gemini answer also reports none). It is usually
  evaluated as part of a trend system, not alone.

## Against, and failure modes

* Gaps through the stop; a rising ATR without a new high *lowers* an
  un-ratcheted stop (implementations differ).
* As with any trailing stop, it gives back a fixed multiple of ATR on
  every exit.

## Fit with volatility-ai

The stop form realises losses outside a regime exit and is excluded.
The profit-only form fits and has relatives here (V10's trailing target,
the PSAR profit exit). An ATR-chandelier profit exit would be a third
variant in `grid_lifecycle.py`.

## How to test it here

Add `chandelier_profit_exits(lots, bars, n=22, k=3.0)` beside
`psar_profit_exits`, routed through the no-loss guard, and compare the
three trailing rules against the fixed +30% target on the champion: do
trailing exits on winners add more than they cost in delayed recycling
of capital?

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* LeBeau, C., Lucas, D. W. (1992). *Computer Analysis of the Futures
  Markets*. Attribution only, via secondary sources.
* Elder, A. (2002). *Come Into My Trading Room*. Wiley. Attribution only.
* Practitioner descriptions (e.g. LuxAlgo, NexusFi) found by search.
* This repository: `research/strategies/grid_lifecycle.py`
  (`psar_profit_exits`), ledger V10.
