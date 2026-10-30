# Multi-scale approach to volatility-surface forecasting

**Concept page** · shared by **11** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #3,776) ·
researched 2026-10-30

| | |
|---|---|
| Task | Volatility-surface forecasting |
| Method | Multi-scale (several horizons combined) |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Options are outside the owner's instrument rule; a surface forecast has nothing to trade here (the VIX regime route is RK168). |
| Implemented in volatility-ai | Option pricing and surface models are research code (`derivatives`, `options`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK168, RK240 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Multi-Scale Scholarly
Volatility Surface Forecaster Ref-35") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Forecast the implied-volatility surface across strikes and expiries for
option valuation, risk limits or hedging. The multi-scale version
combines signals or estimates measured over several horizons. I found no
study of this method on this task.

## The CSV's description

Proposed multi-scale approach to volatility-surface forecasting:
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
* More horizons mean more weights to choose, and the blend can be
  overfitted.

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
| 3776 | Multi-Scale Scholarly Volatility Surface Forecaster Ref-35 | Neural SDEs / Adversarial robustness / Stock options hedging | 10382 | 8427 | No |
| 3862 | Multi-Scale Scholarly Volatility Surface Forecaster Ref-515 | Neural SDEs / Adversarial robustness / Stock options hedging | 10386 | 8447 | No |
| 3948 | Multi-Scale Scholarly Volatility Surface Forecaster Ref-995 | Neural SDEs / Adversarial robustness / Stock options hedging | 10390 | 8467 | No |
| 7481 | Multi-Scale Scholarly Volatility Surface Forecaster Ref-419 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 9305 | 10356 | No |
| 7515 | Multi-Scale Scholarly Volatility Surface Forecaster Ref-899 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 9321 | 10367 | No |
| 8728 | Multi-Scale Scholarly Volatility Surface Forecaster Ref-131 | Delay differential equations / Controlled ODEs / Stock execution | 13613 | 13962 | No |
| 8766 | Multi-Scale Scholarly Volatility Surface Forecaster Ref-227 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12024 | 11884 | No |
| 8802 | Multi-Scale Scholarly Volatility Surface Forecaster Ref-323 | Topological data analysis / Betti persistence / Stock pairs | 11301 | 11888 | No |
| 8919 | Multi-Scale Scholarly Volatility Surface Forecaster Ref-611 | Delay differential equations / Controlled ODEs / Stock execution | 13621 | 13966 | No |
| 8957 | Multi-Scale Scholarly Volatility Surface Forecaster Ref-707 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12032 | 11907 | No |
| 8993 | Multi-Scale Scholarly Volatility Surface Forecaster Ref-803 | Topological data analysis / Betti persistence / Stock pairs | 11326 | 11911 | No |
