# Multi-scale approach to ETF rotation

**Concept page** · shared by **67** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #5,050) ·
researched 2026-10-30

| | |
|---|---|
| Task | ETF rotation |
| Method | Multi-scale (several horizons combined) |
| Fit with this project | 🧪 worth testing · a concrete test is below |
| Useful for volatility-ai | **Worth testing.** 13612W-style multi-lookback momentum (Keller and Keuning) is the documented refinement of single-lookback rotation; X3 can run it. |
| Implemented in volatility-ai | `tools/rotation.py` runs relative strength (X3), defensive rotation (X2), dual momentum (RK3) and HRP weights (A5); Faber's moving-average filter is built (`tactical_allocation`, C-E2, RK17). |
| Evidence | Evidence found (for the task; see the page for the method) |
| Related ledger entries | X3, X2, RK3, RK17, C-E2, A5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Multi-Scale Scholarly ETF
Rotation Model Eng-155") combine a method word, "Scholarly", a task and
a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Rank a defined ETF universe by momentum, trend or risk and rotate on a
fixed schedule, with a defensive asset and a cost model. The multi-scale
version combines signals or estimates measured over several horizons.
Averaging several lookbacks is the documented refinement: Keller and
Keuning's rules weight 1-, 3-, 6- and 12-month returns and add a
crash-protection filter.

## The CSV's description

Proposed multi-scale approach to ETF rotation: Rank a defined ETF
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
* **Keller & Keuning, Protective Asset Allocation (2016, SSRN 2759734)
  and Vigilant Asset Allocation (2017, SSRN 3002624):** ETF rotation
  with crash protection; VAA's "13612W" momentum averages the 1-, 3-, 6-
  and 12-month returns, weighting the recent ones most. Practitioner
  research. (Summaries; the SSRN texts were not opened.)

## Against, and failure modes

* Rotation results depend heavily on the universe and the rebalance day;
  many published variants are fitted on the same few decades.
* Momentum-based rotation lags turning points and whipsaws in sideways
  markets.
* More horizons mean more weights to choose, and the blend can be
  overfitted.

## Fit with volatility-ai

Built as X3 (relative-strength rotation), X2 (defensive rotation), RK3
(dual momentum) and C-E2 (Faber TAA), none yet measured. A rotation
sleeve sits beside the TQQQ grid.

## How to test it here

Add a 13612W score option to X3 and compare it with the single 12-month
lookback on the same universe and dates.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Faber, M. T. (2007). "A Quantitative Approach to Tactical Asset
  Allocation." *Journal of Wealth Management*. Summaries; see RK17.
* Antonacci, G. (2017). "Risk Premia Harvesting Through Dual Momentum."
  See RK3.
* Keller, W. J., Keuning, J. W. (2016, 2017). "Protective Asset
  Allocation" (SSRN 2759734); "Vigilant Asset Allocation" (SSRN
  3002624). Summaries.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 5050 | Multi-Scale Scholarly ETF Rotation Model Eng-155 | Neural SDEs / Adversarial robustness / Stock options hedging | 10476 | 8932 | No |
| 5136 | Multi-Scale Scholarly ETF Rotation Model Eng-635 | Neural SDEs / Adversarial robustness / Stock options hedging | 10483 | 8967 | No |
| 5222 | Multi-Scale Scholarly ETF Rotation Model Eng-1115 | Neural SDEs / Adversarial robustness / Stock options hedging | 10490 | 9002 | No |
| 5308 | Multi-Scale Scholarly ETF Rotation Model Eng-1595 | Neural SDEs / Adversarial robustness / Stock options hedging | 10497 | 9037 | No |
| 5394 | Multi-Scale Scholarly ETF Rotation Model Eng-2075 | Neural SDEs / Adversarial robustness / Stock options hedging | 10504 | 9072 | No |
| 5480 | Multi-Scale Scholarly ETF Rotation Model Eng-2555 | Neural SDEs / Adversarial robustness / Stock options hedging | 10511 | 9107 | No |
| 5566 | Multi-Scale Scholarly ETF Rotation Model Eng-3035 | Neural SDEs / Adversarial robustness / Stock options hedging | 10518 | 9142 | No |
| 5652 | Multi-Scale Scholarly ETF Rotation Model Eng-3515 | Neural SDEs / Adversarial robustness / Stock options hedging | 10525 | 9177 | No |
| 5738 | Multi-Scale Scholarly ETF Rotation Model Eng-3995 | Neural SDEs / Adversarial robustness / Stock options hedging | 10532 | 9212 | No |
| 5824 | Multi-Scale Scholarly ETF Rotation Model Eng-4475 | Neural SDEs / Adversarial robustness / Stock options hedging | 10539 | 9247 | No |
| 5910 | Multi-Scale Scholarly ETF Rotation Model Eng-4955 | Neural SDEs / Adversarial robustness / Stock options hedging | 10546 | 9282 | No |
| 5996 | Multi-Scale Scholarly ETF Rotation Model Eng-5435 | Neural SDEs / Adversarial robustness / Stock options hedging | 10553 | 9317 | No |
| 6082 | Multi-Scale Scholarly ETF Rotation Model Eng-5915 | Neural SDEs / Adversarial robustness / Stock options hedging | 10560 | 9352 | No |
| 7921 | Multi-Scale Scholarly ETF Rotation Model Eng-59 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7099 | 8925 | No |
| 7955 | Multi-Scale Scholarly ETF Rotation Model Eng-539 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7141 | 8960 | No |
| 7989 | Multi-Scale Scholarly ETF Rotation Model Eng-1019 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7183 | 8995 | No |
| 8023 | Multi-Scale Scholarly ETF Rotation Model Eng-1499 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7225 | 9030 | No |
| 8057 | Multi-Scale Scholarly ETF Rotation Model Eng-1979 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7267 | 9065 | No |
| 8091 | Multi-Scale Scholarly ETF Rotation Model Eng-2459 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7309 | 9100 | No |
| 8125 | Multi-Scale Scholarly ETF Rotation Model Eng-2939 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7351 | 9135 | No |
| 8159 | Multi-Scale Scholarly ETF Rotation Model Eng-3419 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7393 | 9170 | No |
| 8193 | Multi-Scale Scholarly ETF Rotation Model Eng-3899 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7435 | 9205 | No |
| 8227 | Multi-Scale Scholarly ETF Rotation Model Eng-4379 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7477 | 9240 | No |
| 8261 | Multi-Scale Scholarly ETF Rotation Model Eng-4859 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7519 | 9275 | No |
| 8295 | Multi-Scale Scholarly ETF Rotation Model Eng-5339 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7561 | 9310 | No |
| 8329 | Multi-Scale Scholarly ETF Rotation Model Eng-5819 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 7603 | 9345 | No |
| 8502 | Multi-Scale Scholarly ETF Rotation Model Alpha-67 | Reinforcement learning / Policy gradient / ETF arbitrage | 12514 | 12510 | No |
| 8542 | Multi-Scale Scholarly ETF Rotation Model Alpha-167 | Reinforcement learning / Policy gradient / ETF arbitrage | 10863 | 10717 | No |
| 8582 | Multi-Scale Scholarly ETF Rotation Model Alpha-267 | Reinforcement learning / Policy gradient / ETF arbitrage | 4624 | 10721 | No |
| 8622 | Multi-Scale Scholarly ETF Rotation Model Alpha-367 | Reinforcement learning / Policy gradient / ETF arbitrage | 12518 | 12525 | No |
| 8662 | Multi-Scale Scholarly ETF Rotation Model Alpha-467 | Reinforcement learning / Policy gradient / ETF arbitrage | 10868 | 10731 | No |
| 11543 | Multi-Scale Scholarly ETF Rotation Model Eng-251 | Delay differential equations / Controlled ODEs / Stock execution | 13321 | 13339 | No |
| 11578 | Multi-Scale Scholarly ETF Rotation Model Eng-347 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10980 | 11038 | No |
| 11618 | Multi-Scale Scholarly ETF Rotation Model Eng-443 | Topological data analysis / Betti persistence / Stock pairs | 11695 | 12231 | No |
| 11734 | Multi-Scale Scholarly ETF Rotation Model Eng-731 | Delay differential equations / Controlled ODEs / Stock execution | 13333 | 13353 | No |
| 11769 | Multi-Scale Scholarly ETF Rotation Model Eng-827 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10989 | 11057 | No |
| 11809 | Multi-Scale Scholarly ETF Rotation Model Eng-923 | Topological data analysis / Betti persistence / Stock pairs | 11720 | 12254 | No |
| 11925 | Multi-Scale Scholarly ETF Rotation Model Eng-1211 | Delay differential equations / Controlled ODEs / Stock execution | 13345 | 13367 | No |
| 11960 | Multi-Scale Scholarly ETF Rotation Model Eng-1307 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10998 | 11076 | No |
| 12000 | Multi-Scale Scholarly ETF Rotation Model Eng-1403 | Topological data analysis / Betti persistence / Stock pairs | 11745 | 12277 | No |
| 12116 | Multi-Scale Scholarly ETF Rotation Model Eng-1691 | Delay differential equations / Controlled ODEs / Stock execution | 13357 | 13381 | No |
| 12151 | Multi-Scale Scholarly ETF Rotation Model Eng-1787 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11007 | 11095 | No |
| 12191 | Multi-Scale Scholarly ETF Rotation Model Eng-1883 | Topological data analysis / Betti persistence / Stock pairs | 11770 | 12300 | No |
| 12307 | Multi-Scale Scholarly ETF Rotation Model Eng-2171 | Delay differential equations / Controlled ODEs / Stock execution | 13369 | 13395 | No |
| 12342 | Multi-Scale Scholarly ETF Rotation Model Eng-2267 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11016 | 11114 | No |
| 12382 | Multi-Scale Scholarly ETF Rotation Model Eng-2363 | Topological data analysis / Betti persistence / Stock pairs | 11795 | 12323 | No |
| 12498 | Multi-Scale Scholarly ETF Rotation Model Eng-2651 | Delay differential equations / Controlled ODEs / Stock execution | 13381 | 13409 | No |
| 12533 | Multi-Scale Scholarly ETF Rotation Model Eng-2747 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11025 | 11133 | No |
| 12573 | Multi-Scale Scholarly ETF Rotation Model Eng-2843 | Topological data analysis / Betti persistence / Stock pairs | 11820 | 12346 | No |
| 12689 | Multi-Scale Scholarly ETF Rotation Model Eng-3131 | Delay differential equations / Controlled ODEs / Stock execution | 13393 | 13423 | No |
| 12724 | Multi-Scale Scholarly ETF Rotation Model Eng-3227 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11034 | 11152 | No |
| 12764 | Multi-Scale Scholarly ETF Rotation Model Eng-3323 | Topological data analysis / Betti persistence / Stock pairs | 11845 | 12369 | No |
| 12880 | Multi-Scale Scholarly ETF Rotation Model Eng-3611 | Delay differential equations / Controlled ODEs / Stock execution | 13405 | 13437 | No |
| 12915 | Multi-Scale Scholarly ETF Rotation Model Eng-3707 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11043 | 11171 | No |
| 12955 | Multi-Scale Scholarly ETF Rotation Model Eng-3803 | Topological data analysis / Betti persistence / Stock pairs | 11870 | 12392 | No |
| 13071 | Multi-Scale Scholarly ETF Rotation Model Eng-4091 | Delay differential equations / Controlled ODEs / Stock execution | 13417 | 13451 | No |
| 13106 | Multi-Scale Scholarly ETF Rotation Model Eng-4187 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11052 | 11190 | No |
| 13146 | Multi-Scale Scholarly ETF Rotation Model Eng-4283 | Topological data analysis / Betti persistence / Stock pairs | 11895 | 12415 | No |
| 13262 | Multi-Scale Scholarly ETF Rotation Model Eng-4571 | Delay differential equations / Controlled ODEs / Stock execution | 13429 | 13465 | No |
| 13297 | Multi-Scale Scholarly ETF Rotation Model Eng-4667 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11061 | 11209 | No |
| 13337 | Multi-Scale Scholarly ETF Rotation Model Eng-4763 | Topological data analysis / Betti persistence / Stock pairs | 11920 | 12438 | No |
| 13453 | Multi-Scale Scholarly ETF Rotation Model Eng-5051 | Delay differential equations / Controlled ODEs / Stock execution | 13441 | 13479 | No |
| 13488 | Multi-Scale Scholarly ETF Rotation Model Eng-5147 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11070 | 11228 | No |
| 13528 | Multi-Scale Scholarly ETF Rotation Model Eng-5243 | Topological data analysis / Betti persistence / Stock pairs | 11945 | 12461 | No |
| 13644 | Multi-Scale Scholarly ETF Rotation Model Eng-5531 | Delay differential equations / Controlled ODEs / Stock execution | 13453 | 13493 | No |
| 13679 | Multi-Scale Scholarly ETF Rotation Model Eng-5627 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 11079 | 11247 | No |
| 13719 | Multi-Scale Scholarly ETF Rotation Model Eng-5723 | Topological data analysis / Betti persistence / Stock pairs | 11970 | 12484 | No |
