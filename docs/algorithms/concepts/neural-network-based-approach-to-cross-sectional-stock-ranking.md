# Neural-network-based approach to cross-sectional stock ranking

**Concept page** · shared by **63** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,875) ·
researched 2026-10-30

| | |
|---|---|
| Task | Cross-sectional stock ranking |
| Method | Neural networks |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Stock ranking needs a stock universe and a multi-name book; the project trades one ETF and holds no stock data. |
| Implemented in volatility-ai | Cross-sectional rankers are research code (`cross_section`, RK214). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK7, RK214, RK291, RK89 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Neural Scholarly
Cross-Sectional Stock Ranker Sys-365") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Score stocks against one another and form a portfolio from the ranks.
The neural-network version fits a neural network to the task. I found no
study of this method on this task.

## The CSV's description

Proposed neural-network-based approach to cross-sectional stock ranking:
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
* Neural forecasts on one index have not reliably beaten simple rules;
  an LSTM's stock picks were largely short-term reversal (Fischer &
  Krauss 2018, RK292).

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
| 1875 | Neural Scholarly Cross-Sectional Stock Ranker Sys-365 | Rough path theory / Tensor signatures / Stock trend forecasting | 8351 | 7653 | No |
| 1924 | Neural Scholarly Cross-Sectional Stock Ranker Sys-845 | Rough path theory / Tensor signatures / Stock trend forecasting | 8391 | 7675 | No |
| 1973 | Neural Scholarly Cross-Sectional Stock Ranker Sys-1325 | Rough path theory / Tensor signatures / Stock trend forecasting | 8431 | 7697 | No |
| 2022 | Neural Scholarly Cross-Sectional Stock Ranker Sys-1805 | Rough path theory / Tensor signatures / Stock trend forecasting | 8471 | 7719 | No |
| 3999 | Neural Scholarly Cross-Sectional Stock Ranker Sys-269 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6604 | 8486 | No |
| 4085 | Neural Scholarly Cross-Sectional Stock Ranker Sys-749 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6643 | 8521 | No |
| 4171 | Neural Scholarly Cross-Sectional Stock Ranker Sys-1229 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6682 | 8556 | No |
| 4257 | Neural Scholarly Cross-Sectional Stock Ranker Sys-1709 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6721 | 8591 | No |
| 4318 | Neural Scholarly Cross-Sectional Stock Ranker Mod-35 | Neural SDEs / Adversarial robustness / Stock options hedging | 10408 | 8615 | No |
| 4403 | Neural Scholarly Cross-Sectional Stock Ranker Mod-515 | Neural SDEs / Adversarial robustness / Stock options hedging | 10416 | 8652 | No |
| 4488 | Neural Scholarly Cross-Sectional Stock Ranker Mod-995 | Neural SDEs / Adversarial robustness / Stock options hedging | 10424 | 8689 | No |
| 4573 | Neural Scholarly Cross-Sectional Stock Ranker Mod-1475 | Neural SDEs / Adversarial robustness / Stock options hedging | 10432 | 8726 | No |
| 4658 | Neural Scholarly Cross-Sectional Stock Ranker Mod-1955 | Neural SDEs / Adversarial robustness / Stock options hedging | 10440 | 8763 | No |
| 4743 | Neural Scholarly Cross-Sectional Stock Ranker Mod-2435 | Neural SDEs / Adversarial robustness / Stock options hedging | 10448 | 8800 | No |
| 4828 | Neural Scholarly Cross-Sectional Stock Ranker Mod-2915 | Neural SDEs / Adversarial robustness / Stock options hedging | 10456 | 8837 | No |
| 4913 | Neural Scholarly Cross-Sectional Stock Ranker Mod-3395 | Neural SDEs / Adversarial robustness / Stock options hedging | 10464 | 8874 | No |
| 4998 | Neural Scholarly Cross-Sectional Stock Ranker Mod-3875 | Neural SDEs / Adversarial robustness / Stock options hedging | 10472 | 8911 | No |
| 6288 | Neural Scholarly Cross-Sectional Stock Ranker Sys-77 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6586 | 6590 | No |
| 6329 | Neural Scholarly Cross-Sectional Stock Ranker Sys-557 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6625 | 6626 | No |
| 6370 | Neural Scholarly Cross-Sectional Stock Ranker Sys-1037 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6664 | 6662 | No |
| 6411 | Neural Scholarly Cross-Sectional Stock Ranker Sys-1517 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6703 | 6698 | No |
| 6452 | Neural Scholarly Cross-Sectional Stock Ranker Sys-1997 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6742 | 6734 | No |
| 9142 | Neural Scholarly Cross-Sectional Stock Ranker Sys-173 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13779 | 12812 | No |
| 9254 | Neural Scholarly Cross-Sectional Stock Ranker Sys-461 | Graph attention / Sector contagion / Stock baskets | 12285 | 13171 | No |
| 9329 | Neural Scholarly Cross-Sectional Stock Ranker Sys-653 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13787 | 12824 | No |
| 9441 | Neural Scholarly Cross-Sectional Stock Ranker Sys-941 | Graph attention / Sector contagion / Stock baskets | 12295 | 13185 | No |
| 9516 | Neural Scholarly Cross-Sectional Stock Ranker Sys-1133 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13795 | 12836 | No |
| 9628 | Neural Scholarly Cross-Sectional Stock Ranker Sys-1421 | Graph attention / Sector contagion / Stock baskets | 12305 | 13199 | No |
| 9703 | Neural Scholarly Cross-Sectional Stock Ranker Sys-1613 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13803 | 12848 | No |
| 9815 | Neural Scholarly Cross-Sectional Stock Ranker Sys-1901 | Graph attention / Sector contagion / Stock baskets | 12315 | 13213 | No |
| 9943 | Neural Scholarly Cross-Sectional Stock Ranker Mod-227 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10911 | 10875 | No |
| 9981 | Neural Scholarly Cross-Sectional Stock Ranker Mod-323 | Topological data analysis / Betti persistence / Stock pairs | 11465 | 12033 | No |
| 10019 | Neural Scholarly Cross-Sectional Stock Ranker Mod-419 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6779 | 8644 | No |
| 10134 | Neural Scholarly Cross-Sectional Stock Ranker Mod-707 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10919 | 10894 | No |
| 10172 | Neural Scholarly Cross-Sectional Stock Ranker Mod-803 | Topological data analysis / Betti persistence / Stock pairs | 11492 | 12056 | No |
| 10210 | Neural Scholarly Cross-Sectional Stock Ranker Mod-899 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6821 | 8681 | No |
| 10325 | Neural Scholarly Cross-Sectional Stock Ranker Mod-1187 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10927 | 10913 | No |
| 10363 | Neural Scholarly Cross-Sectional Stock Ranker Mod-1283 | Topological data analysis / Betti persistence / Stock pairs | 11519 | 12079 | No |
| 10401 | Neural Scholarly Cross-Sectional Stock Ranker Mod-1379 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6863 | 8718 | No |
| 10516 | Neural Scholarly Cross-Sectional Stock Ranker Mod-1667 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10935 | 10932 | No |
| 10554 | Neural Scholarly Cross-Sectional Stock Ranker Mod-1763 | Topological data analysis / Betti persistence / Stock pairs | 11546 | 12102 | No |
| 10592 | Neural Scholarly Cross-Sectional Stock Ranker Mod-1859 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6905 | 8755 | No |
| 10707 | Neural Scholarly Cross-Sectional Stock Ranker Mod-2147 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10943 | 10951 | No |
| 10745 | Neural Scholarly Cross-Sectional Stock Ranker Mod-2243 | Topological data analysis / Betti persistence / Stock pairs | 11573 | 12125 | No |
| 10783 | Neural Scholarly Cross-Sectional Stock Ranker Mod-2339 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6947 | 8792 | No |
| 10898 | Neural Scholarly Cross-Sectional Stock Ranker Mod-2627 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10951 | 10970 | No |
| 10936 | Neural Scholarly Cross-Sectional Stock Ranker Mod-2723 | Topological data analysis / Betti persistence / Stock pairs | 11600 | 12148 | No |
| 10974 | Neural Scholarly Cross-Sectional Stock Ranker Mod-2819 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6989 | 8829 | No |
| 11089 | Neural Scholarly Cross-Sectional Stock Ranker Mod-3107 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10959 | 10989 | No |
| 11127 | Neural Scholarly Cross-Sectional Stock Ranker Mod-3203 | Topological data analysis / Betti persistence / Stock pairs | 11627 | 12171 | No |
| 11165 | Neural Scholarly Cross-Sectional Stock Ranker Mod-3299 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7031 | 8866 | No |
| 11280 | Neural Scholarly Cross-Sectional Stock Ranker Mod-3587 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10967 | 11008 | No |
| 11318 | Neural Scholarly Cross-Sectional Stock Ranker Mod-3683 | Topological data analysis / Betti persistence / Stock pairs | 11654 | 12194 | No |
| 11356 | Neural Scholarly Cross-Sectional Stock Ranker Mod-3779 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7073 | 8903 | No |
| 13976 | Neural Scholarly Cross-Sectional Stock Ranker Mod-131 | Delay differential equations / Controlled ODEs / Stock execution | 13218 | 13219 | No |
| 13990 | Neural Scholarly Cross-Sectional Stock Ranker Mod-611 | Delay differential equations / Controlled ODEs / Stock execution | 13230 | 13233 | No |
| 14004 | Neural Scholarly Cross-Sectional Stock Ranker Mod-1091 | Delay differential equations / Controlled ODEs / Stock execution | 13242 | 13247 | No |
| 14018 | Neural Scholarly Cross-Sectional Stock Ranker Mod-1571 | Delay differential equations / Controlled ODEs / Stock execution | 13254 | 13261 | No |
| 14032 | Neural Scholarly Cross-Sectional Stock Ranker Mod-2051 | Delay differential equations / Controlled ODEs / Stock execution | 13266 | 13275 | No |
| 14046 | Neural Scholarly Cross-Sectional Stock Ranker Mod-2531 | Delay differential equations / Controlled ODEs / Stock execution | 13278 | 13289 | No |
| 14060 | Neural Scholarly Cross-Sectional Stock Ranker Mod-3011 | Delay differential equations / Controlled ODEs / Stock execution | 13290 | 13303 | No |
| 14074 | Neural Scholarly Cross-Sectional Stock Ranker Mod-3491 | Delay differential equations / Controlled ODEs / Stock execution | 13302 | 13317 | No |
| 14088 | Neural Scholarly Cross-Sectional Stock Ranker Mod-3971 | Delay differential equations / Controlled ODEs / Stock execution | 13314 | 13331 | No |
