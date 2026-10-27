# Market-Neutral Residual Mean Reversion

**Ledger ID RK33** · rank 33 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Statistical arbitrage |
| Potential effectiveness rank | 33 (1 = strongest) |
| AI implementability rank | 53 (1 = easiest) |
| Retail advantage rank | 129 (1 = strongest) |
| Fit with this project | ⛔ (market-neutral, short leg) · 🧪 the long-only s-score (C-MR2) |
| Implemented in volatility-ai | **Research code.** Avellaneda–Lee's ETF-residual s-score, `mean_reversion.s_score` and `s_score_long_signal` (ledger C-MR2); the short leg is dropped. |
| Related ledger entries | C-MR2, C-MR4, RK75, RK76, RK96 |

## In one paragraph

Regress each stock's returns on market, sector or statistical factors;
treat the cumulative residual as a mean-reverting process; buy stocks
whose residual is unusually low and short those unusually high, hedged
to be factor-neutral. Avellaneda and Lee's version reached a Sharpe
ratio of 1.44 after costs over 1997–2007 with PCA factors, but only 0.9
over 2003–2007, and it lost in the August 2007 quant unwind. It is a
stock book with a short leg; the long-only half is built here as
research code.

## The rule

```
residual_t = r_stock - beta x r_factor (rolling 60-day regression)
fit X = cumsum(residual) as Ornstein-Uhlenbeck: dX = kappa (m - X) dt + sigma dW
s = (X - m) / sigma_eq
open long s < -1.25, close long s > -0.50; open short s > 1.25, close short s < 0.75
```

## Evidence

* **Avellaneda & Lee (2010), "Statistical arbitrage in the US equities
  market," *Quantitative Finance* 10(7), 761–782:** PCA-factor
  strategies, Sharpe 1.44 after costs over 1997–2007 and 0.9 over
  2003–2007; sector-ETF factors 1.1 over 1997–2007 with similar
  degradation; adding volume lifted ETF signals to 1.51 over 2003–2007;
  August 2007 consistent with Khandani and Lo's unwind explanation.
  (Abstract.)
* **Krauss (2017), *Journal of Economic Surveys* 31(2), 513–545:**
  survey of pairs and residual stat arb. (Abstract.)

## Against, and failure modes

* Factor misspecification turns "residual alpha" into hidden factor
  exposure (the CSV's caveat); crowding and deleveraging (August 2007).
* Returns decayed through the 2000s; borrow and turnover costs dominate.

## Fit with volatility-ai

The long-only form buys single stocks that fell against their sector
ETF; it is net long and picks stocks, not this book. It stays research
code.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Avellaneda, M., Lee, J.-H. (2010). "Statistical arbitrage in the US
  equities market." *Quantitative Finance* 10(7), 761–782.
  <https://ideas.repec.org/a/taf/quantf/v10y2010i7p761-782.html>.
  Abstract; thresholds as transcribed in ledger C-MR2.
* Krauss, C. (2017). "Statistical arbitrage pairs trading strategies:
  review and outlook." *Journal of Economic Surveys* 31(2), 513–545.
  Abstract.
* This repository: `research/strategies/mean_reversion.py`, ledger C-MR2.
