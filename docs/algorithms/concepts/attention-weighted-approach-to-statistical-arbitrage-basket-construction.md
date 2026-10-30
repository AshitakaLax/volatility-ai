# Attention-weighted approach to statistical-arbitrage basket construction

**Concept page** · shared by **7** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #848) ·
researched 2026-10-30

| | |
|---|---|
| Task | Statistical-arbitrage basket construction |
| Method | Attention networks |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Market-neutral baskets need short legs, which the owner's rules exclude; the engine trades one ETF long-only. |
| Implemented in volatility-ai | Johansen baskets and related stat-arb rules are research code (`stat_arb`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK33, RK36, RK89, RK93 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Attentional Scholarly
Statistical Arbitrage Basket Alpha-2") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Score relative mispricing across a basket and build hedged,
market-neutral positions, subject to borrow, liquidity and costs. The
attention version weights its inputs with a learned attention network. I
found no study of this method on this task.

## The CSV's description

Proposed attention-weighted approach to statistical-arbitrage basket
construction: Score relative mispricing across a basket of securities
and construct hedged or market-neutral positions, subject to borrow,
liquidity, and transaction-cost constraints. This is a concept-level
interpretation of the title, not a complete trading specification: the
exact model inputs/target, calibration, entry/exit or rebalance rules,
and position sizing are not fully defined here.

## Evidence

* **Avellaneda & Lee (2010), "Statistical arbitrage in the US equities
  market," *Quantitative Finance* 10(7):** mean-reversion trading of
  stock residuals against PCA factors or sector ETFs, hedged long-short
  (see RK33). (Abstract.)
* **Krauss, Do & Huck (2017), *European Journal of Operational Research*
  259(2), 689–702:** an ensemble of deep nets, boosted trees and random
  forests traded S&P 500 stocks long-short at over 0.45% a day before
  costs, with returns declining in recent years. (Abstract.)

## Against, and failure modes

* Stat-arb returns have declined as the trade crowded (Krauss et al.
  2017).
* Hedged baskets need short legs, borrow and many names.
* Attention networks need far more data than daily bars of a few ETFs
  provide.

## Fit with volatility-ai

Hedged, market-neutral baskets need short legs; the owner's rules are
long-only and the engine trades one leveraged ETF. Out of scope as a
strategy.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Avellaneda, M., Lee, J.-H. (2010). *Quantitative Finance* 10(7).
  Abstract.
* Krauss, C., Do, X. A., Huck, N. (2017). *European Journal of
  Operational Research* 259(2), 689–702. Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 848 | Attentional Scholarly Statistical Arbitrage Basket Alpha-2 | Robust statistics / Mean-CVaR / Index tracking | 4599 | 6498 | No |
| 855 | Attentional Scholarly Statistical Arbitrage Basket Alpha-102 | Robust statistics / Mean-CVaR / Index tracking | 1010 | 1828 | No |
| 862 | Attentional Scholarly Statistical Arbitrage Basket Alpha-202 | Robust statistics / Mean-CVaR / Index tracking | 8202 | 11290 | No |
| 869 | Attentional Scholarly Statistical Arbitrage Basket Alpha-302 | Robust statistics / Mean-CVaR / Index tracking | 4627 | 6517 | No |
| 876 | Attentional Scholarly Statistical Arbitrage Basket Alpha-402 | Robust statistics / Mean-CVaR / Index tracking | 1039 | 1839 | No |
| 6098 | Attention-Weighted Scholarly Statistical Arbitrage Basket MK-17 | Wavelets / Fractional cointegration / Statistical arbitrage stocks | 9258 | 6482 | No |
| 6103 | Attention-Weighted Scholarly Statistical Arbitrage Basket MK-77 | Wavelets / Fractional cointegration / Statistical arbitrage stocks | 9261 | 6486 | No |
