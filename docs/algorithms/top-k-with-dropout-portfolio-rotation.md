# Top-K with Dropout Portfolio Rotation

**Ledger ID RK216** · rank 216 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Portfolio strategy / ML signal deployment |
| Potential effectiveness rank | 216 (1 = strongest) |
| AI implementability rank | 104 (1 = easiest) |
| Retail advantage rank | 24 (1 = strongest) |
| Fit with this project | ⏳ as a turnover rule for a rotation |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK214, X3, RK7 |

## In one paragraph

Qlib's portfolio rule: hold the top K assets by forecast score, but at
each rebalance replace at most N of them (sell the worst-ranked
holdings, buy the best-ranked non-holdings). It is a turnover limiter
for a ranking signal, not a signal. I found no study of it beyond Qlib's
own documentation and benchmarks.

## The rule

```text
each rebalance: rank by score; sell up to N held names ranked worst; buy the N best names not held; hold K in total
```

## Evidence

* Qlib documentation: `TopkDropoutStrategy`, used in its published
  benchmarks. (Documentation.)
* **No independent study found**; its value is the turnover saved for a
  given signal, which depends on that signal.

## Against, and failure modes

* Performance depends on the alpha model, K, N and costs (the CSV's
  caveat).

## Fit with volatility-ai

If X3's relative-strength rotation is ever widened to hold more than one
ETF, a top-K-with-dropout rule is the simplest way to cap switching,
which liquidates grid sleeves here. Not needed while X3 holds one name.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Microsoft Qlib, strategy documentation (`TopkDropoutStrategy`) and
  portfolio examples (the CSV's references).
