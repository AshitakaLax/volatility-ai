# Options Wheel

**Ledger ID RK284** · rank 284 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Options / income |
| Potential effectiveness rank | 284 (1 = strongest) |
| AI implementability rank | 199 (1 = easiest) |
| Retail advantage rank | 222 (1 = strongest) |
| Fit with this project | ⛔ (options) · the grid is a premium-free relative |
| Implemented in volatility-ai | **Research code.** ThetaGang's wheel (`options.wheel_select_contract`, `wheel_should_roll`; ledger S1). |
| Related ledger entries | S1, RK281, RK282, V5 |

## In one paragraph

Sell cash-secured puts until assigned; then hold the shares and sell
covered calls until they are called away; repeat. It alternates the two
legs whose index versions (PUT, BXM) are documented. I found no study of
the wheel as a combined rule. Its known weakness is that it keeps owning
a falling stock: rolling puts down extends the commitment rather than
limiting the loss.

## The rule

```text
state CASH: sell a cash-secured put; on assignment -> state SHARES
state SHARES: sell a covered call (strike >= cost basis, typically); on call-away -> state CASH
```

## Evidence

* **Cboe PUT index (Ennis Knupp study, July 1986–October 2008):**
  selling one-month at-the-money S&P 500 puts against T-bills returned
  10.32% a year with 9.91% volatility, against 8.77% and 15.39% for the
  S&P 500; it lags in sharp rallies. Gross of costs, and the history
  before 2007 was constructed retroactively. (Summaries; Ungar & Moran
  2009 in the *Journal of Alternative Investments* is the published
  version, not opened.)
* **Israelov & Nielsen (2015), "Covered Calls Uncovered," *Financial
  Analysts Journal* 71(6), 44–57:** a BXM-like covered call is equity
  plus short volatility plus an equity-reversal (timing) exposure;
  equity brings most of the risk and return, short volatility realised a
  Sharpe ratio near 1.0 with 10% of the risk, and the reversal piece
  about 25% of the risk for little return. Removing it raises the Sharpe
  ratio. (Abstract.)
* **No study found** of the combined wheel rule.

## Against, and failure modes

* Concentrates exposure in falling assets; rolling changes the risk and
  guarantees no recovery (the CSV's caveat).

## Fit with volatility-ai

Options are outside this project's instrument rules (long-only stocks
and ETFs). The wheel is the closest options analogue of this project's
grid: buy on weakness, sell above cost. The grid does it without
premiums, in many small lots, and with a regime exit that can stop it
buying into a crash.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Ungar & Moran (2009) and Israelov & Nielsen (2015): see RK282 and
  RK281.
* This repository: `research/catalog/options.py`, ledger S1.
