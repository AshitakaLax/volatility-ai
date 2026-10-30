# Adaptive approach to tail-risk hedging and allocation

**Concept page** · shared by **1** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #3,659) ·
researched 2026-10-30

| | |
|---|---|
| Task | Tail-risk hedging and allocation |
| Method | Adaptive (time-varying parameters or thresholds) |
| Fit with this project | ✅ in use · the project already does this |
| Useful for volatility-ai | **In use.** Volatility targeting is the adaptive form, and the project already runs it (V18, RK22); Harvey et al. (2018) find it shrinks equities' left tail. |
| Implemented in volatility-ai | The tail-risk response is the regime exit (V17, N5), volatility targeting (V18) and the drawdown throttle (V11); no hedge allocation. |
| Evidence | Evidence found (for the task; see the page for the method) |
| Related ledger entries | V17, N5, V11, V18, X5, X8, RK22, RK130 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Adaptive Scholarly
Tail-Risk Hedge Allocator MK-49") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Estimate stress or extreme-loss risk and shift into defensive assets or
hedges to cut downside. The adaptive version lets its parameters or
thresholds move with recent data. The adaptive form with strong evidence
is volatility targeting: cutting exposure when volatility is high raised
equity Sharpe ratios and made left-tail events milder across a century
of data.

## The CSV's description

Proposed adaptive approach to tail-risk hedging and allocation: Estimate
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
* **Moreira & Muir (2017), "Volatility-Managed Portfolios," *Journal of
  Finance* 72(4), 1611–1644:** taking less risk when volatility is high
  gave the market portfolio a 4.9% annual alpha and higher Sharpe
  ratios. (Abstract.)
* **Harvey, Hoyle, Korgaonkar, Rattray, Sargaison & Van Hemert (2018),
  "The Impact of Volatility Targeting," *Journal of Portfolio
  Management* 45(1), 14–33:** over 60+ assets since 1926, volatility
  scaling raised Sharpe ratios for equities and credit and made
  left-tail events less severe for all assets. (Abstract.)

## Against, and failure modes

* Hedges cost carry in calm markets, and a de-risking trigger whipsaws.
* Fast crashes outrun daily triggers (V17's one-day lookahead caveat).
* Parameters re-fitted often chase the recent past unless the adaptation
  itself is tested out of sample.

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
* Moreira, A., Muir, T. (2017). "Volatility-Managed Portfolios."
  *Journal of Finance* 72(4), 1611–1644. doi:10.1111/jofi.12513.
  Abstract.
* Harvey, C. R., et al. (2018). "The Impact of Volatility Targeting."
  *Journal of Portfolio Management* 45(1), 14–33. Abstract.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 3659 | Adaptive Scholarly Tail-Risk Hedge Allocator MK-49 | Geometric deep learning / Riemannian optimization / Risk parity | 8168 | 2840 | No |
