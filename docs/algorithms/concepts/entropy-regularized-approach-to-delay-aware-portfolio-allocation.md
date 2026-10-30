# Entropy-regularized approach to delay-aware portfolio allocation

**Concept page** · shared by **62** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,294) ·
researched 2026-10-30

| | |
|---|---|
| Task | Delay-aware portfolio allocation |
| Method | Entropy regularisation |
| Fit with this project | ⏳ reference only · background, nothing to build now |
| Useful for volatility-ai | **Reference only.** Entropy regularisation could model lagged dynamics, but the established result (trade partway toward an aim) needs a multi-asset book this project does not run; background. |
| Implemented in volatility-ai | Nothing; the closest is the top-K dropout turnover rule (RK216). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK216, RK366 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Entropic Scholarly Delay
Differential Allocator Mod-125") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Model delayed or lagged relationships in market variables and use the
estimated dynamics to adjust portfolio weights. The entropy-regularised
version penalises concentrated weights or forecasts, pulling them toward
uniform. I found no study of this method on this task.

## The CSV's description

Proposed entropy-regularized approach to delay-aware portfolio
allocation: Model delayed or lagged relationships in market variables
and use the estimated dynamics to adjust portfolio weights; the state
equations and decision rules require specification. This is a
concept-level interpretation of the title, not a complete trading
specification: the exact model inputs/target, calibration, entry/exit or
rebalance rules, and position sizing are not fully defined here.

## Evidence

* **Gârleanu & Pedersen (2013), "Dynamic Trading with Predictable
  Returns and Transaction Costs," *Journal of Finance* 68(6),
  2309–2340:** with costs, aim in front of the target and trade only
  partway toward the aim; slower-decaying signals get more weight. Net
  of costs it beat naive rules on commodity futures. (Abstract.)

## Against, and failure modes

* The title's delay-differential dynamics are unspecified; lagged
  relations between liquid ETFs are small and quickly arbitraged.
* Entropy regularisation is shrinkage toward equal weights; it adds no
  information.

## Fit with volatility-ai

Trading partway toward a moving target matters for a multi-asset book
turned over at cost. The engine trades one symbol in lots, which is
already a form of partial trading.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Gârleanu, N., Pedersen, L. H. (2013). *Journal of Finance* 68(6),
  2309–2340. doi:10.1111/jofi.12080. Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 1294 | Entropic Scholarly Delay Differential Allocator Mod-125 | Rough path theory / Tensor signatures / Stock trend forecasting | 8497 | 7736 | No |
| 1307 | Entropic Scholarly Delay Differential Allocator Mod-605 | Rough path theory / Tensor signatures / Stock trend forecasting | 8535 | 7766 | No |
| 1320 | Entropic Scholarly Delay Differential Allocator Mod-1085 | Rough path theory / Tensor signatures / Stock trend forecasting | 8573 | 7796 | No |
| 1333 | Entropic Scholarly Delay Differential Allocator Mod-1565 | Rough path theory / Tensor signatures / Stock trend forecasting | 8611 | 7826 | No |
| 1346 | Entropic Scholarly Delay Differential Allocator Mod-2045 | Rough path theory / Tensor signatures / Stock trend forecasting | 8649 | 7856 | No |
| 1359 | Entropic Scholarly Delay Differential Allocator Mod-2525 | Rough path theory / Tensor signatures / Stock trend forecasting | 8687 | 7886 | No |
| 1372 | Entropic Scholarly Delay Differential Allocator Mod-3005 | Rough path theory / Tensor signatures / Stock trend forecasting | 8725 | 7916 | No |
| 1385 | Entropic Scholarly Delay Differential Allocator Mod-3485 | Rough path theory / Tensor signatures / Stock trend forecasting | 8763 | 7946 | No |
| 1398 | Entropic Scholarly Delay Differential Allocator Mod-3965 | Rough path theory / Tensor signatures / Stock trend forecasting | 8801 | 7976 | No |
| 3313 | Entropic Scholarly Delay Differential Allocator Mod-317 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6770 | 6757 | No |
| 3331 | Entropic Scholarly Delay Differential Allocator Mod-797 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6812 | 6791 | No |
| 3349 | Entropic Scholarly Delay Differential Allocator Mod-1277 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6854 | 6825 | No |
| 3367 | Entropic Scholarly Delay Differential Allocator Mod-1757 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6896 | 6859 | No |
| 3385 | Entropic Scholarly Delay Differential Allocator Mod-2237 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6938 | 6893 | No |
| 3403 | Entropic Scholarly Delay Differential Allocator Mod-2717 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6980 | 6927 | No |
| 3421 | Entropic Scholarly Delay Differential Allocator Mod-3197 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 7022 | 6961 | No |
| 3439 | Entropic Scholarly Delay Differential Allocator Mod-3677 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 7064 | 6995 | No |
| 4000 | Entropic Scholarly Delay Differential Allocator Sys-275 | Neural SDEs / Adversarial robustness / Stock options hedging | 10393 | 8487 | No |
| 4086 | Entropic Scholarly Delay Differential Allocator Sys-755 | Neural SDEs / Adversarial robustness / Stock options hedging | 10397 | 8522 | No |
| 4172 | Entropic Scholarly Delay Differential Allocator Sys-1235 | Neural SDEs / Adversarial robustness / Stock options hedging | 10401 | 8557 | No |
| 4258 | Entropic Scholarly Delay Differential Allocator Sys-1715 | Neural SDEs / Adversarial robustness / Stock options hedging | 10405 | 8592 | No |
| 4316 | Entropic Scholarly Delay Differential Allocator Mod-29 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6745 | 8614 | No |
| 4401 | Entropic Scholarly Delay Differential Allocator Mod-509 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6787 | 8651 | No |
| 4486 | Entropic Scholarly Delay Differential Allocator Mod-989 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6829 | 8688 | No |
| 4571 | Entropic Scholarly Delay Differential Allocator Mod-1469 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6871 | 8725 | No |
| 4656 | Entropic Scholarly Delay Differential Allocator Mod-1949 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6913 | 8762 | No |
| 4741 | Entropic Scholarly Delay Differential Allocator Mod-2429 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6955 | 8799 | No |
| 4826 | Entropic Scholarly Delay Differential Allocator Mod-2909 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6997 | 8836 | No |
| 4911 | Entropic Scholarly Delay Differential Allocator Mod-3389 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7039 | 8873 | No |
| 4996 | Entropic Scholarly Delay Differential Allocator Mod-3869 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7081 | 8910 | No |
| 7532 | Entropic Scholarly Delay Differential Allocator Sys-179 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6594 | 8480 | No |
| 7563 | Entropic Scholarly Delay Differential Allocator Sys-659 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6633 | 8515 | No |
| 7594 | Entropic Scholarly Delay Differential Allocator Sys-1139 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6672 | 8550 | No |
| 7625 | Entropic Scholarly Delay Differential Allocator Sys-1619 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6711 | 8585 | No |
| 7663 | Entropic Scholarly Delay Differential Allocator Mod-221 | Graph attention / Sector contagion / Stock baskets | 12320 | 13221 | No |
| 7695 | Entropic Scholarly Delay Differential Allocator Mod-701 | Graph attention / Sector contagion / Stock baskets | 12328 | 13235 | No |
| 7727 | Entropic Scholarly Delay Differential Allocator Mod-1181 | Graph attention / Sector contagion / Stock baskets | 12336 | 13249 | No |
| 7759 | Entropic Scholarly Delay Differential Allocator Mod-1661 | Graph attention / Sector contagion / Stock baskets | 12344 | 13263 | No |
| 7791 | Entropic Scholarly Delay Differential Allocator Mod-2141 | Graph attention / Sector contagion / Stock baskets | 12352 | 13277 | No |
| 7823 | Entropic Scholarly Delay Differential Allocator Mod-2621 | Graph attention / Sector contagion / Stock baskets | 12360 | 13291 | No |
| 7855 | Entropic Scholarly Delay Differential Allocator Mod-3101 | Graph attention / Sector contagion / Stock baskets | 12368 | 13305 | No |
| 7887 | Entropic Scholarly Delay Differential Allocator Mod-3581 | Graph attention / Sector contagion / Stock baskets | 12376 | 13319 | No |
| 9104 | Entropic Scholarly Delay Differential Allocator Sys-83 | Topological data analysis / Betti persistence / Stock pairs | 11342 | 11926 | No |
| 9218 | Entropic Scholarly Delay Differential Allocator Sys-371 | Delay differential equations / Controlled ODEs / Stock execution | 13193 | 13169 | No |
| 9256 | Entropic Scholarly Delay Differential Allocator Sys-467 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10882 | 10794 | No |
| 9291 | Entropic Scholarly Delay Differential Allocator Sys-563 | Topological data analysis / Betti persistence / Stock pairs | 11368 | 11949 | No |
| 9405 | Entropic Scholarly Delay Differential Allocator Sys-851 | Delay differential equations / Controlled ODEs / Stock execution | 13199 | 13183 | No |
| 9443 | Entropic Scholarly Delay Differential Allocator Sys-947 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10890 | 10817 | No |
| 9478 | Entropic Scholarly Delay Differential Allocator Sys-1043 | Topological data analysis / Betti persistence / Stock pairs | 11394 | 11972 | No |
| 9592 | Entropic Scholarly Delay Differential Allocator Sys-1331 | Delay differential equations / Controlled ODEs / Stock execution | 13205 | 13197 | No |
| 9630 | Entropic Scholarly Delay Differential Allocator Sys-1427 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10898 | 10840 | No |
| 9665 | Entropic Scholarly Delay Differential Allocator Sys-1523 | Topological data analysis / Betti persistence / Stock pairs | 11420 | 11995 | No |
| 9779 | Entropic Scholarly Delay Differential Allocator Sys-1811 | Delay differential equations / Controlled ODEs / Stock execution | 13211 | 13211 | No |
| 9817 | Entropic Scholarly Delay Differential Allocator Sys-1907 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10906 | 10863 | No |
| 10018 | Entropic Scholarly Delay Differential Allocator Mod-413 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13813 | 12862 | No |
| 10209 | Entropic Scholarly Delay Differential Allocator Mod-893 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13818 | 12868 | No |
| 10400 | Entropic Scholarly Delay Differential Allocator Mod-1373 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13823 | 12874 | No |
| 10591 | Entropic Scholarly Delay Differential Allocator Mod-1853 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13828 | 12880 | No |
| 10782 | Entropic Scholarly Delay Differential Allocator Mod-2333 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13833 | 12886 | No |
| 10973 | Entropic Scholarly Delay Differential Allocator Mod-2813 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13838 | 12892 | No |
| 11164 | Entropic Scholarly Delay Differential Allocator Mod-3293 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13843 | 12898 | No |
| 11355 | Entropic Scholarly Delay Differential Allocator Mod-3773 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13848 | 12904 | No |
