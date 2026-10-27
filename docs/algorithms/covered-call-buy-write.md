# Covered Call / Buy-Write

**Ledger ID RK281** · rank 281 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Options / income |
| Potential effectiveness rank | 281 (1 = strongest) |
| AI implementability rank | 197 (1 = easiest) |
| Retail advantage rank | 161 (1 = strongest) |
| Fit with this project | ⛔ (options) · the grid is a premium-free relative |
| Implemented in volatility-ai | **Research code.** The call leg of ThetaGang's wheel (`options.wheel_calls_to_write`; ledger S1). |
| Related ledger entries | S1, RK282, RK284 |

## In one paragraph

Hold the underlying and sell calls against it, collecting premium in
exchange for capping the upside. Historically the S&P 500 buy-write
index (BXM) earned close to the index's return with lower volatility. A
decomposition shows why, and where the risk sits: a covered call is
equity plus short volatility (well paid) plus an equity-reversal bet
(risky and poorly paid).

## The rule

```text
hold 100 shares; each month sell one call (BXM: at the money, one month); repeat at expiry
```

## Evidence

* **Whaley (2002), BXM:** similar return to the S&P 500 with markedly
  lower volatility, 1988–2001. (Secondary descriptions; not opened.)
* **Israelov & Nielsen (2015), "Covered Calls Uncovered," *Financial
  Analysts Journal* 71(6), 44–57:** a BXM-like covered call is equity
  plus short volatility plus an equity-reversal (timing) exposure;
  equity brings most of the risk and return, short volatility realised a
  Sharpe ratio near 1.0 with 10% of the risk, and the reversal piece
  about 25% of the risk for little return. Removing it raises the Sharpe
  ratio. (Abstract.)

## Against, and failure modes

* Premium is payment for giving up the upside; sharp rallies lag the
  index (the CSV's caveat).

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

* Whaley, R. E. (2002). "Return and Risk of CBOE Buy Write Monthly
  Index." *Journal of Derivatives* 10(2). Secondary descriptions.
* Israelov, R., Nielsen, L. N. (2015). "Covered Calls Uncovered."
  *Financial Analysts Journal* 71(6), 44–57. Abstract.
* This repository: `research/catalog/options.py`, ledger S1.
