# Markov-state-based approach to regime-aware allocation

**Concept page** · shared by **5** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(best-ranked member #8,497) ·
researched 2026-10-30

| | |
|---|---|
| Task | Regime-aware allocation |
| Method | Hidden Markov / regime-switching states |
| Fit with this project | 🧪 worth testing · a concrete test is below |
| Useful for volatility-ai | **Worth testing.** HMM regimes forecast out of sample in the literature (Kritzman et al. 2012) and are built here (C-R3, RK102); test them against the NATR regime. |
| Implemented in volatility-ai | The NATR regime exit (V17, causal N5) runs through the Ultimate family's `lots_to_liquidate` and `allow_signal_exit`; HMM and Gaussian-mixture regimes are research code (C-R3). |
| Evidence | Evidence found (for the task; see the page for the method) |
| Related ledger entries | V17, N5, N6, C-R3, RK102, RK104 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Markovian Scholarly Regime
Switching Allocator Alpha-56") combine a method word, "Scholarly", a
task and a serial number, and the rows' references are software
libraries or papers the CSV's own review calls unrelated. There is no
specific algorithm behind each name to research, so this page researches
what the members share: the task, done with the method.

## In one paragraph

Infer the market's state from prices, volatility or macro data and vary
exposure by regime. The Markov-state version infers hidden states (calm,
turbulent, crisis) and conditions on the current one. Markov-switching
regimes are the best-studied form: forecast out of sample, they improved
a stock/bond/cash allocation over static weights.

## The CSV's description

Proposed Markov-state-based approach to regime-aware allocation: Infer
changing market states from available price, volatility, or
macroeconomic signals and vary portfolio exposure by estimated regime;
regime labels and transition rules require specification. This is a
concept-level interpretation of the title, not a complete trading
specification: the exact model inputs/target, calibration, entry/exit or
rebalance rules, and position sizing are not fully defined here.

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
* States are clear only after the fact; causal (filtered) state
  probabilities lag turning points.

## Fit with volatility-ai

The project's central line of work (V17, N5, N6, C-R3). A new regime
model earns a place only by beating the NATR regime on causal signals
(N5).

## How to test it here

Use the causal Gaussian HMM (C-R3) as a `lots_to_liquidate` trigger in
place of the NATR regime, with the same liquidation rule, and compare
against N5 on the same windows.

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
| 8497 | Markovian Scholarly Regime Switching Allocator Alpha-56 | Koopman operator / Model predictive control / ETF rebalancing | 13602 | 13695 | No |
| 8537 | Markovian Scholarly Regime Switching Allocator Alpha-156 | Koopman operator / Model predictive control / ETF rebalancing | 5810 | 2934 | No |
| 8577 | Markovian Scholarly Regime Switching Allocator Alpha-256 | Koopman operator / Model predictive control / ETF rebalancing | 5814 | 2954 | No |
| 8617 | Markovian Scholarly Regime Switching Allocator Alpha-356 | Koopman operator / Model predictive control / ETF rebalancing | 13607 | 13706 | No |
| 8657 | Markovian Scholarly Regime Switching Allocator Alpha-456 | Koopman operator / Model predictive control / ETF rebalancing | 5823 | 3002 | No |
