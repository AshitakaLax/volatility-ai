# Kernel-based approach to cross-sectional stock ranking

**Concept page** · shared by **63** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,221) ·
researched 2026-10-30

| | |
|---|---|
| Task | Cross-sectional stock ranking |
| Method | Kernel methods |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Stock ranking needs a stock universe and a multi-name book; the project trades one ETF and holds no stock data. |
| Implemented in volatility-ai | Cross-sectional rankers are research code (`cross_section`, RK214). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK7, RK214, RK291, RK89 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Kernel Scholarly
Cross-Sectional Stock Ranker Sys-5") combine a method word, "Scholarly",
a task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Score stocks against one another and form a portfolio from the ranks.
The kernel-based version replaces linear rules with kernel regressions
or similarity-weighted estimates. I found no study of this method on
this task.

## The CSV's description

Proposed kernel-based approach to cross-sectional stock ranking: Score
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
* Kernel bandwidths are tuning parameters, and with few independent
  episodes they overfit.

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
| 1221 | Kernel Scholarly Cross-Sectional Stock Ranker Sys-5 | Rough path theory / Tensor signatures / Stock trend forecasting | 8321 | 7636 | No |
| 1238 | Kernel Scholarly Cross-Sectional Stock Ranker Sys-485 | Rough path theory / Tensor signatures / Stock trend forecasting | 8361 | 7658 | No |
| 1255 | Kernel Scholarly Cross-Sectional Stock Ranker Sys-965 | Rough path theory / Tensor signatures / Stock trend forecasting | 8401 | 7680 | No |
| 1272 | Kernel Scholarly Cross-Sectional Stock Ranker Sys-1445 | Rough path theory / Tensor signatures / Stock trend forecasting | 8441 | 7702 | No |
| 1289 | Kernel Scholarly Cross-Sectional Stock Ranker Sys-1925 | Rough path theory / Tensor signatures / Stock trend forecasting | 8481 | 7724 | No |
| 3219 | Kernel Scholarly Cross-Sectional Stock Ranker Sys-197 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6596 | 6599 | No |
| 3241 | Kernel Scholarly Cross-Sectional Stock Ranker Sys-677 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6635 | 6635 | No |
| 3263 | Kernel Scholarly Cross-Sectional Stock Ranker Sys-1157 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6674 | 6671 | No |
| 3285 | Kernel Scholarly Cross-Sectional Stock Ranker Sys-1637 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6713 | 6707 | No |
| 4020 | Kernel Scholarly Cross-Sectional Stock Ranker Sys-389 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6613 | 8495 | No |
| 4106 | Kernel Scholarly Cross-Sectional Stock Ranker Sys-869 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6652 | 8530 | No |
| 4192 | Kernel Scholarly Cross-Sectional Stock Ranker Sys-1349 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6691 | 8565 | No |
| 4278 | Kernel Scholarly Cross-Sectional Stock Ranker Sys-1829 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6730 | 8600 | No |
| 4382 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-395 | Neural SDEs / Adversarial robustness / Stock options hedging | 10414 | 8643 | No |
| 4467 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-875 | Neural SDEs / Adversarial robustness / Stock options hedging | 10422 | 8680 | No |
| 4552 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-1355 | Neural SDEs / Adversarial robustness / Stock options hedging | 10430 | 8717 | No |
| 4637 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-1835 | Neural SDEs / Adversarial robustness / Stock options hedging | 10438 | 8754 | No |
| 4722 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-2315 | Neural SDEs / Adversarial robustness / Stock options hedging | 10446 | 8791 | No |
| 4807 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-2795 | Neural SDEs / Adversarial robustness / Stock options hedging | 10454 | 8828 | No |
| 4892 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-3275 | Neural SDEs / Adversarial robustness / Stock options hedging | 10462 | 8865 | No |
| 4977 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-3755 | Neural SDEs / Adversarial robustness / Stock options hedging | 10470 | 8902 | No |
| 7528 | Kernel Scholarly Cross-Sectional Stock Ranker Sys-101 | Graph attention / Sector contagion / Stock baskets | 12277 | 13160 | No |
| 7559 | Kernel Scholarly Cross-Sectional Stock Ranker Sys-581 | Graph attention / Sector contagion / Stock baskets | 12287 | 13174 | No |
| 7590 | Kernel Scholarly Cross-Sectional Stock Ranker Sys-1061 | Graph attention / Sector contagion / Stock baskets | 12297 | 13188 | No |
| 7621 | Kernel Scholarly Cross-Sectional Stock Ranker Sys-1541 | Graph attention / Sector contagion / Stock baskets | 12307 | 13202 | No |
| 7670 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-299 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6768 | 8634 | No |
| 7702 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-779 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6810 | 8671 | No |
| 7734 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-1259 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6852 | 8708 | No |
| 7766 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-1739 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6894 | 8745 | No |
| 7798 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-2219 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6936 | 8782 | No |
| 7830 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-2699 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6978 | 8819 | No |
| 7862 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-3179 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7020 | 8856 | No |
| 7894 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-3659 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7062 | 8893 | No |
| 9189 | Kernel Scholarly Cross-Sectional Stock Ranker Sys-293 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13781 | 12815 | No |
| 9376 | Kernel Scholarly Cross-Sectional Stock Ranker Sys-773 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13789 | 12827 | No |
| 9563 | Kernel Scholarly Cross-Sectional Stock Ranker Sys-1253 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13797 | 12839 | No |
| 9750 | Kernel Scholarly Cross-Sectional Stock Ranker Sys-1733 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13805 | 12851 | No |
| 9857 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-11 | Delay differential equations / Controlled ODEs / Stock execution | 13215 | 13216 | No |
| 9895 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-107 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10909 | 10870 | No |
| 9932 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-203 | Topological data analysis / Betti persistence / Stock pairs | 11459 | 12027 | No |
| 10048 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-491 | Delay differential equations / Controlled ODEs / Stock execution | 13227 | 13230 | No |
| 10086 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-587 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10917 | 10889 | No |
| 10123 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-683 | Topological data analysis / Betti persistence / Stock pairs | 11486 | 12050 | No |
| 10239 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-971 | Delay differential equations / Controlled ODEs / Stock execution | 13239 | 13244 | No |
| 10277 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-1067 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10925 | 10908 | No |
| 10314 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-1163 | Topological data analysis / Betti persistence / Stock pairs | 11513 | 12073 | No |
| 10430 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-1451 | Delay differential equations / Controlled ODEs / Stock execution | 13251 | 13258 | No |
| 10468 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-1547 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10933 | 10927 | No |
| 10505 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-1643 | Topological data analysis / Betti persistence / Stock pairs | 11540 | 12096 | No |
| 10621 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-1931 | Delay differential equations / Controlled ODEs / Stock execution | 13263 | 13272 | No |
| 10659 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-2027 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10941 | 10946 | No |
| 10696 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-2123 | Topological data analysis / Betti persistence / Stock pairs | 11567 | 12119 | No |
| 10812 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-2411 | Delay differential equations / Controlled ODEs / Stock execution | 13275 | 13286 | No |
| 10850 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-2507 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10949 | 10965 | No |
| 10887 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-2603 | Topological data analysis / Betti persistence / Stock pairs | 11594 | 12142 | No |
| 11003 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-2891 | Delay differential equations / Controlled ODEs / Stock execution | 13287 | 13300 | No |
| 11041 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-2987 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10957 | 10984 | No |
| 11078 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-3083 | Topological data analysis / Betti persistence / Stock pairs | 11621 | 12165 | No |
| 11194 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-3371 | Delay differential equations / Controlled ODEs / Stock execution | 13299 | 13314 | No |
| 11232 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-3467 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10965 | 11003 | No |
| 11269 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-3563 | Topological data analysis / Betti persistence / Stock pairs | 11648 | 12188 | No |
| 11385 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-3851 | Delay differential equations / Controlled ODEs / Stock execution | 13311 | 13328 | No |
| 11423 | Kernel Scholarly Cross-Sectional Stock Ranker Mod-3947 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10973 | 11022 | No |
