# Cross-Sectional Reversal with Risk Neutralization

**Ledger ID RK215** · rank 215 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Equity / short-horizon reversal |
| Potential effectiveness rank | 215 (1 = strongest) |
| AI implementability rank | 103 (1 = easiest) |
| Retail advantage rank | 97 (1 = strongest) |
| Fit with this project | 🧪 long-only contrarian weights (C-MR1) · ⛔ market-neutral |
| Implemented in volatility-ai | **Yes, as a backtest book.** `research/strategies/allocators.py` `risk_neutral_reversal`, run by the portfolio book (`python -m tools.portfolio_book --allocator risk_neutral_reversal`), which routes every sale through the no-loss guard. Trading it live needs a multi-asset deployment ([engine/roadmap.md](../../engine/roadmap.md) item 1). Unmeasured. Before this change: **Partial.** Contrarian weights and decayed reversal scores (`mean_reversion.contrarian_weights`, `decayed_reversal_scores`, C-MR1), without factor neutralisation. |
| Related ledger entries | C-MR1, RK33, RK76 |

## In one paragraph

Buy last week's or last month's losers and sell the winners after
removing market, industry and liquidity exposure. The raw one-month
reversal is a classic (Jegadeesh 1990; Lehmann 1990); stripping out the
parts of returns explained by industry moves and cash-flow news makes it
much stronger. One study's residual reversal earns about four times the
standard strategy's risk-adjusted return. Reversal profits behave like
pay for providing liquidity, higher when volatility is high (Nagel 2012,
C-MR1).

## The rule

```text
r_resid = r_i,(t-1) - beta' x factors (market, industry) - expected cash-flow news (analyst revisions)
long the lowest residual decile, short the highest; rebalance weekly or monthly
```

## Evidence

* **Da, Liu & Schaumburg (2014), "A Closer Look at the Short-Term Return
  Reversal," *Management Science* 60(3), 658–674:** returns not
  explained by fundamentals reverse more; the enhanced strategy earns
  about four times the standard one's risk-adjusted return; long-side
  profits are tied to liquidity shocks, short-side to sentiment.
  (Abstract.)
* **Nagel (2012), "Evaporating Liquidity," *Review of Financial
  Studies*:** reversal returns as liquidity provision, rising with the
  VIX. (See ledger C-MR1.)
* **Jegadeesh (1990); Lehmann (1990):** the short-horizon reversal.
  (Standard references; not re-checked here.)

## Against, and failure modes

* Turnover and costs; much of the gross profit sits in illiquid names
  and the short leg.
* Overwhelmed by informed momentum when news drives the move (the CSV's
  caveat).

## Fit with volatility-ai

The grid is itself a single-asset short-horizon reversal bet. The
cross-sectional, risk-neutralised version needs a stock universe and
factor data, and its long-only half would be a separate stock book.
Research code for the contrarian weights exists.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Da, Z., Liu, Q., Schaumburg, E. (2014). *Management Science* 60(3),
  658–674.
  <https://econpapers.repec.org/RePEc:inm:ormnsc:v:60:y:2014:i:3:p:658-674>.
  Abstract.
* Nagel, S. (2012). "Evaporating Liquidity." *Review of Financial
  Studies* 25(7). See C-MR1.
* Jegadeesh, N. (1990), *Journal of Finance* 45(3); Lehmann, B. N.
  (1990), *Quarterly Journal of Economics* 105(1). Not re-checked.
* This repository: `research/strategies/mean_reversion.py`
  (`contrarian_weights`, `decayed_reversal_scores`), ledger C-MR1.
