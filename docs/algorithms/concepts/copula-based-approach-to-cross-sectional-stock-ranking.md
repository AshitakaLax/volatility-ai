# Copula-based approach to cross-sectional stock ranking

**Concept page** · shared by **62** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #5,040) ·
researched 2026-10-30

| | |
|---|---|
| Task | Cross-sectional stock ranking |
| Method | Copula models of dependence |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Stock ranking needs a stock universe and a multi-name book; the project trades one ETF and holds no stock data. |
| Implemented in volatility-ai | Cross-sectional rankers are research code (`cross_section`, RK214). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK7, RK214, RK291, RK89 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Copula Scholarly
Cross-Sectional Stock Ranker Eng-95") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Score stocks against one another and form a portfolio from the ranks.
The copula-based version models joint and tail dependence between assets
separately from each asset's own distribution. I found no study of this
method on this task.

## The CSV's description

Proposed copula-based approach to cross-sectional stock ranking: Score
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
* Copula families and parameters are hard to pin down from the few joint
  extremes the data hold.

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
| 5040 | Copula Scholarly Cross-Sectional Stock Ranker Eng-95 | Neural SDEs / Adversarial robustness / Stock options hedging | 11165 | 10303 | No |
| 5126 | Copula Scholarly Cross-Sectional Stock Ranker Eng-575 | Neural SDEs / Adversarial robustness / Stock options hedging | 11172 | 10305 | No |
| 5212 | Copula Scholarly Cross-Sectional Stock Ranker Eng-1055 | Neural SDEs / Adversarial robustness / Stock options hedging | 11179 | 10307 | No |
| 5298 | Copula Scholarly Cross-Sectional Stock Ranker Eng-1535 | Neural SDEs / Adversarial robustness / Stock options hedging | 11186 | 10309 | No |
| 5384 | Copula Scholarly Cross-Sectional Stock Ranker Eng-2015 | Neural SDEs / Adversarial robustness / Stock options hedging | 11193 | 10311 | No |
| 5470 | Copula Scholarly Cross-Sectional Stock Ranker Eng-2495 | Neural SDEs / Adversarial robustness / Stock options hedging | 11200 | 10313 | No |
| 5556 | Copula Scholarly Cross-Sectional Stock Ranker Eng-2975 | Neural SDEs / Adversarial robustness / Stock options hedging | 11207 | 10315 | No |
| 5642 | Copula Scholarly Cross-Sectional Stock Ranker Eng-3455 | Neural SDEs / Adversarial robustness / Stock options hedging | 11214 | 10317 | No |
| 5728 | Copula Scholarly Cross-Sectional Stock Ranker Eng-3935 | Neural SDEs / Adversarial robustness / Stock options hedging | 11221 | 10319 | No |
| 5814 | Copula Scholarly Cross-Sectional Stock Ranker Eng-4415 | Neural SDEs / Adversarial robustness / Stock options hedging | 11228 | 10321 | No |
| 5900 | Copula Scholarly Cross-Sectional Stock Ranker Eng-4895 | Neural SDEs / Adversarial robustness / Stock options hedging | 11235 | 10323 | No |
| 5986 | Copula Scholarly Cross-Sectional Stock Ranker Eng-5375 | Neural SDEs / Adversarial robustness / Stock options hedging | 11242 | 10325 | No |
| 6072 | Copula Scholarly Cross-Sectional Stock Ranker Eng-5855 | Neural SDEs / Adversarial robustness / Stock options hedging | 11249 | 10327 | No |
| 7951 | Copula Scholarly Cross-Sectional Stock Ranker Eng-479 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 9546 | 8956 | No |
| 7985 | Copula Scholarly Cross-Sectional Stock Ranker Eng-959 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 9562 | 8991 | No |
| 8019 | Copula Scholarly Cross-Sectional Stock Ranker Eng-1439 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 9578 | 9026 | No |
| 8053 | Copula Scholarly Cross-Sectional Stock Ranker Eng-1919 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 9594 | 9061 | No |
| 8087 | Copula Scholarly Cross-Sectional Stock Ranker Eng-2399 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 9610 | 9096 | No |
| 8121 | Copula Scholarly Cross-Sectional Stock Ranker Eng-2879 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 9626 | 9131 | No |
| 8155 | Copula Scholarly Cross-Sectional Stock Ranker Eng-3359 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 9642 | 9166 | No |
| 8189 | Copula Scholarly Cross-Sectional Stock Ranker Eng-3839 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 9658 | 9201 | No |
| 8223 | Copula Scholarly Cross-Sectional Stock Ranker Eng-4319 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 9674 | 9236 | No |
| 8257 | Copula Scholarly Cross-Sectional Stock Ranker Eng-4799 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 9690 | 9271 | No |
| 8291 | Copula Scholarly Cross-Sectional Stock Ranker Eng-5279 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 9706 | 9306 | No |
| 8325 | Copula Scholarly Cross-Sectional Stock Ranker Eng-5759 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 9722 | 9341 | No |
| 11520 | Copula Scholarly Cross-Sectional Stock Ranker Eng-191 | Delay differential equations / Controlled ODEs / Stock execution | 13676 | 13850 | No |
| 11557 | Copula Scholarly Cross-Sectional Stock Ranker Eng-287 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12037 | 11035 | No |
| 11593 | Copula Scholarly Cross-Sectional Stock Ranker Eng-383 | Topological data analysis / Betti persistence / Stock pairs | 12391 | 12228 | No |
| 11711 | Copula Scholarly Cross-Sectional Stock Ranker Eng-671 | Delay differential equations / Controlled ODEs / Stock execution | 13680 | 13859 | No |
| 11748 | Copula Scholarly Cross-Sectional Stock Ranker Eng-767 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12039 | 11054 | No |
| 11784 | Copula Scholarly Cross-Sectional Stock Ranker Eng-863 | Topological data analysis / Betti persistence / Stock pairs | 12401 | 12251 | No |
| 11902 | Copula Scholarly Cross-Sectional Stock Ranker Eng-1151 | Delay differential equations / Controlled ODEs / Stock execution | 13684 | 13868 | No |
| 11939 | Copula Scholarly Cross-Sectional Stock Ranker Eng-1247 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12041 | 11073 | No |
| 11975 | Copula Scholarly Cross-Sectional Stock Ranker Eng-1343 | Topological data analysis / Betti persistence / Stock pairs | 12411 | 12274 | No |
| 12093 | Copula Scholarly Cross-Sectional Stock Ranker Eng-1631 | Delay differential equations / Controlled ODEs / Stock execution | 13688 | 13877 | No |
| 12130 | Copula Scholarly Cross-Sectional Stock Ranker Eng-1727 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12043 | 11092 | No |
| 12166 | Copula Scholarly Cross-Sectional Stock Ranker Eng-1823 | Topological data analysis / Betti persistence / Stock pairs | 12421 | 12297 | No |
| 12284 | Copula Scholarly Cross-Sectional Stock Ranker Eng-2111 | Delay differential equations / Controlled ODEs / Stock execution | 13692 | 13886 | No |
| 12321 | Copula Scholarly Cross-Sectional Stock Ranker Eng-2207 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12045 | 11111 | No |
| 12357 | Copula Scholarly Cross-Sectional Stock Ranker Eng-2303 | Topological data analysis / Betti persistence / Stock pairs | 12431 | 12320 | No |
| 12475 | Copula Scholarly Cross-Sectional Stock Ranker Eng-2591 | Delay differential equations / Controlled ODEs / Stock execution | 13696 | 13895 | No |
| 12512 | Copula Scholarly Cross-Sectional Stock Ranker Eng-2687 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12047 | 11130 | No |
| 12548 | Copula Scholarly Cross-Sectional Stock Ranker Eng-2783 | Topological data analysis / Betti persistence / Stock pairs | 12441 | 12343 | No |
| 12666 | Copula Scholarly Cross-Sectional Stock Ranker Eng-3071 | Delay differential equations / Controlled ODEs / Stock execution | 13700 | 13904 | No |
| 12703 | Copula Scholarly Cross-Sectional Stock Ranker Eng-3167 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12049 | 11149 | No |
| 12739 | Copula Scholarly Cross-Sectional Stock Ranker Eng-3263 | Topological data analysis / Betti persistence / Stock pairs | 12451 | 12366 | No |
| 12857 | Copula Scholarly Cross-Sectional Stock Ranker Eng-3551 | Delay differential equations / Controlled ODEs / Stock execution | 13704 | 13913 | No |
| 12894 | Copula Scholarly Cross-Sectional Stock Ranker Eng-3647 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12051 | 11168 | No |
| 12930 | Copula Scholarly Cross-Sectional Stock Ranker Eng-3743 | Topological data analysis / Betti persistence / Stock pairs | 12461 | 12389 | No |
| 13048 | Copula Scholarly Cross-Sectional Stock Ranker Eng-4031 | Delay differential equations / Controlled ODEs / Stock execution | 13708 | 13922 | No |
| 13085 | Copula Scholarly Cross-Sectional Stock Ranker Eng-4127 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12053 | 11187 | No |
| 13121 | Copula Scholarly Cross-Sectional Stock Ranker Eng-4223 | Topological data analysis / Betti persistence / Stock pairs | 12471 | 12412 | No |
| 13239 | Copula Scholarly Cross-Sectional Stock Ranker Eng-4511 | Delay differential equations / Controlled ODEs / Stock execution | 13712 | 13931 | No |
| 13276 | Copula Scholarly Cross-Sectional Stock Ranker Eng-4607 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12055 | 11206 | No |
| 13312 | Copula Scholarly Cross-Sectional Stock Ranker Eng-4703 | Topological data analysis / Betti persistence / Stock pairs | 12481 | 12435 | No |
| 13430 | Copula Scholarly Cross-Sectional Stock Ranker Eng-4991 | Delay differential equations / Controlled ODEs / Stock execution | 13716 | 13940 | No |
| 13467 | Copula Scholarly Cross-Sectional Stock Ranker Eng-5087 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12057 | 11225 | No |
| 13503 | Copula Scholarly Cross-Sectional Stock Ranker Eng-5183 | Topological data analysis / Betti persistence / Stock pairs | 12491 | 12458 | No |
| 13621 | Copula Scholarly Cross-Sectional Stock Ranker Eng-5471 | Delay differential equations / Controlled ODEs / Stock execution | 13720 | 13949 | No |
| 13658 | Copula Scholarly Cross-Sectional Stock Ranker Eng-5567 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12059 | 11244 | No |
| 13694 | Copula Scholarly Cross-Sectional Stock Ranker Eng-5663 | Topological data analysis / Betti persistence / Stock pairs | 12501 | 12481 | No |
| 13812 | Copula Scholarly Cross-Sectional Stock Ranker Eng-5951 | Delay differential equations / Controlled ODEs / Stock execution | 13724 | 13958 | No |
