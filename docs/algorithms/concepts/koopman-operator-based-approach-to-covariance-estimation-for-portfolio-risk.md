# Koopman-operator-based approach to covariance estimation for portfolio risk

**Concept page** · shared by **62** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(1 of them in ranks 426–700; best-ranked member #694) ·
researched 2026-10-29

| | |
|---|---|
| Task | Covariance estimation for portfolio risk |
| Method | Koopman operators |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **Research code** in `research.catalog.concepts`: `koopman_covariance`; tested on synthetic data, not wired into the engine. Related code already here: HRP's correlation clustering is built (A5) and the minimum-variance weights use the sample covariance (Q13). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK206, RK241 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Koopman Scholarly Manifold
Covariance Estimator Sys-385") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Forecast covariance dynamics with a Koopman linearisation. I found no
study, and the Koopman entries in the list have no trading evidence
(RK206).

## The CSV's description

Proposed Koopman-operator-based approach to covariance estimation for
portfolio risk: Estimate a more stable asset-return covariance matrix
using regularization or geometric constraints, then use it for portfolio
construction, risk budgeting, or hedging. This is a concept-level
interpretation of the title, not a complete trading specification: the
exact model inputs/target, calibration, entry/exit or rebalance rules,
and position sizing are not fully defined here.

## Evidence

* **Ledoit & Wolf (2004, *Journal of Multivariate Analysis*; 2017,
  *Review of Financial Studies*):** linear and nonlinear shrinkage of
  the sample covariance, the baselines any new estimator must beat.
  (Standard references.)
* **Engle (2002), "Dynamic conditional correlation," *Journal of
  Business & Economic Statistics* 20(3):** DCC-GARCH for time-varying
  correlations. (Standard reference.)

## Against, and failure modes

* A learned or exotic estimator must beat nonlinear shrinkage out of
  sample; few studies show it.

## Fit with volatility-ai

A covariance matrix is an input to a multi-asset allocator; the engine
trades one symbol, and HRP (A5) estimates its own correlation-distance
clustering. Not a candidate until a multi-ETF book exists.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Ledoit, O., Wolf, M. (2017). "Nonlinear Shrinkage of the Covariance
  Matrix for Portfolio Selection." *Review of Financial Studies* 30(12).
  Not re-checked.
* Engle, R. (2002). *Journal of Business & Economic Statistics* 20(3).
  Not re-checked.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 694 | Koopman Scholarly Manifold Covariance Estimator Sys-385 | Rough path theory / Tensor signatures / Stock trend forecasting | 6612 | 3333 | No |
| 701 | Koopman Scholarly Manifold Covariance Estimator Sys-865 | Rough path theory / Tensor signatures / Stock trend forecasting | 6651 | 3428 | No |
| 708 | Koopman Scholarly Manifold Covariance Estimator Sys-1345 | Rough path theory / Tensor signatures / Stock trend forecasting | 6690 | 3523 | No |
| 715 | Koopman Scholarly Manifold Covariance Estimator Sys-1825 | Rough path theory / Tensor signatures / Stock trend forecasting | 6729 | 3618 | No |
| 1545 | Koopman Scholarly Manifold Covariance Estimator Sys-97 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 12001 | 12563 | No |
| 1547 | Koopman Scholarly Manifold Covariance Estimator Sys-577 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 12005 | 12575 | No |
| 1549 | Koopman Scholarly Manifold Covariance Estimator Sys-1057 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 12009 | 12587 | No |
| 1551 | Koopman Scholarly Manifold Covariance Estimator Sys-1537 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 12013 | 12599 | No |
| 3950 | Koopman Scholarly Manifold Covariance Estimator Sys-1 | Graph attention / Sector contagion / Stock baskets | 3918 | 3255 | No |
| 3988 | Koopman Scholarly Manifold Covariance Estimator Sys-193 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 10573 | 9833 | No |
| 4004 | Koopman Scholarly Manifold Covariance Estimator Sys-289 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8345 | 3315 | No |
| 4036 | Koopman Scholarly Manifold Covariance Estimator Sys-481 | Graph attention / Sector contagion / Stock baskets | 3947 | 3350 | No |
| 4074 | Koopman Scholarly Manifold Covariance Estimator Sys-673 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 10581 | 9850 | No |
| 4090 | Koopman Scholarly Manifold Covariance Estimator Sys-769 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8385 | 3410 | No |
| 4122 | Koopman Scholarly Manifold Covariance Estimator Sys-961 | Graph attention / Sector contagion / Stock baskets | 3976 | 3445 | No |
| 4160 | Koopman Scholarly Manifold Covariance Estimator Sys-1153 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 10589 | 9867 | No |
| 4176 | Koopman Scholarly Manifold Covariance Estimator Sys-1249 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8425 | 3505 | No |
| 4208 | Koopman Scholarly Manifold Covariance Estimator Sys-1441 | Graph attention / Sector contagion / Stock baskets | 4005 | 3540 | No |
| 4246 | Koopman Scholarly Manifold Covariance Estimator Sys-1633 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 10597 | 9884 | No |
| 4262 | Koopman Scholarly Manifold Covariance Estimator Sys-1729 | Geometric deep learning / Riemannian metrics / Stock risk parity | 8465 | 3600 | No |
| 4294 | Koopman Scholarly Manifold Covariance Estimator Sys-1921 | Graph attention / Sector contagion / Stock baskets | 4034 | 3635 | No |
| 4325 | Koopman Scholarly Manifold Covariance Estimator Mod-79 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 8493 | 3666 | No |
| 4345 | Koopman Scholarly Manifold Covariance Estimator Mod-175 | Neural SDEs / Adversarial robustness / Stock options hedging | 11116 | 9432 | No |
| 4376 | Koopman Scholarly Manifold Covariance Estimator Mod-367 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 13483 | 12616 | No |
| 4392 | Koopman Scholarly Manifold Covariance Estimator Mod-463 | Topological data analysis / Betti persistence / Stock pairs | 2427 | 3744 | No |
| 4410 | Koopman Scholarly Manifold Covariance Estimator Mod-559 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 8531 | 3761 | No |
| 4430 | Koopman Scholarly Manifold Covariance Estimator Mod-655 | Neural SDEs / Adversarial robustness / Stock options hedging | 11122 | 9448 | No |
| 4461 | Koopman Scholarly Manifold Covariance Estimator Mod-847 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 13487 | 12624 | No |
| 4477 | Koopman Scholarly Manifold Covariance Estimator Mod-943 | Topological data analysis / Betti persistence / Stock pairs | 2466 | 3839 | No |
| 4495 | Koopman Scholarly Manifold Covariance Estimator Mod-1039 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 8569 | 3856 | No |
| 4515 | Koopman Scholarly Manifold Covariance Estimator Mod-1135 | Neural SDEs / Adversarial robustness / Stock options hedging | 11128 | 9464 | No |
| 4546 | Koopman Scholarly Manifold Covariance Estimator Mod-1327 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 13491 | 12632 | No |
| 4562 | Koopman Scholarly Manifold Covariance Estimator Mod-1423 | Topological data analysis / Betti persistence / Stock pairs | 2505 | 3934 | No |
| 4580 | Koopman Scholarly Manifold Covariance Estimator Mod-1519 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 8607 | 3951 | No |
| 4600 | Koopman Scholarly Manifold Covariance Estimator Mod-1615 | Neural SDEs / Adversarial robustness / Stock options hedging | 11134 | 9480 | No |
| 4631 | Koopman Scholarly Manifold Covariance Estimator Mod-1807 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 13495 | 12640 | No |
| 4647 | Koopman Scholarly Manifold Covariance Estimator Mod-1903 | Topological data analysis / Betti persistence / Stock pairs | 2544 | 4029 | No |
| 4665 | Koopman Scholarly Manifold Covariance Estimator Mod-1999 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 8645 | 4046 | No |
| 4685 | Koopman Scholarly Manifold Covariance Estimator Mod-2095 | Neural SDEs / Adversarial robustness / Stock options hedging | 11140 | 9496 | No |
| 4716 | Koopman Scholarly Manifold Covariance Estimator Mod-2287 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 13499 | 12648 | No |
| 4732 | Koopman Scholarly Manifold Covariance Estimator Mod-2383 | Topological data analysis / Betti persistence / Stock pairs | 2583 | 4124 | No |
| 4750 | Koopman Scholarly Manifold Covariance Estimator Mod-2479 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 8683 | 4141 | No |
| 4770 | Koopman Scholarly Manifold Covariance Estimator Mod-2575 | Neural SDEs / Adversarial robustness / Stock options hedging | 11146 | 9512 | No |
| 4801 | Koopman Scholarly Manifold Covariance Estimator Mod-2767 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 13503 | 12656 | No |
| 4817 | Koopman Scholarly Manifold Covariance Estimator Mod-2863 | Topological data analysis / Betti persistence / Stock pairs | 2622 | 4219 | No |
| 4835 | Koopman Scholarly Manifold Covariance Estimator Mod-2959 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 8721 | 4236 | No |
| 4855 | Koopman Scholarly Manifold Covariance Estimator Mod-3055 | Neural SDEs / Adversarial robustness / Stock options hedging | 11152 | 9528 | No |
| 4886 | Koopman Scholarly Manifold Covariance Estimator Mod-3247 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 13507 | 12664 | No |
| 4902 | Koopman Scholarly Manifold Covariance Estimator Mod-3343 | Topological data analysis / Betti persistence / Stock pairs | 2661 | 4314 | No |
| 4920 | Koopman Scholarly Manifold Covariance Estimator Mod-3439 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 8759 | 4331 | No |
| 4940 | Koopman Scholarly Manifold Covariance Estimator Mod-3535 | Neural SDEs / Adversarial robustness / Stock options hedging | 11158 | 9544 | No |
| 4971 | Koopman Scholarly Manifold Covariance Estimator Mod-3727 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 13511 | 12672 | No |
| 4987 | Koopman Scholarly Manifold Covariance Estimator Mod-3823 | Topological data analysis / Betti persistence / Stock pairs | 2700 | 4409 | No |
| 5005 | Koopman Scholarly Manifold Covariance Estimator Mod-3919 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 8797 | 4426 | No |
| 7666 | Koopman Scholarly Manifold Covariance Estimator Mod-271 | Delay differential equations / Controlled ODEs / Stock execution | 4054 | 3703 | No |
| 7698 | Koopman Scholarly Manifold Covariance Estimator Mod-751 | Delay differential equations / Controlled ODEs / Stock execution | 4080 | 3798 | No |
| 7730 | Koopman Scholarly Manifold Covariance Estimator Mod-1231 | Delay differential equations / Controlled ODEs / Stock execution | 4106 | 3893 | No |
| 7762 | Koopman Scholarly Manifold Covariance Estimator Mod-1711 | Delay differential equations / Controlled ODEs / Stock execution | 4132 | 3988 | No |
| 7794 | Koopman Scholarly Manifold Covariance Estimator Mod-2191 | Delay differential equations / Controlled ODEs / Stock execution | 4158 | 4083 | No |
| 7826 | Koopman Scholarly Manifold Covariance Estimator Mod-2671 | Delay differential equations / Controlled ODEs / Stock execution | 4184 | 4178 | No |
| 7858 | Koopman Scholarly Manifold Covariance Estimator Mod-3151 | Delay differential equations / Controlled ODEs / Stock execution | 4210 | 4273 | No |
| 7890 | Koopman Scholarly Manifold Covariance Estimator Mod-3631 | Delay differential equations / Controlled ODEs / Stock execution | 4236 | 4368 | No |
