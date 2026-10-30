# Koopman-operator-based approach to delay-aware portfolio allocation

**Concept page** · shared by **63** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #2,513) ·
researched 2026-10-30

| | |
|---|---|
| Task | Delay-aware portfolio allocation |
| Method | Koopman operators (DMD / EDMD) |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of Koopman operators improving allocation through lagged dynamics, and the book trades one symbol. |
| Implemented in volatility-ai | Nothing; the closest is the top-K dropout turnover rule (RK216). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK216, RK366 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Koopman Scholarly Delay
Differential Allocator Eng-305") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Model delayed or lagged relationships in market variables and use the
estimated dynamics to adjust portfolio weights. The Koopman version
linearises the dynamics in a lifted feature space and forecasts with the
linear operator. I found no study of this method on this task.

## The CSV's description

Proposed Koopman-operator-based approach to delay-aware portfolio
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
* The Koopman entries in the list have no peer-reviewed trading evidence
  (RK206).

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
| 2513 | Koopman Scholarly Delay Differential Allocator Eng-305 | Rough path theory / Tensor signatures / Stock trend forecasting | 8828 | 7998 | No |
| 2568 | Koopman Scholarly Delay Differential Allocator Eng-785 | Rough path theory / Tensor signatures / Stock trend forecasting | 8864 | 8030 | No |
| 2623 | Koopman Scholarly Delay Differential Allocator Eng-1265 | Rough path theory / Tensor signatures / Stock trend forecasting | 8900 | 8062 | No |
| 2678 | Koopman Scholarly Delay Differential Allocator Eng-1745 | Rough path theory / Tensor signatures / Stock trend forecasting | 8936 | 8094 | No |
| 2733 | Koopman Scholarly Delay Differential Allocator Eng-2225 | Rough path theory / Tensor signatures / Stock trend forecasting | 8972 | 8126 | No |
| 2788 | Koopman Scholarly Delay Differential Allocator Eng-2705 | Rough path theory / Tensor signatures / Stock trend forecasting | 9008 | 8158 | No |
| 2843 | Koopman Scholarly Delay Differential Allocator Eng-3185 | Rough path theory / Tensor signatures / Stock trend forecasting | 9044 | 8190 | No |
| 2898 | Koopman Scholarly Delay Differential Allocator Eng-3665 | Rough path theory / Tensor signatures / Stock trend forecasting | 9080 | 8222 | No |
| 2953 | Koopman Scholarly Delay Differential Allocator Eng-4145 | Rough path theory / Tensor signatures / Stock trend forecasting | 9116 | 8254 | No |
| 3008 | Koopman Scholarly Delay Differential Allocator Eng-4625 | Rough path theory / Tensor signatures / Stock trend forecasting | 9152 | 8286 | No |
| 3063 | Koopman Scholarly Delay Differential Allocator Eng-5105 | Rough path theory / Tensor signatures / Stock trend forecasting | 9188 | 8318 | No |
| 3118 | Koopman Scholarly Delay Differential Allocator Eng-5585 | Rough path theory / Tensor signatures / Stock trend forecasting | 9224 | 8350 | No |
| 5059 | Koopman Scholarly Delay Differential Allocator Eng-209 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7111 | 8935 | No |
| 5145 | Koopman Scholarly Delay Differential Allocator Eng-689 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7153 | 8970 | No |
| 5231 | Koopman Scholarly Delay Differential Allocator Eng-1169 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7195 | 9005 | No |
| 5317 | Koopman Scholarly Delay Differential Allocator Eng-1649 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7237 | 9040 | No |
| 5403 | Koopman Scholarly Delay Differential Allocator Eng-2129 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7279 | 9075 | No |
| 5489 | Koopman Scholarly Delay Differential Allocator Eng-2609 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7321 | 9110 | No |
| 5575 | Koopman Scholarly Delay Differential Allocator Eng-3089 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7363 | 9145 | No |
| 5661 | Koopman Scholarly Delay Differential Allocator Eng-3569 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7405 | 9180 | No |
| 5747 | Koopman Scholarly Delay Differential Allocator Eng-4049 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7447 | 9215 | No |
| 5833 | Koopman Scholarly Delay Differential Allocator Eng-4529 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7489 | 9250 | No |
| 5919 | Koopman Scholarly Delay Differential Allocator Eng-5009 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7531 | 9285 | No |
| 6005 | Koopman Scholarly Delay Differential Allocator Eng-5489 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7573 | 9320 | No |
| 6091 | Koopman Scholarly Delay Differential Allocator Eng-5969 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7615 | 9355 | No |
| 6830 | Koopman Scholarly Delay Differential Allocator Eng-17 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 7094 | 7020 | No |
| 6876 | Koopman Scholarly Delay Differential Allocator Eng-497 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 7136 | 7052 | No |
| 6922 | Koopman Scholarly Delay Differential Allocator Eng-977 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 7178 | 7084 | No |
| 6968 | Koopman Scholarly Delay Differential Allocator Eng-1457 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 7220 | 7116 | No |
| 7014 | Koopman Scholarly Delay Differential Allocator Eng-1937 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 7262 | 7148 | No |
| 7060 | Koopman Scholarly Delay Differential Allocator Eng-2417 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 7304 | 7180 | No |
| 7106 | Koopman Scholarly Delay Differential Allocator Eng-2897 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 7346 | 7212 | No |
| 7152 | Koopman Scholarly Delay Differential Allocator Eng-3377 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 7388 | 7244 | No |
| 7198 | Koopman Scholarly Delay Differential Allocator Eng-3857 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 7430 | 7276 | No |
| 7244 | Koopman Scholarly Delay Differential Allocator Eng-4337 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 7472 | 7308 | No |
| 7290 | Koopman Scholarly Delay Differential Allocator Eng-4817 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 7514 | 7340 | No |
| 7336 | Koopman Scholarly Delay Differential Allocator Eng-5297 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 7556 | 7372 | No |
| 7382 | Koopman Scholarly Delay Differential Allocator Eng-5777 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 7598 | 7404 | No |
| 11489 | Koopman Scholarly Delay Differential Allocator Eng-113 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13851 | 12909 | No |
| 11603 | Koopman Scholarly Delay Differential Allocator Eng-401 | Graph attention / Sector contagion / Stock baskets | 12392 | 13343 | No |
| 11680 | Koopman Scholarly Delay Differential Allocator Eng-593 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13855 | 12917 | No |
| 11794 | Koopman Scholarly Delay Differential Allocator Eng-881 | Graph attention / Sector contagion / Stock baskets | 12402 | 13357 | No |
| 11871 | Koopman Scholarly Delay Differential Allocator Eng-1073 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13859 | 12925 | No |
| 11985 | Koopman Scholarly Delay Differential Allocator Eng-1361 | Graph attention / Sector contagion / Stock baskets | 12412 | 13371 | No |
| 12062 | Koopman Scholarly Delay Differential Allocator Eng-1553 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13863 | 12933 | No |
| 12176 | Koopman Scholarly Delay Differential Allocator Eng-1841 | Graph attention / Sector contagion / Stock baskets | 12422 | 13385 | No |
| 12253 | Koopman Scholarly Delay Differential Allocator Eng-2033 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13867 | 12941 | No |
| 12367 | Koopman Scholarly Delay Differential Allocator Eng-2321 | Graph attention / Sector contagion / Stock baskets | 12432 | 13399 | No |
| 12444 | Koopman Scholarly Delay Differential Allocator Eng-2513 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13871 | 12949 | No |
| 12558 | Koopman Scholarly Delay Differential Allocator Eng-2801 | Graph attention / Sector contagion / Stock baskets | 12442 | 13413 | No |
| 12635 | Koopman Scholarly Delay Differential Allocator Eng-2993 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13875 | 12957 | No |
| 12749 | Koopman Scholarly Delay Differential Allocator Eng-3281 | Graph attention / Sector contagion / Stock baskets | 12452 | 13427 | No |
| 12826 | Koopman Scholarly Delay Differential Allocator Eng-3473 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13879 | 12965 | No |
| 12940 | Koopman Scholarly Delay Differential Allocator Eng-3761 | Graph attention / Sector contagion / Stock baskets | 12462 | 13441 | No |
| 13017 | Koopman Scholarly Delay Differential Allocator Eng-3953 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13883 | 12973 | No |
| 13131 | Koopman Scholarly Delay Differential Allocator Eng-4241 | Graph attention / Sector contagion / Stock baskets | 12472 | 13455 | No |
| 13208 | Koopman Scholarly Delay Differential Allocator Eng-4433 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13887 | 12981 | No |
| 13322 | Koopman Scholarly Delay Differential Allocator Eng-4721 | Graph attention / Sector contagion / Stock baskets | 12482 | 13469 | No |
| 13399 | Koopman Scholarly Delay Differential Allocator Eng-4913 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13891 | 12989 | No |
| 13513 | Koopman Scholarly Delay Differential Allocator Eng-5201 | Graph attention / Sector contagion / Stock baskets | 12492 | 13483 | No |
| 13590 | Koopman Scholarly Delay Differential Allocator Eng-5393 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13895 | 12997 | No |
| 13704 | Koopman Scholarly Delay Differential Allocator Eng-5681 | Graph attention / Sector contagion / Stock baskets | 12502 | 13497 | No |
| 13781 | Koopman Scholarly Delay Differential Allocator Eng-5873 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13899 | 13005 | No |
