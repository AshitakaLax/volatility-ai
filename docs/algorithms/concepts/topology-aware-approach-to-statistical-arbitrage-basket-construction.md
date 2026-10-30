# Topology-aware approach to statistical-arbitrage basket construction

**Concept page** · shared by **74** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,539) ·
researched 2026-10-30

| | |
|---|---|
| Task | Statistical-arbitrage basket construction |
| Method | Topological data analysis (persistent homology) |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Market-neutral baskets need short legs, which the owner's rules exclude; the engine trades one ETF long-only. |
| Implemented in volatility-ai | Johansen baskets and related stat-arb rules are research code (`stat_arb`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK33, RK36, RK89, RK93 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Topological Scholarly
Statistical Arbitrage Basket Ref-42") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Score relative mispricing across a basket and build hedged,
market-neutral positions, subject to borrow, liquidity and costs. The
topology-aware version derives persistent-homology features (Betti
numbers, persistence landscapes) from sliding windows of returns. I
found no study of this method on this task.

## The CSV's description

Proposed topology-aware approach to statistical-arbitrage basket
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
* The best-known topological crash study is in sample (Gidea & Katz
  2018), and the features depend on window and scale choices.

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
| 1539 | Topological Scholarly Statistical Arbitrage Basket Ref-42 | Robust optimization / Distributionally robust CVaR / Index tracking | 1051 | 1844 | No |
| 1542 | Topological Scholarly Statistical Arbitrage Basket Ref-522 | Robust optimization / Distributionally robust CVaR / Index tracking | 1085 | 1856 | No |
| 1562 | Topological Scholarly Statistical Arbitrage Basket Eng-282 | Robust optimization / Distributionally robust CVaR / Index tracking | 1517 | 1973 | No |
| 1565 | Topological Scholarly Statistical Arbitrage Basket Eng-762 | Robust optimization / Distributionally robust CVaR / Index tracking | 1547 | 1985 | No |
| 1568 | Topological Scholarly Statistical Arbitrage Basket Eng-1242 | Robust optimization / Distributionally robust CVaR / Index tracking | 1577 | 1997 | No |
| 1571 | Topological Scholarly Statistical Arbitrage Basket Eng-1722 | Robust optimization / Distributionally robust CVaR / Index tracking | 1607 | 2009 | No |
| 1574 | Topological Scholarly Statistical Arbitrage Basket Eng-2202 | Robust optimization / Distributionally robust CVaR / Index tracking | 1637 | 2021 | No |
| 1577 | Topological Scholarly Statistical Arbitrage Basket Eng-2682 | Robust optimization / Distributionally robust CVaR / Index tracking | 1667 | 2033 | No |
| 1580 | Topological Scholarly Statistical Arbitrage Basket Eng-3162 | Robust optimization / Distributionally robust CVaR / Index tracking | 1697 | 2045 | No |
| 1583 | Topological Scholarly Statistical Arbitrage Basket Eng-3642 | Robust optimization / Distributionally robust CVaR / Index tracking | 1727 | 2057 | No |
| 1586 | Topological Scholarly Statistical Arbitrage Basket Eng-4122 | Robust optimization / Distributionally robust CVaR / Index tracking | 1757 | 2069 | No |
| 1589 | Topological Scholarly Statistical Arbitrage Basket Eng-4602 | Robust optimization / Distributionally robust CVaR / Index tracking | 1787 | 2081 | No |
| 1592 | Topological Scholarly Statistical Arbitrage Basket Eng-5082 | Robust optimization / Distributionally robust CVaR / Index tracking | 1817 | 2093 | No |
| 1595 | Topological Scholarly Statistical Arbitrage Basket Eng-5562 | Robust optimization / Distributionally robust CVaR / Index tracking | 1847 | 2105 | No |
| 1751 | Topological Scholarly Statistical Arbitrage Basket Ref-234 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1066 | 6542 | No |
| 1806 | Topological Scholarly Statistical Arbitrage Basket Ref-714 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1100 | 6568 | No |
| 2533 | Topological Scholarly Statistical Arbitrage Basket Eng-474 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1529 | 7051 | No |
| 2588 | Topological Scholarly Statistical Arbitrage Basket Eng-954 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1559 | 7083 | No |
| 2643 | Topological Scholarly Statistical Arbitrage Basket Eng-1434 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1589 | 7115 | No |
| 2698 | Topological Scholarly Statistical Arbitrage Basket Eng-1914 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1619 | 7147 | No |
| 2753 | Topological Scholarly Statistical Arbitrage Basket Eng-2394 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1649 | 7179 | No |
| 2808 | Topological Scholarly Statistical Arbitrage Basket Eng-2874 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1679 | 7211 | No |
| 2863 | Topological Scholarly Statistical Arbitrage Basket Eng-3354 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1709 | 7243 | No |
| 2918 | Topological Scholarly Statistical Arbitrage Basket Eng-3834 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1739 | 7275 | No |
| 2973 | Topological Scholarly Statistical Arbitrage Basket Eng-4314 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1769 | 7307 | No |
| 3028 | Topological Scholarly Statistical Arbitrage Basket Eng-4794 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1799 | 7339 | No |
| 3083 | Topological Scholarly Statistical Arbitrage Basket Eng-5274 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1829 | 7371 | No |
| 3138 | Topological Scholarly Statistical Arbitrage Basket Eng-5754 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1859 | 7403 | No |
| 6119 | Topological Scholarly Statistical Arbitrage Basket Ver-91 | Delay differential equations / Jump diffusion / Stock trading | 3830 | 1820 | No |
| 6134 | Topological Scholarly Statistical Arbitrage Basket Ver-191 | Delay differential equations / Jump diffusion / Stock trading | 13173 | 13142 | No |
| 6202 | Topological Scholarly Statistical Arbitrage Basket Ref-138 | Attention networks / Transformer encoders / Stock alpha generation | 3214 | 6538 | No |
| 6220 | Topological Scholarly Statistical Arbitrage Basket Ref-330 | Neural operators / Deep operator networks / ETF rotation | 5839 | 5622 | No |
| 6228 | Topological Scholarly Statistical Arbitrage Basket Ref-426 | Quantum machine learning / Variational circuits / Index prediction | 11306 | 7607 | No |
| 6248 | Topological Scholarly Statistical Arbitrage Basket Ref-618 | Attention networks / Transformer encoders / Stock alpha generation | 3230 | 6564 | No |
| 6266 | Topological Scholarly Statistical Arbitrage Basket Ref-810 | Neural operators / Deep operator networks / ETF rotation | 5864 | 5633 | No |
| 6274 | Topological Scholarly Statistical Arbitrage Basket Ref-906 | Quantum machine learning / Variational circuits / Index prediction | 11331 | 7631 | No |
| 6837 | Topological Scholarly Statistical Arbitrage Basket Eng-90 | Neural operators / Deep operator networks / ETF rotation | 6164 | 5816 | No |
| 6847 | Topological Scholarly Statistical Arbitrage Basket Eng-186 | Quantum machine learning / Variational circuits / Index prediction | 11683 | 7991 | No |
| 6864 | Topological Scholarly Statistical Arbitrage Basket Eng-378 | Attention networks / Transformer encoders / Stock alpha generation | 3524 | 7045 | No |
| 6883 | Topological Scholarly Statistical Arbitrage Basket Eng-570 | Neural operators / Deep operator networks / ETF rotation | 6186 | 5825 | No |
| 6893 | Topological Scholarly Statistical Arbitrage Basket Eng-666 | Quantum machine learning / Variational circuits / Index prediction | 11708 | 8023 | No |
| 6910 | Topological Scholarly Statistical Arbitrage Basket Eng-858 | Attention networks / Transformer encoders / Stock alpha generation | 3544 | 7077 | No |
| 6929 | Topological Scholarly Statistical Arbitrage Basket Eng-1050 | Neural operators / Deep operator networks / ETF rotation | 6208 | 5834 | No |
| 6939 | Topological Scholarly Statistical Arbitrage Basket Eng-1146 | Quantum machine learning / Variational circuits / Index prediction | 11733 | 8055 | No |
| 6956 | Topological Scholarly Statistical Arbitrage Basket Eng-1338 | Attention networks / Transformer encoders / Stock alpha generation | 3564 | 7109 | No |
| 6975 | Topological Scholarly Statistical Arbitrage Basket Eng-1530 | Neural operators / Deep operator networks / ETF rotation | 6230 | 5843 | No |
| 6985 | Topological Scholarly Statistical Arbitrage Basket Eng-1626 | Quantum machine learning / Variational circuits / Index prediction | 11758 | 8087 | No |
| 7002 | Topological Scholarly Statistical Arbitrage Basket Eng-1818 | Attention networks / Transformer encoders / Stock alpha generation | 3584 | 7141 | No |
| 7021 | Topological Scholarly Statistical Arbitrage Basket Eng-2010 | Neural operators / Deep operator networks / ETF rotation | 6252 | 5852 | No |
| 7031 | Topological Scholarly Statistical Arbitrage Basket Eng-2106 | Quantum machine learning / Variational circuits / Index prediction | 11783 | 8119 | No |
| 7048 | Topological Scholarly Statistical Arbitrage Basket Eng-2298 | Attention networks / Transformer encoders / Stock alpha generation | 3604 | 7173 | No |
| 7067 | Topological Scholarly Statistical Arbitrage Basket Eng-2490 | Neural operators / Deep operator networks / ETF rotation | 6274 | 5861 | No |
| 7077 | Topological Scholarly Statistical Arbitrage Basket Eng-2586 | Quantum machine learning / Variational circuits / Index prediction | 11808 | 8151 | No |
| 7094 | Topological Scholarly Statistical Arbitrage Basket Eng-2778 | Attention networks / Transformer encoders / Stock alpha generation | 3624 | 7205 | No |
| 7113 | Topological Scholarly Statistical Arbitrage Basket Eng-2970 | Neural operators / Deep operator networks / ETF rotation | 6296 | 5870 | No |
| 7123 | Topological Scholarly Statistical Arbitrage Basket Eng-3066 | Quantum machine learning / Variational circuits / Index prediction | 11833 | 8183 | No |
| 7140 | Topological Scholarly Statistical Arbitrage Basket Eng-3258 | Attention networks / Transformer encoders / Stock alpha generation | 3644 | 7237 | No |
| 7159 | Topological Scholarly Statistical Arbitrage Basket Eng-3450 | Neural operators / Deep operator networks / ETF rotation | 6318 | 5879 | No |
| 7169 | Topological Scholarly Statistical Arbitrage Basket Eng-3546 | Quantum machine learning / Variational circuits / Index prediction | 11858 | 8215 | No |
| 7186 | Topological Scholarly Statistical Arbitrage Basket Eng-3738 | Attention networks / Transformer encoders / Stock alpha generation | 3664 | 7269 | No |
| 7205 | Topological Scholarly Statistical Arbitrage Basket Eng-3930 | Neural operators / Deep operator networks / ETF rotation | 6340 | 5888 | No |
| 7215 | Topological Scholarly Statistical Arbitrage Basket Eng-4026 | Quantum machine learning / Variational circuits / Index prediction | 11883 | 8247 | No |
| 7232 | Topological Scholarly Statistical Arbitrage Basket Eng-4218 | Attention networks / Transformer encoders / Stock alpha generation | 3684 | 7301 | No |
| 7251 | Topological Scholarly Statistical Arbitrage Basket Eng-4410 | Neural operators / Deep operator networks / ETF rotation | 6362 | 5897 | No |
| 7261 | Topological Scholarly Statistical Arbitrage Basket Eng-4506 | Quantum machine learning / Variational circuits / Index prediction | 11908 | 8279 | No |
| 7278 | Topological Scholarly Statistical Arbitrage Basket Eng-4698 | Attention networks / Transformer encoders / Stock alpha generation | 3704 | 7333 | No |
| 7297 | Topological Scholarly Statistical Arbitrage Basket Eng-4890 | Neural operators / Deep operator networks / ETF rotation | 6384 | 5906 | No |
| 7307 | Topological Scholarly Statistical Arbitrage Basket Eng-4986 | Quantum machine learning / Variational circuits / Index prediction | 11933 | 8311 | No |
| 7324 | Topological Scholarly Statistical Arbitrage Basket Eng-5178 | Attention networks / Transformer encoders / Stock alpha generation | 3724 | 7365 | No |
| 7343 | Topological Scholarly Statistical Arbitrage Basket Eng-5370 | Neural operators / Deep operator networks / ETF rotation | 6406 | 5915 | No |
| 7353 | Topological Scholarly Statistical Arbitrage Basket Eng-5466 | Quantum machine learning / Variational circuits / Index prediction | 11958 | 8343 | No |
| 7370 | Topological Scholarly Statistical Arbitrage Basket Eng-5658 | Attention networks / Transformer encoders / Stock alpha generation | 3744 | 7397 | No |
| 7389 | Topological Scholarly Statistical Arbitrage Basket Eng-5850 | Neural operators / Deep operator networks / ETF rotation | 6428 | 5924 | No |
| 7399 | Topological Scholarly Statistical Arbitrage Basket Eng-5946 | Quantum machine learning / Variational circuits / Index prediction | 11983 | 8375 | No |
