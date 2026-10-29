# Model for regime-aware allocation

**Concept page** · shared by **12** of the 14,225 rows of the
[ranked algorithm list](../../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import)
(1 of them in ranks 426–700; best-ranked member #588) ·
researched 2026-10-29

| | |
|---|---|
| Task | Regime-aware allocation |
| Method | Unspecified model |
| Fit with this project | 🔬 this is the project's own regime work (V17, N5, N6, C-R3) |
| Implemented in volatility-ai | **Research code** in `research.catalog.concepts`: `regime_allocation`; tested on synthetic data, not wired into the engine. Related code already here: The NATR regime with liquidation on the flip (V17; causal version N5), regime sleeves (N6) and HMM regimes (C-R3). |
| Evidence | Evidence found (for the task; see the page for the method) |
| Related ledger entries | V17, N5, N6, C-R3, RK1 |

## What this page covers

The CSV rates every member *Low confidence — reconstructed from the
algorithm title; executable rules and source support are not
established.* The member names (for example "Manifold-Valued Scholarly
Macro Regime Switcher MK-54") combine a method word, "Scholarly", a task
and a serial number, and the rows' references are software libraries or
papers the CSV's own review calls unrelated. There is no specific
algorithm behind each name to research, so this page researches what the
members share: the task, done with the method.

## In one paragraph

Infer the market's state from prices, volatility or macro data and vary
exposure by regime. Regime-switching allocation has academic support
(two-state HMMs beat static weights and cut drawdowns), and it is the
project's central research line: a volatility regime that steps out of
TQQQ when daily range expands is its strongest result, pending a causal
re-measurement.

## The CSV's description

Proposed model for regime-aware allocation: Infer changing market states
from available price, volatility, or macroeconomic signals and vary
portfolio exposure by estimated regime; regime labels and transition
rules require specification. This is a concept-level interpretation of
the title, not a complete trading specification: the exact model
inputs/target, calibration, entry/exit or rebalance rules, and position
sizing are not fully defined here.

## Evidence

* **Nystrup, Hansson, Madsen & Lindström (2016), *Journal of Portfolio
  Management* 42(1):** regime-based allocation can beat static weights;
  later work reports reduced drawdowns. (Abstract.)
* **Ang & Bekaert (2002), "International asset allocation with regime
  shifts," *Review of Financial Studies* 15(4):** regime-switching
  correlations and volatilities change optimal allocations. (Standard
  reference; not re-checked here.)
* **This repository (V17):** NATR(10) below its 100-day median,
  liquidating on the flip, gave 38.64% CAGR at 26.68% maximum drawdown
  against TQQQ's 39.15% at 81.68%, measured with a one-day lookahead;
  the causal version (N5) is the open measurement.

## Against, and failure modes

* Regime labels are fitted after the fact; a causal signal lags, and
  whipsaws cost.

## Fit with volatility-ai

It is the project's own line of work. The open question is not which
regime model to add but how much of V17's result survives without the
lookahead (N5).

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Nystrup, P., et al. (2016). *Journal of Portfolio Management* 42(1),
  103–109. Abstract.
* Ang, A., Bekaert, G. (2002). *Review of Financial Studies* 15(4). Not
  re-checked.
* This repository: `plan.md`, ledger V17, N5, N6, C-R3.

## Members

| Rank | Algorithm | Family | AI | Retail | Implemented |
|---|---|---|---|---|---|
| 588 | Manifold-Valued Scholarly Macro Regime Switcher MK-54 | Vine copulas / Regularization / Multi-factor equity allocation | 4584 | 2763 | No |
| 6107 | Convolutional Scholarly Macro Regime Switcher Ver-17 | Wavelets / Fractional cointegration / Statistical arbitrage stocks | 9263 | 6489 | No |
| 6113 | Cross-Sectional Scholarly Macro Regime Switcher Ver-57 | Wavelets / Fractional cointegration / Statistical arbitrage stocks | 996 | 1819 | No |
| 6117 | Dynamic Scholarly Macro Regime Switcher Ver-77 | Wavelets / Fractional cointegration / Statistical arbitrage stocks | 9265 | 6491 | No |
| 6122 | Convolutional Scholarly Macro Regime Switcher Ver-117 | Wavelets / Fractional cointegration / Statistical arbitrage stocks | 998 | 1821 | No |
| 6128 | Cross-Sectional Scholarly Macro Regime Switcher Ver-157 | Wavelets / Fractional cointegration / Statistical arbitrage stocks | 10859 | 11285 | No |
| 6132 | Dynamic Scholarly Macro Regime Switcher Ver-177 | Wavelets / Fractional cointegration / Statistical arbitrage stocks | 1000 | 1824 | No |
| 8481 | Wasserstein Scholarly Regime Switching Allocator Alpha-16 | Koopman operator / Model predictive control / ETF rebalancing | 5804 | 2901 | No |
| 8521 | Wasserstein Scholarly Regime Switching Allocator Alpha-116 | Koopman operator / Model predictive control / ETF rebalancing | 13603 | 13697 | No |
| 8561 | Wasserstein Scholarly Regime Switching Allocator Alpha-216 | Koopman operator / Model predictive control / ETF rebalancing | 5813 | 2946 | No |
| 8601 | Wasserstein Scholarly Regime Switching Allocator Alpha-316 | Koopman operator / Model predictive control / ETF rebalancing | 5817 | 2969 | No |
| 8641 | Wasserstein Scholarly Regime Switching Allocator Alpha-416 | Koopman operator / Model predictive control / ETF rebalancing | 13608 | 13708 | No |
