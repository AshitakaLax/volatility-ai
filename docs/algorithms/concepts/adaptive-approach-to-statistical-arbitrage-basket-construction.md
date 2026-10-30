# Adaptive approach to statistical-arbitrage basket construction

**Concept page** · shared by **64** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #910) ·
researched 2026-10-30

| | |
|---|---|
| Task | Statistical-arbitrage basket construction |
| Method | Adaptive (time-varying parameters or thresholds) |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Market-neutral baskets need short legs, which the owner's rules exclude; the engine trades one ETF long-only. |
| Implemented in volatility-ai | Johansen baskets and related stat-arb rules are research code (`stat_arb`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK33, RK36, RK89, RK93 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Adaptive Scholarly
Statistical Arbitrage Basket Sys-222") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Score relative mispricing across a basket and build hedged,
market-neutral positions, subject to borrow, liquidity and costs. The
adaptive version lets its parameters or thresholds move with recent
data. I found no study of this method on this task.

## The CSV's description

Proposed adaptive approach to statistical-arbitrage basket construction:
Score relative mispricing across a basket of securities and construct
hedged or market-neutral positions, subject to borrow, liquidity, and
transaction-cost constraints. This is a concept-level interpretation of
the title, not a complete trading specification: the exact model
inputs/target, calibration, entry/exit or rebalance rules, and position
sizing are not fully defined here.

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
* Parameters re-fitted often chase the recent past unless the adaptation
  itself is tested out of sample.

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
| 910 | Adaptive Scholarly Statistical Arbitrage Basket Sys-222 | Robust optimization / Distributionally robust CVaR / Index tracking | 1132 | 1869 | No |
| 922 | Adaptive Scholarly Statistical Arbitrage Basket Sys-702 | Robust optimization / Distributionally robust CVaR / Index tracking | 1162 | 1873 | No |
| 934 | Adaptive Scholarly Statistical Arbitrage Basket Sys-1182 | Robust optimization / Distributionally robust CVaR / Index tracking | 1192 | 1877 | No |
| 946 | Adaptive Scholarly Statistical Arbitrage Basket Sys-1662 | Robust optimization / Distributionally robust CVaR / Index tracking | 1222 | 1881 | No |
| 959 | Adaptive Scholarly Statistical Arbitrage Basket Mod-162 | Robust optimization / Distributionally robust CVaR / Index tracking | 1252 | 1887 | No |
| 972 | Adaptive Scholarly Statistical Arbitrage Basket Mod-642 | Robust optimization / Distributionally robust CVaR / Index tracking | 1283 | 1897 | No |
| 985 | Adaptive Scholarly Statistical Arbitrage Basket Mod-1122 | Robust optimization / Distributionally robust CVaR / Index tracking | 1314 | 1907 | No |
| 998 | Adaptive Scholarly Statistical Arbitrage Basket Mod-1602 | Robust optimization / Distributionally robust CVaR / Index tracking | 1345 | 1917 | No |
| 1011 | Adaptive Scholarly Statistical Arbitrage Basket Mod-2082 | Robust optimization / Distributionally robust CVaR / Index tracking | 1376 | 1927 | No |
| 1024 | Adaptive Scholarly Statistical Arbitrage Basket Mod-2562 | Robust optimization / Distributionally robust CVaR / Index tracking | 1407 | 1937 | No |
| 1037 | Adaptive Scholarly Statistical Arbitrage Basket Mod-3042 | Robust optimization / Distributionally robust CVaR / Index tracking | 1438 | 1947 | No |
| 1050 | Adaptive Scholarly Statistical Arbitrage Basket Mod-3522 | Robust optimization / Distributionally robust CVaR / Index tracking | 1469 | 1957 | No |
| 1234 | Adaptive Scholarly Statistical Arbitrage Basket Sys-414 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1145 | 6615 | No |
| 1251 | Adaptive Scholarly Statistical Arbitrage Basket Sys-894 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1175 | 6651 | No |
| 1268 | Adaptive Scholarly Statistical Arbitrage Basket Sys-1374 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1205 | 6687 | No |
| 1285 | Adaptive Scholarly Statistical Arbitrage Basket Sys-1854 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1235 | 6723 | No |
| 1300 | Adaptive Scholarly Statistical Arbitrage Basket Mod-354 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1265 | 6760 | No |
| 1313 | Adaptive Scholarly Statistical Arbitrage Basket Mod-834 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1296 | 6794 | No |
| 1326 | Adaptive Scholarly Statistical Arbitrage Basket Mod-1314 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1327 | 6828 | No |
| 1339 | Adaptive Scholarly Statistical Arbitrage Basket Mod-1794 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1358 | 6862 | No |
| 1352 | Adaptive Scholarly Statistical Arbitrage Basket Mod-2274 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1389 | 6896 | No |
| 1365 | Adaptive Scholarly Statistical Arbitrage Basket Mod-2754 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1420 | 6930 | No |
| 1378 | Adaptive Scholarly Statistical Arbitrage Basket Mod-3234 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1451 | 6964 | No |
| 1391 | Adaptive Scholarly Statistical Arbitrage Basket Mod-3714 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1482 | 6998 | No |
| 3226 | Adaptive Scholarly Statistical Arbitrage Basket Sys-318 | Attention networks / Transformer encoders / Stock alpha generation | 3258 | 6609 | No |
| 3248 | Adaptive Scholarly Statistical Arbitrage Basket Sys-798 | Attention networks / Transformer encoders / Stock alpha generation | 3282 | 6645 | No |
| 3270 | Adaptive Scholarly Statistical Arbitrage Basket Sys-1278 | Attention networks / Transformer encoders / Stock alpha generation | 3306 | 6681 | No |
| 3292 | Adaptive Scholarly Statistical Arbitrage Basket Sys-1758 | Attention networks / Transformer encoders / Stock alpha generation | 3330 | 6717 | No |
| 3312 | Adaptive Scholarly Statistical Arbitrage Basket Mod-258 | Attention networks / Transformer encoders / Stock alpha generation | 3353 | 6755 | No |
| 3330 | Adaptive Scholarly Statistical Arbitrage Basket Mod-738 | Attention networks / Transformer encoders / Stock alpha generation | 3373 | 6789 | No |
| 3348 | Adaptive Scholarly Statistical Arbitrage Basket Mod-1218 | Attention networks / Transformer encoders / Stock alpha generation | 3393 | 6823 | No |
| 3366 | Adaptive Scholarly Statistical Arbitrage Basket Mod-1698 | Attention networks / Transformer encoders / Stock alpha generation | 3413 | 6857 | No |
| 3384 | Adaptive Scholarly Statistical Arbitrage Basket Mod-2178 | Attention networks / Transformer encoders / Stock alpha generation | 3433 | 6891 | No |
| 3402 | Adaptive Scholarly Statistical Arbitrage Basket Mod-2658 | Attention networks / Transformer encoders / Stock alpha generation | 3453 | 6925 | No |
| 3420 | Adaptive Scholarly Statistical Arbitrage Basket Mod-3138 | Attention networks / Transformer encoders / Stock alpha generation | 3473 | 6959 | No |
| 3438 | Adaptive Scholarly Statistical Arbitrage Basket Mod-3618 | Attention networks / Transformer encoders / Stock alpha generation | 3493 | 6993 | No |
| 6109 | Adaptive Scholarly Statistical Arbitrage Basket Ver-31 | Delay differential equations / Jump diffusion / Stock trading | 3823 | 1817 | No |
| 6124 | Adaptive Scholarly Statistical Arbitrage Basket Ver-131 | Delay differential equations / Jump diffusion / Stock trading | 13172 | 13141 | No |
| 6285 | Adaptive Scholarly Statistical Arbitrage Basket Sys-30 | Neural operators / Deep operator networks / ETF rotation | 5878 | 5637 | No |
| 6292 | Adaptive Scholarly Statistical Arbitrage Basket Sys-126 | Quantum machine learning / Variational circuits / Index prediction | 11344 | 7643 | No |
| 6326 | Adaptive Scholarly Statistical Arbitrage Basket Sys-510 | Neural operators / Deep operator networks / ETF rotation | 5898 | 5654 | No |
| 6333 | Adaptive Scholarly Statistical Arbitrage Basket Sys-606 | Quantum machine learning / Variational circuits / Index prediction | 11370 | 7665 | No |
| 6367 | Adaptive Scholarly Statistical Arbitrage Basket Sys-990 | Neural operators / Deep operator networks / ETF rotation | 5918 | 5671 | No |
| 6374 | Adaptive Scholarly Statistical Arbitrage Basket Sys-1086 | Quantum machine learning / Variational circuits / Index prediction | 11396 | 7687 | No |
| 6408 | Adaptive Scholarly Statistical Arbitrage Basket Sys-1470 | Neural operators / Deep operator networks / ETF rotation | 5938 | 5688 | No |
| 6415 | Adaptive Scholarly Statistical Arbitrage Basket Sys-1566 | Quantum machine learning / Variational circuits / Index prediction | 11422 | 7709 | No |
| 6449 | Adaptive Scholarly Statistical Arbitrage Basket Sys-1950 | Neural operators / Deep operator networks / ETF rotation | 5958 | 5705 | No |
| 6460 | Adaptive Scholarly Statistical Arbitrage Basket Mod-66 | Quantum machine learning / Variational circuits / Index prediction | 11450 | 7732 | No |
| 6496 | Adaptive Scholarly Statistical Arbitrage Basket Mod-450 | Neural operators / Deep operator networks / ETF rotation | 5982 | 5718 | No |
| 6505 | Adaptive Scholarly Statistical Arbitrage Basket Mod-546 | Quantum machine learning / Variational circuits / Index prediction | 11477 | 7762 | No |
| 6541 | Adaptive Scholarly Statistical Arbitrage Basket Mod-930 | Neural operators / Deep operator networks / ETF rotation | 6006 | 5731 | No |
| 6550 | Adaptive Scholarly Statistical Arbitrage Basket Mod-1026 | Quantum machine learning / Variational circuits / Index prediction | 11504 | 7792 | No |
| 6586 | Adaptive Scholarly Statistical Arbitrage Basket Mod-1410 | Neural operators / Deep operator networks / ETF rotation | 6030 | 5744 | No |
| 6595 | Adaptive Scholarly Statistical Arbitrage Basket Mod-1506 | Quantum machine learning / Variational circuits / Index prediction | 11531 | 7822 | No |
| 6631 | Adaptive Scholarly Statistical Arbitrage Basket Mod-1890 | Neural operators / Deep operator networks / ETF rotation | 6054 | 5757 | No |
| 6640 | Adaptive Scholarly Statistical Arbitrage Basket Mod-1986 | Quantum machine learning / Variational circuits / Index prediction | 11558 | 7852 | No |
| 6676 | Adaptive Scholarly Statistical Arbitrage Basket Mod-2370 | Neural operators / Deep operator networks / ETF rotation | 6078 | 5770 | No |
| 6685 | Adaptive Scholarly Statistical Arbitrage Basket Mod-2466 | Quantum machine learning / Variational circuits / Index prediction | 11585 | 7882 | No |
| 6721 | Adaptive Scholarly Statistical Arbitrage Basket Mod-2850 | Neural operators / Deep operator networks / ETF rotation | 6102 | 5783 | No |
| 6730 | Adaptive Scholarly Statistical Arbitrage Basket Mod-2946 | Quantum machine learning / Variational circuits / Index prediction | 11612 | 7912 | No |
| 6766 | Adaptive Scholarly Statistical Arbitrage Basket Mod-3330 | Neural operators / Deep operator networks / ETF rotation | 6126 | 5796 | No |
| 6775 | Adaptive Scholarly Statistical Arbitrage Basket Mod-3426 | Quantum machine learning / Variational circuits / Index prediction | 11639 | 7942 | No |
| 6811 | Adaptive Scholarly Statistical Arbitrage Basket Mod-3810 | Neural operators / Deep operator networks / ETF rotation | 6150 | 5809 | No |
| 6820 | Adaptive Scholarly Statistical Arbitrage Basket Mod-3906 | Quantum machine learning / Variational circuits / Index prediction | 11666 | 7972 | No |
