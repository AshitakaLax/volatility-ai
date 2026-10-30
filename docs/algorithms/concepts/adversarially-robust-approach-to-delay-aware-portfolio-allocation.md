# Adversarially robust approach to delay-aware portfolio allocation

**Concept page** · shared by **62** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,301) ·
researched 2026-10-30

| | |
|---|---|
| Task | Delay-aware portfolio allocation |
| Method | Adversarial training |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of adversarial training improving allocation through lagged dynamics, and the book trades one symbol. |
| Implemented in volatility-ai | Nothing; the closest is the top-K dropout turnover rule (RK216). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK216, RK366 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Adversarial Scholarly Delay
Differential Allocator Mod-365") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Model delayed or lagged relationships in market variables and use the
estimated dynamics to adjust portfolio weights. The adversarially robust
version trains against worst-case perturbations of its inputs. I found
no study of this method on this task.

## The CSV's description

Proposed adversarially robust approach to delay-aware portfolio
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
* Adversarial robustness defends against manipulated inputs; market data
  are noisy, not adversarial.

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
| 1301 | Adversarial Scholarly Delay Differential Allocator Mod-365 | Rough path theory / Tensor signatures / Stock trend forecasting | 8516 | 7752 | No |
| 1314 | Adversarial Scholarly Delay Differential Allocator Mod-845 | Rough path theory / Tensor signatures / Stock trend forecasting | 8554 | 7782 | No |
| 1327 | Adversarial Scholarly Delay Differential Allocator Mod-1325 | Rough path theory / Tensor signatures / Stock trend forecasting | 8592 | 7812 | No |
| 1340 | Adversarial Scholarly Delay Differential Allocator Mod-1805 | Rough path theory / Tensor signatures / Stock trend forecasting | 8630 | 7842 | No |
| 1353 | Adversarial Scholarly Delay Differential Allocator Mod-2285 | Rough path theory / Tensor signatures / Stock trend forecasting | 8668 | 7872 | No |
| 1366 | Adversarial Scholarly Delay Differential Allocator Mod-2765 | Rough path theory / Tensor signatures / Stock trend forecasting | 8706 | 7902 | No |
| 1379 | Adversarial Scholarly Delay Differential Allocator Mod-3245 | Rough path theory / Tensor signatures / Stock trend forecasting | 8744 | 7932 | No |
| 1392 | Adversarial Scholarly Delay Differential Allocator Mod-3725 | Rough path theory / Tensor signatures / Stock trend forecasting | 8782 | 7962 | No |
| 3305 | Adversarial Scholarly Delay Differential Allocator Mod-77 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6749 | 6740 | No |
| 3323 | Adversarial Scholarly Delay Differential Allocator Mod-557 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6791 | 6774 | No |
| 3341 | Adversarial Scholarly Delay Differential Allocator Mod-1037 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6833 | 6808 | No |
| 3359 | Adversarial Scholarly Delay Differential Allocator Mod-1517 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6875 | 6842 | No |
| 3377 | Adversarial Scholarly Delay Differential Allocator Mod-1997 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6917 | 6876 | No |
| 3395 | Adversarial Scholarly Delay Differential Allocator Mod-2477 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6959 | 6910 | No |
| 3413 | Adversarial Scholarly Delay Differential Allocator Mod-2957 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 7001 | 6944 | No |
| 3431 | Adversarial Scholarly Delay Differential Allocator Mod-3437 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 7043 | 6978 | No |
| 3449 | Adversarial Scholarly Delay Differential Allocator Mod-3917 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 7085 | 7012 | No |
| 3957 | Adversarial Scholarly Delay Differential Allocator Sys-35 | Neural SDEs / Adversarial robustness / Stock options hedging | 10391 | 8470 | No |
| 4043 | Adversarial Scholarly Delay Differential Allocator Sys-515 | Neural SDEs / Adversarial robustness / Stock options hedging | 10395 | 8505 | No |
| 4129 | Adversarial Scholarly Delay Differential Allocator Sys-995 | Neural SDEs / Adversarial robustness / Stock options hedging | 10399 | 8540 | No |
| 4215 | Adversarial Scholarly Delay Differential Allocator Sys-1475 | Neural SDEs / Adversarial robustness / Stock options hedging | 10403 | 8575 | No |
| 4301 | Adversarial Scholarly Delay Differential Allocator Sys-1955 | Neural SDEs / Adversarial robustness / Stock options hedging | 10407 | 8610 | No |
| 4361 | Adversarial Scholarly Delay Differential Allocator Mod-269 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6766 | 8632 | No |
| 4446 | Adversarial Scholarly Delay Differential Allocator Mod-749 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6808 | 8669 | No |
| 4531 | Adversarial Scholarly Delay Differential Allocator Mod-1229 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6850 | 8706 | No |
| 4616 | Adversarial Scholarly Delay Differential Allocator Mod-1709 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6892 | 8743 | No |
| 4701 | Adversarial Scholarly Delay Differential Allocator Mod-2189 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6934 | 8780 | No |
| 4786 | Adversarial Scholarly Delay Differential Allocator Mod-2669 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6976 | 8817 | No |
| 4871 | Adversarial Scholarly Delay Differential Allocator Mod-3149 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7018 | 8854 | No |
| 4956 | Adversarial Scholarly Delay Differential Allocator Mod-3629 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7060 | 8891 | No |
| 7546 | Adversarial Scholarly Delay Differential Allocator Sys-419 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6614 | 8498 | No |
| 7577 | Adversarial Scholarly Delay Differential Allocator Sys-899 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6653 | 8533 | No |
| 7608 | Adversarial Scholarly Delay Differential Allocator Sys-1379 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6692 | 8568 | No |
| 7639 | Adversarial Scholarly Delay Differential Allocator Sys-1859 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6731 | 8603 | No |
| 7679 | Adversarial Scholarly Delay Differential Allocator Mod-461 | Graph attention / Sector contagion / Stock baskets | 12324 | 13229 | No |
| 7711 | Adversarial Scholarly Delay Differential Allocator Mod-941 | Graph attention / Sector contagion / Stock baskets | 12332 | 13243 | No |
| 7743 | Adversarial Scholarly Delay Differential Allocator Mod-1421 | Graph attention / Sector contagion / Stock baskets | 12340 | 13257 | No |
| 7775 | Adversarial Scholarly Delay Differential Allocator Mod-1901 | Graph attention / Sector contagion / Stock baskets | 12348 | 13271 | No |
| 7807 | Adversarial Scholarly Delay Differential Allocator Mod-2381 | Graph attention / Sector contagion / Stock baskets | 12356 | 13285 | No |
| 7839 | Adversarial Scholarly Delay Differential Allocator Mod-2861 | Graph attention / Sector contagion / Stock baskets | 12364 | 13299 | No |
| 7871 | Adversarial Scholarly Delay Differential Allocator Mod-3341 | Graph attention / Sector contagion / Stock baskets | 12372 | 13313 | No |
| 7903 | Adversarial Scholarly Delay Differential Allocator Mod-3821 | Graph attention / Sector contagion / Stock baskets | 12380 | 13327 | No |
| 9123 | Adversarial Scholarly Delay Differential Allocator Sys-131 | Delay differential equations / Controlled ODEs / Stock execution | 13191 | 13161 | No |
| 9162 | Adversarial Scholarly Delay Differential Allocator Sys-227 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10878 | 10782 | No |
| 9200 | Adversarial Scholarly Delay Differential Allocator Sys-323 | Topological data analysis / Betti persistence / Stock pairs | 11354 | 11937 | No |
| 9310 | Adversarial Scholarly Delay Differential Allocator Sys-611 | Delay differential equations / Controlled ODEs / Stock execution | 13197 | 13175 | No |
| 9349 | Adversarial Scholarly Delay Differential Allocator Sys-707 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10886 | 10805 | No |
| 9387 | Adversarial Scholarly Delay Differential Allocator Sys-803 | Topological data analysis / Betti persistence / Stock pairs | 11380 | 11960 | No |
| 9497 | Adversarial Scholarly Delay Differential Allocator Sys-1091 | Delay differential equations / Controlled ODEs / Stock execution | 13203 | 13189 | No |
| 9536 | Adversarial Scholarly Delay Differential Allocator Sys-1187 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10894 | 10828 | No |
| 9574 | Adversarial Scholarly Delay Differential Allocator Sys-1283 | Topological data analysis / Betti persistence / Stock pairs | 11406 | 11983 | No |
| 9684 | Adversarial Scholarly Delay Differential Allocator Sys-1571 | Delay differential equations / Controlled ODEs / Stock execution | 13209 | 13203 | No |
| 9723 | Adversarial Scholarly Delay Differential Allocator Sys-1667 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10902 | 10851 | No |
| 9761 | Adversarial Scholarly Delay Differential Allocator Sys-1763 | Topological data analysis / Betti persistence / Stock pairs | 11432 | 12006 | No |
| 9919 | Adversarial Scholarly Delay Differential Allocator Mod-173 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13811 | 12860 | No |
| 10110 | Adversarial Scholarly Delay Differential Allocator Mod-653 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13816 | 12866 | No |
| 10301 | Adversarial Scholarly Delay Differential Allocator Mod-1133 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13821 | 12872 | No |
| 10492 | Adversarial Scholarly Delay Differential Allocator Mod-1613 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13826 | 12878 | No |
| 10683 | Adversarial Scholarly Delay Differential Allocator Mod-2093 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13831 | 12884 | No |
| 10874 | Adversarial Scholarly Delay Differential Allocator Mod-2573 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13836 | 12890 | No |
| 11065 | Adversarial Scholarly Delay Differential Allocator Mod-3053 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13841 | 12896 | No |
| 11256 | Adversarial Scholarly Delay Differential Allocator Mod-3533 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13846 | 12902 | No |
