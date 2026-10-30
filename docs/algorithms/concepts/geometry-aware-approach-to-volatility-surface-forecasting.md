# Geometry-aware approach to volatility-surface forecasting

**Concept page** · shared by **62** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #5,033) ·
researched 2026-10-30

| | |
|---|---|
| Task | Volatility-surface forecasting |
| Method | Geometry-aware (Riemannian) methods |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Options are outside the owner's instrument rule; a surface forecast has nothing to trade here (the VIX regime route is RK168). |
| Implemented in volatility-ai | Option pricing and surface models are research code (`derivatives`, `options`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK168, RK240 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Riemannian Scholarly
Volatility Surface Forecaster Eng-55") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Forecast the implied-volatility surface across strikes and expiries for
option valuation, risk limits or hedging. The geometry-aware version
works on the curved space of covariance matrices or another manifold. I
found no study of this method on this task.

## The CSV's description

Proposed geometry-aware approach to volatility-surface forecasting:
Forecast the implied-volatility surface across option strikes and
expirations, then use those forecasts to inform option valuation, risk
limits, or hedging. This is a concept-level interpretation of the title,
not a complete trading specification: the exact model inputs/target,
calibration, entry/exit or rebalance rules, and position sizing are not
fully defined here.

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
* No portfolio study shows Riemannian methods beating shrinkage (RK230).

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
| 5033 | Riemannian Scholarly Volatility Surface Forecaster Eng-55 | Neural SDEs / Adversarial robustness / Stock options hedging | 11164 | 9561 | No |
| 5119 | Riemannian Scholarly Volatility Surface Forecaster Eng-535 | Neural SDEs / Adversarial robustness / Stock options hedging | 11171 | 9581 | No |
| 5205 | Riemannian Scholarly Volatility Surface Forecaster Eng-1015 | Neural SDEs / Adversarial robustness / Stock options hedging | 11178 | 9601 | No |
| 5291 | Riemannian Scholarly Volatility Surface Forecaster Eng-1495 | Neural SDEs / Adversarial robustness / Stock options hedging | 11185 | 9621 | No |
| 5377 | Riemannian Scholarly Volatility Surface Forecaster Eng-1975 | Neural SDEs / Adversarial robustness / Stock options hedging | 11192 | 9641 | No |
| 5463 | Riemannian Scholarly Volatility Surface Forecaster Eng-2455 | Neural SDEs / Adversarial robustness / Stock options hedging | 11199 | 9661 | No |
| 5549 | Riemannian Scholarly Volatility Surface Forecaster Eng-2935 | Neural SDEs / Adversarial robustness / Stock options hedging | 11206 | 9681 | No |
| 5635 | Riemannian Scholarly Volatility Surface Forecaster Eng-3415 | Neural SDEs / Adversarial robustness / Stock options hedging | 11213 | 9701 | No |
| 5721 | Riemannian Scholarly Volatility Surface Forecaster Eng-3895 | Neural SDEs / Adversarial robustness / Stock options hedging | 11220 | 9721 | No |
| 5807 | Riemannian Scholarly Volatility Surface Forecaster Eng-4375 | Neural SDEs / Adversarial robustness / Stock options hedging | 11227 | 9741 | No |
| 5893 | Riemannian Scholarly Volatility Surface Forecaster Eng-4855 | Neural SDEs / Adversarial robustness / Stock options hedging | 11234 | 9761 | No |
| 5979 | Riemannian Scholarly Volatility Surface Forecaster Eng-5335 | Neural SDEs / Adversarial robustness / Stock options hedging | 11241 | 9781 | No |
| 6065 | Riemannian Scholarly Volatility Surface Forecaster Eng-5815 | Neural SDEs / Adversarial robustness / Stock options hedging | 11248 | 9801 | No |
| 7948 | Riemannian Scholarly Volatility Surface Forecaster Eng-439 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10223 | 9576 | No |
| 7982 | Riemannian Scholarly Volatility Surface Forecaster Eng-919 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10236 | 9596 | No |
| 8016 | Riemannian Scholarly Volatility Surface Forecaster Eng-1399 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10249 | 9616 | No |
| 8050 | Riemannian Scholarly Volatility Surface Forecaster Eng-1879 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10262 | 9636 | No |
| 8084 | Riemannian Scholarly Volatility Surface Forecaster Eng-2359 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10275 | 9656 | No |
| 8118 | Riemannian Scholarly Volatility Surface Forecaster Eng-2839 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10288 | 9676 | No |
| 8152 | Riemannian Scholarly Volatility Surface Forecaster Eng-3319 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10301 | 9696 | No |
| 8186 | Riemannian Scholarly Volatility Surface Forecaster Eng-3799 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10314 | 9716 | No |
| 8220 | Riemannian Scholarly Volatility Surface Forecaster Eng-4279 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10327 | 9736 | No |
| 8254 | Riemannian Scholarly Volatility Surface Forecaster Eng-4759 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10340 | 9756 | No |
| 8288 | Riemannian Scholarly Volatility Surface Forecaster Eng-5239 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10353 | 9776 | No |
| 8322 | Riemannian Scholarly Volatility Surface Forecaster Eng-5719 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10366 | 9796 | No |
| 11507 | Riemannian Scholarly Volatility Surface Forecaster Eng-151 | Delay differential equations / Controlled ODEs / Stock execution | 6167 | 9566 | No |
| 11541 | Riemannian Scholarly Volatility Surface Forecaster Eng-247 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 13729 | 13584 | No |
| 11576 | Riemannian Scholarly Volatility Surface Forecaster Eng-343 | Topological data analysis / Betti persistence / Stock pairs | 5074 | 9572 | No |
| 11698 | Riemannian Scholarly Volatility Surface Forecaster Eng-631 | Delay differential equations / Controlled ODEs / Stock execution | 6189 | 9586 | No |
| 11732 | Riemannian Scholarly Volatility Surface Forecaster Eng-727 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 13730 | 13589 | No |
| 11767 | Riemannian Scholarly Volatility Surface Forecaster Eng-823 | Topological data analysis / Betti persistence / Stock pairs | 5099 | 9592 | No |
| 11889 | Riemannian Scholarly Volatility Surface Forecaster Eng-1111 | Delay differential equations / Controlled ODEs / Stock execution | 6211 | 9606 | No |
| 11923 | Riemannian Scholarly Volatility Surface Forecaster Eng-1207 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 13731 | 13594 | No |
| 11958 | Riemannian Scholarly Volatility Surface Forecaster Eng-1303 | Topological data analysis / Betti persistence / Stock pairs | 5124 | 9612 | No |
| 12080 | Riemannian Scholarly Volatility Surface Forecaster Eng-1591 | Delay differential equations / Controlled ODEs / Stock execution | 6233 | 9626 | No |
| 12114 | Riemannian Scholarly Volatility Surface Forecaster Eng-1687 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 13732 | 13599 | No |
| 12149 | Riemannian Scholarly Volatility Surface Forecaster Eng-1783 | Topological data analysis / Betti persistence / Stock pairs | 5149 | 9632 | No |
| 12271 | Riemannian Scholarly Volatility Surface Forecaster Eng-2071 | Delay differential equations / Controlled ODEs / Stock execution | 6255 | 9646 | No |
| 12305 | Riemannian Scholarly Volatility Surface Forecaster Eng-2167 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 13733 | 13604 | No |
| 12340 | Riemannian Scholarly Volatility Surface Forecaster Eng-2263 | Topological data analysis / Betti persistence / Stock pairs | 5174 | 9652 | No |
| 12462 | Riemannian Scholarly Volatility Surface Forecaster Eng-2551 | Delay differential equations / Controlled ODEs / Stock execution | 6277 | 9666 | No |
| 12496 | Riemannian Scholarly Volatility Surface Forecaster Eng-2647 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 13734 | 13609 | No |
| 12531 | Riemannian Scholarly Volatility Surface Forecaster Eng-2743 | Topological data analysis / Betti persistence / Stock pairs | 5199 | 9672 | No |
| 12653 | Riemannian Scholarly Volatility Surface Forecaster Eng-3031 | Delay differential equations / Controlled ODEs / Stock execution | 6299 | 9686 | No |
| 12687 | Riemannian Scholarly Volatility Surface Forecaster Eng-3127 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 13735 | 13614 | No |
| 12722 | Riemannian Scholarly Volatility Surface Forecaster Eng-3223 | Topological data analysis / Betti persistence / Stock pairs | 5224 | 9692 | No |
| 12844 | Riemannian Scholarly Volatility Surface Forecaster Eng-3511 | Delay differential equations / Controlled ODEs / Stock execution | 6321 | 9706 | No |
| 12878 | Riemannian Scholarly Volatility Surface Forecaster Eng-3607 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 13736 | 13619 | No |
| 12913 | Riemannian Scholarly Volatility Surface Forecaster Eng-3703 | Topological data analysis / Betti persistence / Stock pairs | 5249 | 9712 | No |
| 13035 | Riemannian Scholarly Volatility Surface Forecaster Eng-3991 | Delay differential equations / Controlled ODEs / Stock execution | 6343 | 9726 | No |
| 13069 | Riemannian Scholarly Volatility Surface Forecaster Eng-4087 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 13737 | 13624 | No |
| 13104 | Riemannian Scholarly Volatility Surface Forecaster Eng-4183 | Topological data analysis / Betti persistence / Stock pairs | 5274 | 9732 | No |
| 13226 | Riemannian Scholarly Volatility Surface Forecaster Eng-4471 | Delay differential equations / Controlled ODEs / Stock execution | 6365 | 9746 | No |
| 13260 | Riemannian Scholarly Volatility Surface Forecaster Eng-4567 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 13738 | 13629 | No |
| 13295 | Riemannian Scholarly Volatility Surface Forecaster Eng-4663 | Topological data analysis / Betti persistence / Stock pairs | 5299 | 9752 | No |
| 13417 | Riemannian Scholarly Volatility Surface Forecaster Eng-4951 | Delay differential equations / Controlled ODEs / Stock execution | 6387 | 9766 | No |
| 13451 | Riemannian Scholarly Volatility Surface Forecaster Eng-5047 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 13739 | 13634 | No |
| 13486 | Riemannian Scholarly Volatility Surface Forecaster Eng-5143 | Topological data analysis / Betti persistence / Stock pairs | 5324 | 9772 | No |
| 13608 | Riemannian Scholarly Volatility Surface Forecaster Eng-5431 | Delay differential equations / Controlled ODEs / Stock execution | 6409 | 9786 | No |
| 13642 | Riemannian Scholarly Volatility Surface Forecaster Eng-5527 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 13740 | 13639 | No |
| 13677 | Riemannian Scholarly Volatility Surface Forecaster Eng-5623 | Topological data analysis / Betti persistence / Stock pairs | 5349 | 9792 | No |
| 13799 | Riemannian Scholarly Volatility Surface Forecaster Eng-5911 | Delay differential equations / Controlled ODEs / Stock execution | 6431 | 9806 | No |
