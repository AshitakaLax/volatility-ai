# Variational approach to leveraged-ETF exposure rebalancing

**Concept page** · shared by **10** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #3,839) ·
researched 2026-10-30

| | |
|---|---|
| Task | Leveraged-ETF exposure rebalancing |
| Method | Variational inference / variational autoencoders |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of variational models improving leveraged-ETF exposure; the sibling pages' volatility rules (V18, N7) are the ones to test. |
| Implemented in volatility-ai | The project's exposure levers are built: volatility targeting (V18), the TQQQ/QQQ leverage step-down (N7) and the SMA leverage switch (V16). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | V16, N7, V18, C-MS6, RK22 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Variational Scholarly
Leveraged ETF Rebalancer Ref-375") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Hold a target exposure through a leveraged ETF, rebalancing as the daily
reset and the path of returns pull the realised leverage away from
target, net of costs. The variational version learns latent factors or
distributions with variational inference. I found no study of this
method on this task.

## The CSV's description

Proposed variational approach to leveraged-ETF exposure rebalancing:
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
* Latent factors from a VAE are unstable across refits; no trading
  evidence found.

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
| 3839 | Variational Scholarly Leveraged ETF Rebalancer Ref-375 | Neural SDEs / Adversarial robustness / Stock options hedging | 8265 | 6550 | No |
| 3925 | Variational Scholarly Leveraged ETF Rebalancer Ref-855 | Neural SDEs / Adversarial robustness / Stock options hedging | 8306 | 6576 | No |
| 7472 | Variational Scholarly Leveraged ETF Rebalancer Ref-279 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2144 | 7445 | No |
| 7506 | Variational Scholarly Leveraged ETF Rebalancer Ref-759 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2176 | 7451 | No |
| 8709 | Variational Scholarly Leveraged ETF Rebalancer Ref-87 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4649 | 11754 | No |
| 8748 | Variational Scholarly Leveraged ETF Rebalancer Ref-183 | Topological data analysis / Betti persistence / Stock pairs | 2138 | 9383 | No |
| 8862 | Variational Scholarly Leveraged ETF Rebalancer Ref-471 | Delay differential equations / Controlled ODEs / Stock execution | 3886 | 2172 | No |
| 8900 | Variational Scholarly Leveraged ETF Rebalancer Ref-567 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4676 | 11758 | No |
| 8939 | Variational Scholarly Leveraged ETF Rebalancer Ref-663 | Topological data analysis / Betti persistence / Stock pairs | 2170 | 9389 | No |
| 9053 | Variational Scholarly Leveraged ETF Rebalancer Ref-951 | Delay differential equations / Controlled ODEs / Stock execution | 3913 | 2197 | No |
