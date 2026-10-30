# Conformal Risk-Bounded Dynamic Portfolio Allocation

**Ledger ID RK132** · rank 132 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Conformal prediction / Risk management |
| Potential effectiveness rank | 132 (1 = strongest) |
| AI implementability rank | 157 (1 = easiest) |
| Retail advantage rank | 143 (1 = strongest) |
| Fit with this project | ⏳ worth testing |
| Useful for volatility-ai | **Worth testing.** Conformal lot sizing is already researched (V13); this is its leverage-control form, worth a walk-forward test. |
| Implemented in volatility-ai | **Partly.** `research.strategies.position_sizing`: `conformal_long_size`. |
| Related ledger entries | V13, RK127 |

## In one paragraph

Wrap a return-forecasting model in split conformal intervals and scale
leverage so the bound on losses holds with a stated probability.
Conformal methods give finite-sample coverage under exchangeability;
portfolio uses appear in recent preprints (conformal robust
optimisation, conformal bandits) without trading evidence.

## Evidence

* **Conformal robust optimisation (OpenReview):** calibrated prediction
  sets give finite-sample robustness guarantees; a two-asset portfolio
  example. (Abstract.)
* **This repository:** `conformal_long_size` (V13) and
  `concepts.adaptive_conformal_positions` (adaptive conformal
  inference).

## Against, and failure modes

* Market data are not exchangeable; adaptive conformal inference is
  needed to keep coverage under shift.

## Fit with volatility-ai

Single-instrument and long-only: a conformal bound on each lot's
forecast loss can cap lot size or total exposure. Part of the V13 line;
test the adaptive version walk-forward.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Conformal robust optimisation with a portfolio example. OpenReview.
  Abstract.
* Gibbs, I., Candès, E. (2021). Adaptive Conformal Inference Under
  Distribution Shift. NeurIPS. Standard reference.
