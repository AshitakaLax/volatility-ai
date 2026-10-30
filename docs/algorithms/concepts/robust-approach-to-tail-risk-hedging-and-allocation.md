# Robust approach to tail-risk hedging and allocation

**Concept page** · shared by **5** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #3,700) ·
researched 2026-10-30

| | |
|---|---|
| Task | Tail-risk hedging and allocation |
| Method | Robust (outlier-resistant) estimation |
| Fit with this project | ⏳ reference only · background, nothing to build now |
| Useful for volatility-ai | **Reference only.** Robust estimation is an established risk tool, but this book de-risks by exiting or scaling, not by hedging; it matters only if it beats the inputs already used. Background. |
| Implemented in volatility-ai | The tail-risk response is the regime exit (V17, N5), volatility targeting (V18) and the drawdown throttle (V11); no hedge allocation. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | V17, N5, V11, V18, X5, X8, RK22, RK130 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Robust Scholarly Tail-Risk
Hedge Allocator Alpha-84") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Estimate stress or extreme-loss risk and shift into defensive assets or
hedges to cut downside. The robust version estimates its inputs with
outlier-resistant statistics, so a few extreme days do not drive the
result. I found no study of this method on this task.

## The CSV's description

Proposed robust approach to tail-risk hedging and allocation: Estimate
stress or extreme-loss risk and allocate defensive assets or hedges to
reduce portfolio downside exposure. This is a concept-level
interpretation of the title, not a complete trading specification: the
exact model inputs/target, calibration, entry/exit or rebalance rules,
and position sizing are not fully defined here.

## Evidence

* **Israelov (2019), "Pathetic Protection: The Elusive Benefits of
  Protective Puts," *Journal of Alternative Investments*:**
  put-protected portfolios had worse drawdowns per unit of expected
  return than portfolios that simply held less equity. (Summaries.)
* **Hurst, Ooi & Pedersen (2017), "A Century of Evidence on
  Trend-Following Investing," *Journal of Portfolio Management*:**
  time-series momentum was positive in 8 of the 10 largest drawdowns of
  a 60/40 portfolio since 1880. (Abstract.)

## Against, and failure modes

* Hedges cost carry in calm markets, and a de-risking trigger whipsaws.
* Fast crashes outrun daily triggers (V17's one-day lookahead caveat).
* Robust estimators trade efficiency for stability; in calm data they
  add little.

## Fit with volatility-ai

This project's tail-risk answer is to step out or scale down rather than
hedge: the regime exit (V17, N5), volatility targeting (V18) and the
drawdown throttle (V11). Treasuries as the hedge failed in 2022 (X5), a
long-volatility sleeve is excluded by the owner (X8), and options are
outside the instrument rule. A tail-risk model earns a place only as a
better input to the existing exit or scaling.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Israelov, R. (2019). "Pathetic Protection." *Journal of Alternative
  Investments*. Summaries.
* Hurst, B., Ooi, Y. H., Pedersen, L. H. (2017). "A Century of Evidence
  on Trend-Following Investing." *Journal of Portfolio Management*.
  Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 3700 | Robust Scholarly Tail-Risk Hedge Allocator Alpha-84 | Operator theory / Koopman spectral / ETF allocation | 2085 | 979 | No |
| 3717 | Robust Scholarly Tail-Risk Hedge Allocator Alpha-184 | Operator theory / Koopman spectral / ETF allocation | 8199 | 986 | No |
| 3734 | Robust Scholarly Tail-Risk Hedge Allocator Alpha-284 | Operator theory / Koopman spectral / ETF allocation | 6476 | 2962 | No |
| 3751 | Robust Scholarly Tail-Risk Hedge Allocator Alpha-384 | Operator theory / Koopman spectral / ETF allocation | 2115 | 998 | No |
| 3768 | Robust Scholarly Tail-Risk Hedge Allocator Alpha-484 | Operator theory / Koopman spectral / ETF allocation | 8232 | 1005 | No |
