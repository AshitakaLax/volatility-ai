# Adaptive approach to regime-aware allocation

**Concept page** · shared by **2** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #3,652) ·
researched 2026-10-30

| | |
|---|---|
| Task | Regime-aware allocation |
| Method | Adaptive (time-varying parameters or thresholds) |
| Fit with this project | ✅ in use · the project already does this |
| Useful for volatility-ai | **In use.** The project's regime exit already is one: NATR measured against its own trailing median, an adaptive threshold (V17, causal N5). |
| Implemented in volatility-ai | The NATR regime exit (V17, causal N5) runs through the Ultimate family's `lots_to_liquidate` and `allow_signal_exit`; HMM and Gaussian-mixture regimes are research code (C-R3). |
| Evidence | Evidence found (for the task; see the page for the method) |
| Related ledger entries | V17, N5, N6, C-R3, RK102, RK104 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Adaptive Scholarly Macro
Regime Switcher MK-9") combine a method word, "Scholarly", a task and a
serial number, and the rows' references are software libraries or papers
the CSV's own review calls unrelated. There is no specific algorithm
behind each name to research, so this page researches what the members
share: the task, done with the method.

## In one paragraph

Infer the market's state from prices, volatility or macro data and vary
exposure by regime. The adaptive version lets its parameters or
thresholds move with recent data. The project's strongest result is an
adaptive regime of this kind: the volatility threshold is NATR's own
trailing median, so it moves with the market.

## The CSV's description

Proposed adaptive approach to regime-aware allocation: Infer changing
market states from available price, volatility, or macroeconomic signals
and vary portfolio exposure by estimated regime; regime labels and
transition rules require specification. This is a concept-level
interpretation of the title, not a complete trading specification: the
exact model inputs/target, calibration, entry/exit or rebalance rules,
and position sizing are not fully defined here.

## Evidence

* **Nystrup, Hansson, Madsen & Lindström (2016), *Journal of Portfolio
  Management* 42(1), 103–109:** regime-based allocation can beat static
  weights; later work reports reduced drawdowns. (Abstract.)
* **Kritzman, Page & Turkington (2012), *Financial Analysts Journal*
  68(3):** Markov-switching regimes forecast out of sample and used to
  tilt a stock/bond/cash mix beat static allocation (see RK102).
  (Abstract.)
* **This repository (V17):** NATR(10) below its 100-day median,
  liquidating on the flip, gave 38.64% CAGR at 26.68% maximum drawdown
  against TQQQ's 39.15% at 81.68%, measured with a one-day lookahead;
  the causal version (N5) is the open measurement.

## Against, and failure modes

* Regime labels are clear only after the fact; a causal signal lags, and
  whipsaws cost.
* Parameters re-fitted often chase the recent past unless the adaptation
  itself is tested out of sample.

## Fit with volatility-ai

The project's central line of work (V17, N5, N6, C-R3). A new regime
model earns a place only by beating the NATR regime on causal signals
(N5).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Nystrup, P., et al. (2016). *Journal of Portfolio Management* 42(1),
  103–109. Abstract.
* Kritzman, M., Page, S., Turkington, D. (2012). "Regime Shifts:
  Implications for Dynamic Strategies." *Financial Analysts Journal*
  68(3). Abstract.
* This repository: `plan.md`, ledger V17, N5.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 3652 | Adaptive Scholarly Macro Regime Switcher MK-9 | Geometric deep learning / Riemannian optimization / Risk parity | 6436 | 2831 | No |
| 3662 | Adaptive Scholarly Macro Regime Switcher MK-69 | Geometric deep learning / Riemannian optimization / Risk parity | 6441 | 2843 | No |
