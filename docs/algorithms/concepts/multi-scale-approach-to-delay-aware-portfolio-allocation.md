# Multi-scale approach to delay-aware portfolio allocation

**Concept page** · shared by **63** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,291) ·
researched 2026-10-30

| | |
|---|---|
| Task | Delay-aware portfolio allocation |
| Method | Multi-scale (several horizons combined) |
| Fit with this project | ⏳ reference only · background, nothing to build now |
| Useful for volatility-ai | **Reference only.** A multi-scale blend could model lagged dynamics, but the established result (trade partway toward an aim) needs a multi-asset book this project does not run; background. |
| Implemented in volatility-ai | Nothing; the closest is the top-K dropout turnover rule (RK216). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK216, RK366 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Multi-Scale Scholarly Delay
Differential Allocator Mod-5") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Model delayed or lagged relationships in market variables and use the
estimated dynamics to adjust portfolio weights. The multi-scale version
combines signals or estimates measured over several horizons. I found no
study of this method on this task.

## The CSV's description

Proposed multi-scale approach to delay-aware portfolio allocation: Model
delayed or lagged relationships in market variables and use the
estimated dynamics to adjust portfolio weights; the state equations and
decision rules require specification. This is a concept-level
interpretation of the title, not a complete trading specification: the
exact model inputs/target, calibration, entry/exit or rebalance rules,
and position sizing are not fully defined here.

## Evidence

* **Gârleanu & Pedersen (2013), "Dynamic Trading with Predictable
  Returns and Transaction Costs," *Journal of Finance* 68(6),
  2309–2340:** with costs, aim in front of the target and trade only
  partway toward the aim; slower-decaying signals get more weight. Net
  of costs it beat naive rules on commodity futures. (Abstract.)

## Against, and failure modes

* The title's delay-differential dynamics are unspecified; lagged
  relations between liquid ETFs are small and quickly arbitraged.
* More horizons mean more weights to choose, and the blend can be
  overfitted.

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
| 1291 | Multi-Scale Scholarly Delay Differential Allocator Mod-5 | Rough path theory / Tensor signatures / Stock trend forecasting | 8488 | 7729 | No |
| 1304 | Multi-Scale Scholarly Delay Differential Allocator Mod-485 | Rough path theory / Tensor signatures / Stock trend forecasting | 8526 | 7759 | No |
| 1317 | Multi-Scale Scholarly Delay Differential Allocator Mod-965 | Rough path theory / Tensor signatures / Stock trend forecasting | 8564 | 7789 | No |
| 1330 | Multi-Scale Scholarly Delay Differential Allocator Mod-1445 | Rough path theory / Tensor signatures / Stock trend forecasting | 8602 | 7819 | No |
| 1343 | Multi-Scale Scholarly Delay Differential Allocator Mod-1925 | Rough path theory / Tensor signatures / Stock trend forecasting | 8640 | 7849 | No |
| 1356 | Multi-Scale Scholarly Delay Differential Allocator Mod-2405 | Rough path theory / Tensor signatures / Stock trend forecasting | 8678 | 7879 | No |
| 1369 | Multi-Scale Scholarly Delay Differential Allocator Mod-2885 | Rough path theory / Tensor signatures / Stock trend forecasting | 8716 | 7909 | No |
| 1382 | Multi-Scale Scholarly Delay Differential Allocator Mod-3365 | Rough path theory / Tensor signatures / Stock trend forecasting | 8754 | 7939 | No |
| 1395 | Multi-Scale Scholarly Delay Differential Allocator Mod-3845 | Rough path theory / Tensor signatures / Stock trend forecasting | 8792 | 7969 | No |
| 3310 | Multi-Scale Scholarly Delay Differential Allocator Mod-197 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6759 | 6748 | No |
| 3328 | Multi-Scale Scholarly Delay Differential Allocator Mod-677 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6801 | 6782 | No |
| 3346 | Multi-Scale Scholarly Delay Differential Allocator Mod-1157 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6843 | 6816 | No |
| 3364 | Multi-Scale Scholarly Delay Differential Allocator Mod-1637 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6885 | 6850 | No |
| 3382 | Multi-Scale Scholarly Delay Differential Allocator Mod-2117 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6927 | 6884 | No |
| 3400 | Multi-Scale Scholarly Delay Differential Allocator Mod-2597 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 6969 | 6918 | No |
| 3418 | Multi-Scale Scholarly Delay Differential Allocator Mod-3077 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 7011 | 6952 | No |
| 3436 | Multi-Scale Scholarly Delay Differential Allocator Mod-3557 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 7053 | 6986 | No |
| 4021 | Multi-Scale Scholarly Delay Differential Allocator Sys-395 | Neural SDEs / Adversarial robustness / Stock options hedging | 10394 | 8496 | No |
| 4107 | Multi-Scale Scholarly Delay Differential Allocator Sys-875 | Neural SDEs / Adversarial robustness / Stock options hedging | 10398 | 8531 | No |
| 4193 | Multi-Scale Scholarly Delay Differential Allocator Sys-1355 | Neural SDEs / Adversarial robustness / Stock options hedging | 10402 | 8566 | No |
| 4279 | Multi-Scale Scholarly Delay Differential Allocator Sys-1835 | Neural SDEs / Adversarial robustness / Stock options hedging | 10406 | 8601 | No |
| 4380 | Multi-Scale Scholarly Delay Differential Allocator Mod-389 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6777 | 8642 | No |
| 4465 | Multi-Scale Scholarly Delay Differential Allocator Mod-869 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6819 | 8679 | No |
| 4550 | Multi-Scale Scholarly Delay Differential Allocator Mod-1349 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6861 | 8716 | No |
| 4635 | Multi-Scale Scholarly Delay Differential Allocator Mod-1829 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6903 | 8753 | No |
| 4720 | Multi-Scale Scholarly Delay Differential Allocator Mod-2309 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6945 | 8790 | No |
| 4805 | Multi-Scale Scholarly Delay Differential Allocator Mod-2789 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6987 | 8827 | No |
| 4890 | Multi-Scale Scholarly Delay Differential Allocator Mod-3269 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7029 | 8864 | No |
| 4975 | Multi-Scale Scholarly Delay Differential Allocator Mod-3749 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7071 | 8901 | No |
| 7539 | Multi-Scale Scholarly Delay Differential Allocator Sys-299 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6605 | 8488 | No |
| 7570 | Multi-Scale Scholarly Delay Differential Allocator Sys-779 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6644 | 8523 | No |
| 7601 | Multi-Scale Scholarly Delay Differential Allocator Sys-1259 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6683 | 8558 | No |
| 7632 | Multi-Scale Scholarly Delay Differential Allocator Sys-1739 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 6722 | 8593 | No |
| 7656 | Multi-Scale Scholarly Delay Differential Allocator Mod-101 | Graph attention / Sector contagion / Stock baskets | 12318 | 13218 | No |
| 7688 | Multi-Scale Scholarly Delay Differential Allocator Mod-581 | Graph attention / Sector contagion / Stock baskets | 12326 | 13232 | No |
| 7720 | Multi-Scale Scholarly Delay Differential Allocator Mod-1061 | Graph attention / Sector contagion / Stock baskets | 12334 | 13246 | No |
| 7752 | Multi-Scale Scholarly Delay Differential Allocator Mod-1541 | Graph attention / Sector contagion / Stock baskets | 12342 | 13260 | No |
| 7784 | Multi-Scale Scholarly Delay Differential Allocator Mod-2021 | Graph attention / Sector contagion / Stock baskets | 12350 | 13274 | No |
| 7816 | Multi-Scale Scholarly Delay Differential Allocator Mod-2501 | Graph attention / Sector contagion / Stock baskets | 12358 | 13288 | No |
| 7848 | Multi-Scale Scholarly Delay Differential Allocator Mod-2981 | Graph attention / Sector contagion / Stock baskets | 12366 | 13302 | No |
| 7880 | Multi-Scale Scholarly Delay Differential Allocator Mod-3461 | Graph attention / Sector contagion / Stock baskets | 12374 | 13316 | No |
| 7912 | Multi-Scale Scholarly Delay Differential Allocator Mod-3941 | Graph attention / Sector contagion / Stock baskets | 12382 | 13330 | No |
| 9077 | Multi-Scale Scholarly Delay Differential Allocator Sys-11 | Delay differential equations / Controlled ODEs / Stock execution | 13188 | 13158 | No |
| 9115 | Multi-Scale Scholarly Delay Differential Allocator Sys-107 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10876 | 10776 | No |
| 9151 | Multi-Scale Scholarly Delay Differential Allocator Sys-203 | Topological data analysis / Betti persistence / Stock pairs | 11348 | 11931 | No |
| 9264 | Multi-Scale Scholarly Delay Differential Allocator Sys-491 | Delay differential equations / Controlled ODEs / Stock execution | 13194 | 13172 | No |
| 9302 | Multi-Scale Scholarly Delay Differential Allocator Sys-587 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10884 | 10799 | No |
| 9338 | Multi-Scale Scholarly Delay Differential Allocator Sys-683 | Topological data analysis / Betti persistence / Stock pairs | 11374 | 11954 | No |
| 9451 | Multi-Scale Scholarly Delay Differential Allocator Sys-971 | Delay differential equations / Controlled ODEs / Stock execution | 13200 | 13186 | No |
| 9489 | Multi-Scale Scholarly Delay Differential Allocator Sys-1067 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10892 | 10822 | No |
| 9525 | Multi-Scale Scholarly Delay Differential Allocator Sys-1163 | Topological data analysis / Betti persistence / Stock pairs | 11400 | 11977 | No |
| 9638 | Multi-Scale Scholarly Delay Differential Allocator Sys-1451 | Delay differential equations / Controlled ODEs / Stock execution | 13206 | 13200 | No |
| 9676 | Multi-Scale Scholarly Delay Differential Allocator Sys-1547 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 10900 | 10845 | No |
| 9712 | Multi-Scale Scholarly Delay Differential Allocator Sys-1643 | Topological data analysis / Betti persistence / Stock pairs | 11426 | 12000 | No |
| 9825 | Multi-Scale Scholarly Delay Differential Allocator Sys-1931 | Delay differential equations / Controlled ODEs / Stock execution | 13212 | 13214 | No |
| 9969 | Multi-Scale Scholarly Delay Differential Allocator Mod-293 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13812 | 12861 | No |
| 10160 | Multi-Scale Scholarly Delay Differential Allocator Mod-773 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13817 | 12867 | No |
| 10351 | Multi-Scale Scholarly Delay Differential Allocator Mod-1253 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13822 | 12873 | No |
| 10542 | Multi-Scale Scholarly Delay Differential Allocator Mod-1733 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13827 | 12879 | No |
| 10733 | Multi-Scale Scholarly Delay Differential Allocator Mod-2213 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13832 | 12885 | No |
| 10924 | Multi-Scale Scholarly Delay Differential Allocator Mod-2693 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13837 | 12891 | No |
| 11115 | Multi-Scale Scholarly Delay Differential Allocator Mod-3173 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13842 | 12897 | No |
| 11306 | Multi-Scale Scholarly Delay Differential Allocator Mod-3653 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 13847 | 12903 | No |
