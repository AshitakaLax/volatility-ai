# Koopman Operator Non-Linear Volatility Surface Interpolator

**Ledger ID RK320** · rank 320 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Operator theory / Volatility derivatives |
| Potential effectiveness rank | 320 (1 = strongest) |
| AI implementability rank | 347 (1 = easiest) |
| Retail advantage rank | 10,446 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **Research code** in `research.catalog.koopman`: `koopman_surface_forecast`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK321 |

## In one paragraph

Interpolate the implied-volatility surface with Koopman-linearised
dynamics. The Koopman/MPC entries in the ranked list have no trading
evidence (RK201, RK206, RK219); the nearest finance paper tuned its DMD
windows in sample (Mann & Kutz 2016). I found no volatility-surface
study, and the CSV's reference, arXiv 2004.05678, is a
mathematical-physics paper ("Stable polynomials and crystalline
measures"), unrelated to trading.

## Evidence

* **No volatility-surface study found.**
* **Mann & Kutz (2016):** DMD trading with in-sample window tuning (see
  RK219).

## Against, and failure modes

* Arbitrage-free surface constraints are not built into a Koopman model.

## Fit with volatility-ai

Options are outside the owner's instrument rule (long-only stocks and
ETFs), and the engine has no options data or pricing.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Mann, J., Kutz, J. N. (2016). *Quantitative Finance* 16(11).
  <https://arxiv.org/abs/1508.04487>. Abstract.
