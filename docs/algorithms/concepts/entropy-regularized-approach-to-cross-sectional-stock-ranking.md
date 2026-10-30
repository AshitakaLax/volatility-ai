# Entropy-regularized approach to cross-sectional stock ranking

**Concept page** · shared by **10** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #3,812) ·
researched 2026-10-30

| | |
|---|---|
| Task | Cross-sectional stock ranking |
| Method | Entropy regularisation |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Stock ranking needs a stock universe and a multi-name book; the project trades one ETF and holds no stock data. |
| Implemented in volatility-ai | Cross-sectional rankers are research code (`cross_section`, RK214). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK7, RK214, RK291, RK89 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Entropic Scholarly
Cross-Sectional Stock Ranker Ref-235") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Score stocks against one another and form a portfolio from the ranks.
The entropy-regularised version penalises concentrated weights or
forecasts, pulling them toward uniform. I found no study of this method
on this task.

## The CSV's description

Proposed entropy-regularized approach to cross-sectional stock ranking:
Score stocks relative to one another using model features, then use the
ranks to form a portfolio; the target variable, universe, rebalance
frequency, and long/short rules need definition. This is a concept-level
interpretation of the title, not a complete trading specification: the
exact model inputs/target, calibration, entry/exit or rebalance rules,
and position sizing are not fully defined here.

## Evidence

* **Gu, Kelly & Xiu (2020), "Empirical Asset Pricing via Machine
  Learning," *Review of Financial Studies* 33(5), 2223–2274:** trees and
  neural networks forecast stock returns best, mostly from momentum,
  liquidity and volatility signals; a neural long-short decile spread
  had an out-of-sample Sharpe of 1.35. (Abstract.)
* **McLean & Pontiff (2016), "Does Academic Research Destroy Stock
  Return Predictability?" *Journal of Finance* 71(1):** anomaly
  portfolio returns are 26% lower out of sample and 58% lower after
  publication. (Abstract.)

## Against, and failure modes

* Anomaly returns shrink after publication (McLean & Pontiff); the
  long-only top-k form keeps only part of the long-short spread.
* Entropy regularisation is shrinkage toward equal weights; it adds no
  information.

## Fit with volatility-ai

Needs a stock universe, point-in-time data and a multi-name book; the
engine trades one ETF and the warehouse holds no stock universe. The
researched form is RK214 (long-only top-k), which stays a reference.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Gu, S., Kelly, B., Xiu, D. (2020). *Review of Financial Studies*
  33(5), 2223–2274. Abstract.
* McLean, R. D., Pontiff, J. (2016). *Journal of Finance* 71(1).
  Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 3812 | Entropic Scholarly Cross-Sectional Stock Ranker Ref-235 | Neural SDEs / Adversarial robustness / Stock options hedging | 9740 | 5621 | No |
| 3898 | Entropic Scholarly Cross-Sectional Stock Ranker Ref-715 | Neural SDEs / Adversarial robustness / Stock options hedging | 9746 | 5632 | No |
| 7460 | Entropic Scholarly Cross-Sectional Stock Ranker Ref-139 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 8247 | 3044 | No |
| 7494 | Entropic Scholarly Cross-Sectional Stock Ranker Ref-619 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 8288 | 3161 | No |
| 8693 | Entropic Scholarly Cross-Sectional Stock Ranker Ref-43 | Topological data analysis / Betti persistence / Stock pairs | 2129 | 3021 | No |
| 8804 | Entropic Scholarly Cross-Sectional Stock Ranker Ref-331 | Delay differential equations / Controlled ODEs / Stock execution | 3879 | 1031 | No |
| 8843 | Entropic Scholarly Cross-Sectional Stock Ranker Ref-427 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12529 | 12544 | No |
| 8884 | Entropic Scholarly Cross-Sectional Stock Ranker Ref-523 | Topological data analysis / Betti persistence / Stock pairs | 2161 | 3138 | No |
| 8995 | Entropic Scholarly Cross-Sectional Stock Ranker Ref-811 | Delay differential equations / Controlled ODEs / Stock execution | 3906 | 1066 | No |
| 9034 | Entropic Scholarly Cross-Sectional Stock Ranker Ref-907 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12540 | 12557 | No |
