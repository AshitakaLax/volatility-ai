# Gap-Fade Strategy

**Ledger ID RK149** · rank 149 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Mean reversion / intraday |
| Potential effectiveness rank | 149 (1 = strongest) |
| AI implementability rank | 133 (1 = easiest) |
| Retail advantage rank | 157 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** A day trade whose edge has faded in large caps; gaps on TQQQ are better handled by the grid's resting orders. |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK69, N3, X1 |

## In one paragraph

Fade an opening gap expecting it to close the same day. The
overnight-to-intraday reversal it relies on has faded overall and now
appears mainly in small, illiquid stocks; for S&P 500 names the
relationship has turned positive.

## Evidence

* **Branch & Ma (2018 retrospective, via CXO Advisory):** the
  overnight-intraday reversal has faded; for S&P 500 stocks it is now a
  positive relationship. (Summary.)
* **US data 2011–2024 (Turku thesis, 2025):** the reversal is strongest
  in small, illiquid stocks under market-wide uncertainty and is a
  structural feature of opening price formation rather than an
  exploitable inefficiency. (Abstract.)
* **Gap-fill statistics** for SPY fall sharply with gap size
  (practitioner tools).

## Against, and failure modes

* Large gaps, the ones worth fading, are the ones least likely to fill.

## Fit with volatility-ai

The grid already buys a gap down through its resting orders and sells a
gap up through its targets, without a same-day exit. A gap-fade day
trade adds nothing.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Branch & Ma overnight-intraday reversal retrospective, CXO Advisory
  (2018). Summary.
* University of Turku master's thesis on opening-price reversal (2025).
  Abstract.
