# Nonlinear approach to leveraged-ETF exposure rebalancing

**Concept page** · shared by **11** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #3,774) ·
researched 2026-10-30

| | |
|---|---|
| Task | Leveraged-ETF exposure rebalancing |
| Method | Nonlinear models |
| Fit with this project | ⏳ reference only · background, nothing to build now |
| Useful for volatility-ai | **Reference only.** A nonlinear model is a sound way to set leverage, but no study shows it beating the simple volatility rules already built (V18, N7); background only. |
| Implemented in volatility-ai | The project's exposure levers are built: volatility targeting (V18), the TQQQ/QQQ leverage step-down (N7) and the SMA leverage switch (V16). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | V16, N7, V18, C-MS6, RK22 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Non-Linear Scholarly
Leveraged ETF Rebalancer Ref-15") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Hold a target exposure through a leveraged ETF, rebalancing as the daily
reset and the path of returns pull the realised leverage away from
target, net of costs. The nonlinear version replaces linear rules with
nonlinear regressions or filters. I found no study of this method on
this task.

## The CSV's description

Proposed nonlinear approach to leveraged-ETF exposure rebalancing:
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
* Nonlinear fits on a few thousand daily bars overfit easily; gains over
  linear rules are usually small out of sample.

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
| 3774 | Non-Linear Scholarly Leveraged ETF Rebalancer Ref-15 | Neural SDEs / Adversarial robustness / Stock options hedging | 8236 | 6531 | No |
| 3860 | Non-Linear Scholarly Leveraged ETF Rebalancer Ref-495 | Neural SDEs / Adversarial robustness / Stock options hedging | 8277 | 6557 | No |
| 3946 | Non-Linear Scholarly Leveraged ETF Rebalancer Ref-975 | Neural SDEs / Adversarial robustness / Stock options hedging | 8318 | 6583 | No |
| 7480 | Non-Linear Scholarly Leveraged ETF Rebalancer Ref-399 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2153 | 7447 | No |
| 7514 | Non-Linear Scholarly Leveraged ETF Rebalancer Ref-879 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2185 | 7453 | No |
| 8720 | Non-Linear Scholarly Leveraged ETF Rebalancer Ref-111 | Delay differential equations / Controlled ODEs / Stock execution | 3866 | 2154 | No |
| 8756 | Non-Linear Scholarly Leveraged ETF Rebalancer Ref-207 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4657 | 11755 | No |
| 8794 | Non-Linear Scholarly Leveraged ETF Rebalancer Ref-303 | Topological data analysis / Betti persistence / Stock pairs | 2146 | 9385 | No |
| 8911 | Non-Linear Scholarly Leveraged ETF Rebalancer Ref-591 | Delay differential equations / Controlled ODEs / Stock execution | 3893 | 2179 | No |
| 8947 | Non-Linear Scholarly Leveraged ETF Rebalancer Ref-687 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4684 | 11759 | No |
| 8985 | Non-Linear Scholarly Leveraged ETF Rebalancer Ref-783 | Topological data analysis / Betti persistence / Stock pairs | 2178 | 9391 | No |
