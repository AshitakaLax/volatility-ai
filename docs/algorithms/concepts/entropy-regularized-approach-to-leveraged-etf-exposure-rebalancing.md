# Entropy-regularized approach to leveraged-ETF exposure rebalancing

**Concept page** · shared by **63** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #5,057) ·
researched 2026-10-30

| | |
|---|---|
| Task | Leveraged-ETF exposure rebalancing |
| Method | Entropy regularisation |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Entropy regularisation spreads weight across assets; a single-ETF exposure has no weights to spread. |
| Implemented in volatility-ai | The project's exposure levers are built: volatility targeting (V18), the TQQQ/QQQ leverage step-down (N7) and the SMA leverage switch (V16). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | V16, N7, V18, C-MS6, RK22 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Entropic Scholarly
Leveraged ETF Rebalancer Eng-195") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Hold a target exposure through a leveraged ETF, rebalancing as the daily
reset and the path of returns pull the realised leverage away from
target, net of costs. The entropy-regularised version penalises
concentrated weights or forecasts, pulling them toward uniform. I found
no study of this method on this task.

## The CSV's description

Proposed entropy-regularized approach to leveraged-ETF exposure
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
* Entropy regularisation is shrinkage toward equal weights; it adds no
  information.

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
| 5057 | Entropic Scholarly Leveraged ETF Rebalancer Eng-195 | Neural SDEs / Adversarial robustness / Stock options hedging | 8820 | 7031 | No |
| 5143 | Entropic Scholarly Leveraged ETF Rebalancer Eng-675 | Neural SDEs / Adversarial robustness / Stock options hedging | 8856 | 7063 | No |
| 5229 | Entropic Scholarly Leveraged ETF Rebalancer Eng-1155 | Neural SDEs / Adversarial robustness / Stock options hedging | 8892 | 7095 | No |
| 5315 | Entropic Scholarly Leveraged ETF Rebalancer Eng-1635 | Neural SDEs / Adversarial robustness / Stock options hedging | 8928 | 7127 | No |
| 5401 | Entropic Scholarly Leveraged ETF Rebalancer Eng-2115 | Neural SDEs / Adversarial robustness / Stock options hedging | 8964 | 7159 | No |
| 5487 | Entropic Scholarly Leveraged ETF Rebalancer Eng-2595 | Neural SDEs / Adversarial robustness / Stock options hedging | 9000 | 7191 | No |
| 5573 | Entropic Scholarly Leveraged ETF Rebalancer Eng-3075 | Neural SDEs / Adversarial robustness / Stock options hedging | 9036 | 7223 | No |
| 5659 | Entropic Scholarly Leveraged ETF Rebalancer Eng-3555 | Neural SDEs / Adversarial robustness / Stock options hedging | 9072 | 7255 | No |
| 5745 | Entropic Scholarly Leveraged ETF Rebalancer Eng-4035 | Neural SDEs / Adversarial robustness / Stock options hedging | 9108 | 7287 | No |
| 5831 | Entropic Scholarly Leveraged ETF Rebalancer Eng-4515 | Neural SDEs / Adversarial robustness / Stock options hedging | 9144 | 7319 | No |
| 5917 | Entropic Scholarly Leveraged ETF Rebalancer Eng-4995 | Neural SDEs / Adversarial robustness / Stock options hedging | 9180 | 7351 | No |
| 6003 | Entropic Scholarly Leveraged ETF Rebalancer Eng-5475 | Neural SDEs / Adversarial robustness / Stock options hedging | 9216 | 7383 | No |
| 6089 | Entropic Scholarly Leveraged ETF Rebalancer Eng-5955 | Neural SDEs / Adversarial robustness / Stock options hedging | 9252 | 7415 | No |
| 7923 | Entropic Scholarly Leveraged ETF Rebalancer Eng-99 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2721 | 7506 | No |
| 7957 | Entropic Scholarly Leveraged ETF Rebalancer Eng-579 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2759 | 7510 | No |
| 7991 | Entropic Scholarly Leveraged ETF Rebalancer Eng-1059 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2797 | 7514 | No |
| 8025 | Entropic Scholarly Leveraged ETF Rebalancer Eng-1539 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2835 | 7518 | No |
| 8059 | Entropic Scholarly Leveraged ETF Rebalancer Eng-2019 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2873 | 7522 | No |
| 8093 | Entropic Scholarly Leveraged ETF Rebalancer Eng-2499 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2911 | 7526 | No |
| 8127 | Entropic Scholarly Leveraged ETF Rebalancer Eng-2979 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2949 | 7530 | No |
| 8161 | Entropic Scholarly Leveraged ETF Rebalancer Eng-3459 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2987 | 7534 | No |
| 8195 | Entropic Scholarly Leveraged ETF Rebalancer Eng-3939 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 3025 | 7538 | No |
| 8229 | Entropic Scholarly Leveraged ETF Rebalancer Eng-4419 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 3063 | 7542 | No |
| 8263 | Entropic Scholarly Leveraged ETF Rebalancer Eng-4899 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 3101 | 7546 | No |
| 8297 | Entropic Scholarly Leveraged ETF Rebalancer Eng-5379 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 3139 | 7550 | No |
| 8331 | Entropic Scholarly Leveraged ETF Rebalancer Eng-5859 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 3177 | 7554 | No |
| 11442 | Entropic Scholarly Leveraged ETF Rebalancer Eng-3 | Topological data analysis / Betti persistence / Stock pairs | 2713 | 9559 | No |
| 11559 | Entropic Scholarly Leveraged ETF Rebalancer Eng-291 | Delay differential equations / Controlled ODEs / Stock execution | 4274 | 2486 | No |
| 11596 | Entropic Scholarly Leveraged ETF Rebalancer Eng-387 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5076 | 11798 | No |
| 11633 | Entropic Scholarly Leveraged ETF Rebalancer Eng-483 | Topological data analysis / Betti persistence / Stock pairs | 2751 | 9579 | No |
| 11750 | Entropic Scholarly Leveraged ETF Rebalancer Eng-771 | Delay differential equations / Controlled ODEs / Stock execution | 4300 | 2509 | No |
| 11787 | Entropic Scholarly Leveraged ETF Rebalancer Eng-867 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5101 | 11802 | No |
| 11824 | Entropic Scholarly Leveraged ETF Rebalancer Eng-963 | Topological data analysis / Betti persistence / Stock pairs | 2789 | 9599 | No |
| 11941 | Entropic Scholarly Leveraged ETF Rebalancer Eng-1251 | Delay differential equations / Controlled ODEs / Stock execution | 4326 | 2532 | No |
| 11978 | Entropic Scholarly Leveraged ETF Rebalancer Eng-1347 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5126 | 11806 | No |
| 12015 | Entropic Scholarly Leveraged ETF Rebalancer Eng-1443 | Topological data analysis / Betti persistence / Stock pairs | 2827 | 9619 | No |
| 12132 | Entropic Scholarly Leveraged ETF Rebalancer Eng-1731 | Delay differential equations / Controlled ODEs / Stock execution | 4352 | 2555 | No |
| 12169 | Entropic Scholarly Leveraged ETF Rebalancer Eng-1827 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5151 | 11810 | No |
| 12206 | Entropic Scholarly Leveraged ETF Rebalancer Eng-1923 | Topological data analysis / Betti persistence / Stock pairs | 2865 | 9639 | No |
| 12323 | Entropic Scholarly Leveraged ETF Rebalancer Eng-2211 | Delay differential equations / Controlled ODEs / Stock execution | 4378 | 2578 | No |
| 12360 | Entropic Scholarly Leveraged ETF Rebalancer Eng-2307 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5176 | 11814 | No |
| 12397 | Entropic Scholarly Leveraged ETF Rebalancer Eng-2403 | Topological data analysis / Betti persistence / Stock pairs | 2903 | 9659 | No |
| 12514 | Entropic Scholarly Leveraged ETF Rebalancer Eng-2691 | Delay differential equations / Controlled ODEs / Stock execution | 4404 | 2601 | No |
| 12551 | Entropic Scholarly Leveraged ETF Rebalancer Eng-2787 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5201 | 11818 | No |
| 12588 | Entropic Scholarly Leveraged ETF Rebalancer Eng-2883 | Topological data analysis / Betti persistence / Stock pairs | 2941 | 9679 | No |
| 12705 | Entropic Scholarly Leveraged ETF Rebalancer Eng-3171 | Delay differential equations / Controlled ODEs / Stock execution | 4430 | 2624 | No |
| 12742 | Entropic Scholarly Leveraged ETF Rebalancer Eng-3267 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5226 | 11822 | No |
| 12779 | Entropic Scholarly Leveraged ETF Rebalancer Eng-3363 | Topological data analysis / Betti persistence / Stock pairs | 2979 | 9699 | No |
| 12896 | Entropic Scholarly Leveraged ETF Rebalancer Eng-3651 | Delay differential equations / Controlled ODEs / Stock execution | 4456 | 2647 | No |
| 12933 | Entropic Scholarly Leveraged ETF Rebalancer Eng-3747 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5251 | 11826 | No |
| 12970 | Entropic Scholarly Leveraged ETF Rebalancer Eng-3843 | Topological data analysis / Betti persistence / Stock pairs | 3017 | 9719 | No |
| 13087 | Entropic Scholarly Leveraged ETF Rebalancer Eng-4131 | Delay differential equations / Controlled ODEs / Stock execution | 4482 | 2670 | No |
| 13124 | Entropic Scholarly Leveraged ETF Rebalancer Eng-4227 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5276 | 11830 | No |
| 13161 | Entropic Scholarly Leveraged ETF Rebalancer Eng-4323 | Topological data analysis / Betti persistence / Stock pairs | 3055 | 9739 | No |
| 13278 | Entropic Scholarly Leveraged ETF Rebalancer Eng-4611 | Delay differential equations / Controlled ODEs / Stock execution | 4508 | 2693 | No |
| 13315 | Entropic Scholarly Leveraged ETF Rebalancer Eng-4707 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5301 | 11834 | No |
| 13352 | Entropic Scholarly Leveraged ETF Rebalancer Eng-4803 | Topological data analysis / Betti persistence / Stock pairs | 3093 | 9759 | No |
| 13469 | Entropic Scholarly Leveraged ETF Rebalancer Eng-5091 | Delay differential equations / Controlled ODEs / Stock execution | 4534 | 2716 | No |
| 13506 | Entropic Scholarly Leveraged ETF Rebalancer Eng-5187 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5326 | 11838 | No |
| 13543 | Entropic Scholarly Leveraged ETF Rebalancer Eng-5283 | Topological data analysis / Betti persistence / Stock pairs | 3131 | 9779 | No |
| 13660 | Entropic Scholarly Leveraged ETF Rebalancer Eng-5571 | Delay differential equations / Controlled ODEs / Stock execution | 4560 | 2739 | No |
| 13697 | Entropic Scholarly Leveraged ETF Rebalancer Eng-5667 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 5351 | 11842 | No |
| 13734 | Entropic Scholarly Leveraged ETF Rebalancer Eng-5763 | Topological data analysis / Betti persistence / Stock pairs | 3169 | 9799 | No |
