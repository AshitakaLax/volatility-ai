# Iron Butterfly Credit Strategy

**Ledger ID RK286** · rank 286 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Options / short premium |
| Potential effectiveness rank | 286 (1 = strongest) |
| AI implementability rank | 145 (1 = easiest) |
| Retail advantage rank | 267 (1 = strongest) |
| Fit with this project | ⛔ (options) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK285, RK282 |

## In one paragraph

Sell an at-the-money straddle and buy out-of-the-money wings, profiting
if expiry lands near the centre strike. It is the iron condor with the
short strikes at the money: more credit, a narrower profit zone, more
short gamma. Cboe publishes a benchmark index (BFLY: at-the-money SPX
puts and calls sold, 5% out-of-the-money wings bought), but I did not
find its performance figures.

## The rule

```text
BFLY: sell ATM SPX put and call, buy 5% OTM wings, one month, hold T-bills; roll monthly
```

## Evidence

* Cboe describes BFLY and CNDR as hypothetical SPX strategies with over
  35 years of history, designed to limit downside. BFLY's return,
  volatility and drawdown figures were not found. (Cboe posts.)
* **Coval & Shumway (2001), "Expected Option Returns," *Journal of
  Finance* 56(3), 983–1009:** zero-beta at-the-money index straddles
  lose about 3% a week on average, evidence that volatility risk is
  priced. (Abstract.)

## Against, and failure modes

* Short gamma loses fast around jumps; the defined maximum loss can be
  large against the credit (the CSV's caveat).

## Fit with volatility-ai

Options are outside this project's instrument rules (long-only stocks
and ETFs).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Cboe, "Benchmark Indices Series: Volatility Management with Cboe's
  BFLY and CNDR Indices." Summary.
* Coval, J. D., Shumway, T. (2001). "Expected Option Returns." *Journal
  of Finance* 56(3), 983–1009. Abstract.
