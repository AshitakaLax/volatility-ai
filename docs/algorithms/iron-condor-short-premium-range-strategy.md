# Iron Condor / Short Premium Range Strategy

**Ledger ID RK285** · rank 285 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Options / income |
| Potential effectiveness rank | 285 (1 = strongest) |
| AI implementability rank | 200 (1 = easiest) |
| Retail advantage rank | 280 (1 = strongest) |
| Fit with this project | ⛔ (options) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK286, RK282 |

## In one paragraph

Sell an out-of-the-money call spread and put spread for a net credit,
profiting if the underlying stays in the range until expiry; the bought
wings cap the loss. Cboe's iron condor index (CNDR) had returns similar
to the S&P 500 with lower volatility and drawdowns from 1986 to 2015, in
a study the index sponsor commissioned. Defined risk is not small risk:
a gap through a wing loses many months of credit.

## The rule

```text
CNDR: sell ~0.15-0.20-delta SPX put and call, buy ~0.05-delta wings, one month, hold T-bills; roll monthly
```

## Evidence

* **Cboe-commissioned study of SPX options-selling indexes (mid-1986 to
  2015):** returns similar to the S&P 500 with lower volatility and
  drawdowns; CNDR had 10 monthly losses worse than 6% against the S&P
  500's 15. (Press release and summaries; sponsor-commissioned.)
* **Coval & Shumway (2001), "Expected Option Returns," *Journal of
  Finance* 56(3), 983–1009:** zero-beta at-the-money index straddles
  lose about 3% a week on average, evidence that volatility risk is
  priced. (Abstract.)

## Against, and failure modes

* Gaps, skew, fills and four-leg slippage (the CSV's caveat).

## Fit with volatility-ai

Options are outside this project's instrument rules (long-only stocks
and ETFs).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Cboe, "Study Analyzes Performance of CBOE S&P 500 (SPX)
  Options-Selling Indexes" (2016) and the BFLY/CNDR benchmark-series
  post. Summaries.
* Coval, J. D., Shumway, T. (2001). "Expected Option Returns." *Journal
  of Finance* 56(3), 983–1009. Abstract.
