# Betting Against Beta (BAB)

**Ledger ID RK49** · rank 49 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Factor / systematic equity |
| Potential effectiveness rank | 49 (1 = strongest) |
| AI implementability rank | 90 (1 = easiest) |
| Retail advantage rank | 233 (1 = strongest) |
| Fit with this project | ⛔ (shorting and leverage are the strategy) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK18 |

## In one paragraph

Buy low-beta assets levered up to a beta of one and short high-beta
assets levered down to one, so the portfolio is market-neutral and earns
the gap. Frazzini and Pedersen's theory: investors who cannot borrow buy
high-beta assets to get exposure, bidding them up and leaving low-beta
assets with higher risk-adjusted returns, in US and international
stocks, bonds and futures. Its strongest critique says the published
construction effectively equal-weights stocks, piles into micro-caps and
loses most of its edge to trading costs. Both the short and the leverage
are out of scope here.

## The rule

```
beta_i = correlation(i, market) [5y, daily 3-day returns] x vol_i / vol_market [1y]   # FP's shrunk estimate
rank by beta; low-beta leg and high-beta leg weighted by rank
scale each leg to beta 1: long w_L / beta_L, short w_H / beta_H; rebalance monthly
```

## Evidence

* **Frazzini & Pedersen (2014), *JFE* 111(1), 1–25:** constrained
  investors bid up high-beta assets, lowering their alpha, in US
  equities, 20 international markets, Treasuries, corporate bonds and
  futures; the BAB factor earns significant risk-adjusted returns, and
  does badly when funding constraints tighten. (Abstract.)

## Against, and failure modes

* **Novy-Marx & Velikov (*JFE*, 2022), "Betting Against Betting Against
  Beta":** the construction effectively equal-weights returns, putting
  about $1.05 per dollar in the bottom 1% of stocks by market cap;
  trading costs cut profitability by more than half; the betas are
  predictable from market volatility, hence biased; the costed returns
  that remain come from profitability and investment tilts.
  (Working-paper abstract and summaries.)
* **Funding squeezes** are exactly when it fails (its own prediction).

## Fit with volatility-ai

Out of scope: a short leg and leverage of the low-beta leg are the
strategy. Its long-only shadow is low-volatility equity (RK18), and its
idea, leverage-constrained investors overpay for beta, is a reason to
be careful about owning the highest-beta instruments: TQQQ is one.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Frazzini, A., Pedersen, L. H. (2014). "Betting Against Beta." *Journal
  of Financial Economics* 111(1), 1–25.
  <https://econpapers.repec.org/RePEc:eee:jfinec:v:111:y:2014:i:1:p:1-25>.
  Abstract. The beta-estimation detail in the rule is from the paper as I
  recall it, not re-checked.
* Novy-Marx, R., Velikov, M. (2022). "Betting Against Betting Against
  Beta." *Journal of Financial Economics*.
  <https://mysimon.rochester.edu/novy-marx/research/BABAB.pdf>.
  Working-paper abstract and summaries.
