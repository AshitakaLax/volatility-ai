# Spectral approach to macro-driven index allocation

**Concept page** · shared by **74** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,740) ·
researched 2026-10-30

| | |
|---|---|
| Task | Macro-driven index allocation |
| Method | Spectral (frequency-domain) decomposition |
| Fit with this project | ⏳ reference only · background, nothing to build now |
| Useful for volatility-ai | **Reference only.** A spectral method is a sound way to combine macro inputs, but single macro predictors fail out of sample (Welch & Goyal 2008); background beside RK41. |
| Implemented in volatility-ai | Macro series are in the warehouse with publication lags (`engine/warehouse/queries.py`); no macro allocator. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | RK41, RK211, RK217, N5 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Spectral Scholarly
Macro-Driven Index Allocator Ref-122") combine a method word,
"Scholarly", a task and a serial number, and the rows' references are
software libraries or papers the CSV's own review calls unrelated. There
is no specific algorithm behind each name to research, so this page
researches what the members share: the task, done with the method.

## In one paragraph

Use macroeconomic and market indicators, lagged by their publication
dates, to shift allocations among index-linked assets. The spectral
version works in the frequency domain, filtering or weighting components
by cycle length. I found no study of this method on this task.

## The CSV's description

Proposed spectral approach to macro-driven index allocation: Use
macroeconomic and market indicators to adjust allocations among
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
* Spectral estimates need long stationary windows; market cycles are
  neither.

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
| 1740 | Spectral Scholarly Macro-Driven Index Allocator Ref-122 | Robust optimization / Distributionally robust CVaR / Index tracking | 4652 | 3040 | No |
| 1795 | Spectral Scholarly Macro-Driven Index Allocator Ref-602 | Robust optimization / Distributionally robust CVaR / Index tracking | 4679 | 3157 | No |
| 2501 | Spectral Scholarly Macro-Driven Index Allocator Eng-202 | Robust optimization / Distributionally robust CVaR / Index tracking | 8821 | 11501 | No |
| 2556 | Spectral Scholarly Macro-Driven Index Allocator Eng-682 | Robust optimization / Distributionally robust CVaR / Index tracking | 8857 | 11515 | No |
| 2611 | Spectral Scholarly Macro-Driven Index Allocator Eng-1162 | Robust optimization / Distributionally robust CVaR / Index tracking | 8893 | 11529 | No |
| 2666 | Spectral Scholarly Macro-Driven Index Allocator Eng-1642 | Robust optimization / Distributionally robust CVaR / Index tracking | 8929 | 11543 | No |
| 2721 | Spectral Scholarly Macro-Driven Index Allocator Eng-2122 | Robust optimization / Distributionally robust CVaR / Index tracking | 8965 | 11557 | No |
| 2776 | Spectral Scholarly Macro-Driven Index Allocator Eng-2602 | Robust optimization / Distributionally robust CVaR / Index tracking | 9001 | 11571 | No |
| 2831 | Spectral Scholarly Macro-Driven Index Allocator Eng-3082 | Robust optimization / Distributionally robust CVaR / Index tracking | 9037 | 11585 | No |
| 2886 | Spectral Scholarly Macro-Driven Index Allocator Eng-3562 | Robust optimization / Distributionally robust CVaR / Index tracking | 9073 | 11599 | No |
| 2941 | Spectral Scholarly Macro-Driven Index Allocator Eng-4042 | Robust optimization / Distributionally robust CVaR / Index tracking | 9109 | 11613 | No |
| 2996 | Spectral Scholarly Macro-Driven Index Allocator Eng-4522 | Robust optimization / Distributionally robust CVaR / Index tracking | 9145 | 11627 | No |
| 3051 | Spectral Scholarly Macro-Driven Index Allocator Eng-5002 | Robust optimization / Distributionally robust CVaR / Index tracking | 9181 | 11641 | No |
| 3106 | Spectral Scholarly Macro-Driven Index Allocator Eng-5482 | Robust optimization / Distributionally robust CVaR / Index tracking | 9217 | 11655 | No |
| 3161 | Spectral Scholarly Macro-Driven Index Allocator Eng-5962 | Robust optimization / Distributionally robust CVaR / Index tracking | 9253 | 11669 | No |
| 3186 | Spectral Scholarly Macro-Driven Index Allocator Ref-314 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5393 | 8437 | No |
| 3202 | Spectral Scholarly Macro-Driven Index Allocator Ref-794 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 5397 | 8457 | No |
| 3466 | Spectral Scholarly Macro-Driven Index Allocator Eng-394 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7129 | 4521 | No |
| 3482 | Spectral Scholarly Macro-Driven Index Allocator Eng-874 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7171 | 4614 | No |
| 3498 | Spectral Scholarly Macro-Driven Index Allocator Eng-1354 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7213 | 4707 | No |
| 3514 | Spectral Scholarly Macro-Driven Index Allocator Eng-1834 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7255 | 4800 | No |
| 3530 | Spectral Scholarly Macro-Driven Index Allocator Eng-2314 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7297 | 4893 | No |
| 3546 | Spectral Scholarly Macro-Driven Index Allocator Eng-2794 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7339 | 4986 | No |
| 3562 | Spectral Scholarly Macro-Driven Index Allocator Eng-3274 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7381 | 5079 | No |
| 3578 | Spectral Scholarly Macro-Driven Index Allocator Eng-3754 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7423 | 5172 | No |
| 3594 | Spectral Scholarly Macro-Driven Index Allocator Eng-4234 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7465 | 5265 | No |
| 3610 | Spectral Scholarly Macro-Driven Index Allocator Eng-4714 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7507 | 5358 | No |
| 3626 | Spectral Scholarly Macro-Driven Index Allocator Eng-5194 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7549 | 5451 | No |
| 3642 | Spectral Scholarly Macro-Driven Index Allocator Eng-5674 | Vine copulas / Regularized decision trees / Multi-factor stock allocation | 7591 | 5544 | No |
| 7467 | Spectral Scholarly Macro-Driven Index Allocator Ref-218 | Attention networks / Transformer encoders / Stock alpha generation | 12824 | 11883 | No |
| 7501 | Spectral Scholarly Macro-Driven Index Allocator Ref-698 | Attention networks / Transformer encoders / Stock alpha generation | 12829 | 11906 | No |
| 7938 | Spectral Scholarly Macro-Driven Index Allocator Eng-298 | Attention networks / Transformer encoders / Stock alpha generation | 3520 | 4503 | No |
| 7972 | Spectral Scholarly Macro-Driven Index Allocator Eng-778 | Attention networks / Transformer encoders / Stock alpha generation | 3540 | 4596 | No |
| 8006 | Spectral Scholarly Macro-Driven Index Allocator Eng-1258 | Attention networks / Transformer encoders / Stock alpha generation | 3560 | 4689 | No |
| 8040 | Spectral Scholarly Macro-Driven Index Allocator Eng-1738 | Attention networks / Transformer encoders / Stock alpha generation | 3580 | 4782 | No |
| 8074 | Spectral Scholarly Macro-Driven Index Allocator Eng-2218 | Attention networks / Transformer encoders / Stock alpha generation | 3600 | 4875 | No |
| 8108 | Spectral Scholarly Macro-Driven Index Allocator Eng-2698 | Attention networks / Transformer encoders / Stock alpha generation | 3620 | 4968 | No |
| 8142 | Spectral Scholarly Macro-Driven Index Allocator Eng-3178 | Attention networks / Transformer encoders / Stock alpha generation | 3640 | 5061 | No |
| 8176 | Spectral Scholarly Macro-Driven Index Allocator Eng-3658 | Attention networks / Transformer encoders / Stock alpha generation | 3660 | 5154 | No |
| 8210 | Spectral Scholarly Macro-Driven Index Allocator Eng-4138 | Attention networks / Transformer encoders / Stock alpha generation | 3680 | 5247 | No |
| 8244 | Spectral Scholarly Macro-Driven Index Allocator Eng-4618 | Attention networks / Transformer encoders / Stock alpha generation | 3700 | 5340 | No |
| 8278 | Spectral Scholarly Macro-Driven Index Allocator Eng-5098 | Attention networks / Transformer encoders / Stock alpha generation | 3720 | 5433 | No |
| 8312 | Spectral Scholarly Macro-Driven Index Allocator Eng-5578 | Attention networks / Transformer encoders / Stock alpha generation | 3740 | 5526 | No |
| 8685 | Spectral Scholarly Macro-Driven Index Allocator Ref-26 | Quantum machine learning / Variational circuits / Index prediction | 13983 | 13981 | No |
| 8838 | Spectral Scholarly Macro-Driven Index Allocator Ref-410 | Neural operators / Deep operator networks / ETF rotation | 9304 | 7606 | No |
| 8876 | Spectral Scholarly Macro-Driven Index Allocator Ref-506 | Quantum machine learning / Variational circuits / Index prediction | 13987 | 13989 | No |
| 9029 | Spectral Scholarly Macro-Driven Index Allocator Ref-890 | Neural operators / Deep operator networks / ETF rotation | 9320 | 7630 | No |
| 9067 | Spectral Scholarly Macro-Driven Index Allocator Ref-986 | Quantum machine learning / Variational circuits / Index prediction | 13991 | 13997 | No |
| 11446 | Spectral Scholarly Macro-Driven Index Allocator Eng-10 | Neural operators / Deep operator networks / ETF rotation | 7702 | 4444 | No |
| 11485 | Spectral Scholarly Macro-Driven Index Allocator Eng-106 | Quantum machine learning / Variational circuits / Index prediction | 11678 | 6215 | No |
| 11637 | Spectral Scholarly Macro-Driven Index Allocator Eng-490 | Neural operators / Deep operator networks / ETF rotation | 7706 | 4537 | No |
| 11676 | Spectral Scholarly Macro-Driven Index Allocator Eng-586 | Quantum machine learning / Variational circuits / Index prediction | 11703 | 6236 | No |
| 11828 | Spectral Scholarly Macro-Driven Index Allocator Eng-970 | Neural operators / Deep operator networks / ETF rotation | 7710 | 4630 | No |
| 11867 | Spectral Scholarly Macro-Driven Index Allocator Eng-1066 | Quantum machine learning / Variational circuits / Index prediction | 11728 | 6257 | No |
| 12019 | Spectral Scholarly Macro-Driven Index Allocator Eng-1450 | Neural operators / Deep operator networks / ETF rotation | 7714 | 4723 | No |
| 12058 | Spectral Scholarly Macro-Driven Index Allocator Eng-1546 | Quantum machine learning / Variational circuits / Index prediction | 11753 | 6278 | No |
| 12210 | Spectral Scholarly Macro-Driven Index Allocator Eng-1930 | Neural operators / Deep operator networks / ETF rotation | 7718 | 4816 | No |
| 12249 | Spectral Scholarly Macro-Driven Index Allocator Eng-2026 | Quantum machine learning / Variational circuits / Index prediction | 11778 | 6299 | No |
| 12401 | Spectral Scholarly Macro-Driven Index Allocator Eng-2410 | Neural operators / Deep operator networks / ETF rotation | 7722 | 4909 | No |
| 12440 | Spectral Scholarly Macro-Driven Index Allocator Eng-2506 | Quantum machine learning / Variational circuits / Index prediction | 11803 | 6320 | No |
| 12592 | Spectral Scholarly Macro-Driven Index Allocator Eng-2890 | Neural operators / Deep operator networks / ETF rotation | 7726 | 5002 | No |
| 12631 | Spectral Scholarly Macro-Driven Index Allocator Eng-2986 | Quantum machine learning / Variational circuits / Index prediction | 11828 | 6341 | No |
| 12783 | Spectral Scholarly Macro-Driven Index Allocator Eng-3370 | Neural operators / Deep operator networks / ETF rotation | 7730 | 5095 | No |
| 12822 | Spectral Scholarly Macro-Driven Index Allocator Eng-3466 | Quantum machine learning / Variational circuits / Index prediction | 11853 | 6362 | No |
| 12974 | Spectral Scholarly Macro-Driven Index Allocator Eng-3850 | Neural operators / Deep operator networks / ETF rotation | 7734 | 5188 | No |
| 13013 | Spectral Scholarly Macro-Driven Index Allocator Eng-3946 | Quantum machine learning / Variational circuits / Index prediction | 11878 | 6383 | No |
| 13165 | Spectral Scholarly Macro-Driven Index Allocator Eng-4330 | Neural operators / Deep operator networks / ETF rotation | 7738 | 5281 | No |
| 13204 | Spectral Scholarly Macro-Driven Index Allocator Eng-4426 | Quantum machine learning / Variational circuits / Index prediction | 11903 | 6404 | No |
| 13356 | Spectral Scholarly Macro-Driven Index Allocator Eng-4810 | Neural operators / Deep operator networks / ETF rotation | 7742 | 5374 | No |
| 13395 | Spectral Scholarly Macro-Driven Index Allocator Eng-4906 | Quantum machine learning / Variational circuits / Index prediction | 11928 | 6425 | No |
| 13547 | Spectral Scholarly Macro-Driven Index Allocator Eng-5290 | Neural operators / Deep operator networks / ETF rotation | 7746 | 5467 | No |
| 13586 | Spectral Scholarly Macro-Driven Index Allocator Eng-5386 | Quantum machine learning / Variational circuits / Index prediction | 11953 | 6446 | No |
| 13738 | Spectral Scholarly Macro-Driven Index Allocator Eng-5770 | Neural operators / Deep operator networks / ETF rotation | 7750 | 5560 | No |
| 13777 | Spectral Scholarly Macro-Driven Index Allocator Eng-5866 | Quantum machine learning / Variational circuits / Index prediction | 11978 | 6467 | No |
