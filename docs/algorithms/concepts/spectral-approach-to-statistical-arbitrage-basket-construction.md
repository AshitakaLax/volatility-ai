# Spectral approach to statistical-arbitrage basket construction

**Concept page** · shared by **78** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #849) ·
researched 2026-10-30

| | |
|---|---|
| Task | Statistical-arbitrage basket construction |
| Method | Spectral (frequency-domain) decomposition |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Market-neutral baskets need short legs, which the owner's rules exclude; the engine trades one ETF long-only. |
| Implemented in volatility-ai | Johansen baskets and related stat-arb rules are research code (`stat_arb`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK33, RK36, RK89, RK93 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Spectral Scholarly
Statistical Arbitrage Basket Alpha-22") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Score relative mispricing across a basket and build hedged,
market-neutral positions, subject to borrow, liquidity and costs. The
spectral version works in the frequency domain, filtering or weighting
components by cycle length. I found no study of this method on this
task.

## The CSV's description

Proposed spectral approach to statistical-arbitrage basket construction:
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
* Spectral estimates need long stationary windows; market cycles are
  neither.

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
| 849 | Spectral Scholarly Statistical Arbitrage Basket Alpha-22 | Robust statistics / Mean-CVaR / Index tracking | 8181 | 11287 | No |
| 856 | Spectral Scholarly Statistical Arbitrage Basket Alpha-122 | Robust statistics / Mean-CVaR / Index tracking | 4610 | 6505 | No |
| 863 | Spectral Scholarly Statistical Arbitrage Basket Alpha-222 | Robust statistics / Mean-CVaR / Index tracking | 1021 | 1833 | No |
| 870 | Spectral Scholarly Statistical Arbitrage Basket Alpha-322 | Robust statistics / Mean-CVaR / Index tracking | 8214 | 11293 | No |
| 877 | Spectral Scholarly Statistical Arbitrage Basket Alpha-422 | Robust statistics / Mean-CVaR / Index tracking | 4638 | 6524 | No |
| 890 | Spectral Scholarly Statistical Arbitrage Basket Ref-282 | Robust optimization / Distributionally robust CVaR / Index tracking | 1069 | 1850 | No |
| 900 | Spectral Scholarly Statistical Arbitrage Basket Ref-762 | Robust optimization / Distributionally robust CVaR / Index tracking | 1103 | 1862 | No |
| 1063 | Spectral Scholarly Statistical Arbitrage Basket Eng-42 | Robust optimization / Distributionally robust CVaR / Index tracking | 1501 | 1967 | No |
| 1073 | Spectral Scholarly Statistical Arbitrage Basket Eng-522 | Robust optimization / Distributionally robust CVaR / Index tracking | 1531 | 1979 | No |
| 1083 | Spectral Scholarly Statistical Arbitrage Basket Eng-1002 | Robust optimization / Distributionally robust CVaR / Index tracking | 1561 | 1991 | No |
| 1093 | Spectral Scholarly Statistical Arbitrage Basket Eng-1482 | Robust optimization / Distributionally robust CVaR / Index tracking | 1591 | 2003 | No |
| 1103 | Spectral Scholarly Statistical Arbitrage Basket Eng-1962 | Robust optimization / Distributionally robust CVaR / Index tracking | 1621 | 2015 | No |
| 1113 | Spectral Scholarly Statistical Arbitrage Basket Eng-2442 | Robust optimization / Distributionally robust CVaR / Index tracking | 1651 | 2027 | No |
| 1123 | Spectral Scholarly Statistical Arbitrage Basket Eng-2922 | Robust optimization / Distributionally robust CVaR / Index tracking | 1681 | 2039 | No |
| 1133 | Spectral Scholarly Statistical Arbitrage Basket Eng-3402 | Robust optimization / Distributionally robust CVaR / Index tracking | 1711 | 2051 | No |
| 1143 | Spectral Scholarly Statistical Arbitrage Basket Eng-3882 | Robust optimization / Distributionally robust CVaR / Index tracking | 1741 | 2063 | No |
| 1153 | Spectral Scholarly Statistical Arbitrage Basket Eng-4362 | Robust optimization / Distributionally robust CVaR / Index tracking | 1771 | 2075 | No |
| 1163 | Spectral Scholarly Statistical Arbitrage Basket Eng-4842 | Robust optimization / Distributionally robust CVaR / Index tracking | 1801 | 2087 | No |
| 1173 | Spectral Scholarly Statistical Arbitrage Basket Eng-5322 | Robust optimization / Distributionally robust CVaR / Index tracking | 1831 | 2099 | No |
| 1183 | Spectral Scholarly Statistical Arbitrage Basket Eng-5802 | Robust optimization / Distributionally robust CVaR / Index tracking | 1861 | 2111 | No |
| 1208 | Spectral Scholarly Statistical Arbitrage Basket Ref-474 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1082 | 6555 | No |
| 1219 | Spectral Scholarly Statistical Arbitrage Basket Ref-954 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1116 | 6581 | No |
| 1405 | Spectral Scholarly Statistical Arbitrage Basket Eng-234 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1515 | 7035 | No |
| 1416 | Spectral Scholarly Statistical Arbitrage Basket Eng-714 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1545 | 7067 | No |
| 1427 | Spectral Scholarly Statistical Arbitrage Basket Eng-1194 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1575 | 7099 | No |
| 1438 | Spectral Scholarly Statistical Arbitrage Basket Eng-1674 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1605 | 7131 | No |
| 1449 | Spectral Scholarly Statistical Arbitrage Basket Eng-2154 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1635 | 7163 | No |
| 1460 | Spectral Scholarly Statistical Arbitrage Basket Eng-2634 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1665 | 7195 | No |
| 1471 | Spectral Scholarly Statistical Arbitrage Basket Eng-3114 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1695 | 7227 | No |
| 1482 | Spectral Scholarly Statistical Arbitrage Basket Eng-3594 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1725 | 7259 | No |
| 1493 | Spectral Scholarly Statistical Arbitrage Basket Eng-4074 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1755 | 7291 | No |
| 1504 | Spectral Scholarly Statistical Arbitrage Basket Eng-4554 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1785 | 7323 | No |
| 1515 | Spectral Scholarly Statistical Arbitrage Basket Eng-5034 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1815 | 7355 | No |
| 1526 | Spectral Scholarly Statistical Arbitrage Basket Eng-5514 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1845 | 7387 | No |
| 1537 | Spectral Scholarly Statistical Arbitrage Basket Eng-5994 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1875 | 7419 | No |
| 3189 | Spectral Scholarly Statistical Arbitrage Basket Ref-378 | Attention networks / Transformer encoders / Stock alpha generation | 3222 | 6551 | No |
| 3205 | Spectral Scholarly Statistical Arbitrage Basket Ref-858 | Attention networks / Transformer encoders / Stock alpha generation | 3238 | 6577 | No |
| 3458 | Spectral Scholarly Statistical Arbitrage Basket Eng-138 | Attention networks / Transformer encoders / Stock alpha generation | 3514 | 7029 | No |
| 3474 | Spectral Scholarly Statistical Arbitrage Basket Eng-618 | Attention networks / Transformer encoders / Stock alpha generation | 3534 | 7061 | No |
| 3490 | Spectral Scholarly Statistical Arbitrage Basket Eng-1098 | Attention networks / Transformer encoders / Stock alpha generation | 3554 | 7093 | No |
| 3506 | Spectral Scholarly Statistical Arbitrage Basket Eng-1578 | Attention networks / Transformer encoders / Stock alpha generation | 3574 | 7125 | No |
| 3522 | Spectral Scholarly Statistical Arbitrage Basket Eng-2058 | Attention networks / Transformer encoders / Stock alpha generation | 3594 | 7157 | No |
| 3538 | Spectral Scholarly Statistical Arbitrage Basket Eng-2538 | Attention networks / Transformer encoders / Stock alpha generation | 3614 | 7189 | No |
| 3554 | Spectral Scholarly Statistical Arbitrage Basket Eng-3018 | Attention networks / Transformer encoders / Stock alpha generation | 3634 | 7221 | No |
| 3570 | Spectral Scholarly Statistical Arbitrage Basket Eng-3498 | Attention networks / Transformer encoders / Stock alpha generation | 3654 | 7253 | No |
| 3586 | Spectral Scholarly Statistical Arbitrage Basket Eng-3978 | Attention networks / Transformer encoders / Stock alpha generation | 3674 | 7285 | No |
| 3602 | Spectral Scholarly Statistical Arbitrage Basket Eng-4458 | Attention networks / Transformer encoders / Stock alpha generation | 3694 | 7317 | No |
| 3618 | Spectral Scholarly Statistical Arbitrage Basket Eng-4938 | Attention networks / Transformer encoders / Stock alpha generation | 3714 | 7349 | No |
| 3634 | Spectral Scholarly Statistical Arbitrage Basket Eng-5418 | Attention networks / Transformer encoders / Stock alpha generation | 3734 | 7381 | No |
| 3650 | Spectral Scholarly Statistical Arbitrage Basket Eng-5898 | Attention networks / Transformer encoders / Stock alpha generation | 3754 | 7413 | No |
| 6196 | Spectral Scholarly Statistical Arbitrage Basket Ref-90 | Neural operators / Deep operator networks / ETF rotation | 5828 | 5616 | No |
| 6206 | Spectral Scholarly Statistical Arbitrage Basket Ref-186 | Quantum machine learning / Variational circuits / Index prediction | 11295 | 7595 | No |
| 6242 | Spectral Scholarly Statistical Arbitrage Basket Ref-570 | Neural operators / Deep operator networks / ETF rotation | 5853 | 5627 | No |
| 6252 | Spectral Scholarly Statistical Arbitrage Basket Ref-666 | Quantum machine learning / Variational circuits / Index prediction | 11320 | 7619 | No |
| 6860 | Spectral Scholarly Statistical Arbitrage Basket Eng-330 | Neural operators / Deep operator networks / ETF rotation | 6174 | 5822 | No |
| 6868 | Spectral Scholarly Statistical Arbitrage Basket Eng-426 | Quantum machine learning / Variational circuits / Index prediction | 11694 | 8007 | No |
| 6906 | Spectral Scholarly Statistical Arbitrage Basket Eng-810 | Neural operators / Deep operator networks / ETF rotation | 6196 | 5831 | No |
| 6914 | Spectral Scholarly Statistical Arbitrage Basket Eng-906 | Quantum machine learning / Variational circuits / Index prediction | 11719 | 8039 | No |
| 6952 | Spectral Scholarly Statistical Arbitrage Basket Eng-1290 | Neural operators / Deep operator networks / ETF rotation | 6218 | 5840 | No |
| 6960 | Spectral Scholarly Statistical Arbitrage Basket Eng-1386 | Quantum machine learning / Variational circuits / Index prediction | 11744 | 8071 | No |
| 6998 | Spectral Scholarly Statistical Arbitrage Basket Eng-1770 | Neural operators / Deep operator networks / ETF rotation | 6240 | 5849 | No |
| 7006 | Spectral Scholarly Statistical Arbitrage Basket Eng-1866 | Quantum machine learning / Variational circuits / Index prediction | 11769 | 8103 | No |
| 7044 | Spectral Scholarly Statistical Arbitrage Basket Eng-2250 | Neural operators / Deep operator networks / ETF rotation | 6262 | 5858 | No |
| 7052 | Spectral Scholarly Statistical Arbitrage Basket Eng-2346 | Quantum machine learning / Variational circuits / Index prediction | 11794 | 8135 | No |
| 7090 | Spectral Scholarly Statistical Arbitrage Basket Eng-2730 | Neural operators / Deep operator networks / ETF rotation | 6284 | 5867 | No |
| 7098 | Spectral Scholarly Statistical Arbitrage Basket Eng-2826 | Quantum machine learning / Variational circuits / Index prediction | 11819 | 8167 | No |
| 7136 | Spectral Scholarly Statistical Arbitrage Basket Eng-3210 | Neural operators / Deep operator networks / ETF rotation | 6306 | 5876 | No |
| 7144 | Spectral Scholarly Statistical Arbitrage Basket Eng-3306 | Quantum machine learning / Variational circuits / Index prediction | 11844 | 8199 | No |
| 7182 | Spectral Scholarly Statistical Arbitrage Basket Eng-3690 | Neural operators / Deep operator networks / ETF rotation | 6328 | 5885 | No |
| 7190 | Spectral Scholarly Statistical Arbitrage Basket Eng-3786 | Quantum machine learning / Variational circuits / Index prediction | 11869 | 8231 | No |
| 7228 | Spectral Scholarly Statistical Arbitrage Basket Eng-4170 | Neural operators / Deep operator networks / ETF rotation | 6350 | 5894 | No |
| 7236 | Spectral Scholarly Statistical Arbitrage Basket Eng-4266 | Quantum machine learning / Variational circuits / Index prediction | 11894 | 8263 | No |
| 7274 | Spectral Scholarly Statistical Arbitrage Basket Eng-4650 | Neural operators / Deep operator networks / ETF rotation | 6372 | 5903 | No |
| 7282 | Spectral Scholarly Statistical Arbitrage Basket Eng-4746 | Quantum machine learning / Variational circuits / Index prediction | 11919 | 8295 | No |
| 7320 | Spectral Scholarly Statistical Arbitrage Basket Eng-5130 | Neural operators / Deep operator networks / ETF rotation | 6394 | 5912 | No |
| 7328 | Spectral Scholarly Statistical Arbitrage Basket Eng-5226 | Quantum machine learning / Variational circuits / Index prediction | 11944 | 8327 | No |
| 7366 | Spectral Scholarly Statistical Arbitrage Basket Eng-5610 | Neural operators / Deep operator networks / ETF rotation | 6416 | 5921 | No |
| 7374 | Spectral Scholarly Statistical Arbitrage Basket Eng-5706 | Quantum machine learning / Variational circuits / Index prediction | 11969 | 8359 | No |
