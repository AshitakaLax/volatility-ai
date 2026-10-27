# Put-Write / Cash-Secured Put

**Ledger ID RK282** · rank 282 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Options / income |
| Potential effectiveness rank | 282 (1 = strongest) |
| AI implementability rank | 198 (1 = easiest) |
| Retail advantage rank | 221 (1 = strongest) |
| Fit with this project | ⛔ (options) · the grid is a premium-free relative |
| Implemented in volatility-ai | **Research code.** The put leg of ThetaGang's wheel (`options.wheel_should_write`, `wheel_select_contract`; ledger S1). |
| Related ledger entries | S1, RK281, RK284 |

## In one paragraph

Sell puts fully collateralised by cash: collect the premium, and buy the
stock at the strike if assigned. The Cboe PUT index (monthly
at-the-money S&P 500 puts) beat the S&P 500 from 1986 to 2008 with about
a third less volatility, because put sellers collect the volatility risk
premium. It outperforms in quiet and falling markets and lags sharp
rallies, and its worst losses come in crashes, exactly when the
collateral is needed.

## The rule

```text
hold T-bills equal to strike x 100; each month sell one ATM (or OTM) put; on assignment take the shares
```

## Evidence

* **Cboe PUT index (Ennis Knupp study, July 1986–October 2008):**
  selling one-month at-the-money S&P 500 puts against T-bills returned
  10.32% a year with 9.91% volatility, against 8.77% and 15.39% for the
  S&P 500; it lags in sharp rallies. Gross of costs, and the history
  before 2007 was constructed retroactively. (Summaries; Ungar & Moran
  2009 in the *Journal of Alternative Investments* is the published
  version, not opened.)
* **Coval & Shumway (2001), "Expected Option Returns," *Journal of
  Finance* 56(3), 983–1009:** zero-beta at-the-money index straddles
  lose about 3% a week on average, evidence that volatility risk is
  priced. (Abstract.)

## Against, and failure modes

* The PUT index is a hypothetical collateralised index strategy;
  single-stock puts carry different assignment and concentration risk
  (the CSV's caveat).
* Short puts are the worst position to hold in a decline (ledger S1).

## Fit with volatility-ai

Options are outside this project's instrument rules (long-only stocks
and ETFs). The grid is economically close to these: each resting buy
below the price is a commitment like a short put, and each lot's sale at
its target caps its upside like a covered call, but with no premium
collected and no obligation to buy below the level. The covered-call
decomposition (equity plus short volatility plus a reversal bet) is a
good description of the grid's own risk.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Ungar, J., Moran, M. T. (2009). "The Cash-secured PutWrite Strategy
  and Performance of Related Benchmark Indexes." *Journal of Alternative
  Investments* 11(4), 43–56. Not opened; figures via summaries of the
  Ennis Knupp study.
* Coval, J. D., Shumway, T. (2001). "Expected Option Returns." *Journal
  of Finance* 56(3), 983–1009. Abstract.
* This repository: `research/catalog/options.py`, ledger S1.
