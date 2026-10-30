# Variational approach to cross-sectional stock ranking

**Concept page** · shared by **63** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #5,084) ·
researched 2026-10-30

| | |
|---|---|
| Task | Cross-sectional stock ranking |
| Method | Variational inference / variational autoencoders |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Stock ranking needs a stock universe and a multi-name book; the project trades one ETF and holds no stock data. |
| Implemented in volatility-ai | Cross-sectional rankers are research code (`cross_section`, RK214). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK7, RK214, RK291, RK89 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Variational Scholarly
Cross-Sectional Stock Ranker Eng-335") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Score stocks against one another and form a portfolio from the ranks.
The variational version learns latent factors or distributions with
variational inference. I found no study of this method on this task.

## The CSV's description

Proposed variational approach to cross-sectional stock ranking: Score
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
* Latent factors from a VAE are unstable across refits; no trading
  evidence found.

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
| 5084 | Variational Scholarly Cross-Sectional Stock Ranker Eng-335 | Neural SDEs / Adversarial robustness / Stock options hedging | 10478 | 8944 | No |
| 5170 | Variational Scholarly Cross-Sectional Stock Ranker Eng-815 | Neural SDEs / Adversarial robustness / Stock options hedging | 10485 | 8979 | No |
| 5256 | Variational Scholarly Cross-Sectional Stock Ranker Eng-1295 | Neural SDEs / Adversarial robustness / Stock options hedging | 10492 | 9014 | No |
| 5342 | Variational Scholarly Cross-Sectional Stock Ranker Eng-1775 | Neural SDEs / Adversarial robustness / Stock options hedging | 10499 | 9049 | No |
| 5428 | Variational Scholarly Cross-Sectional Stock Ranker Eng-2255 | Neural SDEs / Adversarial robustness / Stock options hedging | 10506 | 9084 | No |
| 5514 | Variational Scholarly Cross-Sectional Stock Ranker Eng-2735 | Neural SDEs / Adversarial robustness / Stock options hedging | 10513 | 9119 | No |
| 5600 | Variational Scholarly Cross-Sectional Stock Ranker Eng-3215 | Neural SDEs / Adversarial robustness / Stock options hedging | 10520 | 9154 | No |
| 5686 | Variational Scholarly Cross-Sectional Stock Ranker Eng-3695 | Neural SDEs / Adversarial robustness / Stock options hedging | 10527 | 9189 | No |
| 5772 | Variational Scholarly Cross-Sectional Stock Ranker Eng-4175 | Neural SDEs / Adversarial robustness / Stock options hedging | 10534 | 9224 | No |
| 5858 | Variational Scholarly Cross-Sectional Stock Ranker Eng-4655 | Neural SDEs / Adversarial robustness / Stock options hedging | 10541 | 9259 | No |
| 5944 | Variational Scholarly Cross-Sectional Stock Ranker Eng-5135 | Neural SDEs / Adversarial robustness / Stock options hedging | 10548 | 9294 | No |
| 6030 | Variational Scholarly Cross-Sectional Stock Ranker Eng-5615 | Neural SDEs / Adversarial robustness / Stock options hedging | 10555 | 9329 | No |
| 7934 | Variational Scholarly Cross-Sectional Stock Ranker Eng-239 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7113 | 8936 | No |
| 7968 | Variational Scholarly Cross-Sectional Stock Ranker Eng-719 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7155 | 8971 | No |
| 8002 | Variational Scholarly Cross-Sectional Stock Ranker Eng-1199 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7197 | 9006 | No |
| 8036 | Variational Scholarly Cross-Sectional Stock Ranker Eng-1679 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7239 | 9041 | No |
| 8070 | Variational Scholarly Cross-Sectional Stock Ranker Eng-2159 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7281 | 9076 | No |
| 8104 | Variational Scholarly Cross-Sectional Stock Ranker Eng-2639 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7323 | 9111 | No |
| 8138 | Variational Scholarly Cross-Sectional Stock Ranker Eng-3119 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7365 | 9146 | No |
| 8172 | Variational Scholarly Cross-Sectional Stock Ranker Eng-3599 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7407 | 9181 | No |
| 8206 | Variational Scholarly Cross-Sectional Stock Ranker Eng-4079 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7449 | 9216 | No |
| 8240 | Variational Scholarly Cross-Sectional Stock Ranker Eng-4559 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7491 | 9251 | No |
| 8274 | Variational Scholarly Cross-Sectional Stock Ranker Eng-5039 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7533 | 9286 | No |
| 8308 | Variational Scholarly Cross-Sectional Stock Ranker Eng-5519 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7575 | 9321 | No |
| 8342 | Variational Scholarly Cross-Sectional Stock Ranker Eng-5999 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7617 | 9356 | No |
| 11461 | Variational Scholarly Cross-Sectional Stock Ranker Eng-47 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10974 | 11025 | No |
| 11501 | Variational Scholarly Cross-Sectional Stock Ranker Eng-143 | Topological data analysis / Betti persistence / Stock pairs | 11680 | 12216 | No |
| 11615 | Variational Scholarly Cross-Sectional Stock Ranker Eng-431 | Delay differential equations / Controlled ODEs / Stock execution | 13326 | 13344 | No |
| 11652 | Variational Scholarly Cross-Sectional Stock Ranker Eng-527 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10983 | 11044 | No |
| 11692 | Variational Scholarly Cross-Sectional Stock Ranker Eng-623 | Topological data analysis / Betti persistence / Stock pairs | 11705 | 12239 | No |
| 11806 | Variational Scholarly Cross-Sectional Stock Ranker Eng-911 | Delay differential equations / Controlled ODEs / Stock execution | 13338 | 13358 | No |
| 11843 | Variational Scholarly Cross-Sectional Stock Ranker Eng-1007 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10992 | 11063 | No |
| 11883 | Variational Scholarly Cross-Sectional Stock Ranker Eng-1103 | Topological data analysis / Betti persistence / Stock pairs | 11730 | 12262 | No |
| 11997 | Variational Scholarly Cross-Sectional Stock Ranker Eng-1391 | Delay differential equations / Controlled ODEs / Stock execution | 13350 | 13372 | No |
| 12034 | Variational Scholarly Cross-Sectional Stock Ranker Eng-1487 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11001 | 11082 | No |
| 12074 | Variational Scholarly Cross-Sectional Stock Ranker Eng-1583 | Topological data analysis / Betti persistence / Stock pairs | 11755 | 12285 | No |
| 12188 | Variational Scholarly Cross-Sectional Stock Ranker Eng-1871 | Delay differential equations / Controlled ODEs / Stock execution | 13362 | 13386 | No |
| 12225 | Variational Scholarly Cross-Sectional Stock Ranker Eng-1967 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11010 | 11101 | No |
| 12265 | Variational Scholarly Cross-Sectional Stock Ranker Eng-2063 | Topological data analysis / Betti persistence / Stock pairs | 11780 | 12308 | No |
| 12379 | Variational Scholarly Cross-Sectional Stock Ranker Eng-2351 | Delay differential equations / Controlled ODEs / Stock execution | 13374 | 13400 | No |
| 12416 | Variational Scholarly Cross-Sectional Stock Ranker Eng-2447 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11019 | 11120 | No |
| 12456 | Variational Scholarly Cross-Sectional Stock Ranker Eng-2543 | Topological data analysis / Betti persistence / Stock pairs | 11805 | 12331 | No |
| 12570 | Variational Scholarly Cross-Sectional Stock Ranker Eng-2831 | Delay differential equations / Controlled ODEs / Stock execution | 13386 | 13414 | No |
| 12607 | Variational Scholarly Cross-Sectional Stock Ranker Eng-2927 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11028 | 11139 | No |
| 12647 | Variational Scholarly Cross-Sectional Stock Ranker Eng-3023 | Topological data analysis / Betti persistence / Stock pairs | 11830 | 12354 | No |
| 12761 | Variational Scholarly Cross-Sectional Stock Ranker Eng-3311 | Delay differential equations / Controlled ODEs / Stock execution | 13398 | 13428 | No |
| 12798 | Variational Scholarly Cross-Sectional Stock Ranker Eng-3407 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11037 | 11158 | No |
| 12838 | Variational Scholarly Cross-Sectional Stock Ranker Eng-3503 | Topological data analysis / Betti persistence / Stock pairs | 11855 | 12377 | No |
| 12952 | Variational Scholarly Cross-Sectional Stock Ranker Eng-3791 | Delay differential equations / Controlled ODEs / Stock execution | 13410 | 13442 | No |
| 12989 | Variational Scholarly Cross-Sectional Stock Ranker Eng-3887 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11046 | 11177 | No |
| 13029 | Variational Scholarly Cross-Sectional Stock Ranker Eng-3983 | Topological data analysis / Betti persistence / Stock pairs | 11880 | 12400 | No |
| 13143 | Variational Scholarly Cross-Sectional Stock Ranker Eng-4271 | Delay differential equations / Controlled ODEs / Stock execution | 13422 | 13456 | No |
| 13180 | Variational Scholarly Cross-Sectional Stock Ranker Eng-4367 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11055 | 11196 | No |
| 13220 | Variational Scholarly Cross-Sectional Stock Ranker Eng-4463 | Topological data analysis / Betti persistence / Stock pairs | 11905 | 12423 | No |
| 13334 | Variational Scholarly Cross-Sectional Stock Ranker Eng-4751 | Delay differential equations / Controlled ODEs / Stock execution | 13434 | 13470 | No |
| 13371 | Variational Scholarly Cross-Sectional Stock Ranker Eng-4847 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11064 | 11215 | No |
| 13411 | Variational Scholarly Cross-Sectional Stock Ranker Eng-4943 | Topological data analysis / Betti persistence / Stock pairs | 11930 | 12446 | No |
| 13525 | Variational Scholarly Cross-Sectional Stock Ranker Eng-5231 | Delay differential equations / Controlled ODEs / Stock execution | 13446 | 13484 | No |
| 13562 | Variational Scholarly Cross-Sectional Stock Ranker Eng-5327 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11073 | 11234 | No |
| 13602 | Variational Scholarly Cross-Sectional Stock Ranker Eng-5423 | Topological data analysis / Betti persistence / Stock pairs | 11955 | 12469 | No |
| 13716 | Variational Scholarly Cross-Sectional Stock Ranker Eng-5711 | Delay differential equations / Controlled ODEs / Stock execution | 13458 | 13498 | No |
| 13753 | Variational Scholarly Cross-Sectional Stock Ranker Eng-5807 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11082 | 11253 | No |
| 13793 | Variational Scholarly Cross-Sectional Stock Ranker Eng-5903 | Topological data analysis / Betti persistence / Stock pairs | 11980 | 12492 | No |
