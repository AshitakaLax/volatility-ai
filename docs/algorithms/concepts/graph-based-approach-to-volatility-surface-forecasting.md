# Graph-based approach to volatility-surface forecasting

**Concept page** · shared by **10** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #3,819) ·
researched 2026-10-30

| | |
|---|---|
| Task | Volatility-surface forecasting |
| Method | Graph / network models |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Options are outside the owner's instrument rule; a surface forecast has nothing to trade here (the VIX regime route is RK168). |
| Implemented in volatility-ai | Option pricing and surface models are research code (`derivatives`, `options`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK168, RK240 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Graph Scholarly Volatility
Surface Forecaster Ref-275") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Forecast the implied-volatility surface across strikes and expiries for
option valuation, risk limits or hedging. The graph-based version
represents assets as a network of correlation or causality links and
acts on its structure. I found no study of this method on this task.

## The CSV's description

Proposed graph-based approach to volatility-surface forecasting:
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
* Networks estimated from correlations are noisy and change with the
  window.

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
| 3819 | Graph Scholarly Volatility Surface Forecaster Ref-275 | Neural SDEs / Adversarial robustness / Stock options hedging | 10384 | 8436 | No |
| 3905 | Graph Scholarly Volatility Surface Forecaster Ref-755 | Neural SDEs / Adversarial robustness / Stock options hedging | 10388 | 8456 | No |
| 7464 | Graph Scholarly Volatility Surface Forecaster Ref-179 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 9297 | 10350 | No |
| 7498 | Graph Scholarly Volatility Surface Forecaster Ref-659 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 9313 | 10361 | No |
| 8708 | Graph Scholarly Volatility Surface Forecaster Ref-83 | Topological data analysis / Betti persistence / Stock pairs | 11289 | 11877 | No |
| 8823 | Graph Scholarly Volatility Surface Forecaster Ref-371 | Delay differential equations / Controlled ODEs / Stock execution | 13617 | 13964 | No |
| 8861 | Graph Scholarly Volatility Surface Forecaster Ref-467 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12027 | 11896 | No |
| 8899 | Graph Scholarly Volatility Surface Forecaster Ref-563 | Topological data analysis / Betti persistence / Stock pairs | 11314 | 11900 | No |
| 9014 | Graph Scholarly Volatility Surface Forecaster Ref-851 | Delay differential equations / Controlled ODEs / Stock execution | 13625 | 13968 | No |
| 9052 | Graph Scholarly Volatility Surface Forecaster Ref-947 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12035 | 11919 | No |
