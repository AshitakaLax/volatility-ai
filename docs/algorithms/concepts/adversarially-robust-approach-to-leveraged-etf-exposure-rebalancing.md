# Adversarially robust approach to leveraged-ETF exposure rebalancing

**Concept page** · shared by **62** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #5,100) ·
researched 2026-10-30

| | |
|---|---|
| Task | Leveraged-ETF exposure rebalancing |
| Method | Adversarial training |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of adversarial training improving leveraged-ETF exposure; the sibling pages' volatility rules (V18, N7) are the ones to test. |
| Implemented in volatility-ai | The project's exposure levers are built: volatility targeting (V18), the TQQQ/QQQ leverage step-down (N7) and the SMA leverage switch (V16). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | V16, N7, V18, C-MS6, RK22 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Adversarial Scholarly
Leveraged ETF Rebalancer Eng-435") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Hold a target exposure through a leveraged ETF, rebalancing as the daily
reset and the path of returns pull the realised leverage away from
target, net of costs. The adversarially robust version trains against
worst-case perturbations of its inputs. I found no study of this method
on this task.

## The CSV's description

Proposed adversarially robust approach to leveraged-ETF exposure
rebalancing: Adjust exposure to maintain a specified leveraged-ETF
allocation or target exposure, while accounting for daily-reset effects,
path dependency, and transaction costs. This is a concept-level
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
* Adversarial robustness defends against manipulated inputs; market data
  are noisy, not adversarial.

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
| 5100 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-435 | Neural SDEs / Adversarial robustness / Stock options hedging | 8836 | 7047 | No |
| 5186 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-915 | Neural SDEs / Adversarial robustness / Stock options hedging | 8872 | 7079 | No |
| 5272 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-1395 | Neural SDEs / Adversarial robustness / Stock options hedging | 8908 | 7111 | No |
| 5358 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-1875 | Neural SDEs / Adversarial robustness / Stock options hedging | 8944 | 7143 | No |
| 5444 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-2355 | Neural SDEs / Adversarial robustness / Stock options hedging | 8980 | 7175 | No |
| 5530 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-2835 | Neural SDEs / Adversarial robustness / Stock options hedging | 9016 | 7207 | No |
| 5616 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-3315 | Neural SDEs / Adversarial robustness / Stock options hedging | 9052 | 7239 | No |
| 5702 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-3795 | Neural SDEs / Adversarial robustness / Stock options hedging | 9088 | 7271 | No |
| 5788 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-4275 | Neural SDEs / Adversarial robustness / Stock options hedging | 9124 | 7303 | No |
| 5874 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-4755 | Neural SDEs / Adversarial robustness / Stock options hedging | 9160 | 7335 | No |
| 5960 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-5235 | Neural SDEs / Adversarial robustness / Stock options hedging | 9196 | 7367 | No |
| 6046 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-5715 | Neural SDEs / Adversarial robustness / Stock options hedging | 9232 | 7399 | No |
| 7943 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-339 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2739 | 7508 | No |
| 7977 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-819 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2777 | 7512 | No |
| 8011 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-1299 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2815 | 7516 | No |
| 8045 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-1779 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2853 | 7520 | No |
| 8079 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-2259 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2891 | 7524 | No |
| 8113 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-2739 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2929 | 7528 | No |
| 8147 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-3219 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2967 | 7532 | No |
| 8181 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-3699 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 3005 | 7536 | No |
| 8215 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-4179 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 3043 | 7540 | No |
| 8249 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-4659 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 3081 | 7544 | No |
| 8283 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-5139 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 3119 | 7548 | No |
| 8317 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-5619 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 3157 | 7552 | No |
| 11464 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-51 | Delay differential equations / Controlled ODEs / Stock execution | 4261 | 2474 | No |
| 11504 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-147 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5064 | 11796 | No |
| 11538 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-243 | Topological data analysis / Betti persistence / Stock pairs | 2732 | 9570 | No |
| 11655 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-531 | Delay differential equations / Controlled ODEs / Stock execution | 4287 | 2497 | No |
| 11695 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-627 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5089 | 11800 | No |
| 11729 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-723 | Topological data analysis / Betti persistence / Stock pairs | 2770 | 9590 | No |
| 11846 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-1011 | Delay differential equations / Controlled ODEs / Stock execution | 4313 | 2520 | No |
| 11886 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-1107 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5114 | 11804 | No |
| 11920 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-1203 | Topological data analysis / Betti persistence / Stock pairs | 2808 | 9610 | No |
| 12037 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-1491 | Delay differential equations / Controlled ODEs / Stock execution | 4339 | 2543 | No |
| 12077 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-1587 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5139 | 11808 | No |
| 12111 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-1683 | Topological data analysis / Betti persistence / Stock pairs | 2846 | 9630 | No |
| 12228 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-1971 | Delay differential equations / Controlled ODEs / Stock execution | 4365 | 2566 | No |
| 12268 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-2067 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5164 | 11812 | No |
| 12302 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-2163 | Topological data analysis / Betti persistence / Stock pairs | 2884 | 9650 | No |
| 12419 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-2451 | Delay differential equations / Controlled ODEs / Stock execution | 4391 | 2589 | No |
| 12459 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-2547 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5189 | 11816 | No |
| 12493 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-2643 | Topological data analysis / Betti persistence / Stock pairs | 2922 | 9670 | No |
| 12610 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-2931 | Delay differential equations / Controlled ODEs / Stock execution | 4417 | 2612 | No |
| 12650 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-3027 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5214 | 11820 | No |
| 12684 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-3123 | Topological data analysis / Betti persistence / Stock pairs | 2960 | 9690 | No |
| 12801 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-3411 | Delay differential equations / Controlled ODEs / Stock execution | 4443 | 2635 | No |
| 12841 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-3507 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5239 | 11824 | No |
| 12875 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-3603 | Topological data analysis / Betti persistence / Stock pairs | 2998 | 9710 | No |
| 12992 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-3891 | Delay differential equations / Controlled ODEs / Stock execution | 4469 | 2658 | No |
| 13032 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-3987 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5264 | 11828 | No |
| 13066 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-4083 | Topological data analysis / Betti persistence / Stock pairs | 3036 | 9730 | No |
| 13183 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-4371 | Delay differential equations / Controlled ODEs / Stock execution | 4495 | 2681 | No |
| 13223 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-4467 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5289 | 11832 | No |
| 13257 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-4563 | Topological data analysis / Betti persistence / Stock pairs | 3074 | 9750 | No |
| 13374 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-4851 | Delay differential equations / Controlled ODEs / Stock execution | 4521 | 2704 | No |
| 13414 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-4947 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5314 | 11836 | No |
| 13448 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-5043 | Topological data analysis / Betti persistence / Stock pairs | 3112 | 9770 | No |
| 13565 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-5331 | Delay differential equations / Controlled ODEs / Stock execution | 4547 | 2727 | No |
| 13605 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-5427 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5339 | 11840 | No |
| 13639 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-5523 | Topological data analysis / Betti persistence / Stock pairs | 3150 | 9790 | No |
| 13756 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-5811 | Delay differential equations / Controlled ODEs / Stock execution | 4573 | 2750 | No |
| 13796 | Adversarial Scholarly Leveraged ETF Rebalancer Eng-5907 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5364 | 11844 | No |
