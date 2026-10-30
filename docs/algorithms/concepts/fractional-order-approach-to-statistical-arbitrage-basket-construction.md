# Fractional-order approach to statistical-arbitrage basket construction

**Concept page** · shared by **63** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,546) ·
researched 2026-10-30

| | |
|---|---|
| Task | Statistical-arbitrage basket construction |
| Method | Fractional-order models (long memory, fractional calculus) |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Market-neutral baskets need short legs, which the owner's rules exclude; the engine trades one ETF long-only. |
| Implemented in volatility-ai | Johansen baskets and related stat-arb rules are research code (`stat_arb`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK33, RK36, RK89, RK93 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Fractional Scholarly
Statistical Arbitrage Basket Sys-462") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Score relative mispricing across a basket and build hedged,
market-neutral positions, subject to borrow, liquidity and costs. The
fractional-order version models long memory with fractional differencing
or fractional-order dynamics. I found no study of this method on this
task.

## The CSV's description

Proposed fractional-order approach to statistical-arbitrage basket
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
* Long memory in returns is weak once short-range dependence is allowed
  for (Lo 1991); in volatility, the simpler HAR model reproduces it
  (Corsi 2009).

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
| 1546 | Fractional Scholarly Statistical Arbitrage Basket Sys-462 | Robust optimization / Distributionally robust CVaR / Index tracking | 1147 | 1871 | No |
| 1548 | Fractional Scholarly Statistical Arbitrage Basket Sys-942 | Robust optimization / Distributionally robust CVaR / Index tracking | 1177 | 1875 | No |
| 1550 | Fractional Scholarly Statistical Arbitrage Basket Sys-1422 | Robust optimization / Distributionally robust CVaR / Index tracking | 1207 | 1879 | No |
| 1552 | Fractional Scholarly Statistical Arbitrage Basket Sys-1902 | Robust optimization / Distributionally robust CVaR / Index tracking | 1237 | 1883 | No |
| 1553 | Fractional Scholarly Statistical Arbitrage Basket Mod-402 | Robust optimization / Distributionally robust CVaR / Index tracking | 1267 | 1892 | No |
| 1554 | Fractional Scholarly Statistical Arbitrage Basket Mod-882 | Robust optimization / Distributionally robust CVaR / Index tracking | 1298 | 1902 | No |
| 1555 | Fractional Scholarly Statistical Arbitrage Basket Mod-1362 | Robust optimization / Distributionally robust CVaR / Index tracking | 1329 | 1912 | No |
| 1556 | Fractional Scholarly Statistical Arbitrage Basket Mod-1842 | Robust optimization / Distributionally robust CVaR / Index tracking | 1360 | 1922 | No |
| 1557 | Fractional Scholarly Statistical Arbitrage Basket Mod-2322 | Robust optimization / Distributionally robust CVaR / Index tracking | 1391 | 1932 | No |
| 1558 | Fractional Scholarly Statistical Arbitrage Basket Mod-2802 | Robust optimization / Distributionally robust CVaR / Index tracking | 1422 | 1942 | No |
| 1559 | Fractional Scholarly Statistical Arbitrage Basket Mod-3282 | Robust optimization / Distributionally robust CVaR / Index tracking | 1453 | 1952 | No |
| 1560 | Fractional Scholarly Statistical Arbitrage Basket Mod-3762 | Robust optimization / Distributionally robust CVaR / Index tracking | 1484 | 1962 | No |
| 1855 | Fractional Scholarly Statistical Arbitrage Basket Sys-174 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1130 | 6597 | No |
| 1904 | Fractional Scholarly Statistical Arbitrage Basket Sys-654 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1160 | 6633 | No |
| 1953 | Fractional Scholarly Statistical Arbitrage Basket Sys-1134 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1190 | 6669 | No |
| 2002 | Fractional Scholarly Statistical Arbitrage Basket Sys-1614 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1220 | 6705 | No |
| 2051 | Fractional Scholarly Statistical Arbitrage Basket Mod-114 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1250 | 6743 | No |
| 2104 | Fractional Scholarly Statistical Arbitrage Basket Mod-594 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1281 | 6777 | No |
| 2157 | Fractional Scholarly Statistical Arbitrage Basket Mod-1074 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1312 | 6811 | No |
| 2210 | Fractional Scholarly Statistical Arbitrage Basket Mod-1554 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1343 | 6845 | No |
| 2263 | Fractional Scholarly Statistical Arbitrage Basket Mod-2034 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1374 | 6879 | No |
| 2316 | Fractional Scholarly Statistical Arbitrage Basket Mod-2514 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1405 | 6913 | No |
| 2369 | Fractional Scholarly Statistical Arbitrage Basket Mod-2994 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1436 | 6947 | No |
| 2422 | Fractional Scholarly Statistical Arbitrage Basket Mod-3474 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1467 | 6981 | No |
| 2475 | Fractional Scholarly Statistical Arbitrage Basket Mod-3954 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1498 | 7015 | No |
| 6289 | Fractional Scholarly Statistical Arbitrage Basket Sys-78 | Attention networks / Transformer encoders / Stock alpha generation | 3246 | 6591 | No |
| 6304 | Fractional Scholarly Statistical Arbitrage Basket Sys-270 | Neural operators / Deep operator networks / ETF rotation | 5887 | 5646 | No |
| 6312 | Fractional Scholarly Statistical Arbitrage Basket Sys-366 | Quantum machine learning / Variational circuits / Index prediction | 11356 | 7654 | No |
| 6330 | Fractional Scholarly Statistical Arbitrage Basket Sys-558 | Attention networks / Transformer encoders / Stock alpha generation | 3270 | 6627 | No |
| 6345 | Fractional Scholarly Statistical Arbitrage Basket Sys-750 | Neural operators / Deep operator networks / ETF rotation | 5907 | 5663 | No |
| 6353 | Fractional Scholarly Statistical Arbitrage Basket Sys-846 | Quantum machine learning / Variational circuits / Index prediction | 11382 | 7676 | No |
| 6371 | Fractional Scholarly Statistical Arbitrage Basket Sys-1038 | Attention networks / Transformer encoders / Stock alpha generation | 3294 | 6663 | No |
| 6386 | Fractional Scholarly Statistical Arbitrage Basket Sys-1230 | Neural operators / Deep operator networks / ETF rotation | 5927 | 5680 | No |
| 6394 | Fractional Scholarly Statistical Arbitrage Basket Sys-1326 | Quantum machine learning / Variational circuits / Index prediction | 11408 | 7698 | No |
| 6412 | Fractional Scholarly Statistical Arbitrage Basket Sys-1518 | Attention networks / Transformer encoders / Stock alpha generation | 3318 | 6699 | No |
| 6427 | Fractional Scholarly Statistical Arbitrage Basket Sys-1710 | Neural operators / Deep operator networks / ETF rotation | 5947 | 5697 | No |
| 6435 | Fractional Scholarly Statistical Arbitrage Basket Sys-1806 | Quantum machine learning / Variational circuits / Index prediction | 11434 | 7720 | No |
| 6453 | Fractional Scholarly Statistical Arbitrage Basket Sys-1998 | Attention networks / Transformer encoders / Stock alpha generation | 3342 | 6735 | No |
| 6455 | Fractional Scholarly Statistical Arbitrage Basket Mod-18 | Attention networks / Transformer encoders / Stock alpha generation | 3343 | 6739 | No |
| 6472 | Fractional Scholarly Statistical Arbitrage Basket Mod-210 | Neural operators / Deep operator networks / ETF rotation | 5970 | 5712 | No |
| 6483 | Fractional Scholarly Statistical Arbitrage Basket Mod-306 | Quantum machine learning / Variational circuits / Index prediction | 11464 | 7748 | No |
| 6500 | Fractional Scholarly Statistical Arbitrage Basket Mod-498 | Attention networks / Transformer encoders / Stock alpha generation | 3363 | 6773 | No |
| 6517 | Fractional Scholarly Statistical Arbitrage Basket Mod-690 | Neural operators / Deep operator networks / ETF rotation | 5994 | 5725 | No |
| 6528 | Fractional Scholarly Statistical Arbitrage Basket Mod-786 | Quantum machine learning / Variational circuits / Index prediction | 11491 | 7778 | No |
| 6545 | Fractional Scholarly Statistical Arbitrage Basket Mod-978 | Attention networks / Transformer encoders / Stock alpha generation | 3383 | 6807 | No |
| 6562 | Fractional Scholarly Statistical Arbitrage Basket Mod-1170 | Neural operators / Deep operator networks / ETF rotation | 6018 | 5738 | No |
| 6573 | Fractional Scholarly Statistical Arbitrage Basket Mod-1266 | Quantum machine learning / Variational circuits / Index prediction | 11518 | 7808 | No |
| 6590 | Fractional Scholarly Statistical Arbitrage Basket Mod-1458 | Attention networks / Transformer encoders / Stock alpha generation | 3403 | 6841 | No |
| 6607 | Fractional Scholarly Statistical Arbitrage Basket Mod-1650 | Neural operators / Deep operator networks / ETF rotation | 6042 | 5751 | No |
| 6618 | Fractional Scholarly Statistical Arbitrage Basket Mod-1746 | Quantum machine learning / Variational circuits / Index prediction | 11545 | 7838 | No |
| 6635 | Fractional Scholarly Statistical Arbitrage Basket Mod-1938 | Attention networks / Transformer encoders / Stock alpha generation | 3423 | 6875 | No |
| 6652 | Fractional Scholarly Statistical Arbitrage Basket Mod-2130 | Neural operators / Deep operator networks / ETF rotation | 6066 | 5764 | No |
| 6663 | Fractional Scholarly Statistical Arbitrage Basket Mod-2226 | Quantum machine learning / Variational circuits / Index prediction | 11572 | 7868 | No |
| 6680 | Fractional Scholarly Statistical Arbitrage Basket Mod-2418 | Attention networks / Transformer encoders / Stock alpha generation | 3443 | 6909 | No |
| 6697 | Fractional Scholarly Statistical Arbitrage Basket Mod-2610 | Neural operators / Deep operator networks / ETF rotation | 6090 | 5777 | No |
| 6708 | Fractional Scholarly Statistical Arbitrage Basket Mod-2706 | Quantum machine learning / Variational circuits / Index prediction | 11599 | 7898 | No |
| 6725 | Fractional Scholarly Statistical Arbitrage Basket Mod-2898 | Attention networks / Transformer encoders / Stock alpha generation | 3463 | 6943 | No |
| 6742 | Fractional Scholarly Statistical Arbitrage Basket Mod-3090 | Neural operators / Deep operator networks / ETF rotation | 6114 | 5790 | No |
| 6753 | Fractional Scholarly Statistical Arbitrage Basket Mod-3186 | Quantum machine learning / Variational circuits / Index prediction | 11626 | 7928 | No |
| 6770 | Fractional Scholarly Statistical Arbitrage Basket Mod-3378 | Attention networks / Transformer encoders / Stock alpha generation | 3483 | 6977 | No |
| 6787 | Fractional Scholarly Statistical Arbitrage Basket Mod-3570 | Neural operators / Deep operator networks / ETF rotation | 6138 | 5803 | No |
| 6798 | Fractional Scholarly Statistical Arbitrage Basket Mod-3666 | Quantum machine learning / Variational circuits / Index prediction | 11653 | 7958 | No |
| 6815 | Fractional Scholarly Statistical Arbitrage Basket Mod-3858 | Attention networks / Transformer encoders / Stock alpha generation | 3503 | 7011 | No |
