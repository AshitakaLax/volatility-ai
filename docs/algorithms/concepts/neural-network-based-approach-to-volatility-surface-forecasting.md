# Neural-network-based approach to volatility-surface forecasting

**Concept page** · shared by **62** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,856) ·
researched 2026-10-30

| | |
|---|---|
| Task | Volatility-surface forecasting |
| Method | Neural networks |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Options are outside the owner's instrument rule; a surface forecast has nothing to trade here (the VIX regime route is RK168). |
| Implemented in volatility-ai | Option pricing and surface models are research code (`derivatives`, `options`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK168, RK240 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Neural Scholarly Volatility
Surface Forecaster Sys-205") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Forecast the implied-volatility surface across strikes and expiries for
option valuation, risk limits or hedging. The neural-network version
fits a neural network to the task. I found no study of this method on
this task.

## The CSV's description

Proposed neural-network-based approach to volatility-surface
forecasting: Forecast the implied-volatility surface across option
strikes and expirations, then use those forecasts to inform option
valuation, risk limits, or hedging. This is a concept-level
interpretation of the title, not a complete trading specification: the
exact model inputs/target, calibration, entry/exit or rebalance rules,
and position sizing are not fully defined here.

## Evidence

* **Cont & da Fonseca (2002), "Dynamics of implied volatility surfaces,"
  *Quantitative Finance* 2(1), 45–60:** a few mean-reverting factors
  drive daily moves of the S&P 500 and FTSE surfaces. (Abstract.)
* **Gonçalves & Guidolin (2006), *Journal of Business* 79(3):** the S&P
  500 implied-volatility surface moves predictably, but trading the
  forecasts earns no abnormal profit after transaction costs.
  (Abstract.)

## Against, and failure modes

* Surface dynamics are statistically predictable but did not pay after
  costs (Gonçalves & Guidolin).
* Neural forecasts on one index have not reliably beaten simple rules;
  an LSTM's stock picks were largely short-term reversal (Fischer &
  Krauss 2018, RK292).

## Fit with volatility-ai

Options are outside the instrument rule, so a surface forecast has
nothing to trade. The one route into this book is a volatility regime
input, covered by the VIX term-structure entry (RK168).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Cont, R., da Fonseca, J. (2002). *Quantitative Finance* 2(1), 45–60.
  Abstract.
* Gonçalves, S., Guidolin, M. (2006). "Predictable dynamics in the S&P
  500 index options implied volatility surface." *Journal of Business*
  79(3). Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 1856 | Neural Scholarly Volatility Surface Forecaster Sys-205 | Rough path theory / Tensor signatures / Stock trend forecasting | 9329 | 9396 | No |
| 1905 | Neural Scholarly Volatility Surface Forecaster Sys-685 | Rough path theory / Tensor signatures / Stock trend forecasting | 9345 | 9404 | No |
| 1954 | Neural Scholarly Volatility Surface Forecaster Sys-1165 | Rough path theory / Tensor signatures / Stock trend forecasting | 9361 | 9412 | No |
| 2003 | Neural Scholarly Volatility Surface Forecaster Sys-1645 | Rough path theory / Tensor signatures / Stock trend forecasting | 9377 | 9420 | No |
| 3971 | Neural Scholarly Volatility Surface Forecaster Sys-109 | Geometric deep learning / Riemannian metrics / Stock risk parity | 10069 | 9395 | No |
| 4057 | Neural Scholarly Volatility Surface Forecaster Sys-589 | Geometric deep learning / Riemannian metrics / Stock risk parity | 10080 | 9403 | No |
| 4143 | Neural Scholarly Volatility Surface Forecaster Sys-1069 | Geometric deep learning / Riemannian metrics / Stock risk parity | 10091 | 9411 | No |
| 4229 | Neural Scholarly Volatility Surface Forecaster Sys-1549 | Geometric deep learning / Riemannian metrics / Stock risk parity | 10102 | 9419 | No |
| 4374 | Neural Scholarly Volatility Surface Forecaster Mod-355 | Neural SDEs / Adversarial robustness / Stock options hedging | 9769 | 5717 | No |
| 4459 | Neural Scholarly Volatility Surface Forecaster Mod-835 | Neural SDEs / Adversarial robustness / Stock options hedging | 9775 | 5730 | No |
| 4544 | Neural Scholarly Volatility Surface Forecaster Mod-1315 | Neural SDEs / Adversarial robustness / Stock options hedging | 9781 | 5743 | No |
| 4629 | Neural Scholarly Volatility Surface Forecaster Mod-1795 | Neural SDEs / Adversarial robustness / Stock options hedging | 9787 | 5756 | No |
| 4714 | Neural Scholarly Volatility Surface Forecaster Mod-2275 | Neural SDEs / Adversarial robustness / Stock options hedging | 9793 | 5769 | No |
| 4799 | Neural Scholarly Volatility Surface Forecaster Mod-2755 | Neural SDEs / Adversarial robustness / Stock options hedging | 9799 | 5782 | No |
| 4884 | Neural Scholarly Volatility Surface Forecaster Mod-3235 | Neural SDEs / Adversarial robustness / Stock options hedging | 9805 | 5795 | No |
| 4969 | Neural Scholarly Volatility Surface Forecaster Mod-3715 | Neural SDEs / Adversarial robustness / Stock options hedging | 9811 | 5808 | No |
| 6317 | Neural Scholarly Volatility Surface Forecaster Sys-397 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10881 | 12817 | No |
| 6358 | Neural Scholarly Volatility Surface Forecaster Sys-877 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10889 | 12829 | No |
| 6399 | Neural Scholarly Volatility Surface Forecaster Sys-1357 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10897 | 12841 | No |
| 6440 | Neural Scholarly Volatility Surface Forecaster Sys-1837 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10905 | 12853 | No |
| 9078 | Neural Scholarly Volatility Surface Forecaster Sys-13 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 9900 | 10174 | No |
| 9190 | Neural Scholarly Volatility Surface Forecaster Sys-301 | Graph attention / Sector contagion / Stock baskets | 2222 | 5648 | No |
| 9265 | Neural Scholarly Volatility Surface Forecaster Sys-493 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 9911 | 10184 | No |
| 9377 | Neural Scholarly Volatility Surface Forecaster Sys-781 | Graph attention / Sector contagion / Stock baskets | 2269 | 5665 | No |
| 9452 | Neural Scholarly Volatility Surface Forecaster Sys-973 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 9922 | 10194 | No |
| 9564 | Neural Scholarly Volatility Surface Forecaster Sys-1261 | Graph attention / Sector contagion / Stock baskets | 2316 | 5682 | No |
| 9639 | Neural Scholarly Volatility Surface Forecaster Sys-1453 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 9933 | 10204 | No |
| 9751 | Neural Scholarly Volatility Surface Forecaster Sys-1741 | Graph attention / Sector contagion / Stock baskets | 2363 | 5699 | No |
| 9826 | Neural Scholarly Volatility Surface Forecaster Sys-1933 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 9944 | 10214 | No |
| 9877 | Neural Scholarly Volatility Surface Forecaster Mod-67 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12876 | 13523 | No |
| 9913 | Neural Scholarly Volatility Surface Forecaster Mod-163 | Topological data analysis / Betti persistence / Stock pairs | 4841 | 9431 | No |
| 9956 | Neural Scholarly Volatility Surface Forecaster Mod-259 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10118 | 9434 | No |
| 10068 | Neural Scholarly Volatility Surface Forecaster Mod-547 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12888 | 13530 | No |
| 10104 | Neural Scholarly Volatility Surface Forecaster Mod-643 | Topological data analysis / Betti persistence / Stock pairs | 4868 | 9447 | No |
| 10147 | Neural Scholarly Volatility Surface Forecaster Mod-739 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10130 | 9450 | No |
| 10259 | Neural Scholarly Volatility Surface Forecaster Mod-1027 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12900 | 13537 | No |
| 10295 | Neural Scholarly Volatility Surface Forecaster Mod-1123 | Topological data analysis / Betti persistence / Stock pairs | 4895 | 9463 | No |
| 10338 | Neural Scholarly Volatility Surface Forecaster Mod-1219 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10142 | 9466 | No |
| 10450 | Neural Scholarly Volatility Surface Forecaster Mod-1507 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12912 | 13544 | No |
| 10486 | Neural Scholarly Volatility Surface Forecaster Mod-1603 | Topological data analysis / Betti persistence / Stock pairs | 4922 | 9479 | No |
| 10529 | Neural Scholarly Volatility Surface Forecaster Mod-1699 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10154 | 9482 | No |
| 10641 | Neural Scholarly Volatility Surface Forecaster Mod-1987 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12924 | 13551 | No |
| 10677 | Neural Scholarly Volatility Surface Forecaster Mod-2083 | Topological data analysis / Betti persistence / Stock pairs | 4949 | 9495 | No |
| 10720 | Neural Scholarly Volatility Surface Forecaster Mod-2179 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10166 | 9498 | No |
| 10832 | Neural Scholarly Volatility Surface Forecaster Mod-2467 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12936 | 13558 | No |
| 10868 | Neural Scholarly Volatility Surface Forecaster Mod-2563 | Topological data analysis / Betti persistence / Stock pairs | 4976 | 9511 | No |
| 10911 | Neural Scholarly Volatility Surface Forecaster Mod-2659 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10178 | 9514 | No |
| 11023 | Neural Scholarly Volatility Surface Forecaster Mod-2947 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12948 | 13565 | No |
| 11059 | Neural Scholarly Volatility Surface Forecaster Mod-3043 | Topological data analysis / Betti persistence / Stock pairs | 5003 | 9527 | No |
| 11102 | Neural Scholarly Volatility Surface Forecaster Mod-3139 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10190 | 9530 | No |
| 11214 | Neural Scholarly Volatility Surface Forecaster Mod-3427 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12960 | 13572 | No |
| 11250 | Neural Scholarly Volatility Surface Forecaster Mod-3523 | Topological data analysis / Betti persistence / Stock pairs | 5030 | 9543 | No |
| 11293 | Neural Scholarly Volatility Surface Forecaster Mod-3619 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10202 | 9546 | No |
| 11405 | Neural Scholarly Volatility Surface Forecaster Mod-3907 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12972 | 13579 | No |
| 13986 | Neural Scholarly Volatility Surface Forecaster Mod-451 | Delay differential equations / Controlled ODEs / Stock execution | 5983 | 5719 | No |
| 14000 | Neural Scholarly Volatility Surface Forecaster Mod-931 | Delay differential equations / Controlled ODEs / Stock execution | 6007 | 5732 | No |
| 14014 | Neural Scholarly Volatility Surface Forecaster Mod-1411 | Delay differential equations / Controlled ODEs / Stock execution | 6031 | 5745 | No |
| 14028 | Neural Scholarly Volatility Surface Forecaster Mod-1891 | Delay differential equations / Controlled ODEs / Stock execution | 6055 | 5758 | No |
| 14042 | Neural Scholarly Volatility Surface Forecaster Mod-2371 | Delay differential equations / Controlled ODEs / Stock execution | 6079 | 5771 | No |
| 14056 | Neural Scholarly Volatility Surface Forecaster Mod-2851 | Delay differential equations / Controlled ODEs / Stock execution | 6103 | 5784 | No |
| 14070 | Neural Scholarly Volatility Surface Forecaster Mod-3331 | Delay differential equations / Controlled ODEs / Stock execution | 6127 | 5797 | No |
| 14084 | Neural Scholarly Volatility Surface Forecaster Mod-3811 | Delay differential equations / Controlled ODEs / Stock execution | 6151 | 5810 | No |
