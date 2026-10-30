# Path-signature-based approach to cross-sectional stock ranking

**Concept page** · shared by **68** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,228) ·
researched 2026-10-30

| | |
|---|---|
| Task | Cross-sectional stock ranking |
| Method | Path signatures |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Stock ranking needs a stock universe and a multi-name book; the project trades one ETF and holds no stock data. |
| Implemented in volatility-ai | Cross-sectional rankers are research code (`cross_section`, RK214). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK7, RK214, RK291, RK89 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Signature Scholarly
Cross-Sectional Stock Ranker Sys-245") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Score stocks against one another and form a portfolio from the ranks.
The path-signature version describes price paths by their
iterated-integral signatures and fits on those features. I found no
study of this method on this task.

## The CSV's description

Proposed path-signature-based approach to cross-sectional stock ranking:
Score stocks relative to one another using model features, then use the
ranks to form a portfolio; the target variable, universe, rebalance
frequency, and long/short rules need definition. This is a concept-level
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
* Signature features multiply with depth and dimension; no out-of-sample
  trading evidence found (RK328).

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
| 1228 | Signature Scholarly Cross-Sectional Stock Ranker Sys-245 | Rough path theory / Tensor signatures / Stock trend forecasting | 8340 | 7648 | No |
| 1245 | Signature Scholarly Cross-Sectional Stock Ranker Sys-725 | Rough path theory / Tensor signatures / Stock trend forecasting | 8380 | 7670 | No |
| 1262 | Signature Scholarly Cross-Sectional Stock Ranker Sys-1205 | Rough path theory / Tensor signatures / Stock trend forecasting | 8420 | 7692 | No |
| 1279 | Signature Scholarly Cross-Sectional Stock Ranker Sys-1685 | Rough path theory / Tensor signatures / Stock trend forecasting | 8460 | 7714 | No |
| 3229 | Signature Scholarly Cross-Sectional Stock Ranker Sys-437 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6616 | 6617 | No |
| 3251 | Signature Scholarly Cross-Sectional Stock Ranker Sys-917 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6655 | 6653 | No |
| 3273 | Signature Scholarly Cross-Sectional Stock Ranker Sys-1397 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6694 | 6689 | No |
| 3295 | Signature Scholarly Cross-Sectional Stock Ranker Sys-1877 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6733 | 6725 | No |
| 3978 | Signature Scholarly Cross-Sectional Stock Ranker Sys-149 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6593 | 8478 | No |
| 4064 | Signature Scholarly Cross-Sectional Stock Ranker Sys-629 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6632 | 8513 | No |
| 4150 | Signature Scholarly Cross-Sectional Stock Ranker Sys-1109 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6671 | 8548 | No |
| 4236 | Signature Scholarly Cross-Sectional Stock Ranker Sys-1589 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6710 | 8583 | No |
| 4342 | Signature Scholarly Cross-Sectional Stock Ranker Mod-155 | Neural SDEs / Adversarial robustness / Stock options hedging | 10410 | 8625 | No |
| 4427 | Signature Scholarly Cross-Sectional Stock Ranker Mod-635 | Neural SDEs / Adversarial robustness / Stock options hedging | 10418 | 8662 | No |
| 4512 | Signature Scholarly Cross-Sectional Stock Ranker Mod-1115 | Neural SDEs / Adversarial robustness / Stock options hedging | 10426 | 8699 | No |
| 4597 | Signature Scholarly Cross-Sectional Stock Ranker Mod-1595 | Neural SDEs / Adversarial robustness / Stock options hedging | 10434 | 8736 | No |
| 4682 | Signature Scholarly Cross-Sectional Stock Ranker Mod-2075 | Neural SDEs / Adversarial robustness / Stock options hedging | 10442 | 8773 | No |
| 4767 | Signature Scholarly Cross-Sectional Stock Ranker Mod-2555 | Neural SDEs / Adversarial robustness / Stock options hedging | 10450 | 8810 | No |
| 4852 | Signature Scholarly Cross-Sectional Stock Ranker Mod-3035 | Neural SDEs / Adversarial robustness / Stock options hedging | 10458 | 8847 | No |
| 4937 | Signature Scholarly Cross-Sectional Stock Ranker Mod-3515 | Neural SDEs / Adversarial robustness / Stock options hedging | 10466 | 8884 | No |
| 5022 | Signature Scholarly Cross-Sectional Stock Ranker Mod-3995 | Neural SDEs / Adversarial robustness / Stock options hedging | 10474 | 8921 | No |
| 7542 | Signature Scholarly Cross-Sectional Stock Ranker Sys-341 | Graph attention / Sector contagion / Stock baskets | 12283 | 13168 | No |
| 7573 | Signature Scholarly Cross-Sectional Stock Ranker Sys-821 | Graph attention / Sector contagion / Stock baskets | 12293 | 13182 | No |
| 7604 | Signature Scholarly Cross-Sectional Stock Ranker Sys-1301 | Graph attention / Sector contagion / Stock baskets | 12303 | 13196 | No |
| 7635 | Signature Scholarly Cross-Sectional Stock Ranker Sys-1781 | Graph attention / Sector contagion / Stock baskets | 12313 | 13210 | No |
| 7654 | Signature Scholarly Cross-Sectional Stock Ranker Mod-59 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6747 | 8617 | No |
| 7686 | Signature Scholarly Cross-Sectional Stock Ranker Mod-539 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6789 | 8654 | No |
| 7718 | Signature Scholarly Cross-Sectional Stock Ranker Mod-1019 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6831 | 8691 | No |
| 7750 | Signature Scholarly Cross-Sectional Stock Ranker Mod-1499 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6873 | 8728 | No |
| 7782 | Signature Scholarly Cross-Sectional Stock Ranker Mod-1979 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6915 | 8765 | No |
| 7814 | Signature Scholarly Cross-Sectional Stock Ranker Mod-2459 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6957 | 8802 | No |
| 7846 | Signature Scholarly Cross-Sectional Stock Ranker Mod-2939 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6999 | 8839 | No |
| 7878 | Signature Scholarly Cross-Sectional Stock Ranker Mod-3419 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7041 | 8876 | No |
| 7910 | Signature Scholarly Cross-Sectional Stock Ranker Mod-3899 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7083 | 8913 | No |
| 9095 | Signature Scholarly Cross-Sectional Stock Ranker Sys-53 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13777 | 12809 | No |
| 9282 | Signature Scholarly Cross-Sectional Stock Ranker Sys-533 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13785 | 12821 | No |
| 9469 | Signature Scholarly Cross-Sectional Stock Ranker Sys-1013 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13793 | 12833 | No |
| 9656 | Signature Scholarly Cross-Sectional Stock Ranker Sys-1493 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13801 | 12845 | No |
| 9843 | Signature Scholarly Cross-Sectional Stock Ranker Sys-1973 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13809 | 12857 | No |
| 9954 | Signature Scholarly Cross-Sectional Stock Ranker Mod-251 | Delay differential equations / Controlled ODEs / Stock execution | 13221 | 13222 | No |
| 9992 | Signature Scholarly Cross-Sectional Stock Ranker Mod-347 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10913 | 10880 | No |
| 10029 | Signature Scholarly Cross-Sectional Stock Ranker Mod-443 | Topological data analysis / Betti persistence / Stock pairs | 11471 | 12039 | No |
| 10145 | Signature Scholarly Cross-Sectional Stock Ranker Mod-731 | Delay differential equations / Controlled ODEs / Stock execution | 13233 | 13236 | No |
| 10183 | Signature Scholarly Cross-Sectional Stock Ranker Mod-827 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10921 | 10899 | No |
| 10220 | Signature Scholarly Cross-Sectional Stock Ranker Mod-923 | Topological data analysis / Betti persistence / Stock pairs | 11498 | 12062 | No |
| 10336 | Signature Scholarly Cross-Sectional Stock Ranker Mod-1211 | Delay differential equations / Controlled ODEs / Stock execution | 13245 | 13250 | No |
| 10374 | Signature Scholarly Cross-Sectional Stock Ranker Mod-1307 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10929 | 10918 | No |
| 10411 | Signature Scholarly Cross-Sectional Stock Ranker Mod-1403 | Topological data analysis / Betti persistence / Stock pairs | 11525 | 12085 | No |
| 10527 | Signature Scholarly Cross-Sectional Stock Ranker Mod-1691 | Delay differential equations / Controlled ODEs / Stock execution | 13257 | 13264 | No |
| 10565 | Signature Scholarly Cross-Sectional Stock Ranker Mod-1787 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10937 | 10937 | No |
| 10602 | Signature Scholarly Cross-Sectional Stock Ranker Mod-1883 | Topological data analysis / Betti persistence / Stock pairs | 11552 | 12108 | No |
| 10718 | Signature Scholarly Cross-Sectional Stock Ranker Mod-2171 | Delay differential equations / Controlled ODEs / Stock execution | 13269 | 13278 | No |
| 10756 | Signature Scholarly Cross-Sectional Stock Ranker Mod-2267 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10945 | 10956 | No |
| 10793 | Signature Scholarly Cross-Sectional Stock Ranker Mod-2363 | Topological data analysis / Betti persistence / Stock pairs | 11579 | 12131 | No |
| 10909 | Signature Scholarly Cross-Sectional Stock Ranker Mod-2651 | Delay differential equations / Controlled ODEs / Stock execution | 13281 | 13292 | No |
| 10947 | Signature Scholarly Cross-Sectional Stock Ranker Mod-2747 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10953 | 10975 | No |
| 10984 | Signature Scholarly Cross-Sectional Stock Ranker Mod-2843 | Topological data analysis / Betti persistence / Stock pairs | 11606 | 12154 | No |
| 11100 | Signature Scholarly Cross-Sectional Stock Ranker Mod-3131 | Delay differential equations / Controlled ODEs / Stock execution | 13293 | 13306 | No |
| 11138 | Signature Scholarly Cross-Sectional Stock Ranker Mod-3227 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10961 | 10994 | No |
| 11175 | Signature Scholarly Cross-Sectional Stock Ranker Mod-3323 | Topological data analysis / Betti persistence / Stock pairs | 11633 | 12177 | No |
| 11291 | Signature Scholarly Cross-Sectional Stock Ranker Mod-3611 | Delay differential equations / Controlled ODEs / Stock execution | 13305 | 13320 | No |
| 11329 | Signature Scholarly Cross-Sectional Stock Ranker Mod-3707 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10969 | 11013 | No |
| 11366 | Signature Scholarly Cross-Sectional Stock Ranker Mod-3803 | Topological data analysis / Betti persistence / Stock pairs | 11660 | 12200 | No |
| 13847 | Signature Scholarly Cross-Sectional Stock Ranker Alpha-11 | Delay differential equations / Neural CDEs / Stock execution | 13902 | 13143 | No |
| 13853 | Signature Scholarly Cross-Sectional Stock Ranker Alpha-111 | Delay differential equations / Neural CDEs / Stock execution | 8191 | 980 | No |
| 13859 | Signature Scholarly Cross-Sectional Stock Ranker Alpha-211 | Delay differential equations / Neural CDEs / Stock execution | 8203 | 988 | No |
| 13865 | Signature Scholarly Cross-Sectional Stock Ranker Alpha-311 | Delay differential equations / Neural CDEs / Stock execution | 13908 | 13147 | No |
| 13871 | Signature Scholarly Cross-Sectional Stock Ranker Alpha-411 | Delay differential equations / Neural CDEs / Stock execution | 8224 | 999 | No |
