# Index Futures vs Cash Basis Arbitrage

**Ledger ID RK25** · rank 25 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Index arbitrage / basis |
| Potential effectiveness rank | 25 (1 = strongest) |
| AI implementability rank | 141 (1 = easiest) |
| Retail advantage rank | 2,759 (1 = strongest) |
| Fit with this project | ⛔ (futures, short legs, institutional execution) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK24, RK26 |

## In one paragraph

An index future's fair value is the spot index carried forward at the
financing rate minus the expected dividends. When the future trades
outside a band set by trading costs, buy the cheap side and sell the
rich one (program trading). The classic study finds the mispricing is
larger for longer-dated contracts and path-dependent. It is an
institutional trade: the CSV ranks it 2,759th for retail advantage.

## The rule

```
fair = S x exp((r - q) x T)        # r financing rate, q expected dividend yield, T time to expiry
F > fair + band: sell futures, buy the basket; F < fair - band: buy futures, short the basket
unwind at convergence or hold to expiry
```

## Evidence

* **MacKinlay & Ramaswamy (1988), "Index-Futures Arbitrage and the
  Behavior of Stock Index Futures Prices," *Review of Financial Studies*
  1(2), 137–158:** intraday S&P 500 futures and index data; mispricing
  increases on average with maturity and is path-dependent; futures
  price changes are more volatile than index changes. (Abstract.)

## Against, and failure modes

* Replicating the cash basket is costly; dividend forecast error,
  funding, taxes and latency set the band (the CSV's caveat).
* Short legs and futures are out of scope.

## Fit with volatility-ai

Out of scope, and no long-only form exists.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* MacKinlay, A. C., Ramaswamy, K. (1988). "Index-Futures Arbitrage and
  the Behavior of Stock Index Futures Prices." *Review of Financial
  Studies* 1(2), 137–158.
  <https://econpapers.repec.org/RePEc:oup:rfinst:v:1:y:1988:i:2:p:137-158>.
  Abstract.
* The CSV's reference: CME Group, "Introduction to Equity Index
  Products" (course).
