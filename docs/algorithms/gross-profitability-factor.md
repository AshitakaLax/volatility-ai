# Gross Profitability Factor

**Ledger ID RK13** · rank 13 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Equity factor / fundamental |
| Potential effectiveness rank | 13 (1 = strongest) |
| AI implementability rank | 167 (1 = easiest) |
| Retail advantage rank | 106 (1 = strongest) |
| Fit with this project | ⏳ long-only stock basket (needs fundamentals) · ⛔ long/short |
| Implemented in volatility-ai | **Yes, as a backtest book.** Selectable as `--allocator gross_profitability` in the portfolio book (`python -m tools.portfolio_book` --data fundamentals=FILE; `research/strategies/allocator_library.py`), which routes every sale through the no-loss guard. Trading it live needs a multi-asset deployment ([engine/roadmap.md](../../engine/roadmap.md) item 1). Unmeasured. Before this change: **Research code** in `research.catalog.factors`: `gross_profitability`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK12, RK48, RK5 |

## In one paragraph

Rank stocks by gross profits (revenue minus cost of goods sold) divided
by total assets, and buy the most profitable. Novy-Marx's point is that
gross profit is the cleanest measure of economic profitability: it sits
above the expense lines (R&D, advertising, SG&A) that accounting treats
as costs but that are really investment. Profitable firms earn higher
returns even though they look expensive, so profitability and value
hedge each other and work best together.

## The rule

```
GP/A = (revenue - cost of goods sold) / total assets       # from the latest public annual statement
rank within the universe (excluding financials); long the top tercile or quintile
combine with book-to-market (rank sum) for the "profitable value" strategy
```

## Evidence

* **Novy-Marx (2013), JFE 108(1), 1–28** (NBER w15940): GP/A predicts
  returns about as well as book-to-market; profitable firms outperform
  despite higher valuations; controlling for profitability dramatically
  improves value strategies, especially among the largest, most liquid
  stocks; hard to reconcile with distress-based value explanations.
  1962–2010. (Abstract.)

## Against, and failure modes

* Requires release-date-aware statements and consistent definitions
  (the CSV's caveat); COGS classification differs by industry, so
  industry controls matter.
* Profitable growth firms are the stocks a TQQQ-heavy book already owns
  through the index, so as an addition it diversifies little.

## Fit with volatility-ai

A long-only stock basket fits the instrument rule; the data and the
multi-stock book are missing. The Nasdaq-100 is probably tilted toward
high gross profitability (an assumption, not checked here); if so, part
of TQQQ's history is a profitability tilt, which the RK9 attribution
would show.

## What it would take

Point-in-time annual statements with filing dates, a survivorship-free
universe, and a portfolio book outside the single-symbol engine.
Reference entry until then.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Novy-Marx, R. (2013). "The Other Side of Value: The Gross
  Profitability Premium." *Journal of Financial Economics* 108(1), 1–28.
  NBER w15940 <https://www.nber.org/papers/w15940> (the CSV's reference).
  Abstract.
