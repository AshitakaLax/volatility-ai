# Variational approach to ETF rotation

**Concept page** · shared by **10** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #3,780) ·
researched 2026-10-30

| | |
|---|---|
| Task | ETF rotation |
| Method | Variational inference / variational autoencoders |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of variational models improving ETF rotation over relative strength with an absolute filter (X3, RK3). |
| Implemented in volatility-ai | `tools/rotation.py` runs relative strength (X3), defensive rotation (X2), dual momentum (RK3) and HRP weights (A5); Faber's moving-average filter is built (`tactical_allocation`, C-E2, RK17). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | X3, X2, RK3, RK17, C-E2, A5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Variational Scholarly ETF
Rotation Model Ref-55") combine a method word, "Scholarly", a task and a
serial number, and the rows' references are software libraries or papers
the CSV's own review calls unrelated. There is no specific algorithm
behind each name to research, so this page researches what the members
share: the task, done with the method.

## In one paragraph

Rank a defined ETF universe by momentum, trend or risk and rotate on a
fixed schedule, with a defensive asset and a cost model. The variational
version learns latent factors or distributions with variational
inference. I found no study of this method on this task.

## The CSV's description

Proposed variational approach to ETF rotation: Rank a defined ETF
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
* Latent factors from a VAE are unstable across refits; no trading
  evidence found.

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
| 3780 | Variational Scholarly ETF Rotation Model Ref-55 | Neural SDEs / Adversarial robustness / Stock options hedging | 9737 | 5615 | No |
| 3866 | Variational Scholarly ETF Rotation Model Ref-535 | Neural SDEs / Adversarial robustness / Stock options hedging | 9743 | 5626 | No |
| 7484 | Variational Scholarly ETF Rotation Model Ref-439 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 8271 | 3120 | No |
| 7518 | Variational Scholarly ETF Rotation Model Ref-919 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 8312 | 3237 | No |
| 8735 | Variational Scholarly ETF Rotation Model Ref-151 | Delay differential equations / Controlled ODEs / Stock execution | 3869 | 1018 | No |
| 8773 | Variational Scholarly ETF Rotation Model Ref-247 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12524 | 12541 | No |
| 8810 | Variational Scholarly ETF Rotation Model Ref-343 | Topological data analysis / Betti persistence / Stock pairs | 2150 | 3095 | No |
| 8926 | Variational Scholarly ETF Rotation Model Ref-631 | Delay differential equations / Controlled ODEs / Stock execution | 3896 | 1053 | No |
| 8964 | Variational Scholarly ETF Rotation Model Ref-727 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12535 | 12554 | No |
| 9001 | Variational Scholarly ETF Rotation Model Ref-823 | Topological data analysis / Betti persistence / Stock pairs | 2182 | 3212 | No |
