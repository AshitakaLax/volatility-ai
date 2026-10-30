# Geometry-aware approach to leveraged-ETF exposure rebalancing

**Concept page** · shared by **10** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #3,817) ·
researched 2026-10-30

| | |
|---|---|
| Task | Leveraged-ETF exposure rebalancing |
| Method | Geometry-aware (Riemannian) methods |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of Riemannian geometry improving leveraged-ETF exposure; the sibling pages' volatility rules (V18, N7) are the ones to test. |
| Implemented in volatility-ai | The project's exposure levers are built: volatility targeting (V18), the TQQQ/QQQ leverage step-down (N7) and the SMA leverage switch (V16). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | V16, N7, V18, C-MS6, RK22 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Riemannian Scholarly
Leveraged ETF Rebalancer Ref-255") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Hold a target exposure through a leveraged ETF, rebalancing as the daily
reset and the path of returns pull the realised leverage away from
target, net of costs. The geometry-aware version works on the curved
space of covariance matrices or another manifold. I found no study of
this method on this task.

## The CSV's description

Proposed geometry-aware approach to leveraged-ETF exposure rebalancing:
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
* No portfolio study shows Riemannian methods beating shrinkage (RK230).

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
| 3817 | Riemannian Scholarly Leveraged ETF Rebalancer Ref-255 | Neural SDEs / Adversarial robustness / Stock options hedging | 10741 | 10171 | No |
| 3903 | Riemannian Scholarly Leveraged ETF Rebalancer Ref-735 | Neural SDEs / Adversarial robustness / Stock options hedging | 10743 | 10173 | No |
| 7463 | Riemannian Scholarly Leveraged ETF Rebalancer Ref-159 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2135 | 7443 | No |
| 7497 | Riemannian Scholarly Leveraged ETF Rebalancer Ref-639 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2167 | 7449 | No |
| 8701 | Riemannian Scholarly Leveraged ETF Rebalancer Ref-63 | Topological data analysis / Betti persistence / Stock pairs | 2130 | 9382 | No |
| 8814 | Riemannian Scholarly Leveraged ETF Rebalancer Ref-351 | Delay differential equations / Controlled ODEs / Stock execution | 3880 | 7446 | No |
| 8850 | Riemannian Scholarly Leveraged ETF Rebalancer Ref-447 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 8273 | 11757 | No |
| 8892 | Riemannian Scholarly Leveraged ETF Rebalancer Ref-543 | Topological data analysis / Betti persistence / Stock pairs | 2162 | 9388 | No |
| 9005 | Riemannian Scholarly Leveraged ETF Rebalancer Ref-831 | Delay differential equations / Controlled ODEs / Stock execution | 3907 | 7452 | No |
| 9041 | Riemannian Scholarly Leveraged ETF Rebalancer Ref-927 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 8314 | 11761 | No |
