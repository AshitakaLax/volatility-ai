# Neural-network-based approach to tail-risk hedging and allocation

**Concept page** · shared by **5** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #3,687) ·
researched 2026-10-30

| | |
|---|---|
| Task | Tail-risk hedging and allocation |
| Method | Neural networks |
| Fit with this project | ⛔ not useful · out of scope or without evidence |
| Useful for volatility-ai | **Not useful.** No published evidence of neural networks forecasting tail risk better than volatility itself; the project's volatility rules (V17, V18) are the bar. |
| Implemented in volatility-ai | The tail-risk response is the regime exit (V17, N5), volatility targeting (V18) and the drawdown throttle (V11); no hedge allocation. |
| Evidence | Unable to find more details (no study of this method on this task) |
| Related ledger entries | V17, N5, V11, V18, X5, X8, RK22, RK130 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Neural Scholarly Tail-Risk
Hedge Allocator Alpha-4") combine a method word, "Scholarly", a task and
a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Estimate stress or extreme-loss risk and shift into defensive assets or
hedges to cut downside. The neural-network version fits a neural network
to the task. I found no study of this method on this task.

## The CSV's description

Proposed neural-network-based approach to tail-risk hedging and
allocation: Estimate stress or extreme-loss risk and allocate defensive
assets or hedges to reduce portfolio downside exposure. This is a
concept-level interpretation of the title, not a complete trading
specification: the exact model inputs/target, calibration, entry/exit or
rebalance rules, and position sizing are not fully defined here.

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
* Neural forecasts on one index have not reliably beaten simple rules;
  an LSTM's stock picks were largely short-term reversal (Fischer &
  Krauss 2018, RK292).

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
| 3687 | Neural Scholarly Tail-Risk Hedge Allocator Alpha-4 | Operator theory / Koopman spectral / ETF allocation | 8179 | 974 | No |
| 3704 | Neural Scholarly Tail-Risk Hedge Allocator Alpha-104 | Operator theory / Koopman spectral / ETF allocation | 6465 | 2922 | No |
| 3721 | Neural Scholarly Tail-Risk Hedge Allocator Alpha-204 | Operator theory / Koopman spectral / ETF allocation | 2097 | 987 | No |
| 3738 | Neural Scholarly Tail-Risk Hedge Allocator Alpha-304 | Operator theory / Koopman spectral / ETF allocation | 8212 | 993 | No |
| 3755 | Neural Scholarly Tail-Risk Hedge Allocator Alpha-404 | Operator theory / Koopman spectral / ETF allocation | 6483 | 2990 | No |
