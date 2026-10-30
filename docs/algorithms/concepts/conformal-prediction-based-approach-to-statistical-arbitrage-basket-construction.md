# Conformal-prediction-based approach to statistical-arbitrage basket construction

**Concept page** · shared by **73** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #886) ·
researched 2026-10-30

| | |
|---|---|
| Task | Statistical-arbitrage basket construction |
| Method | Conformal prediction intervals |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Market-neutral baskets need short legs, which the owner's rules exclude; the engine trades one ETF long-only. |
| Implemented in volatility-ai | Johansen baskets and related stat-arb rules are research code (`stat_arb`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK33, RK36, RK89, RK93 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Conformal Scholarly
Statistical Arbitrage Basket Ref-162") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Score relative mispricing across a basket and build hedged,
market-neutral positions, subject to borrow, liquidity and costs. The
conformal version wraps a forecast in distribution-free prediction
intervals and acts only when the interval is decisive. I found no study
of this method on this task.

## The CSV's description

Proposed conformal-prediction-based approach to statistical-arbitrage
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
* Conformal intervals measure a forecast's uncertainty; they do not
  create a forecast where none exists.

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
| 886 | Conformal Scholarly Statistical Arbitrage Basket Ref-162 | Robust optimization / Distributionally robust CVaR / Index tracking | 1060 | 1847 | No |
| 896 | Conformal Scholarly Statistical Arbitrage Basket Ref-642 | Robust optimization / Distributionally robust CVaR / Index tracking | 1094 | 1859 | No |
| 1070 | Conformal Scholarly Statistical Arbitrage Basket Eng-402 | Robust optimization / Distributionally robust CVaR / Index tracking | 1524 | 1976 | No |
| 1080 | Conformal Scholarly Statistical Arbitrage Basket Eng-882 | Robust optimization / Distributionally robust CVaR / Index tracking | 1554 | 1988 | No |
| 1090 | Conformal Scholarly Statistical Arbitrage Basket Eng-1362 | Robust optimization / Distributionally robust CVaR / Index tracking | 1584 | 2000 | No |
| 1100 | Conformal Scholarly Statistical Arbitrage Basket Eng-1842 | Robust optimization / Distributionally robust CVaR / Index tracking | 1614 | 2012 | No |
| 1110 | Conformal Scholarly Statistical Arbitrage Basket Eng-2322 | Robust optimization / Distributionally robust CVaR / Index tracking | 1644 | 2024 | No |
| 1120 | Conformal Scholarly Statistical Arbitrage Basket Eng-2802 | Robust optimization / Distributionally robust CVaR / Index tracking | 1674 | 2036 | No |
| 1130 | Conformal Scholarly Statistical Arbitrage Basket Eng-3282 | Robust optimization / Distributionally robust CVaR / Index tracking | 1704 | 2048 | No |
| 1140 | Conformal Scholarly Statistical Arbitrage Basket Eng-3762 | Robust optimization / Distributionally robust CVaR / Index tracking | 1734 | 2060 | No |
| 1150 | Conformal Scholarly Statistical Arbitrage Basket Eng-4242 | Robust optimization / Distributionally robust CVaR / Index tracking | 1764 | 2072 | No |
| 1160 | Conformal Scholarly Statistical Arbitrage Basket Eng-4722 | Robust optimization / Distributionally robust CVaR / Index tracking | 1794 | 2084 | No |
| 1170 | Conformal Scholarly Statistical Arbitrage Basket Eng-5202 | Robust optimization / Distributionally robust CVaR / Index tracking | 1824 | 2096 | No |
| 1180 | Conformal Scholarly Statistical Arbitrage Basket Eng-5682 | Robust optimization / Distributionally robust CVaR / Index tracking | 1854 | 2108 | No |
| 1205 | Conformal Scholarly Statistical Arbitrage Basket Ref-354 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1074 | 6548 | No |
| 1216 | Conformal Scholarly Statistical Arbitrage Basket Ref-834 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1108 | 6574 | No |
| 1401 | Conformal Scholarly Statistical Arbitrage Basket Eng-114 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1508 | 7027 | No |
| 1412 | Conformal Scholarly Statistical Arbitrage Basket Eng-594 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1538 | 7059 | No |
| 1423 | Conformal Scholarly Statistical Arbitrage Basket Eng-1074 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1568 | 7091 | No |
| 1434 | Conformal Scholarly Statistical Arbitrage Basket Eng-1554 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1598 | 7123 | No |
| 1445 | Conformal Scholarly Statistical Arbitrage Basket Eng-2034 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1628 | 7155 | No |
| 1456 | Conformal Scholarly Statistical Arbitrage Basket Eng-2514 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1658 | 7187 | No |
| 1467 | Conformal Scholarly Statistical Arbitrage Basket Eng-2994 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1688 | 7219 | No |
| 1478 | Conformal Scholarly Statistical Arbitrage Basket Eng-3474 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1718 | 7251 | No |
| 1489 | Conformal Scholarly Statistical Arbitrage Basket Eng-3954 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1748 | 7283 | No |
| 1500 | Conformal Scholarly Statistical Arbitrage Basket Eng-4434 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1778 | 7315 | No |
| 1511 | Conformal Scholarly Statistical Arbitrage Basket Eng-4914 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1808 | 7347 | No |
| 1522 | Conformal Scholarly Statistical Arbitrage Basket Eng-5394 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1838 | 7379 | No |
| 1533 | Conformal Scholarly Statistical Arbitrage Basket Eng-5874 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1868 | 7411 | No |
| 3184 | Conformal Scholarly Statistical Arbitrage Basket Ref-258 | Attention networks / Transformer encoders / Stock alpha generation | 3218 | 6544 | No |
| 3200 | Conformal Scholarly Statistical Arbitrage Basket Ref-738 | Attention networks / Transformer encoders / Stock alpha generation | 3234 | 6570 | No |
| 3453 | Conformal Scholarly Statistical Arbitrage Basket Eng-18 | Attention networks / Transformer encoders / Stock alpha generation | 3509 | 7021 | No |
| 3469 | Conformal Scholarly Statistical Arbitrage Basket Eng-498 | Attention networks / Transformer encoders / Stock alpha generation | 3529 | 7053 | No |
| 3485 | Conformal Scholarly Statistical Arbitrage Basket Eng-978 | Attention networks / Transformer encoders / Stock alpha generation | 3549 | 7085 | No |
| 3501 | Conformal Scholarly Statistical Arbitrage Basket Eng-1458 | Attention networks / Transformer encoders / Stock alpha generation | 3569 | 7117 | No |
| 3517 | Conformal Scholarly Statistical Arbitrage Basket Eng-1938 | Attention networks / Transformer encoders / Stock alpha generation | 3589 | 7149 | No |
| 3533 | Conformal Scholarly Statistical Arbitrage Basket Eng-2418 | Attention networks / Transformer encoders / Stock alpha generation | 3609 | 7181 | No |
| 3549 | Conformal Scholarly Statistical Arbitrage Basket Eng-2898 | Attention networks / Transformer encoders / Stock alpha generation | 3629 | 7213 | No |
| 3565 | Conformal Scholarly Statistical Arbitrage Basket Eng-3378 | Attention networks / Transformer encoders / Stock alpha generation | 3649 | 7245 | No |
| 3581 | Conformal Scholarly Statistical Arbitrage Basket Eng-3858 | Attention networks / Transformer encoders / Stock alpha generation | 3669 | 7277 | No |
| 3597 | Conformal Scholarly Statistical Arbitrage Basket Eng-4338 | Attention networks / Transformer encoders / Stock alpha generation | 3689 | 7309 | No |
| 3613 | Conformal Scholarly Statistical Arbitrage Basket Eng-4818 | Attention networks / Transformer encoders / Stock alpha generation | 3709 | 7341 | No |
| 3629 | Conformal Scholarly Statistical Arbitrage Basket Eng-5298 | Attention networks / Transformer encoders / Stock alpha generation | 3729 | 7373 | No |
| 3645 | Conformal Scholarly Statistical Arbitrage Basket Eng-5778 | Attention networks / Transformer encoders / Stock alpha generation | 3749 | 7405 | No |
| 6192 | Conformal Scholarly Statistical Arbitrage Basket Ref-66 | Quantum machine learning / Variational circuits / Index prediction | 11288 | 7589 | No |
| 6230 | Conformal Scholarly Statistical Arbitrage Basket Ref-450 | Neural operators / Deep operator networks / ETF rotation | 5847 | 5624 | No |
| 6238 | Conformal Scholarly Statistical Arbitrage Basket Ref-546 | Quantum machine learning / Variational circuits / Index prediction | 11313 | 7613 | No |
| 6276 | Conformal Scholarly Statistical Arbitrage Basket Ref-930 | Neural operators / Deep operator networks / ETF rotation | 5872 | 5635 | No |
| 6849 | Conformal Scholarly Statistical Arbitrage Basket Eng-210 | Neural operators / Deep operator networks / ETF rotation | 6170 | 5819 | No |
| 6858 | Conformal Scholarly Statistical Arbitrage Basket Eng-306 | Quantum machine learning / Variational circuits / Index prediction | 11689 | 7999 | No |
| 6895 | Conformal Scholarly Statistical Arbitrage Basket Eng-690 | Neural operators / Deep operator networks / ETF rotation | 6192 | 5828 | No |
| 6904 | Conformal Scholarly Statistical Arbitrage Basket Eng-786 | Quantum machine learning / Variational circuits / Index prediction | 11714 | 8031 | No |
| 6941 | Conformal Scholarly Statistical Arbitrage Basket Eng-1170 | Neural operators / Deep operator networks / ETF rotation | 6214 | 5837 | No |
| 6950 | Conformal Scholarly Statistical Arbitrage Basket Eng-1266 | Quantum machine learning / Variational circuits / Index prediction | 11739 | 8063 | No |
| 6987 | Conformal Scholarly Statistical Arbitrage Basket Eng-1650 | Neural operators / Deep operator networks / ETF rotation | 6236 | 5846 | No |
| 6996 | Conformal Scholarly Statistical Arbitrage Basket Eng-1746 | Quantum machine learning / Variational circuits / Index prediction | 11764 | 8095 | No |
| 7033 | Conformal Scholarly Statistical Arbitrage Basket Eng-2130 | Neural operators / Deep operator networks / ETF rotation | 6258 | 5855 | No |
| 7042 | Conformal Scholarly Statistical Arbitrage Basket Eng-2226 | Quantum machine learning / Variational circuits / Index prediction | 11789 | 8127 | No |
| 7079 | Conformal Scholarly Statistical Arbitrage Basket Eng-2610 | Neural operators / Deep operator networks / ETF rotation | 6280 | 5864 | No |
| 7088 | Conformal Scholarly Statistical Arbitrage Basket Eng-2706 | Quantum machine learning / Variational circuits / Index prediction | 11814 | 8159 | No |
| 7125 | Conformal Scholarly Statistical Arbitrage Basket Eng-3090 | Neural operators / Deep operator networks / ETF rotation | 6302 | 5873 | No |
| 7134 | Conformal Scholarly Statistical Arbitrage Basket Eng-3186 | Quantum machine learning / Variational circuits / Index prediction | 11839 | 8191 | No |
| 7171 | Conformal Scholarly Statistical Arbitrage Basket Eng-3570 | Neural operators / Deep operator networks / ETF rotation | 6324 | 5882 | No |
| 7180 | Conformal Scholarly Statistical Arbitrage Basket Eng-3666 | Quantum machine learning / Variational circuits / Index prediction | 11864 | 8223 | No |
| 7217 | Conformal Scholarly Statistical Arbitrage Basket Eng-4050 | Neural operators / Deep operator networks / ETF rotation | 6346 | 5891 | No |
| 7226 | Conformal Scholarly Statistical Arbitrage Basket Eng-4146 | Quantum machine learning / Variational circuits / Index prediction | 11889 | 8255 | No |
| 7263 | Conformal Scholarly Statistical Arbitrage Basket Eng-4530 | Neural operators / Deep operator networks / ETF rotation | 6368 | 5900 | No |
| 7272 | Conformal Scholarly Statistical Arbitrage Basket Eng-4626 | Quantum machine learning / Variational circuits / Index prediction | 11914 | 8287 | No |
| 7309 | Conformal Scholarly Statistical Arbitrage Basket Eng-5010 | Neural operators / Deep operator networks / ETF rotation | 6390 | 5909 | No |
| 7318 | Conformal Scholarly Statistical Arbitrage Basket Eng-5106 | Quantum machine learning / Variational circuits / Index prediction | 11939 | 8319 | No |
| 7355 | Conformal Scholarly Statistical Arbitrage Basket Eng-5490 | Neural operators / Deep operator networks / ETF rotation | 6412 | 5918 | No |
| 7364 | Conformal Scholarly Statistical Arbitrage Basket Eng-5586 | Quantum machine learning / Variational circuits / Index prediction | 11964 | 8351 | No |
| 7401 | Conformal Scholarly Statistical Arbitrage Basket Eng-5970 | Neural operators / Deep operator networks / ETF rotation | 6434 | 5927 | No |
