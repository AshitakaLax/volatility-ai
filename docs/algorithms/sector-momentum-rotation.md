# Sector Momentum Rotation

**Ledger ID RK19** · rank 19 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Trend / allocation |
| Potential effectiveness rank | 19 (1 = strongest) |
| AI implementability rank | 23 (1 = easiest) |
| Retail advantage rank | 1 (1 = strongest) |
| Fit with this project | 🧪 fits; X3's harness runs it with a sector-ETF universe |
| Implemented in volatility-ai | **Yes, as a backtest book.** `research/strategies/allocators.py` `cross_sectional_momentum`, run by the portfolio book (`python -m tools.portfolio_book --allocator cross_sectional_momentum --preset sectors`), which routes every sale through the no-loss guard. Trading it live needs a multi-asset deployment ([engine/roadmap.md](../../engine/roadmap.md) item 1). Unmeasured. Before this change: **Partial.** `tools/rotation.py --mode relative_strength --universe XLK XLF ...` holds the single best sector ETF by trailing return, cash when even the best is negative. Never run with sectors. |
| Related ledger entries | X3, RK3, RK7, RK10 |

## In one paragraph

Rank the eleven sector ETFs by trailing return and hold the strongest
one or few, rebalancing monthly. It is the retail-friendly form of
industry momentum, which Moskowitz & Grinblatt found accounts for much of
individual-stock momentum and survives controls for size, value and
stock momentum. The CSV ranks it first of 14,225 for retail advantage:
cheap ETFs, a monthly trade, no shorting. The cost is concentration: one
or two sectors can sit far from the index for years.

## The rule

```
universe: the 11 SPDR sector ETFs (XLB XLC XLE XLF XLI XLK XLP XLRE XLU XLV XLY)
monthly: score = trailing 6- or 12-month total return (optionally skip the last month)
hold the top 1–3, equal weight; optional market filter (cash when the market is below its 10-month SMA)
```

## Evidence

* **Moskowitz & Grinblatt (1999):** industry momentum is highly
  profitable even after controlling for size, book-to-market, individual
  stock momentum, cross-sectional dispersion and microstructure; once it
  is controlled for, individual-stock momentum is much weaker.
  (Abstract.)
* **Arnott, Kalesnik & Linnainmaa (2023):** momentum in industry-neutral
  *factors* explains industry momentum, not the other way round; the
  industry effect may be a factor effect in disguise. (Abstract.)

## Against, and failure modes

* **Concentration and tracking error**: holding one sector is a
  single-sector bet (XLK through 2000–02, XLE through 2014–15).
* **XLC and XLRE are recent** (2018 and 2015), so a long backtest has a
  changing universe; fix the universe by date to avoid survivorship.
* **Short lookbacks whipsaw**; the published effect is a 6–12-month one.

## Fit with volatility-ai

Long-only ETFs, fits the constraints. In the X3 harness each held ETF
runs the champion grid scaled by its range, and a rotation out
liquidates that sleeve through the regime exit, so the harness measures
"grid in the leading sector", not "hold the leading sector". Both are
worth running.

## How to test it here

```bash
python -m tools.rotation --mode relative_strength --rs-days 126 \
    --universe XLB XLE XLF XLI XLK XLP XLU XLV XLY     # ingest these first
python -m tools.rotation --mode relative_strength --rs-days 252 --universe ...
```

Pair it with a market filter (RK10's shape) and report switches;
compare against holding RSP and QQQ.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Moskowitz, T., Grinblatt, M. (1999). "Do Industries Explain
  Momentum?" *Journal of Finance* 54(4), 1249–1290.
  <https://ideas.repec.org/a/bla/jfinan/v54y1999i4p1249-1290.html>.
  Abstract.
* Arnott, R. D., Kalesnik, V., Linnainmaa, J. T. (2023). "Factor
  Momentum." *Review of Financial Studies* 36(8), 3034–3070.
  <https://doi.org/10.1093/rfs/hhad006>. Abstract.
