# Markov-state-based approach to macro-driven index allocation

**Concept page** · shared by **63** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,840) ·
researched 2026-10-30

| | |
|---|---|
| Task | Macro-driven index allocation |
| Method | Hidden Markov / regime-switching states |
| Fit with this project | ⏳ reference only · background, nothing to build now |
| Useful for volatility-ai | **Reference only.** A hidden Markov model is a sound way to combine macro inputs, but single macro predictors fail out of sample (Welch & Goyal 2008); background beside RK41. |
| Implemented in volatility-ai | Macro series are in the warehouse with publication lags (`engine/warehouse/queries.py`); no macro allocator. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK41, RK211, RK217, N5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Markovian Scholarly
Macro-Driven Index Allocator Sys-22") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Use macroeconomic and market indicators, lagged by their publication
dates, to shift allocations among index-linked assets. The Markov-state
version infers hidden states (calm, turbulent, crisis) and conditions on
the current one. I found no study of this method on this task.

## The CSV's description

Proposed Markov-state-based approach to macro-driven index allocation:
Use macroeconomic and market indicators to adjust allocations among
index-linked assets, with explicit publication lags and rebalance rules
needed to prevent look-ahead bias. This is a concept-level
interpretation of the title, not a complete trading specification: the
exact model inputs/target, calibration, entry/exit or rebalance rules,
and position sizing are not fully defined here.

## Evidence

* **Welch & Goyal (2008), "A Comprehensive Look at the Empirical
  Performance of Equity Premium Prediction," *Review of Financial
  Studies* 21(4), 1455–1508:** the standard macro and valuation
  predictors of the equity premium performed poorly out of sample.
  (Standard reference.)
* **Rapach, Strauss & Zhou (2010), *Review of Financial Studies* 23(2),
  821–862:** combining the individual predictors' forecasts gives small
  but consistent out-of-sample gains, linked to the business cycle.
  (Abstract.)

## Against, and failure modes

* Macro data are monthly or quarterly, revised and published with lags;
  a few decades give few independent observations.
* Each predictor alone has failed out of sample (Welch & Goyal); gains
  come only from combining many, and they are small.
* States are clear only after the fact; causal (filtered) state
  probabilities lag turning points.

## Fit with volatility-ai

The warehouse already holds macro series, shifted by their publication
lag before the as-of join (`engine/warehouse/queries.py`), so a macro
input is possible. The evidence says expect little; a macro signal would
be one more regime input, tested against the NATR exit like any other.
The inflation-regime rotation (RK41) is the researched candidate.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Welch, I., Goyal, A. (2008). *Review of Financial Studies* 21(4),
  1455–1508. Standard reference.
* Rapach, D. E., Strauss, J. K., Zhou, G. (2010). *Review of Financial
  Studies* 23(2), 821–862. Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 1840 | Markovian Scholarly Macro-Driven Index Allocator Sys-22 | Robust optimization / Distributionally robust CVaR / Index tracking | 8323 | 11340 | No |
| 1889 | Markovian Scholarly Macro-Driven Index Allocator Sys-502 | Robust optimization / Distributionally robust CVaR / Index tracking | 8363 | 11350 | No |
| 1938 | Markovian Scholarly Macro-Driven Index Allocator Sys-982 | Robust optimization / Distributionally robust CVaR / Index tracking | 8403 | 11360 | No |
| 1987 | Markovian Scholarly Macro-Driven Index Allocator Sys-1462 | Robust optimization / Distributionally robust CVaR / Index tracking | 8443 | 11370 | No |
| 2036 | Markovian Scholarly Macro-Driven Index Allocator Sys-1942 | Robust optimization / Distributionally robust CVaR / Index tracking | 8483 | 11380 | No |
| 2061 | Markovian Scholarly Macro-Driven Index Allocator Mod-202 | Robust optimization / Distributionally robust CVaR / Index tracking | 8503 | 11386 | No |
| 2114 | Markovian Scholarly Macro-Driven Index Allocator Mod-682 | Robust optimization / Distributionally robust CVaR / Index tracking | 8541 | 11400 | No |
| 2167 | Markovian Scholarly Macro-Driven Index Allocator Mod-1162 | Robust optimization / Distributionally robust CVaR / Index tracking | 8579 | 11414 | No |
| 2220 | Markovian Scholarly Macro-Driven Index Allocator Mod-1642 | Robust optimization / Distributionally robust CVaR / Index tracking | 8617 | 11428 | No |
| 2273 | Markovian Scholarly Macro-Driven Index Allocator Mod-2122 | Robust optimization / Distributionally robust CVaR / Index tracking | 8655 | 11442 | No |
| 2326 | Markovian Scholarly Macro-Driven Index Allocator Mod-2602 | Robust optimization / Distributionally robust CVaR / Index tracking | 8693 | 11456 | No |
| 2379 | Markovian Scholarly Macro-Driven Index Allocator Mod-3082 | Robust optimization / Distributionally robust CVaR / Index tracking | 8731 | 11470 | No |
| 2432 | Markovian Scholarly Macro-Driven Index Allocator Mod-3562 | Robust optimization / Distributionally robust CVaR / Index tracking | 8769 | 11484 | No |
| 3221 | Markovian Scholarly Macro-Driven Index Allocator Sys-214 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6599 | 3298 | No |
| 3243 | Markovian Scholarly Macro-Driven Index Allocator Sys-694 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6638 | 3393 | No |
| 3265 | Markovian Scholarly Macro-Driven Index Allocator Sys-1174 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6677 | 3488 | No |
| 3287 | Markovian Scholarly Macro-Driven Index Allocator Sys-1654 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6716 | 3583 | No |
| 3317 | Markovian Scholarly Macro-Driven Index Allocator Mod-394 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6778 | 3731 | No |
| 3335 | Markovian Scholarly Macro-Driven Index Allocator Mod-874 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6820 | 3826 | No |
| 3353 | Markovian Scholarly Macro-Driven Index Allocator Mod-1354 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6862 | 3921 | No |
| 3371 | Markovian Scholarly Macro-Driven Index Allocator Mod-1834 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6904 | 4016 | No |
| 3389 | Markovian Scholarly Macro-Driven Index Allocator Mod-2314 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6946 | 4111 | No |
| 3407 | Markovian Scholarly Macro-Driven Index Allocator Mod-2794 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 6988 | 4206 | No |
| 3425 | Markovian Scholarly Macro-Driven Index Allocator Mod-3274 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7030 | 4301 | No |
| 3443 | Markovian Scholarly Macro-Driven Index Allocator Mod-3754 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7072 | 4396 | No |
| 7530 | Markovian Scholarly Macro-Driven Index Allocator Sys-118 | Attention networks / Transformer encoders / Stock alpha generation | 3248 | 3278 | No |
| 7561 | Markovian Scholarly Macro-Driven Index Allocator Sys-598 | Attention networks / Transformer encoders / Stock alpha generation | 3272 | 3373 | No |
| 7592 | Markovian Scholarly Macro-Driven Index Allocator Sys-1078 | Attention networks / Transformer encoders / Stock alpha generation | 3296 | 3468 | No |
| 7623 | Markovian Scholarly Macro-Driven Index Allocator Sys-1558 | Attention networks / Transformer encoders / Stock alpha generation | 3320 | 3563 | No |
| 7669 | Markovian Scholarly Macro-Driven Index Allocator Mod-298 | Attention networks / Transformer encoders / Stock alpha generation | 3354 | 3710 | No |
| 7701 | Markovian Scholarly Macro-Driven Index Allocator Mod-778 | Attention networks / Transformer encoders / Stock alpha generation | 3374 | 3805 | No |
| 7733 | Markovian Scholarly Macro-Driven Index Allocator Mod-1258 | Attention networks / Transformer encoders / Stock alpha generation | 3394 | 3900 | No |
| 7765 | Markovian Scholarly Macro-Driven Index Allocator Mod-1738 | Attention networks / Transformer encoders / Stock alpha generation | 3414 | 3995 | No |
| 7797 | Markovian Scholarly Macro-Driven Index Allocator Mod-2218 | Attention networks / Transformer encoders / Stock alpha generation | 3434 | 4090 | No |
| 7829 | Markovian Scholarly Macro-Driven Index Allocator Mod-2698 | Attention networks / Transformer encoders / Stock alpha generation | 3454 | 4185 | No |
| 7861 | Markovian Scholarly Macro-Driven Index Allocator Mod-3178 | Attention networks / Transformer encoders / Stock alpha generation | 3474 | 4280 | No |
| 7893 | Markovian Scholarly Macro-Driven Index Allocator Mod-3658 | Attention networks / Transformer encoders / Stock alpha generation | 3494 | 4375 | No |
| 9195 | Markovian Scholarly Macro-Driven Index Allocator Sys-310 | Neural operators / Deep operator networks / ETF rotation | 7653 | 3319 | No |
| 9232 | Markovian Scholarly Macro-Driven Index Allocator Sys-406 | Quantum machine learning / Variational circuits / Index prediction | 11358 | 6015 | No |
| 9382 | Markovian Scholarly Macro-Driven Index Allocator Sys-790 | Neural operators / Deep operator networks / ETF rotation | 7657 | 3414 | No |
| 9419 | Markovian Scholarly Macro-Driven Index Allocator Sys-886 | Quantum machine learning / Variational circuits / Index prediction | 11384 | 6030 | No |
| 9569 | Markovian Scholarly Macro-Driven Index Allocator Sys-1270 | Neural operators / Deep operator networks / ETF rotation | 7661 | 3509 | No |
| 9606 | Markovian Scholarly Macro-Driven Index Allocator Sys-1366 | Quantum machine learning / Variational circuits / Index prediction | 11410 | 6045 | No |
| 9756 | Markovian Scholarly Macro-Driven Index Allocator Sys-1750 | Neural operators / Deep operator networks / ETF rotation | 7665 | 3604 | No |
| 9793 | Markovian Scholarly Macro-Driven Index Allocator Sys-1846 | Quantum machine learning / Variational circuits / Index prediction | 11436 | 6060 | No |
| 9856 | Markovian Scholarly Macro-Driven Index Allocator Mod-10 | Neural operators / Deep operator networks / ETF rotation | 7668 | 3653 | No |
| 9894 | Markovian Scholarly Macro-Driven Index Allocator Mod-106 | Quantum machine learning / Variational circuits / Index prediction | 11452 | 6070 | No |
| 10047 | Markovian Scholarly Macro-Driven Index Allocator Mod-490 | Neural operators / Deep operator networks / ETF rotation | 7672 | 3748 | No |
| 10085 | Markovian Scholarly Macro-Driven Index Allocator Mod-586 | Quantum machine learning / Variational circuits / Index prediction | 11479 | 6087 | No |
| 10238 | Markovian Scholarly Macro-Driven Index Allocator Mod-970 | Neural operators / Deep operator networks / ETF rotation | 7676 | 3843 | No |
| 10276 | Markovian Scholarly Macro-Driven Index Allocator Mod-1066 | Quantum machine learning / Variational circuits / Index prediction | 11506 | 6104 | No |
| 10429 | Markovian Scholarly Macro-Driven Index Allocator Mod-1450 | Neural operators / Deep operator networks / ETF rotation | 7680 | 3938 | No |
| 10467 | Markovian Scholarly Macro-Driven Index Allocator Mod-1546 | Quantum machine learning / Variational circuits / Index prediction | 11533 | 6121 | No |
| 10620 | Markovian Scholarly Macro-Driven Index Allocator Mod-1930 | Neural operators / Deep operator networks / ETF rotation | 7684 | 4033 | No |
| 10658 | Markovian Scholarly Macro-Driven Index Allocator Mod-2026 | Quantum machine learning / Variational circuits / Index prediction | 11560 | 6138 | No |
| 10811 | Markovian Scholarly Macro-Driven Index Allocator Mod-2410 | Neural operators / Deep operator networks / ETF rotation | 7688 | 4128 | No |
| 10849 | Markovian Scholarly Macro-Driven Index Allocator Mod-2506 | Quantum machine learning / Variational circuits / Index prediction | 11587 | 6155 | No |
| 11002 | Markovian Scholarly Macro-Driven Index Allocator Mod-2890 | Neural operators / Deep operator networks / ETF rotation | 7692 | 4223 | No |
| 11040 | Markovian Scholarly Macro-Driven Index Allocator Mod-2986 | Quantum machine learning / Variational circuits / Index prediction | 11614 | 6172 | No |
| 11193 | Markovian Scholarly Macro-Driven Index Allocator Mod-3370 | Neural operators / Deep operator networks / ETF rotation | 7696 | 4318 | No |
| 11231 | Markovian Scholarly Macro-Driven Index Allocator Mod-3466 | Quantum machine learning / Variational circuits / Index prediction | 11641 | 6189 | No |
| 11384 | Markovian Scholarly Macro-Driven Index Allocator Mod-3850 | Neural operators / Deep operator networks / ETF rotation | 7700 | 4413 | No |
| 11422 | Markovian Scholarly Macro-Driven Index Allocator Mod-3946 | Quantum machine learning / Variational circuits / Index prediction | 11668 | 6206 | No |
