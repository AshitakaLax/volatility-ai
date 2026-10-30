# Multi-scale approach to tail-risk hedging and allocation

**Concept page** · shared by **2** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #1,623) ·
researched 2026-10-30

| | |
|---|---|
| Task | Tail-risk hedging and allocation |
| Method | Multi-scale (several horizons combined) |
| Fit with this project | ⏳ worth testing · a concrete test is below |
| Useful for volatility-ai | **Worth testing.** HAR-RV, a daily-weekly-monthly volatility model, is a well-tested forecaster (Corsi 2009); test it as the volatility input to the existing targeting and regime rules. |
| Implemented in volatility-ai | The tail-risk response is the regime exit (V17, N5), volatility targeting (V18) and the drawdown throttle (V11); no hedge allocation. |
| Evidence | Evidence found (for the task; see the page for the method) |
| Related ledger entries | V17, N5, V11, V18, X5, X8, RK22, RK130 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Multi-Scale Scholarly
Tail-Risk Hedge Allocator Ver-62") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Estimate stress or extreme-loss risk and shift into defensive assets or
hedges to cut downside. The multi-scale version combines signals or
estimates measured over several horizons. The multi-scale tool with the
best record is HAR-RV, which forecasts volatility from its daily, weekly
and monthly averages and reproduces long memory with a plain regression.

## The CSV's description

Proposed multi-scale approach to tail-risk hedging and allocation:
Estimate stress or extreme-loss risk and allocate defensive assets or
hedges to reduce portfolio downside exposure. This is a concept-level
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
* **Corsi (2009), "A Simple Approximate Long-Memory Model of Realized
  Volatility," *Journal of Financial Econometrics* 7(2), 174–196:**
  HAR-RV regresses realised volatility on its daily, weekly and monthly
  averages; simple, it reproduces long memory and fat tails and
  forecasts well out of sample. (Abstract.)

## Against, and failure modes

* Hedges cost carry in calm markets, and a de-risking trigger whipsaws.
* Fast crashes outrun daily triggers (V17's one-day lookahead caveat).
* More horizons mean more weights to choose, and the blend can be
  overfitted.

## Fit with volatility-ai

This project's tail-risk answer is to step out or scale down rather than
hedge: the regime exit (V17, N5), volatility targeting (V18) and the
drawdown throttle (V11). Treasuries as the hedge failed in 2022 (X5), a
long-volatility sleeve is excluded by the owner (X8), and options are
outside the instrument rule. A tail-risk model earns a place only as a
better input to the existing exit or scaling.

## How to test it here

Fit HAR on QQQ's daily realised volatility (from minute bars where the
warehouse has them, else squared returns), causally, and feed its
forecast to V18's targeting and the NATR regime in place of trailing
volatility; compare drawdown and Calmar.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Israelov, R. (2019). "Pathetic Protection." *Journal of Alternative
  Investments*. Summaries.
* Hurst, B., Ooi, Y. H., Pedersen, L. H. (2017). "A Century of Evidence
  on Trend-Following Investing." *Journal of Portfolio Management*.
  Abstract.
* Corsi, F. (2009). "A Simple Approximate Long-Memory Model of Realized
  Volatility." *Journal of Financial Econometrics* 7(2), 174–196.
  Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 1623 | Multi-Scale Scholarly Tail-Risk Hedge Allocator Ver-62 | Robust statistics / Mean-variance / Index tracking | 2060 | 2863 | No |
| 1647 | Multi-Scale Scholarly Tail-Risk Hedge Allocator Ver-162 | Robust statistics / Mean-variance / Index tracking | 391 | 973 | No |
