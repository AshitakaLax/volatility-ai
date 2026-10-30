# Nonlinear approach to volatility-surface forecasting

**Concept page** · shared by **63** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #5,075) ·
researched 2026-10-30

| | |
|---|---|
| Task | Volatility-surface forecasting |
| Method | Nonlinear models |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Options are outside the owner's instrument rule; a surface forecast has nothing to trade here (the VIX regime route is RK168). |
| Implemented in volatility-ai | Option pricing and surface models are research code (`derivatives`, `options`). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK168, RK240 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Non-Linear Scholarly
Volatility Surface Forecaster Eng-295") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Forecast the implied-volatility surface across strikes and expiries for
option valuation, risk limits or hedging. The nonlinear version replaces
linear rules with nonlinear regressions or filters. I found no study of
this method on this task.

## The CSV's description

Proposed nonlinear approach to volatility-surface forecasting: Forecast
the implied-volatility surface across option strikes and expirations,
then use those forecasts to inform option valuation, risk limits, or
hedging. This is a concept-level interpretation of the title, not a
complete trading specification: the exact model inputs/target,
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
* Nonlinear fits on a few thousand daily bars overfit easily; gains over
  linear rules are usually small out of sample.

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
| 5075 | Non-Linear Scholarly Volatility Surface Forecaster Eng-295 | Neural SDEs / Adversarial robustness / Stock options hedging | 9818 | 5821 | No |
| 5161 | Non-Linear Scholarly Volatility Surface Forecaster Eng-775 | Neural SDEs / Adversarial robustness / Stock options hedging | 9824 | 5830 | No |
| 5247 | Non-Linear Scholarly Volatility Surface Forecaster Eng-1255 | Neural SDEs / Adversarial robustness / Stock options hedging | 9830 | 5839 | No |
| 5333 | Non-Linear Scholarly Volatility Surface Forecaster Eng-1735 | Neural SDEs / Adversarial robustness / Stock options hedging | 9836 | 5848 | No |
| 5419 | Non-Linear Scholarly Volatility Surface Forecaster Eng-2215 | Neural SDEs / Adversarial robustness / Stock options hedging | 9842 | 5857 | No |
| 5505 | Non-Linear Scholarly Volatility Surface Forecaster Eng-2695 | Neural SDEs / Adversarial robustness / Stock options hedging | 9848 | 5866 | No |
| 5591 | Non-Linear Scholarly Volatility Surface Forecaster Eng-3175 | Neural SDEs / Adversarial robustness / Stock options hedging | 9854 | 5875 | No |
| 5677 | Non-Linear Scholarly Volatility Surface Forecaster Eng-3655 | Neural SDEs / Adversarial robustness / Stock options hedging | 9860 | 5884 | No |
| 5763 | Non-Linear Scholarly Volatility Surface Forecaster Eng-4135 | Neural SDEs / Adversarial robustness / Stock options hedging | 9866 | 5893 | No |
| 5849 | Non-Linear Scholarly Volatility Surface Forecaster Eng-4615 | Neural SDEs / Adversarial robustness / Stock options hedging | 9872 | 5902 | No |
| 5935 | Non-Linear Scholarly Volatility Surface Forecaster Eng-5095 | Neural SDEs / Adversarial robustness / Stock options hedging | 9878 | 5911 | No |
| 6021 | Non-Linear Scholarly Volatility Surface Forecaster Eng-5575 | Neural SDEs / Adversarial robustness / Stock options hedging | 9884 | 5920 | No |
| 7931 | Non-Linear Scholarly Volatility Surface Forecaster Eng-199 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10216 | 9567 | No |
| 7965 | Non-Linear Scholarly Volatility Surface Forecaster Eng-679 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10229 | 9587 | No |
| 7999 | Non-Linear Scholarly Volatility Surface Forecaster Eng-1159 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10242 | 9607 | No |
| 8033 | Non-Linear Scholarly Volatility Surface Forecaster Eng-1639 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10255 | 9627 | No |
| 8067 | Non-Linear Scholarly Volatility Surface Forecaster Eng-2119 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10268 | 9647 | No |
| 8101 | Non-Linear Scholarly Volatility Surface Forecaster Eng-2599 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10281 | 9667 | No |
| 8135 | Non-Linear Scholarly Volatility Surface Forecaster Eng-3079 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10294 | 9687 | No |
| 8169 | Non-Linear Scholarly Volatility Surface Forecaster Eng-3559 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10307 | 9707 | No |
| 8203 | Non-Linear Scholarly Volatility Surface Forecaster Eng-4039 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10320 | 9727 | No |
| 8237 | Non-Linear Scholarly Volatility Surface Forecaster Eng-4519 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10333 | 9747 | No |
| 8271 | Non-Linear Scholarly Volatility Surface Forecaster Eng-4999 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10346 | 9767 | No |
| 8305 | Non-Linear Scholarly Volatility Surface Forecaster Eng-5479 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10359 | 9787 | No |
| 8339 | Non-Linear Scholarly Volatility Surface Forecaster Eng-5959 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 10372 | 9807 | No |
| 11445 | Non-Linear Scholarly Volatility Surface Forecaster Eng-7 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12975 | 13581 | No |
| 11484 | Non-Linear Scholarly Volatility Surface Forecaster Eng-103 | Topological data analysis / Betti persistence / Stock pairs | 5061 | 9563 | No |
| 11599 | Non-Linear Scholarly Volatility Surface Forecaster Eng-391 | Delay differential equations / Controlled ODEs / Stock execution | 6178 | 5823 | No |
| 11636 | Non-Linear Scholarly Volatility Surface Forecaster Eng-487 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12985 | 13586 | No |
| 11675 | Non-Linear Scholarly Volatility Surface Forecaster Eng-583 | Topological data analysis / Betti persistence / Stock pairs | 5086 | 9583 | No |
| 11790 | Non-Linear Scholarly Volatility Surface Forecaster Eng-871 | Delay differential equations / Controlled ODEs / Stock execution | 6200 | 5832 | No |
| 11827 | Non-Linear Scholarly Volatility Surface Forecaster Eng-967 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12995 | 13591 | No |
| 11866 | Non-Linear Scholarly Volatility Surface Forecaster Eng-1063 | Topological data analysis / Betti persistence / Stock pairs | 5111 | 9603 | No |
| 11981 | Non-Linear Scholarly Volatility Surface Forecaster Eng-1351 | Delay differential equations / Controlled ODEs / Stock execution | 6222 | 5841 | No |
| 12018 | Non-Linear Scholarly Volatility Surface Forecaster Eng-1447 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 13005 | 13596 | No |
| 12057 | Non-Linear Scholarly Volatility Surface Forecaster Eng-1543 | Topological data analysis / Betti persistence / Stock pairs | 5136 | 9623 | No |
| 12172 | Non-Linear Scholarly Volatility Surface Forecaster Eng-1831 | Delay differential equations / Controlled ODEs / Stock execution | 6244 | 5850 | No |
| 12209 | Non-Linear Scholarly Volatility Surface Forecaster Eng-1927 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 13015 | 13601 | No |
| 12248 | Non-Linear Scholarly Volatility Surface Forecaster Eng-2023 | Topological data analysis / Betti persistence / Stock pairs | 5161 | 9643 | No |
| 12363 | Non-Linear Scholarly Volatility Surface Forecaster Eng-2311 | Delay differential equations / Controlled ODEs / Stock execution | 6266 | 5859 | No |
| 12400 | Non-Linear Scholarly Volatility Surface Forecaster Eng-2407 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 13025 | 13606 | No |
| 12439 | Non-Linear Scholarly Volatility Surface Forecaster Eng-2503 | Topological data analysis / Betti persistence / Stock pairs | 5186 | 9663 | No |
| 12554 | Non-Linear Scholarly Volatility Surface Forecaster Eng-2791 | Delay differential equations / Controlled ODEs / Stock execution | 6288 | 5868 | No |
| 12591 | Non-Linear Scholarly Volatility Surface Forecaster Eng-2887 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 13035 | 13611 | No |
| 12630 | Non-Linear Scholarly Volatility Surface Forecaster Eng-2983 | Topological data analysis / Betti persistence / Stock pairs | 5211 | 9683 | No |
| 12745 | Non-Linear Scholarly Volatility Surface Forecaster Eng-3271 | Delay differential equations / Controlled ODEs / Stock execution | 6310 | 5877 | No |
| 12782 | Non-Linear Scholarly Volatility Surface Forecaster Eng-3367 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 13045 | 13616 | No |
| 12821 | Non-Linear Scholarly Volatility Surface Forecaster Eng-3463 | Topological data analysis / Betti persistence / Stock pairs | 5236 | 9703 | No |
| 12936 | Non-Linear Scholarly Volatility Surface Forecaster Eng-3751 | Delay differential equations / Controlled ODEs / Stock execution | 6332 | 5886 | No |
| 12973 | Non-Linear Scholarly Volatility Surface Forecaster Eng-3847 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 13055 | 13621 | No |
| 13012 | Non-Linear Scholarly Volatility Surface Forecaster Eng-3943 | Topological data analysis / Betti persistence / Stock pairs | 5261 | 9723 | No |
| 13127 | Non-Linear Scholarly Volatility Surface Forecaster Eng-4231 | Delay differential equations / Controlled ODEs / Stock execution | 6354 | 5895 | No |
| 13164 | Non-Linear Scholarly Volatility Surface Forecaster Eng-4327 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 13065 | 13626 | No |
| 13203 | Non-Linear Scholarly Volatility Surface Forecaster Eng-4423 | Topological data analysis / Betti persistence / Stock pairs | 5286 | 9743 | No |
| 13318 | Non-Linear Scholarly Volatility Surface Forecaster Eng-4711 | Delay differential equations / Controlled ODEs / Stock execution | 6376 | 5904 | No |
| 13355 | Non-Linear Scholarly Volatility Surface Forecaster Eng-4807 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 13075 | 13631 | No |
| 13394 | Non-Linear Scholarly Volatility Surface Forecaster Eng-4903 | Topological data analysis / Betti persistence / Stock pairs | 5311 | 9763 | No |
| 13509 | Non-Linear Scholarly Volatility Surface Forecaster Eng-5191 | Delay differential equations / Controlled ODEs / Stock execution | 6398 | 5913 | No |
| 13546 | Non-Linear Scholarly Volatility Surface Forecaster Eng-5287 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 13085 | 13636 | No |
| 13585 | Non-Linear Scholarly Volatility Surface Forecaster Eng-5383 | Topological data analysis / Betti persistence / Stock pairs | 5336 | 9783 | No |
| 13700 | Non-Linear Scholarly Volatility Surface Forecaster Eng-5671 | Delay differential equations / Controlled ODEs / Stock execution | 6420 | 5922 | No |
| 13737 | Non-Linear Scholarly Volatility Surface Forecaster Eng-5767 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 13095 | 13641 | No |
| 13776 | Non-Linear Scholarly Volatility Surface Forecaster Eng-5863 | Topological data analysis / Betti persistence / Stock pairs | 5361 | 9803 | No |
