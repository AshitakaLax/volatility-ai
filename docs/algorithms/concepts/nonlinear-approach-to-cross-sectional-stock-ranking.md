# Nonlinear approach to cross-sectional stock ranking

**Concept page** · shared by **67** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #5,105) ·
researched 2026-10-30

| | |
|---|---|
| Task | Cross-sectional stock ranking |
| Method | Nonlinear models |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Stock ranking needs a stock universe and a multi-name book; the project trades one ETF and holds no stock data. |
| Implemented in volatility-ai | Cross-sectional rankers are research code (`cross_section`, RK214). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK7, RK214, RK291, RK89 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Non-Linear Scholarly
Cross-Sectional Stock Ranker Eng-455") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Score stocks against one another and form a portfolio from the ranks.
The nonlinear version replaces linear rules with nonlinear regressions
or filters. I found no study of this method on this task.

## The CSV's description

Proposed nonlinear approach to cross-sectional stock ranking: Score
stocks relative to one another using model features, then use the ranks
to form a portfolio; the target variable, universe, rebalance frequency,
and long/short rules need definition. This is a concept-level
interpretation of the title, not a complete trading specification: the
exact model inputs/target, calibration, entry/exit or rebalance rules,
and position sizing are not fully defined here.

## Evidence

* **Gu, Kelly & Xiu (2020), "Empirical Asset Pricing via Machine
  Learning," *Review of Financial Studies* 33(5), 2223–2274:** trees and
  neural networks forecast stock returns best, mostly from momentum,
  liquidity and volatility signals; a neural long-short decile spread
  had an out-of-sample Sharpe of 1.35. (Abstract.)
* **McLean & Pontiff (2016), "Does Academic Research Destroy Stock
  Return Predictability?" *Journal of Finance* 71(1):** anomaly
  portfolio returns are 26% lower out of sample and 58% lower after
  publication. (Abstract.)

## Against, and failure modes

* Anomaly returns shrink after publication (McLean & Pontiff); the
  long-only top-k form keeps only part of the long-short spread.
* Nonlinear fits on a few thousand daily bars overfit easily; gains over
  linear rules are usually small out of sample.

## Fit with volatility-ai

Needs a stock universe, point-in-time data and a multi-name book; the
engine trades one ETF and the warehouse holds no stock universe. The
researched form is RK214 (long-only top-k), which stays a reference.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Gu, S., Kelly, B., Xiu, D. (2020). *Review of Financial Studies*
  33(5), 2223–2274. Abstract.
* McLean, R. D., Pontiff, J. (2016). *Journal of Finance* 71(1).
  Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 5105 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-455 | Neural SDEs / Adversarial robustness / Stock options hedging | 10481 | 8954 | No |
| 5191 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-935 | Neural SDEs / Adversarial robustness / Stock options hedging | 10488 | 8989 | No |
| 5277 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-1415 | Neural SDEs / Adversarial robustness / Stock options hedging | 10495 | 9024 | No |
| 5363 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-1895 | Neural SDEs / Adversarial robustness / Stock options hedging | 10502 | 9059 | No |
| 5449 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-2375 | Neural SDEs / Adversarial robustness / Stock options hedging | 10509 | 9094 | No |
| 5535 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-2855 | Neural SDEs / Adversarial robustness / Stock options hedging | 10516 | 9129 | No |
| 5621 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-3335 | Neural SDEs / Adversarial robustness / Stock options hedging | 10523 | 9164 | No |
| 5707 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-3815 | Neural SDEs / Adversarial robustness / Stock options hedging | 10530 | 9199 | No |
| 5793 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-4295 | Neural SDEs / Adversarial robustness / Stock options hedging | 10537 | 9234 | No |
| 5879 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-4775 | Neural SDEs / Adversarial robustness / Stock options hedging | 10544 | 9269 | No |
| 5965 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-5255 | Neural SDEs / Adversarial robustness / Stock options hedging | 10551 | 9304 | No |
| 6051 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-5735 | Neural SDEs / Adversarial robustness / Stock options hedging | 10558 | 9339 | No |
| 7944 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-359 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7124 | 8946 | No |
| 7978 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-839 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7166 | 8981 | No |
| 8012 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-1319 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7208 | 9016 | No |
| 8046 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-1799 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7250 | 9051 | No |
| 8080 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-2279 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7292 | 9086 | No |
| 8114 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-2759 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7334 | 9121 | No |
| 8148 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-3239 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7376 | 9156 | No |
| 8182 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-3719 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7418 | 9191 | No |
| 8216 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-4199 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7460 | 9226 | No |
| 8250 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-4679 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7502 | 9261 | No |
| 8284 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-5159 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7544 | 9296 | No |
| 8318 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-5639 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7586 | 9331 | No |
| 11471 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-71 | Delay differential equations / Controlled ODEs / Stock execution | 13318 | 13334 | No |
| 11511 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-167 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10977 | 11030 | No |
| 11547 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-263 | Topological data analysis / Betti persistence / Stock pairs | 11687 | 12222 | No |
| 11662 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-551 | Delay differential equations / Controlled ODEs / Stock execution | 13330 | 13348 | No |
| 11702 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-647 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10986 | 11049 | No |
| 11738 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-743 | Topological data analysis / Betti persistence / Stock pairs | 11712 | 12245 | No |
| 11853 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-1031 | Delay differential equations / Controlled ODEs / Stock execution | 13342 | 13362 | No |
| 11893 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-1127 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10995 | 11068 | No |
| 11929 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-1223 | Topological data analysis / Betti persistence / Stock pairs | 11737 | 12268 | No |
| 12044 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-1511 | Delay differential equations / Controlled ODEs / Stock execution | 13354 | 13376 | No |
| 12084 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-1607 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11004 | 11087 | No |
| 12120 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-1703 | Topological data analysis / Betti persistence / Stock pairs | 11762 | 12291 | No |
| 12235 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-1991 | Delay differential equations / Controlled ODEs / Stock execution | 13366 | 13390 | No |
| 12275 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-2087 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11013 | 11106 | No |
| 12311 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-2183 | Topological data analysis / Betti persistence / Stock pairs | 11787 | 12314 | No |
| 12426 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-2471 | Delay differential equations / Controlled ODEs / Stock execution | 13378 | 13404 | No |
| 12466 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-2567 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11022 | 11125 | No |
| 12502 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-2663 | Topological data analysis / Betti persistence / Stock pairs | 11812 | 12337 | No |
| 12617 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-2951 | Delay differential equations / Controlled ODEs / Stock execution | 13390 | 13418 | No |
| 12657 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-3047 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11031 | 11144 | No |
| 12693 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-3143 | Topological data analysis / Betti persistence / Stock pairs | 11837 | 12360 | No |
| 12808 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-3431 | Delay differential equations / Controlled ODEs / Stock execution | 13402 | 13432 | No |
| 12848 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-3527 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11040 | 11163 | No |
| 12884 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-3623 | Topological data analysis / Betti persistence / Stock pairs | 11862 | 12383 | No |
| 12999 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-3911 | Delay differential equations / Controlled ODEs / Stock execution | 13414 | 13446 | No |
| 13039 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-4007 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11049 | 11182 | No |
| 13075 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-4103 | Topological data analysis / Betti persistence / Stock pairs | 11887 | 12406 | No |
| 13190 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-4391 | Delay differential equations / Controlled ODEs / Stock execution | 13426 | 13460 | No |
| 13230 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-4487 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11058 | 11201 | No |
| 13266 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-4583 | Topological data analysis / Betti persistence / Stock pairs | 11912 | 12429 | No |
| 13381 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-4871 | Delay differential equations / Controlled ODEs / Stock execution | 13438 | 13474 | No |
| 13421 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-4967 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11067 | 11220 | No |
| 13457 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-5063 | Topological data analysis / Betti persistence / Stock pairs | 11937 | 12452 | No |
| 13572 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-5351 | Delay differential equations / Controlled ODEs / Stock execution | 13450 | 13488 | No |
| 13612 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-5447 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11076 | 11239 | No |
| 13648 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-5543 | Topological data analysis / Betti persistence / Stock pairs | 11962 | 12475 | No |
| 13763 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-5831 | Delay differential equations / Controlled ODEs / Stock execution | 13462 | 13502 | No |
| 13803 | Non-Linear Scholarly Cross-Sectional Stock Ranker Eng-5927 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11085 | 11258 | No |
| 13849 | Non-Linear Scholarly Cross-Sectional Stock Ranker Alpha-51 | Delay differential equations / Neural CDEs / Stock execution | 8184 | 977 | No |
| 13855 | Non-Linear Scholarly Cross-Sectional Stock Ranker Alpha-151 | Delay differential equations / Neural CDEs / Stock execution | 8196 | 983 | No |
| 13861 | Non-Linear Scholarly Cross-Sectional Stock Ranker Alpha-251 | Delay differential equations / Neural CDEs / Stock execution | 13907 | 13146 | No |
| 13867 | Non-Linear Scholarly Cross-Sectional Stock Ranker Alpha-351 | Delay differential equations / Neural CDEs / Stock execution | 8217 | 996 | No |
| 13873 | Non-Linear Scholarly Cross-Sectional Stock Ranker Alpha-451 | Delay differential equations / Neural CDEs / Stock execution | 8229 | 1002 | No |
