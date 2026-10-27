# Futures Cash-and-Carry Basis Trading

**Ledger ID RK26** · rank 26 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Basis / carry |
| Potential effectiveness rank | 26 (1 = strongest) |
| AI implementability rank | 95 (1 = easiest) |
| Retail advantage rank | 163 (1 = strongest) |
| Fit with this project | ⛔ (a short futures or short underlying leg is the trade) |
| Implemented in volatility-ai | **Partial**, crypto only: a spot-perpetual funding carry (`crypto.funding_carry_positions`, ledger C-RJ2, rejected) that enters and exits on funding thresholds, not on the futures basis. |
| Related ledger entries | RK25, RK85, C-RJ2 |

## In one paragraph

A future should trade at spot plus the cost of carrying the spot asset
to expiry (financing, storage, minus dividends or convenience yield).
When it trades rich, buy spot and sell the future and hold to
convergence; when it trades cheap, do the reverse. In liquid index
futures the gap rarely exceeds transaction costs for long; the trade
lives where financing, borrow or inventory is constrained, which is
also where it carries real risk (margin, delivery, funding).

## The rule

```
fair futures price F* = S x exp((r - q) T)               # equity index: r financing, q dividend yield
                       = S x exp((r + storage - convenience) T)   # physical commodity
basis gap = F - F*
if gap > costs: buy S, sell F, hold to expiry (cash-and-carry)
if gap < -costs: sell/short S, buy F (reverse cash-and-carry)
```

## Evidence

* **MacKinlay & Ramaswamy (1988), *Review of Financial Studies* 1(2),
  137–158:** intraday S&P 500 futures against the index: futures price
  changes are more volatile than index changes; deviations from the
  cost-of-carry value grow with maturity and are path-dependent,
  consistent with arbitrage bands. (Abstract.)
* The cost-of-carry relation is textbook (CME's futures primers, the
  CSV's reference); its practical content is in the costs and limits.

## Against, and failure modes

* Not risk-free until financing, collateral, margin calls and delivery
  are handled (the CSV's caveat); 2020's Treasury basis unwind is the
  modern example of a "carry" trade that blew up on funding.
* Retail cannot finance or short the underlying at institutional rates.

## Fit with volatility-ai

Out of scope: one leg is always a short future or a short underlying.
The nearest code is a crypto relative (long spot, short perpetual, timed
on funding rather than the basis), research code and rejected (C-RJ2).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* MacKinlay, A. C., Ramaswamy, K. (1988). "Index-Futures Arbitrage and
  the Behavior of Stock Index Futures Prices." *Review of Financial
  Studies* 1(2), 137–158. <https://doi.org/10.1093/rfs/1.2.137>. Abstract.
* The CSV's own references: CME Group, "Introduction to Futures";
  Hummingbot v1 strategies (crypto basis bots).
* This repository: `research/catalog/crypto.py` (C-RJ2).
