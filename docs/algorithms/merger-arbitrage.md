# Merger Arbitrage

**Ledger ID RK39** · rank 39 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Event-driven / relative value |
| Potential effectiveness rank | 39 (1 = strongest) |
| AI implementability rank | 140 (1 = easiest) |
| Retail advantage rank | 235 (1 = strongest) |
| Fit with this project | ⏳ (long the target in cash deals) · ⛔ (stock deals hedged by shorting the acquirer) |
| Implemented in volatility-ai | **Research code** in `research.catalog.stat_arb`: `merger_arb_return`, `merger_implied_probability`; tested on synthetic data, not wired into the engine. No deal data in the warehouse. |
| Related ledger entries | RK47 |

## In one paragraph

After a takeover is announced, the target trades below the offer price
because the deal might fail. Buy the target (and, in a stock deal, short
the acquirer at the exchange ratio) and collect the spread when the deal
closes. Over 4,750 US deals from 1963 to 1998 this earned about 4% a
year in excess returns after costs. The payoff looks like writing index
puts: little market sensitivity in calm or rising markets, and losses
that arrive together when markets fall sharply. That is the same time
this book's grid accumulates lots.

## The rule

```
cash deal: buy target at P < offer; spread = offer / P - 1; annualise over the expected time to close
stock deal: buy target, short ratio x acquirer shares
skip or size down: regulatory, financing or shareholder risk; exit on completion or break
```

## Evidence

* **Mitchell & Pulvino (2001), "Characteristics of Risk and Return in
  Risk Arbitrage," *Journal of Finance* 56(6), 2135–2175:** 4,750 mergers
  1963–1998; returns correlated with the market only in sharp declines,
  like uncovered index puts; about 4% a year excess return after a
  contingent-claims adjustment and costs. (Abstract.)

## Against, and failure modes

* Deal breaks lose many times the spread; correlated breaks in crises
  (the CSV's caveat).
* Stock deals need a short leg.

## Fit with volatility-ai

Cash-deal targets are long-only stock positions and would pass the
instrument rule, but it is a separate event book with its own data
(deal terms, dates, regulatory status), and its losses coincide with
this book's worst periods. Not a priority.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Mitchell, M., Pulvino, T. (2001). *Journal of Finance* 56(6),
  2135–2175.
  <https://ideas.repec.org/a/bla/jfinan/v56y2001i6p2135-2175.html>.
  Abstract.
