# Markov-state-based approach to statistical-arbitrage basket construction

**Concept page** · shared by **63** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #913) ·
researched 2026-10-30

| | |
|---|---|
| Task | Statistical-arbitrage basket construction |
| Method | Hidden Markov / regime-switching states |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Market-neutral baskets need short legs, which the owner's rules exclude; the engine trades one ETF long-only. |
| Implemented in volatility-ai | Johansen baskets and related stat-arb rules are research code (`stat_arb`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK33, RK36, RK89, RK93 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Markovian Scholarly
Statistical Arbitrage Basket Sys-342") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Score relative mispricing across a basket and build hedged,
market-neutral positions, subject to borrow, liquidity and costs. The
Markov-state version infers hidden states (calm, turbulent, crisis) and
conditions on the current one. I found no study of this method on this
task.

## The CSV's description

Proposed Markov-state-based approach to statistical-arbitrage basket
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
* States are clear only after the fact; causal (filtered) state
  probabilities lag turning points.

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
| 913 | Markovian Scholarly Statistical Arbitrage Basket Sys-342 | Robust optimization / Distributionally robust CVaR / Index tracking | 1139 | 1870 | No |
| 925 | Markovian Scholarly Statistical Arbitrage Basket Sys-822 | Robust optimization / Distributionally robust CVaR / Index tracking | 1169 | 1874 | No |
| 937 | Markovian Scholarly Statistical Arbitrage Basket Sys-1302 | Robust optimization / Distributionally robust CVaR / Index tracking | 1199 | 1878 | No |
| 949 | Markovian Scholarly Statistical Arbitrage Basket Sys-1782 | Robust optimization / Distributionally robust CVaR / Index tracking | 1229 | 1882 | No |
| 955 | Markovian Scholarly Statistical Arbitrage Basket Mod-42 | Robust optimization / Distributionally robust CVaR / Index tracking | 1245 | 1884 | No |
| 968 | Markovian Scholarly Statistical Arbitrage Basket Mod-522 | Robust optimization / Distributionally robust CVaR / Index tracking | 1276 | 1894 | No |
| 981 | Markovian Scholarly Statistical Arbitrage Basket Mod-1002 | Robust optimization / Distributionally robust CVaR / Index tracking | 1307 | 1904 | No |
| 994 | Markovian Scholarly Statistical Arbitrage Basket Mod-1482 | Robust optimization / Distributionally robust CVaR / Index tracking | 1338 | 1914 | No |
| 1007 | Markovian Scholarly Statistical Arbitrage Basket Mod-1962 | Robust optimization / Distributionally robust CVaR / Index tracking | 1369 | 1924 | No |
| 1020 | Markovian Scholarly Statistical Arbitrage Basket Mod-2442 | Robust optimization / Distributionally robust CVaR / Index tracking | 1400 | 1934 | No |
| 1033 | Markovian Scholarly Statistical Arbitrage Basket Mod-2922 | Robust optimization / Distributionally robust CVaR / Index tracking | 1431 | 1944 | No |
| 1046 | Markovian Scholarly Statistical Arbitrage Basket Mod-3402 | Robust optimization / Distributionally robust CVaR / Index tracking | 1462 | 1954 | No |
| 1059 | Markovian Scholarly Statistical Arbitrage Basket Mod-3882 | Robust optimization / Distributionally robust CVaR / Index tracking | 1493 | 1964 | No |
| 1222 | Markovian Scholarly Statistical Arbitrage Basket Sys-54 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1122 | 6588 | No |
| 1239 | Markovian Scholarly Statistical Arbitrage Basket Sys-534 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1152 | 6624 | No |
| 1256 | Markovian Scholarly Statistical Arbitrage Basket Sys-1014 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1182 | 6660 | No |
| 1273 | Markovian Scholarly Statistical Arbitrage Basket Sys-1494 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1212 | 6696 | No |
| 1290 | Markovian Scholarly Statistical Arbitrage Basket Sys-1974 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1242 | 6732 | No |
| 1296 | Markovian Scholarly Statistical Arbitrage Basket Mod-234 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1258 | 6751 | No |
| 1309 | Markovian Scholarly Statistical Arbitrage Basket Mod-714 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1289 | 6785 | No |
| 1322 | Markovian Scholarly Statistical Arbitrage Basket Mod-1194 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1320 | 6819 | No |
| 1335 | Markovian Scholarly Statistical Arbitrage Basket Mod-1674 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1351 | 6853 | No |
| 1348 | Markovian Scholarly Statistical Arbitrage Basket Mod-2154 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1382 | 6887 | No |
| 1361 | Markovian Scholarly Statistical Arbitrage Basket Mod-2634 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1413 | 6921 | No |
| 1374 | Markovian Scholarly Statistical Arbitrage Basket Mod-3114 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1444 | 6955 | No |
| 1387 | Markovian Scholarly Statistical Arbitrage Basket Mod-3594 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1475 | 6989 | No |
| 3230 | Markovian Scholarly Statistical Arbitrage Basket Sys-438 | Attention networks / Transformer encoders / Stock alpha generation | 3264 | 6618 | No |
| 3252 | Markovian Scholarly Statistical Arbitrage Basket Sys-918 | Attention networks / Transformer encoders / Stock alpha generation | 3288 | 6654 | No |
| 3274 | Markovian Scholarly Statistical Arbitrage Basket Sys-1398 | Attention networks / Transformer encoders / Stock alpha generation | 3312 | 6690 | No |
| 3296 | Markovian Scholarly Statistical Arbitrage Basket Sys-1878 | Attention networks / Transformer encoders / Stock alpha generation | 3336 | 6726 | No |
| 3307 | Markovian Scholarly Statistical Arbitrage Basket Mod-138 | Attention networks / Transformer encoders / Stock alpha generation | 3348 | 6747 | No |
| 3325 | Markovian Scholarly Statistical Arbitrage Basket Mod-618 | Attention networks / Transformer encoders / Stock alpha generation | 3368 | 6781 | No |
| 3343 | Markovian Scholarly Statistical Arbitrage Basket Mod-1098 | Attention networks / Transformer encoders / Stock alpha generation | 3388 | 6815 | No |
| 3361 | Markovian Scholarly Statistical Arbitrage Basket Mod-1578 | Attention networks / Transformer encoders / Stock alpha generation | 3408 | 6849 | No |
| 3379 | Markovian Scholarly Statistical Arbitrage Basket Mod-2058 | Attention networks / Transformer encoders / Stock alpha generation | 3428 | 6883 | No |
| 3397 | Markovian Scholarly Statistical Arbitrage Basket Mod-2538 | Attention networks / Transformer encoders / Stock alpha generation | 3448 | 6917 | No |
| 3415 | Markovian Scholarly Statistical Arbitrage Basket Mod-3018 | Attention networks / Transformer encoders / Stock alpha generation | 3468 | 6951 | No |
| 3433 | Markovian Scholarly Statistical Arbitrage Basket Mod-3498 | Attention networks / Transformer encoders / Stock alpha generation | 3488 | 6985 | No |
| 3451 | Markovian Scholarly Statistical Arbitrage Basket Mod-3978 | Attention networks / Transformer encoders / Stock alpha generation | 3508 | 7019 | No |
| 6294 | Markovian Scholarly Statistical Arbitrage Basket Sys-150 | Neural operators / Deep operator networks / ETF rotation | 5883 | 5641 | No |
| 6300 | Markovian Scholarly Statistical Arbitrage Basket Sys-246 | Quantum machine learning / Variational circuits / Index prediction | 11350 | 7649 | No |
| 6335 | Markovian Scholarly Statistical Arbitrage Basket Sys-630 | Neural operators / Deep operator networks / ETF rotation | 5903 | 5658 | No |
| 6341 | Markovian Scholarly Statistical Arbitrage Basket Sys-726 | Quantum machine learning / Variational circuits / Index prediction | 11376 | 7671 | No |
| 6376 | Markovian Scholarly Statistical Arbitrage Basket Sys-1110 | Neural operators / Deep operator networks / ETF rotation | 5923 | 5675 | No |
| 6382 | Markovian Scholarly Statistical Arbitrage Basket Sys-1206 | Quantum machine learning / Variational circuits / Index prediction | 11402 | 7693 | No |
| 6417 | Markovian Scholarly Statistical Arbitrage Basket Sys-1590 | Neural operators / Deep operator networks / ETF rotation | 5943 | 5692 | No |
| 6423 | Markovian Scholarly Statistical Arbitrage Basket Sys-1686 | Quantum machine learning / Variational circuits / Index prediction | 11428 | 7715 | No |
| 6485 | Markovian Scholarly Statistical Arbitrage Basket Mod-330 | Neural operators / Deep operator networks / ETF rotation | 5975 | 5715 | No |
| 6494 | Markovian Scholarly Statistical Arbitrage Basket Mod-426 | Quantum machine learning / Variational circuits / Index prediction | 11470 | 7755 | No |
| 6530 | Markovian Scholarly Statistical Arbitrage Basket Mod-810 | Neural operators / Deep operator networks / ETF rotation | 5999 | 5728 | No |
| 6539 | Markovian Scholarly Statistical Arbitrage Basket Mod-906 | Quantum machine learning / Variational circuits / Index prediction | 11497 | 7785 | No |
| 6575 | Markovian Scholarly Statistical Arbitrage Basket Mod-1290 | Neural operators / Deep operator networks / ETF rotation | 6023 | 5741 | No |
| 6584 | Markovian Scholarly Statistical Arbitrage Basket Mod-1386 | Quantum machine learning / Variational circuits / Index prediction | 11524 | 7815 | No |
| 6620 | Markovian Scholarly Statistical Arbitrage Basket Mod-1770 | Neural operators / Deep operator networks / ETF rotation | 6047 | 5754 | No |
| 6629 | Markovian Scholarly Statistical Arbitrage Basket Mod-1866 | Quantum machine learning / Variational circuits / Index prediction | 11551 | 7845 | No |
| 6665 | Markovian Scholarly Statistical Arbitrage Basket Mod-2250 | Neural operators / Deep operator networks / ETF rotation | 6071 | 5767 | No |
| 6674 | Markovian Scholarly Statistical Arbitrage Basket Mod-2346 | Quantum machine learning / Variational circuits / Index prediction | 11578 | 7875 | No |
| 6710 | Markovian Scholarly Statistical Arbitrage Basket Mod-2730 | Neural operators / Deep operator networks / ETF rotation | 6095 | 5780 | No |
| 6719 | Markovian Scholarly Statistical Arbitrage Basket Mod-2826 | Quantum machine learning / Variational circuits / Index prediction | 11605 | 7905 | No |
| 6755 | Markovian Scholarly Statistical Arbitrage Basket Mod-3210 | Neural operators / Deep operator networks / ETF rotation | 6119 | 5793 | No |
| 6764 | Markovian Scholarly Statistical Arbitrage Basket Mod-3306 | Quantum machine learning / Variational circuits / Index prediction | 11632 | 7935 | No |
| 6800 | Markovian Scholarly Statistical Arbitrage Basket Mod-3690 | Neural operators / Deep operator networks / ETF rotation | 6143 | 5806 | No |
| 6809 | Markovian Scholarly Statistical Arbitrage Basket Mod-3786 | Quantum machine learning / Variational circuits / Index prediction | 11659 | 7965 | No |
