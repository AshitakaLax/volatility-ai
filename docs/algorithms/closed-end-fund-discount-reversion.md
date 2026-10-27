# Closed-End Fund Discount Reversion

**Ledger ID RK82** · rank 82 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Relative value / fund discounts |
| Potential effectiveness rank | 82 (1 = strongest) |
| AI implementability rank | 4 (1 = easiest) |
| Retail advantage rank | 57 (1 = strongest) |
| Fit with this project | ⏳ (a long-only basket of listed funds; a separate book) |
| Implemented in volatility-ai | **No.** The warehouse has no closed-end fund prices or NAV history. |
| Related ledger entries | RK24 |

## In one paragraph

Closed-end funds trade on exchanges at prices that can sit well below
(or above) the value of their holdings, and the discount mean-reverts.
Buy funds at unusually wide discounts and hold them for the narrowing
(optionally hedging the holdings' asset class or waiting for catalysts
such as tender offers and activists). Unlike most of the arbitrage
entries on this list, the basic form is long-only in listed securities.
The evidence is old but solid. Pontiff found that a fund at a 20%
discount had a 12-month expected return about 6 points higher than an
undiscounted fund, driven by the discount narrowing.

## The rule

```
discount = price / NAV - 1; z = (discount - its own 1-3 year mean) / std
buy when the discount is wide in absolute terms and relative to its history (z < -2); sell as it narrows (z > 0)
screens: liquidity, leverage, expense ratio, distribution source (avoid return-of-capital payers), catalysts
```

## Evidence

* **Pontiff (1995), "Closed-end fund premia and returns: Implications
  for financial market equilibrium," *Journal of Financial Economics* 37,
  341–370:** confirms Thompson's (1978) finding that premia predict
  returns negatively. Funds at a 20% discount have 12-month expected
  returns about 6% higher than undiscounted funds, from premium mean
  reversion rather than better portfolio performance. (Abstract.)
* **Lee, Shleifer & Thaler (1991), *Journal of Finance* 46(1):**
  discounts move with small-investor sentiment. (Standard reference.)
* **Pontiff (1996), "Costly arbitrage: evidence from closed-end funds,"
  *Quarterly Journal of Economics* 111(4), 1135–1151:** discounts are
  wider where arbitrage is costlier. (Listing.)
* **Patro, Piccotti & Wu (2017):** the history of premia adds
  information beyond the current premium. (Summary.)

## Against, and failure modes

* Discounts can persist or widen for years; NAVs of illiquid holdings
  are stale; leverage, fees and return-of-capital distributions erode the
  return (the CSV's caveat).
* Many CEFs trade thinly; spreads are wide.

## Fit with volatility-ai

The instrument rule allows it (long-only, listed funds). It is a
separate income book with nothing in common with the TQQQ grid, and the
data (daily NAVs, distributions, corporate actions) is not in the
warehouse.

## What it would take

A CEF universe with daily NAV history (for example from fund sponsors or
a vendor), a monthly rebalance into the widest z-scored discounts, and a
backtest that books distributions and wide spreads.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Pontiff, J. (1995). *Journal of Financial Economics* 37, 341–370.
  Abstract.
* Thompson, R. (1978). "The information content of discounts and
  premiums on closed-end fund shares." *Journal of Financial Economics*.
  Via Pontiff.
* Lee, C. M. C., Shleifer, A., Thaler, R. H. (1991). "Investor Sentiment
  and the Closed-End Fund Puzzle." *Journal of Finance* 46(1).
* Pontiff, J. (1996). *Quarterly Journal of Economics* 111(4),
  1135–1151. Listing.
