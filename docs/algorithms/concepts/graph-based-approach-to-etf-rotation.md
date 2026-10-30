# Graph-based approach to ETF rotation

**Concept page** · shared by **63** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #5,093) ·
researched 2026-10-30

| | |
|---|---|
| Task | ETF rotation |
| Method | Graph / network models |
| Fit with this project | ⏳ reference only · background, nothing to build now |
| Useful for volatility-ai | **Reference only.** A network model could rank or weight the rotation, but no study shows it beating plain relative strength with an absolute-momentum filter; background until X3 is measured. |
| Implemented in volatility-ai | `tools/rotation.py` runs relative strength (X3), defensive rotation (X2), dual momentum (RK3) and HRP weights (A5); Faber's moving-average filter is built (`tactical_allocation`, C-E2, RK17). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | X3, X2, RK3, RK17, C-E2, A5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Graph Scholarly ETF
Rotation Model Eng-395") combine a method word, "Scholarly", a task and
a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Rank a defined ETF universe by momentum, trend or risk and rotate on a
fixed schedule, with a defensive asset and a cost model. The graph-based
version represents assets as a network of correlation or causality links
and acts on its structure. I found no study of this method on this task.

## The CSV's description

Proposed graph-based approach to ETF rotation: Rank a defined ETF
universe using a specified momentum, trend, or risk signal and rotate
exposure on a fixed schedule, with a defined defensive allocation and
trading-cost model. This is a concept-level interpretation of the title,
not a complete trading specification: the exact model inputs/target,
calibration, entry/exit or rebalance rules, and position sizing are not
fully defined here.

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
* Networks estimated from correlations are noisy and change with the
  window.

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
| 5093 | Graph Scholarly ETF Rotation Model Eng-395 | Neural SDEs / Adversarial robustness / Stock options hedging | 10479 | 8949 | No |
| 5179 | Graph Scholarly ETF Rotation Model Eng-875 | Neural SDEs / Adversarial robustness / Stock options hedging | 10486 | 8984 | No |
| 5265 | Graph Scholarly ETF Rotation Model Eng-1355 | Neural SDEs / Adversarial robustness / Stock options hedging | 10493 | 9019 | No |
| 5351 | Graph Scholarly ETF Rotation Model Eng-1835 | Neural SDEs / Adversarial robustness / Stock options hedging | 10500 | 9054 | No |
| 5437 | Graph Scholarly ETF Rotation Model Eng-2315 | Neural SDEs / Adversarial robustness / Stock options hedging | 10507 | 9089 | No |
| 5523 | Graph Scholarly ETF Rotation Model Eng-2795 | Neural SDEs / Adversarial robustness / Stock options hedging | 10514 | 9124 | No |
| 5609 | Graph Scholarly ETF Rotation Model Eng-3275 | Neural SDEs / Adversarial robustness / Stock options hedging | 10521 | 9159 | No |
| 5695 | Graph Scholarly ETF Rotation Model Eng-3755 | Neural SDEs / Adversarial robustness / Stock options hedging | 10528 | 9194 | No |
| 5781 | Graph Scholarly ETF Rotation Model Eng-4235 | Neural SDEs / Adversarial robustness / Stock options hedging | 10535 | 9229 | No |
| 5867 | Graph Scholarly ETF Rotation Model Eng-4715 | Neural SDEs / Adversarial robustness / Stock options hedging | 10542 | 9264 | No |
| 5953 | Graph Scholarly ETF Rotation Model Eng-5195 | Neural SDEs / Adversarial robustness / Stock options hedging | 10549 | 9299 | No |
| 6039 | Graph Scholarly ETF Rotation Model Eng-5675 | Neural SDEs / Adversarial robustness / Stock options hedging | 10556 | 9334 | No |
| 7939 | Graph Scholarly ETF Rotation Model Eng-299 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7120 | 8940 | No |
| 7973 | Graph Scholarly ETF Rotation Model Eng-779 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7162 | 8975 | No |
| 8007 | Graph Scholarly ETF Rotation Model Eng-1259 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7204 | 9010 | No |
| 8041 | Graph Scholarly ETF Rotation Model Eng-1739 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7246 | 9045 | No |
| 8075 | Graph Scholarly ETF Rotation Model Eng-2219 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7288 | 9080 | No |
| 8109 | Graph Scholarly ETF Rotation Model Eng-2699 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7330 | 9115 | No |
| 8143 | Graph Scholarly ETF Rotation Model Eng-3179 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7372 | 9150 | No |
| 8177 | Graph Scholarly ETF Rotation Model Eng-3659 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7414 | 9185 | No |
| 8211 | Graph Scholarly ETF Rotation Model Eng-4139 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7456 | 9220 | No |
| 8245 | Graph Scholarly ETF Rotation Model Eng-4619 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7498 | 9255 | No |
| 8279 | Graph Scholarly ETF Rotation Model Eng-5099 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7540 | 9290 | No |
| 8313 | Graph Scholarly ETF Rotation Model Eng-5579 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7582 | 9325 | No |
| 11447 | Graph Scholarly ETF Rotation Model Eng-11 | Delay differential equations / Controlled ODEs / Stock execution | 13315 | 13332 | No |
| 11486 | Graph Scholarly ETF Rotation Model Eng-107 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10976 | 11028 | No |
| 11523 | Graph Scholarly ETF Rotation Model Eng-203 | Topological data analysis / Betti persistence / Stock pairs | 11684 | 12219 | No |
| 11638 | Graph Scholarly ETF Rotation Model Eng-491 | Delay differential equations / Controlled ODEs / Stock execution | 13327 | 13346 | No |
| 11677 | Graph Scholarly ETF Rotation Model Eng-587 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10985 | 11047 | No |
| 11714 | Graph Scholarly ETF Rotation Model Eng-683 | Topological data analysis / Betti persistence / Stock pairs | 11709 | 12242 | No |
| 11829 | Graph Scholarly ETF Rotation Model Eng-971 | Delay differential equations / Controlled ODEs / Stock execution | 13339 | 13360 | No |
| 11868 | Graph Scholarly ETF Rotation Model Eng-1067 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10994 | 11066 | No |
| 11905 | Graph Scholarly ETF Rotation Model Eng-1163 | Topological data analysis / Betti persistence / Stock pairs | 11734 | 12265 | No |
| 12020 | Graph Scholarly ETF Rotation Model Eng-1451 | Delay differential equations / Controlled ODEs / Stock execution | 13351 | 13374 | No |
| 12059 | Graph Scholarly ETF Rotation Model Eng-1547 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11003 | 11085 | No |
| 12096 | Graph Scholarly ETF Rotation Model Eng-1643 | Topological data analysis / Betti persistence / Stock pairs | 11759 | 12288 | No |
| 12211 | Graph Scholarly ETF Rotation Model Eng-1931 | Delay differential equations / Controlled ODEs / Stock execution | 13363 | 13388 | No |
| 12250 | Graph Scholarly ETF Rotation Model Eng-2027 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11012 | 11104 | No |
| 12287 | Graph Scholarly ETF Rotation Model Eng-2123 | Topological data analysis / Betti persistence / Stock pairs | 11784 | 12311 | No |
| 12402 | Graph Scholarly ETF Rotation Model Eng-2411 | Delay differential equations / Controlled ODEs / Stock execution | 13375 | 13402 | No |
| 12441 | Graph Scholarly ETF Rotation Model Eng-2507 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11021 | 11123 | No |
| 12478 | Graph Scholarly ETF Rotation Model Eng-2603 | Topological data analysis / Betti persistence / Stock pairs | 11809 | 12334 | No |
| 12593 | Graph Scholarly ETF Rotation Model Eng-2891 | Delay differential equations / Controlled ODEs / Stock execution | 13387 | 13416 | No |
| 12632 | Graph Scholarly ETF Rotation Model Eng-2987 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11030 | 11142 | No |
| 12669 | Graph Scholarly ETF Rotation Model Eng-3083 | Topological data analysis / Betti persistence / Stock pairs | 11834 | 12357 | No |
| 12784 | Graph Scholarly ETF Rotation Model Eng-3371 | Delay differential equations / Controlled ODEs / Stock execution | 13399 | 13430 | No |
| 12823 | Graph Scholarly ETF Rotation Model Eng-3467 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11039 | 11161 | No |
| 12860 | Graph Scholarly ETF Rotation Model Eng-3563 | Topological data analysis / Betti persistence / Stock pairs | 11859 | 12380 | No |
| 12975 | Graph Scholarly ETF Rotation Model Eng-3851 | Delay differential equations / Controlled ODEs / Stock execution | 13411 | 13444 | No |
| 13014 | Graph Scholarly ETF Rotation Model Eng-3947 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11048 | 11180 | No |
| 13051 | Graph Scholarly ETF Rotation Model Eng-4043 | Topological data analysis / Betti persistence / Stock pairs | 11884 | 12403 | No |
| 13166 | Graph Scholarly ETF Rotation Model Eng-4331 | Delay differential equations / Controlled ODEs / Stock execution | 13423 | 13458 | No |
| 13205 | Graph Scholarly ETF Rotation Model Eng-4427 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11057 | 11199 | No |
| 13242 | Graph Scholarly ETF Rotation Model Eng-4523 | Topological data analysis / Betti persistence / Stock pairs | 11909 | 12426 | No |
| 13357 | Graph Scholarly ETF Rotation Model Eng-4811 | Delay differential equations / Controlled ODEs / Stock execution | 13435 | 13472 | No |
| 13396 | Graph Scholarly ETF Rotation Model Eng-4907 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11066 | 11218 | No |
| 13433 | Graph Scholarly ETF Rotation Model Eng-5003 | Topological data analysis / Betti persistence / Stock pairs | 11934 | 12449 | No |
| 13548 | Graph Scholarly ETF Rotation Model Eng-5291 | Delay differential equations / Controlled ODEs / Stock execution | 13447 | 13486 | No |
| 13587 | Graph Scholarly ETF Rotation Model Eng-5387 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11075 | 11237 | No |
| 13624 | Graph Scholarly ETF Rotation Model Eng-5483 | Topological data analysis / Betti persistence / Stock pairs | 11959 | 12472 | No |
| 13739 | Graph Scholarly ETF Rotation Model Eng-5771 | Delay differential equations / Controlled ODEs / Stock execution | 13459 | 13500 | No |
| 13778 | Graph Scholarly ETF Rotation Model Eng-5867 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11084 | 11256 | No |
| 13815 | Graph Scholarly ETF Rotation Model Eng-5963 | Topological data analysis / Betti persistence / Stock pairs | 11984 | 12495 | No |
