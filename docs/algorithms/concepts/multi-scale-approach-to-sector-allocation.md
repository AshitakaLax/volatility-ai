# Multi-scale approach to sector allocation

**Concept page** · shared by **64** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,295) ·
researched 2026-10-30

| | |
|---|---|
| Task | Sector allocation |
| Method | Multi-scale (several horizons combined) |
| Fit with this project | 🧪 worth testing · a concrete test is below |
| Useful for volatility-ai | **Worth testing.** Multi-lookback industry momentum is the documented signal in a form X3 can already run; measure it there. |
| Implemented in volatility-ai | `tools/rotation.py --mode relative_strength` (X3) rotates across a small ETF universe, including sector momentum (RK19), with an HRP mode (A5). |
| Evidence | Evidence found (for the task; see the page for the method) |
| Related ledger entries | X3, RK19, RK3, RK7, A5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Multi-Scale Scholarly
Sector Allocation Strategy Mod-165") combine a method word, "Scholarly",
a task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Compare sector-level return, trend or risk signals and periodically
re-weight among sector funds, controlling concentration and turnover.
The multi-scale version combines signals or estimates measured over
several horizons. Industry momentum is the documented sector signal, and
averaging several lookbacks is the standard way to make it less
sensitive to one window.

## The CSV's description

Proposed multi-scale approach to sector allocation: Compare sector-level
return, trend, or risk signals and periodically adjust weights among
sector funds; concentration and turnover need to be controlled. This is
a concept-level interpretation of the title, not a complete trading
specification: the exact model inputs/target, calibration, entry/exit or
rebalance rules, and position sizing are not fully defined here.

## Evidence

* **Moskowitz & Grinblatt (1999), "Do Industries Explain Momentum?"
  *Journal of Finance* 54(4), 1249–1290:** industry momentum is highly
  profitable after controls and accounts for much of stock momentum.
  (Abstract.)
* **Keller & Keuning, Protective Asset Allocation (2016, SSRN 2759734)
  and Vigilant Asset Allocation (2017, SSRN 3002624):** ETF rotation
  with crash protection; VAA's "13612W" momentum averages the 1-, 3-, 6-
  and 12-month returns, weighting the recent ones most. Practitioner
  research. (Summaries; the SSRN texts were not opened.)

## Against, and failure modes

* Sector rotation adds turnover and taxes; the long-only half keeps only
  part of the long-short industry-momentum premium.
* More horizons mean more weights to choose, and the blend can be
  overfitted.

## Fit with volatility-ai

Built as X3 (relative-strength rotation across a small ETF universe) and
RK19 (sector momentum), neither yet measured. A sector sleeve would sit
beside the grid, not inside it.

## How to test it here

Run `tools/rotation.py --mode relative_strength` on the sector ETFs with
a 13612W score in place of one lookback, against equal weight and the
QQQ benchmark.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Moskowitz, T. J., Grinblatt, M. (1999). *Journal of Finance* 54(4),
  1249–1290. Abstract.
* Keller, W. J., Keuning, J. W. (2016, 2017). "Protective Asset
  Allocation" (SSRN 2759734); "Vigilant Asset Allocation" (SSRN
  3002624). Summaries.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 1295 | Multi-Scale Scholarly Sector Allocation Strategy Mod-165 | Rough path theory / Tensor signatures / Stock trend forecasting | 5636 | 2287 | No |
| 1308 | Multi-Scale Scholarly Sector Allocation Strategy Mod-645 | Rough path theory / Tensor signatures / Stock trend forecasting | 5643 | 2310 | No |
| 1321 | Multi-Scale Scholarly Sector Allocation Strategy Mod-1125 | Rough path theory / Tensor signatures / Stock trend forecasting | 5650 | 2333 | No |
| 1334 | Multi-Scale Scholarly Sector Allocation Strategy Mod-1605 | Rough path theory / Tensor signatures / Stock trend forecasting | 5657 | 2356 | No |
| 1347 | Multi-Scale Scholarly Sector Allocation Strategy Mod-2085 | Rough path theory / Tensor signatures / Stock trend forecasting | 5664 | 2379 | No |
| 1360 | Multi-Scale Scholarly Sector Allocation Strategy Mod-2565 | Rough path theory / Tensor signatures / Stock trend forecasting | 5671 | 2402 | No |
| 1373 | Multi-Scale Scholarly Sector Allocation Strategy Mod-3045 | Rough path theory / Tensor signatures / Stock trend forecasting | 5678 | 2425 | No |
| 1386 | Multi-Scale Scholarly Sector Allocation Strategy Mod-3525 | Rough path theory / Tensor signatures / Stock trend forecasting | 5685 | 2448 | No |
| 3314 | Multi-Scale Scholarly Sector Allocation Strategy Mod-357 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 463 | 1891 | No |
| 3332 | Multi-Scale Scholarly Sector Allocation Strategy Mod-837 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 473 | 1901 | No |
| 3350 | Multi-Scale Scholarly Sector Allocation Strategy Mod-1317 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 483 | 1911 | No |
| 3368 | Multi-Scale Scholarly Sector Allocation Strategy Mod-1797 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 493 | 1921 | No |
| 3386 | Multi-Scale Scholarly Sector Allocation Strategy Mod-2277 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 503 | 1931 | No |
| 3404 | Multi-Scale Scholarly Sector Allocation Strategy Mod-2757 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 513 | 1941 | No |
| 3422 | Multi-Scale Scholarly Sector Allocation Strategy Mod-3237 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 523 | 1951 | No |
| 3440 | Multi-Scale Scholarly Sector Allocation Strategy Mod-3717 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 533 | 1961 | No |
| 3966 | Multi-Scale Scholarly Sector Allocation Strategy Sys-75 | Neural SDEs / Adversarial robustness / Stock options hedging | 8326 | 2802 | No |
| 4052 | Multi-Scale Scholarly Sector Allocation Strategy Sys-555 | Neural SDEs / Adversarial robustness / Stock options hedging | 8366 | 2808 | No |
| 4138 | Multi-Scale Scholarly Sector Allocation Strategy Sys-1035 | Neural SDEs / Adversarial robustness / Stock options hedging | 8406 | 2814 | No |
| 4224 | Multi-Scale Scholarly Sector Allocation Strategy Sys-1515 | Neural SDEs / Adversarial robustness / Stock options hedging | 8446 | 2820 | No |
| 4310 | Multi-Scale Scholarly Sector Allocation Strategy Sys-1995 | Neural SDEs / Adversarial robustness / Stock options hedging | 8486 | 2826 | No |
| 4323 | Multi-Scale Scholarly Sector Allocation Strategy Mod-69 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6748 | 3664 | No |
| 4408 | Multi-Scale Scholarly Sector Allocation Strategy Mod-549 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6790 | 3759 | No |
| 4493 | Multi-Scale Scholarly Sector Allocation Strategy Mod-1029 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6832 | 3854 | No |
| 4578 | Multi-Scale Scholarly Sector Allocation Strategy Mod-1509 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6874 | 3949 | No |
| 4663 | Multi-Scale Scholarly Sector Allocation Strategy Mod-1989 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6916 | 4044 | No |
| 4748 | Multi-Scale Scholarly Sector Allocation Strategy Mod-2469 | Geometric deep learning / Riemannian metrics / Stock risk parity | 6958 | 4139 | No |
| 4833 | Multi-Scale Scholarly Sector Allocation Strategy Mod-2949 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7000 | 4234 | No |
| 4918 | Multi-Scale Scholarly Sector Allocation Strategy Mod-3429 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7042 | 4329 | No |
| 5003 | Multi-Scale Scholarly Sector Allocation Strategy Mod-3909 | Geometric deep learning / Riemannian metrics / Stock risk parity | 7084 | 4424 | No |
| 7550 | Multi-Scale Scholarly Sector Allocation Strategy Sys-459 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2237 | 3347 | No |
| 7581 | Multi-Scale Scholarly Sector Allocation Strategy Sys-939 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2284 | 3442 | No |
| 7612 | Multi-Scale Scholarly Sector Allocation Strategy Sys-1419 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2331 | 3537 | No |
| 7643 | Multi-Scale Scholarly Sector Allocation Strategy Sys-1899 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 2378 | 3632 | No |
| 7665 | Multi-Scale Scholarly Sector Allocation Strategy Mod-261 | Graph attention / Sector contagion / Stock baskets | 757 | 1193 | No |
| 7697 | Multi-Scale Scholarly Sector Allocation Strategy Mod-741 | Graph attention / Sector contagion / Stock baskets | 767 | 1217 | No |
| 7729 | Multi-Scale Scholarly Sector Allocation Strategy Mod-1221 | Graph attention / Sector contagion / Stock baskets | 777 | 1241 | No |
| 7761 | Multi-Scale Scholarly Sector Allocation Strategy Mod-1701 | Graph attention / Sector contagion / Stock baskets | 787 | 1265 | No |
| 7793 | Multi-Scale Scholarly Sector Allocation Strategy Mod-2181 | Graph attention / Sector contagion / Stock baskets | 797 | 1289 | No |
| 7825 | Multi-Scale Scholarly Sector Allocation Strategy Mod-2661 | Graph attention / Sector contagion / Stock baskets | 807 | 1313 | No |
| 7857 | Multi-Scale Scholarly Sector Allocation Strategy Mod-3141 | Graph attention / Sector contagion / Stock baskets | 817 | 1337 | No |
| 7889 | Multi-Scale Scholarly Sector Allocation Strategy Mod-3621 | Graph attention / Sector contagion / Stock baskets | 827 | 1361 | No |
| 8421 | Multi-Scale Scholarly Sector ETF Allocator Ver-12 | Persistence landscapes / Topological data analysis / Equity index | 2055 | 2855 | No |
| 8450 | Multi-Scale Scholarly Sector ETF Allocator Ver-112 | Persistence landscapes / Topological data analysis / Equity index | 9892 | 12503 | No |
| 9140 | Multi-Scale Scholarly Sector Allocation Strategy Sys-171 | Delay differential equations / Controlled ODEs / Stock execution | 3928 | 1088 | No |
| 9179 | Multi-Scale Scholarly Sector Allocation Strategy Sys-267 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4719 | 10784 | No |
| 9215 | Multi-Scale Scholarly Sector Allocation Strategy Sys-363 | Topological data analysis / Betti persistence / Stock pairs | 2228 | 6612 | No |
| 9327 | Multi-Scale Scholarly Sector Allocation Strategy Sys-651 | Delay differential equations / Controlled ODEs / Stock execution | 3957 | 1112 | No |
| 9366 | Multi-Scale Scholarly Sector Allocation Strategy Sys-747 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4750 | 10807 | No |
| 9402 | Multi-Scale Scholarly Sector Allocation Strategy Sys-843 | Topological data analysis / Betti persistence / Stock pairs | 2275 | 6648 | No |
| 9514 | Multi-Scale Scholarly Sector Allocation Strategy Sys-1131 | Delay differential equations / Controlled ODEs / Stock execution | 3986 | 1136 | No |
| 9553 | Multi-Scale Scholarly Sector Allocation Strategy Sys-1227 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4781 | 10830 | No |
| 9589 | Multi-Scale Scholarly Sector Allocation Strategy Sys-1323 | Topological data analysis / Betti persistence / Stock pairs | 2322 | 6684 | No |
| 9701 | Multi-Scale Scholarly Sector Allocation Strategy Sys-1611 | Delay differential equations / Controlled ODEs / Stock execution | 4015 | 1160 | No |
| 9740 | Multi-Scale Scholarly Sector Allocation Strategy Sys-1707 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 4812 | 10853 | No |
| 9776 | Multi-Scale Scholarly Sector Allocation Strategy Sys-1803 | Topological data analysis / Betti persistence / Stock pairs | 2369 | 6720 | No |
| 10033 | Multi-Scale Scholarly Sector Allocation Strategy Mod-453 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7850 | 7757 | No |
| 10224 | Multi-Scale Scholarly Sector Allocation Strategy Mod-933 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7864 | 7787 | No |
| 10415 | Multi-Scale Scholarly Sector Allocation Strategy Mod-1413 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7878 | 7817 | No |
| 10606 | Multi-Scale Scholarly Sector Allocation Strategy Mod-1893 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7892 | 7847 | No |
| 10797 | Multi-Scale Scholarly Sector Allocation Strategy Mod-2373 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7906 | 7877 | No |
| 10988 | Multi-Scale Scholarly Sector Allocation Strategy Mod-2853 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7920 | 7907 | No |
| 11179 | Multi-Scale Scholarly Sector Allocation Strategy Mod-3333 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7934 | 7937 | No |
| 11370 | Multi-Scale Scholarly Sector Allocation Strategy Mod-3813 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 7948 | 7967 | No |
