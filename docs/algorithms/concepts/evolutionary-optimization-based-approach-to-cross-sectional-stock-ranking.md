# Evolutionary-optimization-based approach to cross-sectional stock ranking

**Concept page** · shared by **62** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,225) ·
researched 2026-10-30

| | |
|---|---|
| Task | Cross-sectional stock ranking |
| Method | Evolutionary / genetic optimisation |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Stock ranking needs a stock universe and a multi-name book; the project trades one ETF and holds no stock data. |
| Implemented in volatility-ai | Cross-sectional rankers are research code (`cross_section`, RK214). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK7, RK214, RK291, RK89 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Evolutionary Scholarly
Cross-Sectional Stock Ranker Sys-125") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Score stocks against one another and form a portfolio from the ranks.
The evolutionary version searches parameters or weights with genetic
algorithms. I found no study of this method on this task.

## The CSV's description

Proposed evolutionary-optimization-based approach to cross-sectional
stock ranking: Score stocks relative to one another using model
features, then use the ranks to form a portfolio; the target variable,
universe, rebalance frequency, and long/short rules need definition.
This is a concept-level interpretation of the title, not a complete
trading specification: the exact model inputs/target, calibration,
entry/exit or rebalance rules, and position sizing are not fully defined
here.

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
* A genetic search over a backtest is a large multiple-testing exercise
  that finds the noise that fits best.

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
| 1225 | Evolutionary Scholarly Cross-Sectional Stock Ranker Sys-125 | Rough path theory / Tensor signatures / Stock trend forecasting | 8330 | 7642 | No |
| 1242 | Evolutionary Scholarly Cross-Sectional Stock Ranker Sys-605 | Rough path theory / Tensor signatures / Stock trend forecasting | 8370 | 7664 | No |
| 1259 | Evolutionary Scholarly Cross-Sectional Stock Ranker Sys-1085 | Rough path theory / Tensor signatures / Stock trend forecasting | 8410 | 7686 | No |
| 1276 | Evolutionary Scholarly Cross-Sectional Stock Ranker Sys-1565 | Rough path theory / Tensor signatures / Stock trend forecasting | 8450 | 7708 | No |
| 3225 | Evolutionary Scholarly Cross-Sectional Stock Ranker Sys-317 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6607 | 6608 | No |
| 3247 | Evolutionary Scholarly Cross-Sectional Stock Ranker Sys-797 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6646 | 6644 | No |
| 3269 | Evolutionary Scholarly Cross-Sectional Stock Ranker Sys-1277 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6685 | 6680 | No |
| 3291 | Evolutionary Scholarly Cross-Sectional Stock Ranker Sys-1757 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6724 | 6716 | No |
| 3956 | Evolutionary Scholarly Cross-Sectional Stock Ranker Sys-29 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6583 | 8469 | No |
| 4042 | Evolutionary Scholarly Cross-Sectional Stock Ranker Sys-509 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6622 | 8504 | No |
| 4128 | Evolutionary Scholarly Cross-Sectional Stock Ranker Sys-989 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6661 | 8539 | No |
| 4214 | Evolutionary Scholarly Cross-Sectional Stock Ranker Sys-1469 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6700 | 8574 | No |
| 4300 | Evolutionary Scholarly Cross-Sectional Stock Ranker Sys-1949 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6739 | 8609 | No |
| 4362 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-275 | Neural SDEs / Adversarial robustness / Stock options hedging | 10412 | 8633 | No |
| 4447 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-755 | Neural SDEs / Adversarial robustness / Stock options hedging | 10420 | 8670 | No |
| 4532 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-1235 | Neural SDEs / Adversarial robustness / Stock options hedging | 10428 | 8707 | No |
| 4617 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-1715 | Neural SDEs / Adversarial robustness / Stock options hedging | 10436 | 8744 | No |
| 4702 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-2195 | Neural SDEs / Adversarial robustness / Stock options hedging | 10444 | 8781 | No |
| 4787 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-2675 | Neural SDEs / Adversarial robustness / Stock options hedging | 10452 | 8818 | No |
| 4872 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-3155 | Neural SDEs / Adversarial robustness / Stock options hedging | 10460 | 8855 | No |
| 4957 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-3635 | Neural SDEs / Adversarial robustness / Stock options hedging | 10468 | 8892 | No |
| 7536 | Evolutionary Scholarly Cross-Sectional Stock Ranker Sys-221 | Graph attention / Sector contagion / Stock baskets | 12280 | 13164 | No |
| 7567 | Evolutionary Scholarly Cross-Sectional Stock Ranker Sys-701 | Graph attention / Sector contagion / Stock baskets | 12290 | 13178 | No |
| 7598 | Evolutionary Scholarly Cross-Sectional Stock Ranker Sys-1181 | Graph attention / Sector contagion / Stock baskets | 12300 | 13192 | No |
| 7629 | Evolutionary Scholarly Cross-Sectional Stock Ranker Sys-1661 | Graph attention / Sector contagion / Stock baskets | 12310 | 13206 | No |
| 7662 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-179 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6757 | 8626 | No |
| 7694 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-659 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6799 | 8663 | No |
| 7726 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-1139 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6841 | 8700 | No |
| 7758 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-1619 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6883 | 8737 | No |
| 7790 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-2099 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6925 | 8774 | No |
| 7822 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-2579 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6967 | 8811 | No |
| 7854 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-3059 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7009 | 8848 | No |
| 7886 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-3539 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7051 | 8885 | No |
| 9237 | Evolutionary Scholarly Cross-Sectional Stock Ranker Sys-413 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13783 | 12818 | No |
| 9424 | Evolutionary Scholarly Cross-Sectional Stock Ranker Sys-893 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13791 | 12830 | No |
| 9611 | Evolutionary Scholarly Cross-Sectional Stock Ranker Sys-1373 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13799 | 12842 | No |
| 9798 | Evolutionary Scholarly Cross-Sectional Stock Ranker Sys-1853 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13807 | 12854 | No |
| 9884 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-83 | Topological data analysis / Betti persistence / Stock pairs | 11451 | 12022 | No |
| 10002 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-371 | Delay differential equations / Controlled ODEs / Stock execution | 13225 | 13226 | No |
| 10038 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-467 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10915 | 10885 | No |
| 10075 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-563 | Topological data analysis / Betti persistence / Stock pairs | 11478 | 12045 | No |
| 10193 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-851 | Delay differential equations / Controlled ODEs / Stock execution | 13237 | 13240 | No |
| 10229 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-947 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10923 | 10904 | No |
| 10266 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-1043 | Topological data analysis / Betti persistence / Stock pairs | 11505 | 12068 | No |
| 10384 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-1331 | Delay differential equations / Controlled ODEs / Stock execution | 13249 | 13254 | No |
| 10420 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-1427 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10931 | 10923 | No |
| 10457 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-1523 | Topological data analysis / Betti persistence / Stock pairs | 11532 | 12091 | No |
| 10575 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-1811 | Delay differential equations / Controlled ODEs / Stock execution | 13261 | 13268 | No |
| 10611 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-1907 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10939 | 10942 | No |
| 10648 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-2003 | Topological data analysis / Betti persistence / Stock pairs | 11559 | 12114 | No |
| 10766 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-2291 | Delay differential equations / Controlled ODEs / Stock execution | 13273 | 13282 | No |
| 10802 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-2387 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10947 | 10961 | No |
| 10839 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-2483 | Topological data analysis / Betti persistence / Stock pairs | 11586 | 12137 | No |
| 10957 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-2771 | Delay differential equations / Controlled ODEs / Stock execution | 13285 | 13296 | No |
| 10993 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-2867 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10955 | 10980 | No |
| 11030 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-2963 | Topological data analysis / Betti persistence / Stock pairs | 11613 | 12160 | No |
| 11148 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-3251 | Delay differential equations / Controlled ODEs / Stock execution | 13297 | 13310 | No |
| 11184 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-3347 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10963 | 10999 | No |
| 11221 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-3443 | Topological data analysis / Betti persistence / Stock pairs | 11640 | 12183 | No |
| 11339 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-3731 | Delay differential equations / Controlled ODEs / Stock execution | 13309 | 13324 | No |
| 11375 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-3827 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10971 | 11018 | No |
| 11412 | Evolutionary Scholarly Cross-Sectional Stock Ranker Mod-3923 | Topological data analysis / Betti persistence / Stock pairs | 11667 | 12206 | No |
