# Long-Volatility Breakout (Options)

**Ledger ID RK242** · rank 242 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Options / volatility |
| Potential effectiveness rank | 242 (1 = strongest) |
| AI implementability rank | 41 (1 = easiest) |
| Retail advantage rank | 102 (1 = strongest) |
| Fit with this project | ⛔ (options) |
| Implemented in volatility-ai | **Research code.** quant-trading's straddle (`options.straddle_entry`, `straddle_pnl_at_expiry`; ledger Q12). |
| Related ledger entries | Q12, RK281, RK282 |

## In one paragraph

Buy straddles or strangles before an expected catalyst, betting the move
will exceed what implied volatility prices in. On average the bet loses:
at-the- money index straddles lose about 3% a week, because option
buyers pay a volatility risk premium; and around scheduled events
implied volatility collapses after the news, so being right on the size
of the move is not enough.

## The rule

```text
before a catalyst: buy ATM call + ATM put (or OTM strangle) if implied vol < forecast realised vol
exit after the event or at a vol/time stop
```

## Evidence

* **Coval & Shumway (2001), "Expected Option Returns," *Journal of
  Finance* 56(3), 983–1009:** zero-beta at-the-money index straddles
  lose about 3% a week on average, evidence that volatility risk is
  priced. (Abstract.)

## Against, and failure modes

* Theta, implied-volatility crush and overpaying for the event (the
  CSV's caveat).

## Fit with volatility-ai

Options are outside this project's instrument rules (long-only stocks
and ETFs). The grid harvests volatility the other way round (it is short
gamma), which is the side the risk premium pays.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Coval, J. D., Shumway, T. (2001). "Expected Option Returns." *Journal
  of Finance* 56(3), 983–1009. Abstract.
* This repository: `research/catalog/options.py`, ledger Q12.
