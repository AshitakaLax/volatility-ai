# Adversarially robust approach to cross-sectional stock ranking

**Concept page** · shared by **10** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #3,857) ·
researched 2026-10-30

| | |
|---|---|
| Task | Cross-sectional stock ranking |
| Method | Adversarial training |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** Stock ranking needs a stock universe and a multi-name book; the project trades one ETF and holds no stock data. |
| Implemented in volatility-ai | Cross-sectional rankers are research code (`cross_section`, RK214). |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK7, RK214, RK291, RK89 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Adversarial Scholarly
Cross-Sectional Stock Ranker Ref-475") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Score stocks against one another and form a portfolio from the ranks.
The adversarially robust version trains against worst-case perturbations
of its inputs. I found no study of this method on this task.

## The CSV's description

Proposed adversarially robust approach to cross-sectional stock ranking:
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
* Adversarial robustness defends against manipulated inputs; market data
  are noisy, not adversarial.

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
| 3857 | Adversarial Scholarly Cross-Sectional Stock Ranker Ref-475 | Neural SDEs / Adversarial robustness / Stock options hedging | 9742 | 5625 | No |
| 3943 | Adversarial Scholarly Cross-Sectional Stock Ranker Ref-955 | Neural SDEs / Adversarial robustness / Stock options hedging | 9748 | 5636 | No |
| 7477 | Adversarial Scholarly Cross-Sectional Stock Ranker Ref-379 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 8266 | 3104 | No |
| 7511 | Adversarial Scholarly Cross-Sectional Stock Ranker Ref-859 | Riemannian manifold / Geodesic gradient descent / Stock portfolio optimization | 8307 | 3221 | No |
| 8710 | Adversarial Scholarly Cross-Sectional Stock Ranker Ref-91 | Delay differential equations / Controlled ODEs / Stock execution | 3865 | 1012 | No |
| 8749 | Adversarial Scholarly Cross-Sectional Stock Ranker Ref-187 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12522 | 12539 | No |
| 8787 | Adversarial Scholarly Cross-Sectional Stock Ranker Ref-283 | Topological data analysis / Betti persistence / Stock pairs | 2145 | 3079 | No |
| 8901 | Adversarial Scholarly Cross-Sectional Stock Ranker Ref-571 | Delay differential equations / Controlled ODEs / Stock execution | 3892 | 1047 | No |
| 8940 | Adversarial Scholarly Cross-Sectional Stock Ranker Ref-667 | Reinforcement learning / Actor-critic PPO / ETF arbitrage | 12533 | 12552 | No |
| 8978 | Adversarial Scholarly Cross-Sectional Stock Ranker Ref-763 | Topological data analysis / Betti persistence / Stock pairs | 2177 | 3196 | No |
