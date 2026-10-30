# Multi-scale approach to leveraged-ETF exposure rebalancing

**Concept page** · shared by **63** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #5,079) ·
researched 2026-10-30

| | |
|---|---|
| Task | Leveraged-ETF exposure rebalancing |
| Method | Multi-scale (several horizons combined) |
| Fit with this project | ⏳ reference only · background, nothing to build now |
| Useful for volatility-ai | **Reference only.** A multi-scale blend is a sound way to set leverage, but no study shows it beating the simple volatility rules already built (V18, N7); background only. |
| Implemented in volatility-ai | The project's exposure levers are built: volatility targeting (V18), the TQQQ/QQQ leverage step-down (N7) and the SMA leverage switch (V16). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | V16, N7, V18, C-MS6, RK22 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Multi-Scale Scholarly
Leveraged ETF Rebalancer Eng-315") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Hold a target exposure through a leveraged ETF, rebalancing as the daily
reset and the path of returns pull the realised leverage away from
target, net of costs. The multi-scale version combines signals or
estimates measured over several horizons. I found no study of this
method on this task.

## The CSV's description

Proposed multi-scale approach to leveraged-ETF exposure rebalancing:
Adjust exposure to maintain a specified leveraged-ETF allocation or
target exposure, while accounting for daily-reset effects, path
dependency, and transaction costs. This is a concept-level
interpretation of the title, not a complete trading specification: the
exact model inputs/target, calibration, entry/exit or rebalance rules,
and position sizing are not fully defined here.

## Evidence

* **Avellaneda & Zhang (2010), "Path-Dependence of Leveraged ETF
  Returns," *SIAM Journal on Financial Mathematics* 1, 586–603:** the
  gap between a leveraged ETF and a static leveraged position is driven
  mainly by the underlying's realised variance; fees and funding are
  predictable. (Abstract and author slides.)
* **Cheng & Madhavan (2009), "The Dynamics of Leveraged and Inverse
  ETFs," *Journal of Investment Management*:** daily rebalancing makes
  leveraged ETFs path-dependent and creates end-of-day rebalancing flows
  in the direction of the day's move (see C-MS6). (Paper; cited in the
  ledger.)
* **Gayed & Bilello (2016), "Leverage for the Long Run":** hold leverage
  above the index's 200-day average and T-bills below it; volatility,
  which erodes daily-reset leverage, clusters below the average. The
  repository's measurement of the same switch carries a same-session
  lookahead (V16, R1). (Paper summary in
  `docs/research/correction-strategies.md`.)

## Against, and failure modes

* Volatility decay is a property of the path, not a forecastable edge:
  rebalancing toward a target chooses how much leverage to hold, it does
  not remove the decay.
* A target-exposure rule and a lot-harvesting grid pull in different
  directions; every sale still has to pass the no-loss guard.
* More horizons mean more weights to choose, and the blend can be
  overfitted.

## Fit with volatility-ai

This is the project's home ground. The engine trades TQQQ and already
varies its exposure three ways: volatility targeting (V18), the leverage
step-down between TQQQ and QQQ (N7) and the SMA leverage switch (V16).
An exposure rule here is a sizing lever on the grid, not a separate
strategy.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Avellaneda, M., Zhang, S. (2010). "Path-Dependence of Leveraged ETF
  Returns." *SIAM Journal on Financial Mathematics* 1, 586–603.
  doi:10.1137/090760805. Abstract.
* Cheng, M., Madhavan, A. (2009). "The Dynamics of Leveraged and Inverse
  ETFs." *Journal of Investment Management*. Cited in the ledger
  (C-MS6).
* Gayed, M. A., Bilello, C. (2016). "Leverage for the Long Run."
  Practitioner paper; see `docs/research/correction-strategies.md` R1.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 5079 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-315 | Neural SDEs / Adversarial robustness / Stock options hedging | 8829 | 7039 | No |
| 5165 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-795 | Neural SDEs / Adversarial robustness / Stock options hedging | 8865 | 7071 | No |
| 5251 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-1275 | Neural SDEs / Adversarial robustness / Stock options hedging | 8901 | 7103 | No |
| 5337 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-1755 | Neural SDEs / Adversarial robustness / Stock options hedging | 8937 | 7135 | No |
| 5423 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-2235 | Neural SDEs / Adversarial robustness / Stock options hedging | 8973 | 7167 | No |
| 5509 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-2715 | Neural SDEs / Adversarial robustness / Stock options hedging | 9009 | 7199 | No |
| 5595 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-3195 | Neural SDEs / Adversarial robustness / Stock options hedging | 9045 | 7231 | No |
| 5681 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-3675 | Neural SDEs / Adversarial robustness / Stock options hedging | 9081 | 7263 | No |
| 5767 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-4155 | Neural SDEs / Adversarial robustness / Stock options hedging | 9117 | 7295 | No |
| 5853 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-4635 | Neural SDEs / Adversarial robustness / Stock options hedging | 9153 | 7327 | No |
| 5939 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-5115 | Neural SDEs / Adversarial robustness / Stock options hedging | 9189 | 7359 | No |
| 6025 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-5595 | Neural SDEs / Adversarial robustness / Stock options hedging | 9225 | 7391 | No |
| 7933 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-219 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2730 | 7507 | No |
| 7967 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-699 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2768 | 7511 | No |
| 8001 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-1179 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2806 | 7515 | No |
| 8035 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-1659 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2844 | 7519 | No |
| 8069 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-2139 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2882 | 7523 | No |
| 8103 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-2619 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2920 | 7527 | No |
| 8137 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-3099 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2958 | 7531 | No |
| 8171 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-3579 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2996 | 7535 | No |
| 8205 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-4059 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 3034 | 7539 | No |
| 8239 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-4539 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 3072 | 7543 | No |
| 8273 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-5019 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 3110 | 7547 | No |
| 8307 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-5499 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 3148 | 7551 | No |
| 8341 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-5979 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 3186 | 7555 | No |
| 11454 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-27 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5058 | 11795 | No |
| 11492 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-123 | Topological data analysis / Betti persistence / Stock pairs | 2723 | 9565 | No |
| 11608 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-411 | Delay differential equations / Controlled ODEs / Stock execution | 4280 | 2491 | No |
| 11645 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-507 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5083 | 11799 | No |
| 11683 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-603 | Topological data analysis / Betti persistence / Stock pairs | 2761 | 9585 | No |
| 11799 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-891 | Delay differential equations / Controlled ODEs / Stock execution | 4306 | 2514 | No |
| 11836 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-987 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5108 | 11803 | No |
| 11874 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-1083 | Topological data analysis / Betti persistence / Stock pairs | 2799 | 9605 | No |
| 11990 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-1371 | Delay differential equations / Controlled ODEs / Stock execution | 4332 | 2537 | No |
| 12027 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-1467 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5133 | 11807 | No |
| 12065 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-1563 | Topological data analysis / Betti persistence / Stock pairs | 2837 | 9625 | No |
| 12181 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-1851 | Delay differential equations / Controlled ODEs / Stock execution | 4358 | 2560 | No |
| 12218 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-1947 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5158 | 11811 | No |
| 12256 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-2043 | Topological data analysis / Betti persistence / Stock pairs | 2875 | 9645 | No |
| 12372 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-2331 | Delay differential equations / Controlled ODEs / Stock execution | 4384 | 2583 | No |
| 12409 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-2427 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5183 | 11815 | No |
| 12447 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-2523 | Topological data analysis / Betti persistence / Stock pairs | 2913 | 9665 | No |
| 12563 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-2811 | Delay differential equations / Controlled ODEs / Stock execution | 4410 | 2606 | No |
| 12600 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-2907 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5208 | 11819 | No |
| 12638 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-3003 | Topological data analysis / Betti persistence / Stock pairs | 2951 | 9685 | No |
| 12754 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-3291 | Delay differential equations / Controlled ODEs / Stock execution | 4436 | 2629 | No |
| 12791 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-3387 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5233 | 11823 | No |
| 12829 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-3483 | Topological data analysis / Betti persistence / Stock pairs | 2989 | 9705 | No |
| 12945 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-3771 | Delay differential equations / Controlled ODEs / Stock execution | 4462 | 2652 | No |
| 12982 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-3867 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5258 | 11827 | No |
| 13020 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-3963 | Topological data analysis / Betti persistence / Stock pairs | 3027 | 9725 | No |
| 13136 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-4251 | Delay differential equations / Controlled ODEs / Stock execution | 4488 | 2675 | No |
| 13173 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-4347 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5283 | 11831 | No |
| 13211 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-4443 | Topological data analysis / Betti persistence / Stock pairs | 3065 | 9745 | No |
| 13327 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-4731 | Delay differential equations / Controlled ODEs / Stock execution | 4514 | 2698 | No |
| 13364 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-4827 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5308 | 11835 | No |
| 13402 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-4923 | Topological data analysis / Betti persistence / Stock pairs | 3103 | 9765 | No |
| 13518 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-5211 | Delay differential equations / Controlled ODEs / Stock execution | 4540 | 2721 | No |
| 13555 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-5307 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5333 | 11839 | No |
| 13593 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-5403 | Topological data analysis / Betti persistence / Stock pairs | 3141 | 9785 | No |
| 13709 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-5691 | Delay differential equations / Controlled ODEs / Stock execution | 4566 | 2744 | No |
| 13746 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-5787 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5358 | 11843 | No |
| 13784 | Multi-Scale Scholarly Leveraged ETF Rebalancer Eng-5883 | Topological data analysis / Betti persistence / Stock pairs | 3179 | 9805 | No |
