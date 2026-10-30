# Path-signature-based approach to volatility-surface forecasting

**Concept page** · shared by **61** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,223) ·
researched 2026-10-30

| | |
|---|---|
| Task | Volatility-surface forecasting |
| Method | Path signatures |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Options are outside the owner's instrument rule; a surface forecast has nothing to trade here (the VIX regime route is RK168). |
| Implemented in volatility-ai | Option pricing and surface models are research code (`derivatives`, `options`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK168, RK240 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Signature Scholarly
Volatility Surface Forecaster Sys-85") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Forecast the implied-volatility surface across strikes and expiries for
option valuation, risk limits or hedging. The path-signature version
describes price paths by their iterated-integral signatures and fits on
those features. I found no study of this method on this task.

## The CSV's description

Proposed path-signature-based approach to volatility-surface
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
* Signature features multiply with depth and dimension; no out-of-sample
  trading evidence found (RK328).

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
| 1223 | Signature Scholarly Volatility Surface Forecaster Sys-85 | Rough path theory / Tensor signatures / Stock trend forecasting | 9325 | 9394 | No |
| 1240 | Signature Scholarly Volatility Surface Forecaster Sys-565 | Rough path theory / Tensor signatures / Stock trend forecasting | 9341 | 9402 | No |
| 1257 | Signature Scholarly Volatility Surface Forecaster Sys-1045 | Rough path theory / Tensor signatures / Stock trend forecasting | 9357 | 9410 | No |
| 1274 | Signature Scholarly Volatility Surface Forecaster Sys-1525 | Rough path theory / Tensor signatures / Stock trend forecasting | 9373 | 9418 | No |
| 3223 | Signature Scholarly Volatility Surface Forecaster Sys-277 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10879 | 12814 | No |
| 3245 | Signature Scholarly Volatility Surface Forecaster Sys-757 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10887 | 12826 | No |
| 3267 | Signature Scholarly Volatility Surface Forecaster Sys-1237 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10895 | 12838 | No |
| 3289 | Signature Scholarly Volatility Surface Forecaster Sys-1717 | Wavelet transforms / Multi-resolution filtering / Statistical arbitrage stocks | 10903 | 12850 | No |
| 4035 | Signature Scholarly Volatility Surface Forecaster Sys-469 | Geometric deep learning / Riemannian metrics / Stock risk parity | 10076 | 9401 | No |
| 4121 | Signature Scholarly Volatility Surface Forecaster Sys-949 | Geometric deep learning / Riemannian metrics / Stock risk parity | 10087 | 9409 | No |
| 4207 | Signature Scholarly Volatility Surface Forecaster Sys-1429 | Geometric deep learning / Riemannian metrics / Stock risk parity | 10098 | 9417 | No |
| 4293 | Signature Scholarly Volatility Surface Forecaster Sys-1909 | Geometric deep learning / Riemannian metrics / Stock risk parity | 10109 | 9425 | No |
| 4395 | Signature Scholarly Volatility Surface Forecaster Mod-475 | Neural SDEs / Adversarial robustness / Stock options hedging | 9770 | 5720 | No |
| 4480 | Signature Scholarly Volatility Surface Forecaster Mod-955 | Neural SDEs / Adversarial robustness / Stock options hedging | 9776 | 5733 | No |
| 4565 | Signature Scholarly Volatility Surface Forecaster Mod-1435 | Neural SDEs / Adversarial robustness / Stock options hedging | 9782 | 5746 | No |
| 4650 | Signature Scholarly Volatility Surface Forecaster Mod-1915 | Neural SDEs / Adversarial robustness / Stock options hedging | 9788 | 5759 | No |
| 4735 | Signature Scholarly Volatility Surface Forecaster Mod-2395 | Neural SDEs / Adversarial robustness / Stock options hedging | 9794 | 5772 | No |
| 4820 | Signature Scholarly Volatility Surface Forecaster Mod-2875 | Neural SDEs / Adversarial robustness / Stock options hedging | 9800 | 5785 | No |
| 4905 | Signature Scholarly Volatility Surface Forecaster Mod-3355 | Neural SDEs / Adversarial robustness / Stock options hedging | 9806 | 5798 | No |
| 4990 | Signature Scholarly Volatility Surface Forecaster Mod-3835 | Neural SDEs / Adversarial robustness / Stock options hedging | 9812 | 5811 | No |
| 7533 | Signature Scholarly Volatility Surface Forecaster Sys-181 | Graph attention / Sector contagion / Stock baskets | 2211 | 5644 | No |
| 7564 | Signature Scholarly Volatility Surface Forecaster Sys-661 | Graph attention / Sector contagion / Stock baskets | 2258 | 5661 | No |
| 7595 | Signature Scholarly Volatility Surface Forecaster Sys-1141 | Graph attention / Sector contagion / Stock baskets | 2305 | 5678 | No |
| 7626 | Signature Scholarly Volatility Surface Forecaster Sys-1621 | Graph attention / Sector contagion / Stock baskets | 2352 | 5695 | No |
| 7674 | Signature Scholarly Volatility Surface Forecaster Mod-379 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10121 | 9438 | No |
| 7706 | Signature Scholarly Volatility Surface Forecaster Mod-859 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10133 | 9454 | No |
| 7738 | Signature Scholarly Volatility Surface Forecaster Mod-1339 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10145 | 9470 | No |
| 7770 | Signature Scholarly Volatility Surface Forecaster Mod-1819 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10157 | 9486 | No |
| 7802 | Signature Scholarly Volatility Surface Forecaster Mod-2299 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10169 | 9502 | No |
| 7834 | Signature Scholarly Volatility Surface Forecaster Mod-2779 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10181 | 9518 | No |
| 7866 | Signature Scholarly Volatility Surface Forecaster Mod-3259 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10193 | 9534 | No |
| 7898 | Signature Scholarly Volatility Surface Forecaster Mod-3739 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10205 | 9550 | No |
| 9219 | Signature Scholarly Volatility Surface Forecaster Sys-373 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 9908 | 10181 | No |
| 9406 | Signature Scholarly Volatility Surface Forecaster Sys-853 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 9919 | 10191 | No |
| 9593 | Signature Scholarly Volatility Surface Forecaster Sys-1333 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 9930 | 10201 | No |
| 9780 | Signature Scholarly Volatility Surface Forecaster Sys-1813 | Quantum annealing / QUBO combinatorial / Stock index rebalancing | 9941 | 10211 | No |
| 9888 | Signature Scholarly Volatility Surface Forecaster Mod-91 | Delay differential equations / Controlled ODEs / Stock execution | 5966 | 5709 | No |
| 9924 | Signature Scholarly Volatility Surface Forecaster Mod-187 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12879 | 13525 | No |
| 9964 | Signature Scholarly Volatility Surface Forecaster Mod-283 | Topological data analysis / Betti persistence / Stock pairs | 4849 | 9435 | No |
| 10079 | Signature Scholarly Volatility Surface Forecaster Mod-571 | Delay differential equations / Controlled ODEs / Stock execution | 5990 | 5722 | No |
| 10115 | Signature Scholarly Volatility Surface Forecaster Mod-667 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12891 | 13532 | No |
| 10155 | Signature Scholarly Volatility Surface Forecaster Mod-763 | Topological data analysis / Betti persistence / Stock pairs | 4876 | 9451 | No |
| 10270 | Signature Scholarly Volatility Surface Forecaster Mod-1051 | Delay differential equations / Controlled ODEs / Stock execution | 6014 | 5735 | No |
| 10306 | Signature Scholarly Volatility Surface Forecaster Mod-1147 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12903 | 13539 | No |
| 10346 | Signature Scholarly Volatility Surface Forecaster Mod-1243 | Topological data analysis / Betti persistence / Stock pairs | 4903 | 9467 | No |
| 10461 | Signature Scholarly Volatility Surface Forecaster Mod-1531 | Delay differential equations / Controlled ODEs / Stock execution | 6038 | 5748 | No |
| 10497 | Signature Scholarly Volatility Surface Forecaster Mod-1627 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12915 | 13546 | No |
| 10537 | Signature Scholarly Volatility Surface Forecaster Mod-1723 | Topological data analysis / Betti persistence / Stock pairs | 4930 | 9483 | No |
| 10652 | Signature Scholarly Volatility Surface Forecaster Mod-2011 | Delay differential equations / Controlled ODEs / Stock execution | 6062 | 5761 | No |
| 10688 | Signature Scholarly Volatility Surface Forecaster Mod-2107 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12927 | 13553 | No |
| 10728 | Signature Scholarly Volatility Surface Forecaster Mod-2203 | Topological data analysis / Betti persistence / Stock pairs | 4957 | 9499 | No |
| 10843 | Signature Scholarly Volatility Surface Forecaster Mod-2491 | Delay differential equations / Controlled ODEs / Stock execution | 6086 | 5774 | No |
| 10879 | Signature Scholarly Volatility Surface Forecaster Mod-2587 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12939 | 13560 | No |
| 10919 | Signature Scholarly Volatility Surface Forecaster Mod-2683 | Topological data analysis / Betti persistence / Stock pairs | 4984 | 9515 | No |
| 11034 | Signature Scholarly Volatility Surface Forecaster Mod-2971 | Delay differential equations / Controlled ODEs / Stock execution | 6110 | 5787 | No |
| 11070 | Signature Scholarly Volatility Surface Forecaster Mod-3067 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12951 | 13567 | No |
| 11110 | Signature Scholarly Volatility Surface Forecaster Mod-3163 | Topological data analysis / Betti persistence / Stock pairs | 5011 | 9531 | No |
| 11225 | Signature Scholarly Volatility Surface Forecaster Mod-3451 | Delay differential equations / Controlled ODEs / Stock execution | 6134 | 5800 | No |
| 11261 | Signature Scholarly Volatility Surface Forecaster Mod-3547 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12963 | 13574 | No |
| 11301 | Signature Scholarly Volatility Surface Forecaster Mod-3643 | Topological data analysis / Betti persistence / Stock pairs | 5038 | 9547 | No |
| 11416 | Signature Scholarly Volatility Surface Forecaster Mod-3931 | Delay differential equations / Controlled ODEs / Stock execution | 6158 | 5813 | No |
