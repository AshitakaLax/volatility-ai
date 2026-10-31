# Quality / Profitability Factor

**Ledger ID RK12** · rank 12 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Factor / systematic equity |
| Potential effectiveness rank | 12 (1 = strongest) |
| AI implementability rank | 110 (1 = easiest) |
| Retail advantage rank | 245 (1 = strongest) |
| Fit with this project | ⏳ long-only (stock basket or quality ETF) · ⛔ long/short |
| Implemented in volatility-ai | **Yes, as a backtest book.** Selectable as `--allocator operating_profitability` in the portfolio book (`python -m tools.portfolio_book` --data fundamentals=FILE; `research/strategies/allocator_library.py`), which routes every sale through the no-loss guard. Trading it live needs a multi-asset deployment ([engine/roadmap.md](../../engine/roadmap.md) item 1). Unmeasured. Before this change: **Research code** in `research.catalog.factors`: `operating_profitability`, `quantile_weights`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK9, RK11, RK13 |

## In one paragraph

Rank firms by profitability (gross profits, operating profitability,
ROE/ROA), margins and balance-sheet strength, and favour the strongest.
It is the broad family of which gross profitability (RK13), RMW in the
five-factor model (RK9) and the profitability leg of QMJ (RK11) are
specific definitions. Profitable firms earn higher returns despite
higher valuations, which is what makes the factor a natural partner to
value.

## The rule

```
annually (after statements are public) or monthly with lagged data:
    score = operating profitability = (revenue - COGS - SG&A - interest) / book equity   # FF RMW
         or gross profits / total assets                                             # Novy-Marx
long the top 30% (academic: short the bottom 30%), within size groups
```

## Evidence

* **Novy-Marx (2013):** gross profits-to-assets predicts the
  cross-section about as well as book-to-market; profitable firms earn
  more despite higher valuation ratios; controlling for profitability
  sharply improves value strategies, especially among large, liquid
  stocks. 1962–2010. (Abstract.)
* **Fama & French (2015):** the profitability factor (RMW) is one of the
  five; with it and CMA, HML is redundant in their US sample. (Abstract.)

## Against, and failure modes

* Accounting restatements, stale statements and industry comparability
  (the CSV's caveat): margins mean different things in software and
  retail.
* Long periods of flat returns in speculative markets.

## Fit with volatility-ai

A long-only stock basket or a quality ETF fits the instrument rule, as a
separate allocation book; neither touches the TQQQ grid. No fundamentals
are in the warehouse.

## What it would take

Point-in-time statements for a stock universe, or the ETF route. The
cheaper research step is attribution: the RMW loading of this project's
books (see RK9).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Novy-Marx, R. (2013). "The Other Side of Value: The Gross
  Profitability Premium." *Journal of Financial Economics* 108(1), 1–28.
  <https://econpapers.repec.org/RePEc:eee:jfinec:v:108:y:2013:i:1:p:1-28>.
  Abstract.
* Fama, E. F., French, K. R. (2015). "A Five-Factor Asset Pricing
  Model." *Journal of Financial Economics* 116(1), 1–22. Abstract.
* Kenneth R. French data library (the CSV's reference).
