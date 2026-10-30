# Geometry-aware approach to cross-sectional stock ranking

**Concept page** · shared by **63** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #5,061) ·
researched 2026-10-30

| | |
|---|---|
| Task | Cross-sectional stock ranking |
| Method | Geometry-aware (Riemannian) methods |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Stock ranking needs a stock universe and a multi-name book; the project trades one ETF and holds no stock data. |
| Implemented in volatility-ai | Cross-sectional rankers are research code (`cross_section`, RK214). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK7, RK214, RK291, RK89 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Riemannian Scholarly
Cross-Sectional Stock Ranker Eng-215") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Score stocks against one another and form a portfolio from the ranks.
The geometry-aware version works on the curved space of covariance
matrices or another manifold. I found no study of this method on this
task.

## The CSV's description

Proposed geometry-aware approach to cross-sectional stock ranking: Score
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
* No portfolio study shows Riemannian methods beating shrinkage (RK230).

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
| 5061 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-215 | Neural SDEs / Adversarial robustness / Stock options hedging | 12036 | 10304 | No |
| 5147 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-695 | Neural SDEs / Adversarial robustness / Stock options hedging | 12038 | 10306 | No |
| 5233 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-1175 | Neural SDEs / Adversarial robustness / Stock options hedging | 12040 | 10308 | No |
| 5319 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-1655 | Neural SDEs / Adversarial robustness / Stock options hedging | 12042 | 10310 | No |
| 5405 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-2135 | Neural SDEs / Adversarial robustness / Stock options hedging | 12044 | 10312 | No |
| 5491 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-2615 | Neural SDEs / Adversarial robustness / Stock options hedging | 12046 | 10314 | No |
| 5577 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-3095 | Neural SDEs / Adversarial robustness / Stock options hedging | 12048 | 10316 | No |
| 5663 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-3575 | Neural SDEs / Adversarial robustness / Stock options hedging | 12050 | 10318 | No |
| 5749 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-4055 | Neural SDEs / Adversarial robustness / Stock options hedging | 12052 | 10320 | No |
| 5835 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-4535 | Neural SDEs / Adversarial robustness / Stock options hedging | 12054 | 10322 | No |
| 5921 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-5015 | Neural SDEs / Adversarial robustness / Stock options hedging | 12056 | 10324 | No |
| 6007 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-5495 | Neural SDEs / Adversarial robustness / Stock options hedging | 12058 | 10326 | No |
| 6093 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-5975 | Neural SDEs / Adversarial robustness / Stock options hedging | 12060 | 10328 | No |
| 7924 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-119 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7102 | 8929 | No |
| 7958 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-599 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7144 | 8964 | No |
| 7992 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-1079 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7186 | 8999 | No |
| 8026 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-1559 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7228 | 9034 | No |
| 8060 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-2039 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7270 | 9069 | No |
| 8094 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-2519 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7312 | 9104 | No |
| 8128 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-2999 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7354 | 9139 | No |
| 8162 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-3479 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7396 | 9174 | No |
| 8196 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-3959 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7438 | 9209 | No |
| 8230 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-4439 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7480 | 9244 | No |
| 8264 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-4919 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7522 | 9279 | No |
| 8298 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-5399 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7564 | 9314 | No |
| 8332 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-5879 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7606 | 9349 | No |
| 11451 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-23 | Topological data analysis / Betti persistence / Stock pairs | 11673 | 12211 | No |
| 11565 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-311 | Delay differential equations / Controlled ODEs / Stock execution | 13323 | 13853 | No |
| 11605 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-407 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10981 | 11039 | No |
| 11642 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-503 | Topological data analysis / Betti persistence / Stock pairs | 11698 | 12234 | No |
| 11756 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-791 | Delay differential equations / Controlled ODEs / Stock execution | 13335 | 13862 | No |
| 11796 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-887 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10990 | 11058 | No |
| 11833 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-983 | Topological data analysis / Betti persistence / Stock pairs | 11723 | 12257 | No |
| 11947 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-1271 | Delay differential equations / Controlled ODEs / Stock execution | 13347 | 13871 | No |
| 11987 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-1367 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10999 | 11077 | No |
| 12024 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-1463 | Topological data analysis / Betti persistence / Stock pairs | 11748 | 12280 | No |
| 12138 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-1751 | Delay differential equations / Controlled ODEs / Stock execution | 13359 | 13880 | No |
| 12178 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-1847 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11008 | 11096 | No |
| 12215 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-1943 | Topological data analysis / Betti persistence / Stock pairs | 11773 | 12303 | No |
| 12329 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-2231 | Delay differential equations / Controlled ODEs / Stock execution | 13371 | 13889 | No |
| 12369 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-2327 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11017 | 11115 | No |
| 12406 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-2423 | Topological data analysis / Betti persistence / Stock pairs | 11798 | 12326 | No |
| 12520 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-2711 | Delay differential equations / Controlled ODEs / Stock execution | 13383 | 13898 | No |
| 12560 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-2807 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11026 | 11134 | No |
| 12597 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-2903 | Topological data analysis / Betti persistence / Stock pairs | 11823 | 12349 | No |
| 12711 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-3191 | Delay differential equations / Controlled ODEs / Stock execution | 13395 | 13907 | No |
| 12751 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-3287 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11035 | 11153 | No |
| 12788 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-3383 | Topological data analysis / Betti persistence / Stock pairs | 11848 | 12372 | No |
| 12902 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-3671 | Delay differential equations / Controlled ODEs / Stock execution | 13407 | 13916 | No |
| 12942 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-3767 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11044 | 11172 | No |
| 12979 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-3863 | Topological data analysis / Betti persistence / Stock pairs | 11873 | 12395 | No |
| 13093 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-4151 | Delay differential equations / Controlled ODEs / Stock execution | 13419 | 13925 | No |
| 13133 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-4247 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11053 | 11191 | No |
| 13170 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-4343 | Topological data analysis / Betti persistence / Stock pairs | 11898 | 12418 | No |
| 13284 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-4631 | Delay differential equations / Controlled ODEs / Stock execution | 13431 | 13934 | No |
| 13324 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-4727 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11062 | 11210 | No |
| 13361 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-4823 | Topological data analysis / Betti persistence / Stock pairs | 11923 | 12441 | No |
| 13475 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-5111 | Delay differential equations / Controlled ODEs / Stock execution | 13443 | 13943 | No |
| 13515 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-5207 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11071 | 11229 | No |
| 13552 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-5303 | Topological data analysis / Betti persistence / Stock pairs | 11948 | 12464 | No |
| 13666 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-5591 | Delay differential equations / Controlled ODEs / Stock execution | 13455 | 13952 | No |
| 13706 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-5687 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11080 | 11248 | No |
| 13743 | Riemannian Scholarly Cross-Sectional Stock Ranker Eng-5783 | Topological data analysis / Betti persistence / Stock pairs | 11973 | 12487 | No |
