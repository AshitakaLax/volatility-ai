# Stochastic-process-based approach to statistical-arbitrage basket construction

**Concept page** · shared by **64** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #906) ·
researched 2026-10-30

| | |
|---|---|
| Task | Statistical-arbitrage basket construction |
| Method | Stochastic-process model (diffusion, jumps, mean reversion) |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Market-neutral baskets need short legs, which the owner's rules exclude; the engine trades one ETF long-only. |
| Implemented in volatility-ai | Johansen baskets and related stat-arb rules are research code (`stat_arb`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK33, RK36, RK89, RK93 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Stochastic Scholarly
Statistical Arbitrage Basket Sys-102") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Score relative mispricing across a basket and build hedged,
market-neutral positions, subject to borrow, liquidity and costs. The
stochastic-process version models the quantity as a diffusion, jump or
mean-reverting process and acts on the fitted parameters. I found no
study of this method on this task.

## The CSV's description

Proposed stochastic-process-based approach to statistical-arbitrage
basket construction: Score relative mispricing across a basket of
securities and construct hedged or market-neutral positions, subject to
borrow, liquidity, and transaction-cost constraints. This is a
concept-level interpretation of the title, not a complete trading
specification: the exact model inputs/target, calibration, entry/exit or
rebalance rules, and position sizing are not fully defined here.

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
* A fitted process is only as good as its specification, and its
  parameters drift between regimes.

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
| 906 | Stochastic Scholarly Statistical Arbitrage Basket Sys-102 | Robust optimization / Distributionally robust CVaR / Index tracking | 1125 | 1868 | No |
| 918 | Stochastic Scholarly Statistical Arbitrage Basket Sys-582 | Robust optimization / Distributionally robust CVaR / Index tracking | 1155 | 1872 | No |
| 930 | Stochastic Scholarly Statistical Arbitrage Basket Sys-1062 | Robust optimization / Distributionally robust CVaR / Index tracking | 1185 | 1876 | No |
| 942 | Stochastic Scholarly Statistical Arbitrage Basket Sys-1542 | Robust optimization / Distributionally robust CVaR / Index tracking | 1215 | 1880 | No |
| 962 | Stochastic Scholarly Statistical Arbitrage Basket Mod-282 | Robust optimization / Distributionally robust CVaR / Index tracking | 1259 | 1890 | No |
| 975 | Stochastic Scholarly Statistical Arbitrage Basket Mod-762 | Robust optimization / Distributionally robust CVaR / Index tracking | 1290 | 1900 | No |
| 988 | Stochastic Scholarly Statistical Arbitrage Basket Mod-1242 | Robust optimization / Distributionally robust CVaR / Index tracking | 1321 | 1910 | No |
| 1001 | Stochastic Scholarly Statistical Arbitrage Basket Mod-1722 | Robust optimization / Distributionally robust CVaR / Index tracking | 1352 | 1920 | No |
| 1014 | Stochastic Scholarly Statistical Arbitrage Basket Mod-2202 | Robust optimization / Distributionally robust CVaR / Index tracking | 1383 | 1930 | No |
| 1027 | Stochastic Scholarly Statistical Arbitrage Basket Mod-2682 | Robust optimization / Distributionally robust CVaR / Index tracking | 1414 | 1940 | No |
| 1040 | Stochastic Scholarly Statistical Arbitrage Basket Mod-3162 | Robust optimization / Distributionally robust CVaR / Index tracking | 1445 | 1950 | No |
| 1053 | Stochastic Scholarly Statistical Arbitrage Basket Mod-3642 | Robust optimization / Distributionally robust CVaR / Index tracking | 1476 | 1960 | No |
| 1229 | Stochastic Scholarly Statistical Arbitrage Basket Sys-294 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1137 | 6606 | No |
| 1246 | Stochastic Scholarly Statistical Arbitrage Basket Sys-774 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1167 | 6642 | No |
| 1263 | Stochastic Scholarly Statistical Arbitrage Basket Sys-1254 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1197 | 6678 | No |
| 1280 | Stochastic Scholarly Statistical Arbitrage Basket Sys-1734 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1227 | 6714 | No |
| 1303 | Stochastic Scholarly Statistical Arbitrage Basket Mod-474 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1274 | 6769 | No |
| 1316 | Stochastic Scholarly Statistical Arbitrage Basket Mod-954 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1305 | 6803 | No |
| 1329 | Stochastic Scholarly Statistical Arbitrage Basket Mod-1434 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1336 | 6837 | No |
| 1342 | Stochastic Scholarly Statistical Arbitrage Basket Mod-1914 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1367 | 6871 | No |
| 1355 | Stochastic Scholarly Statistical Arbitrage Basket Mod-2394 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1398 | 6905 | No |
| 1368 | Stochastic Scholarly Statistical Arbitrage Basket Mod-2874 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1429 | 6939 | No |
| 1381 | Stochastic Scholarly Statistical Arbitrage Basket Mod-3354 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1460 | 6973 | No |
| 1394 | Stochastic Scholarly Statistical Arbitrage Basket Mod-3834 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1491 | 7007 | No |
| 3220 | Stochastic Scholarly Statistical Arbitrage Basket Sys-198 | Attention networks / Transformer encoders / Stock alpha generation | 3252 | 6600 | No |
| 3242 | Stochastic Scholarly Statistical Arbitrage Basket Sys-678 | Attention networks / Transformer encoders / Stock alpha generation | 3276 | 6636 | No |
| 3264 | Stochastic Scholarly Statistical Arbitrage Basket Sys-1158 | Attention networks / Transformer encoders / Stock alpha generation | 3300 | 6672 | No |
| 3286 | Stochastic Scholarly Statistical Arbitrage Basket Sys-1638 | Attention networks / Transformer encoders / Stock alpha generation | 3324 | 6708 | No |
| 3316 | Stochastic Scholarly Statistical Arbitrage Basket Mod-378 | Attention networks / Transformer encoders / Stock alpha generation | 3358 | 6764 | No |
| 3334 | Stochastic Scholarly Statistical Arbitrage Basket Mod-858 | Attention networks / Transformer encoders / Stock alpha generation | 3378 | 6798 | No |
| 3352 | Stochastic Scholarly Statistical Arbitrage Basket Mod-1338 | Attention networks / Transformer encoders / Stock alpha generation | 3398 | 6832 | No |
| 3370 | Stochastic Scholarly Statistical Arbitrage Basket Mod-1818 | Attention networks / Transformer encoders / Stock alpha generation | 3418 | 6866 | No |
| 3388 | Stochastic Scholarly Statistical Arbitrage Basket Mod-2298 | Attention networks / Transformer encoders / Stock alpha generation | 3438 | 6900 | No |
| 3406 | Stochastic Scholarly Statistical Arbitrage Basket Mod-2778 | Attention networks / Transformer encoders / Stock alpha generation | 3458 | 6934 | No |
| 3424 | Stochastic Scholarly Statistical Arbitrage Basket Mod-3258 | Attention networks / Transformer encoders / Stock alpha generation | 3478 | 6968 | No |
| 3442 | Stochastic Scholarly Statistical Arbitrage Basket Mod-3738 | Attention networks / Transformer encoders / Stock alpha generation | 3498 | 7002 | No |
| 6099 | Stochastic Scholarly Statistical Arbitrage Basket MK-32 | Persistence landscapes / Topological data analysis / Equity index | 2042 | 6483 | No |
| 6104 | Stochastic Scholarly Statistical Arbitrage Basket MK-92 | Persistence landscapes / Topological data analysis / Equity index | 2050 | 6487 | No |
| 6282 | Stochastic Scholarly Statistical Arbitrage Basket Sys-6 | Quantum machine learning / Variational circuits / Index prediction | 11337 | 7637 | No |
| 6315 | Stochastic Scholarly Statistical Arbitrage Basket Sys-390 | Neural operators / Deep operator networks / ETF rotation | 5892 | 5650 | No |
| 6323 | Stochastic Scholarly Statistical Arbitrage Basket Sys-486 | Quantum machine learning / Variational circuits / Index prediction | 11363 | 7659 | No |
| 6356 | Stochastic Scholarly Statistical Arbitrage Basket Sys-870 | Neural operators / Deep operator networks / ETF rotation | 5912 | 5667 | No |
| 6364 | Stochastic Scholarly Statistical Arbitrage Basket Sys-966 | Quantum machine learning / Variational circuits / Index prediction | 11389 | 7681 | No |
| 6397 | Stochastic Scholarly Statistical Arbitrage Basket Sys-1350 | Neural operators / Deep operator networks / ETF rotation | 5932 | 5684 | No |
| 6405 | Stochastic Scholarly Statistical Arbitrage Basket Sys-1446 | Quantum machine learning / Variational circuits / Index prediction | 11415 | 7703 | No |
| 6438 | Stochastic Scholarly Statistical Arbitrage Basket Sys-1830 | Neural operators / Deep operator networks / ETF rotation | 5952 | 5701 | No |
| 6446 | Stochastic Scholarly Statistical Arbitrage Basket Sys-1926 | Quantum machine learning / Variational circuits / Index prediction | 11441 | 7725 | No |
| 6462 | Stochastic Scholarly Statistical Arbitrage Basket Mod-90 | Neural operators / Deep operator networks / ETF rotation | 5965 | 5708 | No |
| 6470 | Stochastic Scholarly Statistical Arbitrage Basket Mod-186 | Quantum machine learning / Variational circuits / Index prediction | 11458 | 7740 | No |
| 6507 | Stochastic Scholarly Statistical Arbitrage Basket Mod-570 | Neural operators / Deep operator networks / ETF rotation | 5989 | 5721 | No |
| 6515 | Stochastic Scholarly Statistical Arbitrage Basket Mod-666 | Quantum machine learning / Variational circuits / Index prediction | 11485 | 7770 | No |
| 6552 | Stochastic Scholarly Statistical Arbitrage Basket Mod-1050 | Neural operators / Deep operator networks / ETF rotation | 6013 | 5734 | No |
| 6560 | Stochastic Scholarly Statistical Arbitrage Basket Mod-1146 | Quantum machine learning / Variational circuits / Index prediction | 11512 | 7800 | No |
| 6597 | Stochastic Scholarly Statistical Arbitrage Basket Mod-1530 | Neural operators / Deep operator networks / ETF rotation | 6037 | 5747 | No |
| 6605 | Stochastic Scholarly Statistical Arbitrage Basket Mod-1626 | Quantum machine learning / Variational circuits / Index prediction | 11539 | 7830 | No |
| 6642 | Stochastic Scholarly Statistical Arbitrage Basket Mod-2010 | Neural operators / Deep operator networks / ETF rotation | 6061 | 5760 | No |
| 6650 | Stochastic Scholarly Statistical Arbitrage Basket Mod-2106 | Quantum machine learning / Variational circuits / Index prediction | 11566 | 7860 | No |
| 6687 | Stochastic Scholarly Statistical Arbitrage Basket Mod-2490 | Neural operators / Deep operator networks / ETF rotation | 6085 | 5773 | No |
| 6695 | Stochastic Scholarly Statistical Arbitrage Basket Mod-2586 | Quantum machine learning / Variational circuits / Index prediction | 11593 | 7890 | No |
| 6732 | Stochastic Scholarly Statistical Arbitrage Basket Mod-2970 | Neural operators / Deep operator networks / ETF rotation | 6109 | 5786 | No |
| 6740 | Stochastic Scholarly Statistical Arbitrage Basket Mod-3066 | Quantum machine learning / Variational circuits / Index prediction | 11620 | 7920 | No |
| 6777 | Stochastic Scholarly Statistical Arbitrage Basket Mod-3450 | Neural operators / Deep operator networks / ETF rotation | 6133 | 5799 | No |
| 6785 | Stochastic Scholarly Statistical Arbitrage Basket Mod-3546 | Quantum machine learning / Variational circuits / Index prediction | 11647 | 7950 | No |
| 6822 | Stochastic Scholarly Statistical Arbitrage Basket Mod-3930 | Neural operators / Deep operator networks / ETF rotation | 6157 | 5812 | No |
