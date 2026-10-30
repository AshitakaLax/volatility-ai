# Diffusion-model-based approach to statistical-arbitrage basket construction

**Concept page** · shared by **73** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,540) ·
researched 2026-10-30

| | |
|---|---|
| Task | Statistical-arbitrage basket construction |
| Method | Diffusion generative models |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Market-neutral baskets need short legs, which the owner's rules exclude; the engine trades one ETF long-only. |
| Implemented in volatility-ai | Johansen baskets and related stat-arb rules are research code (`stat_arb`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK33, RK36, RK89, RK93 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Diffusion Scholarly
Statistical Arbitrage Basket Ref-402") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Score relative mispricing across a basket and build hedged,
market-neutral positions, subject to borrow, liquidity and costs. The
diffusion-model version trains a denoising generative model and samples
scenarios or forecasts from it. I found no study of this method on this
task.

## The CSV's description

Proposed diffusion-model-based approach to statistical-arbitrage basket
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
* Generative models trained on a few thousand days memorise more than
  they generalise; no trading evidence found.

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
| 1540 | Diffusion Scholarly Statistical Arbitrage Basket Ref-402 | Robust optimization / Distributionally robust CVaR / Index tracking | 1077 | 1853 | No |
| 1543 | Diffusion Scholarly Statistical Arbitrage Basket Ref-882 | Robust optimization / Distributionally robust CVaR / Index tracking | 1111 | 1865 | No |
| 1561 | Diffusion Scholarly Statistical Arbitrage Basket Eng-162 | Robust optimization / Distributionally robust CVaR / Index tracking | 1509 | 1970 | No |
| 1564 | Diffusion Scholarly Statistical Arbitrage Basket Eng-642 | Robust optimization / Distributionally robust CVaR / Index tracking | 1539 | 1982 | No |
| 1567 | Diffusion Scholarly Statistical Arbitrage Basket Eng-1122 | Robust optimization / Distributionally robust CVaR / Index tracking | 1569 | 1994 | No |
| 1570 | Diffusion Scholarly Statistical Arbitrage Basket Eng-1602 | Robust optimization / Distributionally robust CVaR / Index tracking | 1599 | 2006 | No |
| 1573 | Diffusion Scholarly Statistical Arbitrage Basket Eng-2082 | Robust optimization / Distributionally robust CVaR / Index tracking | 1629 | 2018 | No |
| 1576 | Diffusion Scholarly Statistical Arbitrage Basket Eng-2562 | Robust optimization / Distributionally robust CVaR / Index tracking | 1659 | 2030 | No |
| 1579 | Diffusion Scholarly Statistical Arbitrage Basket Eng-3042 | Robust optimization / Distributionally robust CVaR / Index tracking | 1689 | 2042 | No |
| 1582 | Diffusion Scholarly Statistical Arbitrage Basket Eng-3522 | Robust optimization / Distributionally robust CVaR / Index tracking | 1719 | 2054 | No |
| 1585 | Diffusion Scholarly Statistical Arbitrage Basket Eng-4002 | Robust optimization / Distributionally robust CVaR / Index tracking | 1749 | 2066 | No |
| 1588 | Diffusion Scholarly Statistical Arbitrage Basket Eng-4482 | Robust optimization / Distributionally robust CVaR / Index tracking | 1779 | 2078 | No |
| 1591 | Diffusion Scholarly Statistical Arbitrage Basket Eng-4962 | Robust optimization / Distributionally robust CVaR / Index tracking | 1809 | 2090 | No |
| 1594 | Diffusion Scholarly Statistical Arbitrage Basket Eng-5442 | Robust optimization / Distributionally robust CVaR / Index tracking | 1839 | 2102 | No |
| 1597 | Diffusion Scholarly Statistical Arbitrage Basket Eng-5922 | Robust optimization / Distributionally robust CVaR / Index tracking | 1869 | 2114 | No |
| 1736 | Diffusion Scholarly Statistical Arbitrage Basket Ref-114 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1058 | 6536 | No |
| 1791 | Diffusion Scholarly Statistical Arbitrage Basket Ref-594 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1092 | 6562 | No |
| 2519 | Diffusion Scholarly Statistical Arbitrage Basket Eng-354 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1522 | 7043 | No |
| 2574 | Diffusion Scholarly Statistical Arbitrage Basket Eng-834 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1552 | 7075 | No |
| 2629 | Diffusion Scholarly Statistical Arbitrage Basket Eng-1314 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1582 | 7107 | No |
| 2684 | Diffusion Scholarly Statistical Arbitrage Basket Eng-1794 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1612 | 7139 | No |
| 2739 | Diffusion Scholarly Statistical Arbitrage Basket Eng-2274 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1642 | 7171 | No |
| 2794 | Diffusion Scholarly Statistical Arbitrage Basket Eng-2754 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1672 | 7203 | No |
| 2849 | Diffusion Scholarly Statistical Arbitrage Basket Eng-3234 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1702 | 7235 | No |
| 2904 | Diffusion Scholarly Statistical Arbitrage Basket Eng-3714 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1732 | 7267 | No |
| 2959 | Diffusion Scholarly Statistical Arbitrage Basket Eng-4194 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1762 | 7299 | No |
| 3014 | Diffusion Scholarly Statistical Arbitrage Basket Eng-4674 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1792 | 7331 | No |
| 3069 | Diffusion Scholarly Statistical Arbitrage Basket Eng-5154 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1822 | 7363 | No |
| 3124 | Diffusion Scholarly Statistical Arbitrage Basket Eng-5634 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 1852 | 7395 | No |
| 6188 | Diffusion Scholarly Statistical Arbitrage Basket Ref-18 | Attention networks / Transformer encoders / Stock alpha generation | 3210 | 6532 | No |
| 6209 | Diffusion Scholarly Statistical Arbitrage Basket Ref-210 | Neural operators / Deep operator networks / ETF rotation | 5834 | 5620 | No |
| 6217 | Diffusion Scholarly Statistical Arbitrage Basket Ref-306 | Quantum machine learning / Variational circuits / Index prediction | 11300 | 7601 | No |
| 6234 | Diffusion Scholarly Statistical Arbitrage Basket Ref-498 | Attention networks / Transformer encoders / Stock alpha generation | 3226 | 6558 | No |
| 6255 | Diffusion Scholarly Statistical Arbitrage Basket Ref-690 | Neural operators / Deep operator networks / ETF rotation | 5859 | 5631 | No |
| 6263 | Diffusion Scholarly Statistical Arbitrage Basket Ref-786 | Quantum machine learning / Variational circuits / Index prediction | 11325 | 7625 | No |
| 6280 | Diffusion Scholarly Statistical Arbitrage Basket Ref-978 | Attention networks / Transformer encoders / Stock alpha generation | 3242 | 6584 | No |
| 6835 | Diffusion Scholarly Statistical Arbitrage Basket Eng-66 | Quantum machine learning / Variational circuits / Index prediction | 11676 | 7983 | No |
| 6854 | Diffusion Scholarly Statistical Arbitrage Basket Eng-258 | Attention networks / Transformer encoders / Stock alpha generation | 3519 | 7037 | No |
| 6870 | Diffusion Scholarly Statistical Arbitrage Basket Eng-450 | Neural operators / Deep operator networks / ETF rotation | 6181 | 5824 | No |
| 6881 | Diffusion Scholarly Statistical Arbitrage Basket Eng-546 | Quantum machine learning / Variational circuits / Index prediction | 11701 | 8015 | No |
| 6900 | Diffusion Scholarly Statistical Arbitrage Basket Eng-738 | Attention networks / Transformer encoders / Stock alpha generation | 3539 | 7069 | No |
| 6916 | Diffusion Scholarly Statistical Arbitrage Basket Eng-930 | Neural operators / Deep operator networks / ETF rotation | 6203 | 5833 | No |
| 6927 | Diffusion Scholarly Statistical Arbitrage Basket Eng-1026 | Quantum machine learning / Variational circuits / Index prediction | 11726 | 8047 | No |
| 6946 | Diffusion Scholarly Statistical Arbitrage Basket Eng-1218 | Attention networks / Transformer encoders / Stock alpha generation | 3559 | 7101 | No |
| 6962 | Diffusion Scholarly Statistical Arbitrage Basket Eng-1410 | Neural operators / Deep operator networks / ETF rotation | 6225 | 5842 | No |
| 6973 | Diffusion Scholarly Statistical Arbitrage Basket Eng-1506 | Quantum machine learning / Variational circuits / Index prediction | 11751 | 8079 | No |
| 6992 | Diffusion Scholarly Statistical Arbitrage Basket Eng-1698 | Attention networks / Transformer encoders / Stock alpha generation | 3579 | 7133 | No |
| 7008 | Diffusion Scholarly Statistical Arbitrage Basket Eng-1890 | Neural operators / Deep operator networks / ETF rotation | 6247 | 5851 | No |
| 7019 | Diffusion Scholarly Statistical Arbitrage Basket Eng-1986 | Quantum machine learning / Variational circuits / Index prediction | 11776 | 8111 | No |
| 7038 | Diffusion Scholarly Statistical Arbitrage Basket Eng-2178 | Attention networks / Transformer encoders / Stock alpha generation | 3599 | 7165 | No |
| 7054 | Diffusion Scholarly Statistical Arbitrage Basket Eng-2370 | Neural operators / Deep operator networks / ETF rotation | 6269 | 5860 | No |
| 7065 | Diffusion Scholarly Statistical Arbitrage Basket Eng-2466 | Quantum machine learning / Variational circuits / Index prediction | 11801 | 8143 | No |
| 7084 | Diffusion Scholarly Statistical Arbitrage Basket Eng-2658 | Attention networks / Transformer encoders / Stock alpha generation | 3619 | 7197 | No |
| 7100 | Diffusion Scholarly Statistical Arbitrage Basket Eng-2850 | Neural operators / Deep operator networks / ETF rotation | 6291 | 5869 | No |
| 7111 | Diffusion Scholarly Statistical Arbitrage Basket Eng-2946 | Quantum machine learning / Variational circuits / Index prediction | 11826 | 8175 | No |
| 7130 | Diffusion Scholarly Statistical Arbitrage Basket Eng-3138 | Attention networks / Transformer encoders / Stock alpha generation | 3639 | 7229 | No |
| 7146 | Diffusion Scholarly Statistical Arbitrage Basket Eng-3330 | Neural operators / Deep operator networks / ETF rotation | 6313 | 5878 | No |
| 7157 | Diffusion Scholarly Statistical Arbitrage Basket Eng-3426 | Quantum machine learning / Variational circuits / Index prediction | 11851 | 8207 | No |
| 7176 | Diffusion Scholarly Statistical Arbitrage Basket Eng-3618 | Attention networks / Transformer encoders / Stock alpha generation | 3659 | 7261 | No |
| 7192 | Diffusion Scholarly Statistical Arbitrage Basket Eng-3810 | Neural operators / Deep operator networks / ETF rotation | 6335 | 5887 | No |
| 7203 | Diffusion Scholarly Statistical Arbitrage Basket Eng-3906 | Quantum machine learning / Variational circuits / Index prediction | 11876 | 8239 | No |
| 7222 | Diffusion Scholarly Statistical Arbitrage Basket Eng-4098 | Attention networks / Transformer encoders / Stock alpha generation | 3679 | 7293 | No |
| 7238 | Diffusion Scholarly Statistical Arbitrage Basket Eng-4290 | Neural operators / Deep operator networks / ETF rotation | 6357 | 5896 | No |
| 7249 | Diffusion Scholarly Statistical Arbitrage Basket Eng-4386 | Quantum machine learning / Variational circuits / Index prediction | 11901 | 8271 | No |
| 7268 | Diffusion Scholarly Statistical Arbitrage Basket Eng-4578 | Attention networks / Transformer encoders / Stock alpha generation | 3699 | 7325 | No |
| 7284 | Diffusion Scholarly Statistical Arbitrage Basket Eng-4770 | Neural operators / Deep operator networks / ETF rotation | 6379 | 5905 | No |
| 7295 | Diffusion Scholarly Statistical Arbitrage Basket Eng-4866 | Quantum machine learning / Variational circuits / Index prediction | 11926 | 8303 | No |
| 7314 | Diffusion Scholarly Statistical Arbitrage Basket Eng-5058 | Attention networks / Transformer encoders / Stock alpha generation | 3719 | 7357 | No |
| 7330 | Diffusion Scholarly Statistical Arbitrage Basket Eng-5250 | Neural operators / Deep operator networks / ETF rotation | 6401 | 5914 | No |
| 7341 | Diffusion Scholarly Statistical Arbitrage Basket Eng-5346 | Quantum machine learning / Variational circuits / Index prediction | 11951 | 8335 | No |
| 7360 | Diffusion Scholarly Statistical Arbitrage Basket Eng-5538 | Attention networks / Transformer encoders / Stock alpha generation | 3739 | 7389 | No |
| 7376 | Diffusion Scholarly Statistical Arbitrage Basket Eng-5730 | Neural operators / Deep operator networks / ETF rotation | 6423 | 5923 | No |
| 7387 | Diffusion Scholarly Statistical Arbitrage Basket Eng-5826 | Quantum machine learning / Variational circuits / Index prediction | 11976 | 8367 | No |
