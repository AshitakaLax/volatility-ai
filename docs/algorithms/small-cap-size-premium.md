# Small-Cap Size Premium

**Ledger ID RK58** · rank 58 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Factor / systematic equity |
| Potential effectiveness rank | 58 (1 = strongest) |
| AI implementability rank | 89 (1 = easiest) |
| Retail advantage rank | 81 (1 = strongest) |
| Fit with this project | ⏳ long-only (small-cap ETF, ideally quality-screened) |
| Implemented in volatility-ai | **Yes, as a backtest book.** Selectable as `--allocator small_cap_quality` in the portfolio book (`python -m tools.portfolio_book` --data fundamentals=FILE; `research/strategies/allocator_library.py`), which routes every sale through the no-loss guard. Trading it live needs a multi-asset deployment ([engine/roadmap.md](../../engine/roadmap.md) item 1). Unmeasured. Before this change: **Research code** in `research.catalog.factors`: `size_with_quality`; tested on synthetic data, not wired into the engine. RSP (equal-weight S&P 500) is traded and carries a mild size tilt relative to the cap-weighted index, but it is not a small-cap strategy. |
| Related ledger entries | RK11, RK9 |

## In one paragraph

Tilt toward smaller companies. Banz (1981) found small US stocks earned
more than large ones beyond what beta explained; the premium then
weakened for decades after its discovery. Asness and co-authors revived
it by controlling for "junk": small, low-quality firms drag the premium
down, and once quality is held constant a size premium reappears,
stable over time and across markets and not confined to micro-caps.

## The rule

```
market cap ranks (NYSE breakpoints); long the smallest 30% (SMB: minus the largest 30%), within value groups
quality-controlled version: size premium measured after neutralising QMJ (RK11) exposure
retail form: a small-cap index fund, preferably with profitability screens
```

## Evidence

* **Banz (1981):** small stocks have higher average returns than large,
  not accounted for by beta. (As described by Asness et al.)
* **Asness, Frazzini, Israel, Moskowitz & Pedersen (2018), *JFE* 129(3),
  479–509:** the size premium's weaknesses (it disappeared, it is
  concentrated in January and micro-caps, it is not robust) are
  "dismantled" when controlling for quality; the resulting premium is
  stable, robust, consistent across seasons and markets, and not
  concentrated in micro-caps. (Abstract.)

## Against, and failure modes

* Capacity, trading costs and long stretches without a premium (the
  CSV's caveat); the raw premium has been weak since the 1980s.
* Small caps fall harder in recessions and credit stress.

## Fit with volatility-ai

A small-cap ETF fits the instrument rule. It would be a separate
holding; the grid's instruments are large-cap index funds and their
leveraged versions, so a small-cap fund would mainly diversify beta.

## What it would take

Bars for a small-cap ETF (and ideally a quality-screened one) through
`tools/refresh_warehouse.py`, then the rotation or HRP harness. Reference
entry until then.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Banz, R. W. (1981). "The Relationship between Return and Market Value
  of Common Stocks." *Journal of Financial Economics* 9(1), 3–18. As
  described by Asness et al.; citation details from memory.
* Asness, C., Frazzini, A., Israel, R., Moskowitz, T., Pedersen, L. H.
  (2018). "Size Matters, if You Control Your Junk." *Journal of
  Financial Economics* 129(3), 479–509.
  <https://doi.org/10.1016/j.jfineco.2018.05.006>. Abstract.
