# Entropy-regularized approach to ETF rotation

**Concept page** · shared by **63** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #5,029) ·
researched 2026-10-30

| | |
|---|---|
| Task | ETF rotation |
| Method | Entropy regularisation |
| Fit with this project | ⏳ reference only · background, nothing to build now |
| Useful for volatility-ai | **Reference only.** Entropy regularisation could rank or weight the rotation, but no study shows it beating plain relative strength with an absolute-momentum filter; background until X3 is measured. |
| Implemented in volatility-ai | `tools/rotation.py` runs relative strength (X3), defensive rotation (X2), dual momentum (RK3) and HRP weights (A5); Faber's moving-average filter is built (`tactical_allocation`, C-E2, RK17). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | X3, X2, RK3, RK17, C-E2, A5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Entropic Scholarly ETF
Rotation Model Eng-35") combine a method word, "Scholarly", a task and a
serial number, and the rows' references are software libraries or papers
the CSV's own review calls unrelated. There is no specific algorithm
behind each name to research, so this page researches what the members
share: the task, done with the method.

## In one paragraph

Rank a defined ETF universe by momentum, trend or risk and rotate on a
fixed schedule, with a defensive asset and a cost model. The
entropy-regularised version penalises concentrated weights or forecasts,
pulling them toward uniform. I found no study of this method on this
task.

## The CSV's description

Proposed entropy-regularized approach to ETF rotation: Rank a defined
ETF universe using a specified momentum, trend, or risk signal and
rotate exposure on a fixed schedule, with a defined defensive allocation
and trading-cost model. This is a concept-level interpretation of the
title, not a complete trading specification: the exact model
inputs/target, calibration, entry/exit or rebalance rules, and position
sizing are not fully defined here.

## Evidence

* **Faber (2007), "A Quantitative Approach to Tactical Asset
  Allocation":** a 10-month moving-average filter across asset classes
  gave comparable returns with much lower volatility and drawdown (see
  RK17). (Summaries.)
* **Antonacci (2012, published 2017), "Risk Premia Harvesting Through
  Dual Momentum":** relative strength picks the asset, absolute momentum
  against T-bills decides whether to hold it (see RK3). (Paper summary.)

## Against, and failure modes

* Rotation results depend heavily on the universe and the rebalance day;
  many published variants are fitted on the same few decades.
* Momentum-based rotation lags turning points and whipsaws in sideways
  markets.
* Entropy regularisation is shrinkage toward equal weights; it adds no
  information.

## Fit with volatility-ai

Built as X3 (relative-strength rotation), X2 (defensive rotation), RK3
(dual momentum) and C-E2 (Faber TAA), none yet measured. A rotation
sleeve sits beside the TQQQ grid.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Faber, M. T. (2007). "A Quantitative Approach to Tactical Asset
  Allocation." *Journal of Wealth Management*. Summaries; see RK17.
* Antonacci, G. (2017). "Risk Premia Harvesting Through Dual Momentum."
  See RK3.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 5029 | Entropic Scholarly ETF Rotation Model Eng-35 | Neural SDEs / Adversarial robustness / Stock options hedging | 10475 | 8924 | No |
| 5115 | Entropic Scholarly ETF Rotation Model Eng-515 | Neural SDEs / Adversarial robustness / Stock options hedging | 10482 | 8959 | No |
| 5201 | Entropic Scholarly ETF Rotation Model Eng-995 | Neural SDEs / Adversarial robustness / Stock options hedging | 10489 | 8994 | No |
| 5287 | Entropic Scholarly ETF Rotation Model Eng-1475 | Neural SDEs / Adversarial robustness / Stock options hedging | 10496 | 9029 | No |
| 5373 | Entropic Scholarly ETF Rotation Model Eng-1955 | Neural SDEs / Adversarial robustness / Stock options hedging | 10503 | 9064 | No |
| 5459 | Entropic Scholarly ETF Rotation Model Eng-2435 | Neural SDEs / Adversarial robustness / Stock options hedging | 10510 | 9099 | No |
| 5545 | Entropic Scholarly ETF Rotation Model Eng-2915 | Neural SDEs / Adversarial robustness / Stock options hedging | 10517 | 9134 | No |
| 5631 | Entropic Scholarly ETF Rotation Model Eng-3395 | Neural SDEs / Adversarial robustness / Stock options hedging | 10524 | 9169 | No |
| 5717 | Entropic Scholarly ETF Rotation Model Eng-3875 | Neural SDEs / Adversarial robustness / Stock options hedging | 10531 | 9204 | No |
| 5803 | Entropic Scholarly ETF Rotation Model Eng-4355 | Neural SDEs / Adversarial robustness / Stock options hedging | 10538 | 9239 | No |
| 5889 | Entropic Scholarly ETF Rotation Model Eng-4835 | Neural SDEs / Adversarial robustness / Stock options hedging | 10545 | 9274 | No |
| 5975 | Entropic Scholarly ETF Rotation Model Eng-5315 | Neural SDEs / Adversarial robustness / Stock options hedging | 10552 | 9309 | No |
| 6061 | Entropic Scholarly ETF Rotation Model Eng-5795 | Neural SDEs / Adversarial robustness / Stock options hedging | 10559 | 9344 | No |
| 7946 | Entropic Scholarly ETF Rotation Model Eng-419 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7131 | 8951 | No |
| 7980 | Entropic Scholarly ETF Rotation Model Eng-899 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7173 | 8986 | No |
| 8014 | Entropic Scholarly ETF Rotation Model Eng-1379 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7215 | 9021 | No |
| 8048 | Entropic Scholarly ETF Rotation Model Eng-1859 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7257 | 9056 | No |
| 8082 | Entropic Scholarly ETF Rotation Model Eng-2339 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7299 | 9091 | No |
| 8116 | Entropic Scholarly ETF Rotation Model Eng-2819 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7341 | 9126 | No |
| 8150 | Entropic Scholarly ETF Rotation Model Eng-3299 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7383 | 9161 | No |
| 8184 | Entropic Scholarly ETF Rotation Model Eng-3779 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7425 | 9196 | No |
| 8218 | Entropic Scholarly ETF Rotation Model Eng-4259 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7467 | 9231 | No |
| 8252 | Entropic Scholarly ETF Rotation Model Eng-4739 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7509 | 9266 | No |
| 8286 | Entropic Scholarly ETF Rotation Model Eng-5219 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7551 | 9301 | No |
| 8320 | Entropic Scholarly ETF Rotation Model Eng-5699 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7593 | 9336 | No |
| 11497 | Entropic Scholarly ETF Rotation Model Eng-131 | Delay differential equations / Controlled ODEs / Stock execution | 13319 | 13336 | No |
| 11533 | Entropic Scholarly ETF Rotation Model Eng-227 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10978 | 11033 | No |
| 11568 | Entropic Scholarly ETF Rotation Model Eng-323 | Topological data analysis / Betti persistence / Stock pairs | 11690 | 12225 | No |
| 11688 | Entropic Scholarly ETF Rotation Model Eng-611 | Delay differential equations / Controlled ODEs / Stock execution | 13331 | 13350 | No |
| 11724 | Entropic Scholarly ETF Rotation Model Eng-707 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10987 | 11052 | No |
| 11759 | Entropic Scholarly ETF Rotation Model Eng-803 | Topological data analysis / Betti persistence / Stock pairs | 11715 | 12248 | No |
| 11879 | Entropic Scholarly ETF Rotation Model Eng-1091 | Delay differential equations / Controlled ODEs / Stock execution | 13343 | 13364 | No |
| 11915 | Entropic Scholarly ETF Rotation Model Eng-1187 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10996 | 11071 | No |
| 11950 | Entropic Scholarly ETF Rotation Model Eng-1283 | Topological data analysis / Betti persistence / Stock pairs | 11740 | 12271 | No |
| 12070 | Entropic Scholarly ETF Rotation Model Eng-1571 | Delay differential equations / Controlled ODEs / Stock execution | 13355 | 13378 | No |
| 12106 | Entropic Scholarly ETF Rotation Model Eng-1667 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11005 | 11090 | No |
| 12141 | Entropic Scholarly ETF Rotation Model Eng-1763 | Topological data analysis / Betti persistence / Stock pairs | 11765 | 12294 | No |
| 12261 | Entropic Scholarly ETF Rotation Model Eng-2051 | Delay differential equations / Controlled ODEs / Stock execution | 13367 | 13392 | No |
| 12297 | Entropic Scholarly ETF Rotation Model Eng-2147 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11014 | 11109 | No |
| 12332 | Entropic Scholarly ETF Rotation Model Eng-2243 | Topological data analysis / Betti persistence / Stock pairs | 11790 | 12317 | No |
| 12452 | Entropic Scholarly ETF Rotation Model Eng-2531 | Delay differential equations / Controlled ODEs / Stock execution | 13379 | 13406 | No |
| 12488 | Entropic Scholarly ETF Rotation Model Eng-2627 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11023 | 11128 | No |
| 12523 | Entropic Scholarly ETF Rotation Model Eng-2723 | Topological data analysis / Betti persistence / Stock pairs | 11815 | 12340 | No |
| 12643 | Entropic Scholarly ETF Rotation Model Eng-3011 | Delay differential equations / Controlled ODEs / Stock execution | 13391 | 13420 | No |
| 12679 | Entropic Scholarly ETF Rotation Model Eng-3107 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11032 | 11147 | No |
| 12714 | Entropic Scholarly ETF Rotation Model Eng-3203 | Topological data analysis / Betti persistence / Stock pairs | 11840 | 12363 | No |
| 12834 | Entropic Scholarly ETF Rotation Model Eng-3491 | Delay differential equations / Controlled ODEs / Stock execution | 13403 | 13434 | No |
| 12870 | Entropic Scholarly ETF Rotation Model Eng-3587 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11041 | 11166 | No |
| 12905 | Entropic Scholarly ETF Rotation Model Eng-3683 | Topological data analysis / Betti persistence / Stock pairs | 11865 | 12386 | No |
| 13025 | Entropic Scholarly ETF Rotation Model Eng-3971 | Delay differential equations / Controlled ODEs / Stock execution | 13415 | 13448 | No |
| 13061 | Entropic Scholarly ETF Rotation Model Eng-4067 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11050 | 11185 | No |
| 13096 | Entropic Scholarly ETF Rotation Model Eng-4163 | Topological data analysis / Betti persistence / Stock pairs | 11890 | 12409 | No |
| 13216 | Entropic Scholarly ETF Rotation Model Eng-4451 | Delay differential equations / Controlled ODEs / Stock execution | 13427 | 13462 | No |
| 13252 | Entropic Scholarly ETF Rotation Model Eng-4547 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11059 | 11204 | No |
| 13287 | Entropic Scholarly ETF Rotation Model Eng-4643 | Topological data analysis / Betti persistence / Stock pairs | 11915 | 12432 | No |
| 13407 | Entropic Scholarly ETF Rotation Model Eng-4931 | Delay differential equations / Controlled ODEs / Stock execution | 13439 | 13476 | No |
| 13443 | Entropic Scholarly ETF Rotation Model Eng-5027 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11068 | 11223 | No |
| 13478 | Entropic Scholarly ETF Rotation Model Eng-5123 | Topological data analysis / Betti persistence / Stock pairs | 11940 | 12455 | No |
| 13598 | Entropic Scholarly ETF Rotation Model Eng-5411 | Delay differential equations / Controlled ODEs / Stock execution | 13451 | 13490 | No |
| 13634 | Entropic Scholarly ETF Rotation Model Eng-5507 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11077 | 11242 | No |
| 13669 | Entropic Scholarly ETF Rotation Model Eng-5603 | Topological data analysis / Betti persistence / Stock pairs | 11965 | 12478 | No |
| 13789 | Entropic Scholarly ETF Rotation Model Eng-5891 | Delay differential equations / Controlled ODEs / Stock execution | 13463 | 13504 | No |
| 13825 | Entropic Scholarly ETF Rotation Model Eng-5987 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11086 | 11261 | No |
