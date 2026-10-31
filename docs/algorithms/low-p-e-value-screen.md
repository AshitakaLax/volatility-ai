# Low P/E Value Screen

**Ledger ID RK57** · rank 57 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Factor / systematic equity |
| Potential effectiveness rank | 57 (1 = strongest) |
| AI implementability rank | 72 (1 = easiest) |
| Retail advantage rank | 244 (1 = strongest) |
| Fit with this project | ⏳ long-only stock basket or value ETF |
| Implemented in volatility-ai | **Yes, as a backtest book.** Selectable as `--allocator low_pe` in the portfolio book (`python -m tools.portfolio_book` --data fundamentals=FILE; `research/strategies/allocator_library.py`), which routes every sale through the no-loss guard. Trading it live needs a multi-asset deployment ([engine/roadmap.md](../../engine/roadmap.md) item 1). Unmeasured. Before this change: **Research code** in `research.catalog.factors`: `low_pe_screen`; tested on synthetic data, not wired into the engine. (COWZ, a free-cash-flow-yield ETF, is traded by the grid as an instrument only.) |
| Related ledger entries | RK48, RK5 |

## In one paragraph

Buy stocks with low price-to-earnings ratios, typically after excluding
losses and screening for leverage and profitability. Basu's 1977 test
was one of the first challenges to market efficiency: low-P/E NYSE
portfolios beat high-P/E ones by about six or seven percent a year over
roughly 1957–1971. It is the earnings-based sibling of book-to-market
value, with the same long dry spells and the extra problem that P/E is
meaningless for negative or one-off earnings.

## The rule

```
E/P = trailing 12-month diluted EPS / price          # use E/P, not P/E, so losses sort sensibly
exclude negative and extraordinary earnings; apply leverage/profitability screens
annually: hold the top quintile by E/P, equal weight
```

## Evidence

* **Basu (1977), *Journal of Finance* 32(3), 663–682:** NYSE stocks,
  about 1957–1971; low-P/E portfolios earned roughly 6–7% a year more
  than high-P/E portfolios (summaries differ on the window and figure);
  portfolios formed on E/P quintiles, re-ranked annually. (Summaries.)

## Against, and failure modes

* **Mixed replications:** a Toronto Stock Exchange study found no
  excess return for 1975–1984; Johnson, Fiore & Zuber (1989) could not
  link excess return to low P/E using Basu's method on later data.
  (Summaries.)
* Earnings are noisier than book value and easier to manage; cheapness
  alone is not undervaluation (the CSV's caveat).
* Shares value's long drawdowns (RK48).

## Fit with volatility-ai

A long-only basket fits the instrument rule; the earnings data and the
multi-stock book are missing. Reference entry; the ETF route and RK9's
attribution are the cheap paths.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Basu, S. (1977). "Investment Performance of Common Stocks in Relation
  to Their Price-Earnings Ratios: A Test of the Efficient Market
  Hypothesis." *Journal of Finance* 32(3), 663–682. Summaries.
* Johnson, R., Fiore, L., Zuber, R. (1989), and a Toronto Stock Exchange
  replication. Search-result summaries only.
