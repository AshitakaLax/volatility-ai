# Opening Range Breakout (ORB)

**Ledger ID RK110** · rank 110 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Trend / breakout |
| Potential effectiveness rank | 110 (1 = strongest) |
| AI implementability rank | 131 (1 = easiest) |
| Retail advantage rank | 218 (1 = strongest) |
| Fit with this project | 🧪 reference only |
| Useful for volatility-ai | **Reference only.** A day-trading rule; the index replications are net zero after costs, and the research code and gate form exist (C-M2, N2). |
| Implemented in volatility-ai | **Yes.** Its own strategy id, `rk110_orb`, selectable for backtests: `LibrarySizing` (`research/strategies/library_sizing.py`) with `signal=orb`, component `OpeningRangeGate`. Tune it with `signal_params`. Unmeasured. Before this change: **Research code** `research.catalog.trend_following`: `orb_trade`; `research.strategies.entry_gates`: `BreakdownGate`. |
| Related ledger entries | C-M2, N2, RK70 |

## In one paragraph

Trade the break of the first minutes' high or low. Zarattini, Barbon and
Aziz report large net profits on "stocks in play" (unusually high volume
on news); an independent replication on five index CFDs reproduced the
gross edge and found nothing net. TQQQ is an index product, so the index
result is the relevant one.

## Evidence

* **Zarattini, Barbon & Aziz (2024, Swiss Finance Institute):** a
  5-minute ORB on the top 20 stocks in play earned over 1,600% net with
  a Sharpe ratio of 2.81; the authors' own results. (Abstract.)
* **Independent replication (2026, MQL5 blog):** the ORB on NQ, SPX,
  Dow, DAX and FTSE CFDs, 2015–2026: gross reproduced, net zero. (Title
  and summary.)
* **This repository:** `trend_following.orb_trade` (C-M2) and the
  opening-range gate (N2) are research code.

## Against, and failure modes

* The edge depends on stock-specific news flow; for indices it does not
  survive costs.

## Fit with volatility-ai

A day trade that sells the same session contradicts the grid's per-lot
targets. As a gate (N2) it was researched; no further work is indicated.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Zarattini, C., Barbon, A., Aziz, A. (2024). A Profitable Day Trading
  Strategy For The U.S. Equity Market. Swiss Finance Institute RP 24-98.
  Abstract.
* The opening-range breakout paper, replicated on five indices: gross
  reproduced, net zero. MQL5 blog, 2026. Title and summary.
