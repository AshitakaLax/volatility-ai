# iNAV Dislocation ETF Arbitrage

**Ledger ID RK91** · rank 91 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Relative value / ETF arbitrage |
| Potential effectiveness rank | 91 (1 = strongest) |
| AI implementability rank | 262 (1 = easiest) |
| Retail advantage rank | 2,827 (1 = strongest) |
| Fit with this project | ⛔ (market making with a hedge leg; forced end-of-day exits) |
| Implemented in volatility-ai | **Partial.** Only the authorized participant's create/redeem decision (`excluded.creation_redemption_action`, C-RJ6); no iNAV estimate or intraday dislocation trade. |
| Related ledger entries | C-RJ6, RK24 |

## In one paragraph

Rebuild the ETF's intraday NAV yourself from live quotes of its
holdings. When the ETF's bid or ask moves past that value by more than
the spread, post passive limit orders on the cheap side, hedge with the
basket, and flatten by the close. It is the intraday, market-making
form of RK24. The evidence that ETF prices stray from fair value (about
100 bp bands after correcting stale NAVs) supports the premise. Capturing
it needs Level 1/2 data on every holding and queue priority.

## The rule

```
iNAV_t = sum(weight_i x mid_i,t) + cash (from the daily basket file)
ETF ask < iNAV - costs: post a buy at the bid; ETF bid > iNAV + costs: post a sell at the ask; hedge with the basket
flatten everything by the close
```

## Evidence

* **Petajisto (2017), *Financial Analysts Journal* 73(1), 24–54:**
  deviations typically within about 200 bp, about 100 bp after removing
  stale pricing; trading them earns abnormal returns before costs; short-
  term mean reversion in ETF prices. (Abstract.)
* The passive-limit-order and end-of-day rules are the CSV's own
  construction; no study of this exact form was found.

## Against, and failure modes

* Passive orders fill when the price moves against them (adverse
  selection); unhedged fills are directional; mandatory end-of-day
  liquidation can realise losses.

## Fit with volatility-ai

Out of scope. Its iNAV estimate would be a sensible execution check for
this book's market orders, but no such need has come up.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Petajisto, A. (2017). "Inefficiencies in the Pricing of Exchange-Traded
  Funds." *Financial Analysts Journal* 73(1), 24–54. Abstract.
* The CSV's references: alpaca-py; Alpaca ETF trading documentation.
* This repository: `research/catalog/excluded.py`, ledger C-RJ6.
