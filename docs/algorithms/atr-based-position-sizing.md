# ATR-Based Position Sizing

**Ledger ID RK67** · rank 67 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Position sizing |
| Potential effectiveness rank | 67 (1 = strongest) |
| AI implementability rank | 48 (1 = easiest) |
| Retail advantage rank | 124 (1 = strongest) |
| Fit with this project | 🧪 as volatility-normalised lot sizing · ⛔ the stop-distance form (no price stops) |
| Implemented in volatility-ai | **Research code.** Turtle units (`position_sizing.turtle_unit_shares`, `turtle_atr`, `TurtlePyramid`; C-G5). The wired relatives scale lots by volatility: V7 (fast/slow ratio) and S4 (target over realized). |
| Related ledger entries | C-G5, V7, S4, RK43 |

## In one paragraph

Size each position so that a move of one ATR (average true range), or
the distance to a stop, costs a fixed fraction of equity. The Turtles'
version: a "unit" is 1% of equity divided by N, the 20-day ATR in
dollars. It equalises risk across instruments and over time. The
stop-distance form needs price stops, which this project's loss policy
excludes; the volatility-normalisation idea is already in the grid in two
forms.

## The rule

```
N = 20-day ATR (Wilder smoothing)
dollar volatility = N x point value
unit (shares) = (risk fraction x equity) / dollar volatility        # Turtles: 1%
stop form: shares = (risk fraction x equity) / (entry - stop)
```

## Evidence

* **Faith (2003), "The Original Turtle Trading Rules":** the unit
  definition above, with pyramiding by half an N and a 2N stop; the
  rules behind the Turtle program (the CSV's reference). (Practitioner
  document; not a study.)
* The ATR is Wilder's (1978); sizing by volatility is the same
  mechanism as volatility targeting (RK22), applied per trade.

## Against, and failure modes

* Gaps and stop slippage exceed the planned risk; ATR is backward-looking
  (the CSV's caveat).
* Per-trade risk parity does not cap total exposure across many open
  lots, which is the grid's actual risk.

## Fit with volatility-ai

The stop form is out (no price stops). ATR-normalised lot size fits and
is effectively what V7 and S4 do with other volatility measures; the
Turtle unit code is in `research/strategies/position_sizing.py` for the
scale-in pyramid (C-G5). There is little new to build.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Faith, C. (2003). "The Original Turtle Trading Rules." The CSV's
  reference:
  <https://analyzingalpha.com/wp-content/uploads/2022/04/original-turtle-trading-rules.pdf>.
  Not opened here; the rule is as transcribed in
  `research/catalog/trend_following.py` (`turtle_original_trades`).
* Wilder, J. W. (1978). *New Concepts in Technical Trading Systems*.
  Trend Research. (ATR's definition; not re-checked.)
* This repository: `research/strategies/position_sizing.py`, ledger C-G5,
  V7, S4.
