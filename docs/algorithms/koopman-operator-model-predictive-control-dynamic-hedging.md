# Koopman Operator Model Predictive Control Dynamic Hedging

**Ledger ID RK416** · rank 416 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-29

| | |
|---|---|
| Family | Operator theory / Model predictive control / Derivatives hedging |
| Potential effectiveness rank | 416 (1 = strongest) |
| AI implementability rank | 286 (1 = easiest) |
| Retail advantage rank | 295 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK418, RK352 |

## In one paragraph

Linearise an option book's Greek dynamics with a Koopman dictionary and
plan hedges with MPC. The Koopman/MPC entries in the list have no
trading evidence (RK201, RK206); the nearest finance paper tuned its DMD
windows in sample. The CSV's reference, arXiv 2004.05678, is a
mathematical-physics paper ("Stable polynomials and crystalline
measures"), unrelated to trading.

## Evidence

* **Mann & Kutz (2016), *Quantitative Finance* 16(11):** DMD trading
  whose windows were tuned on in-sample "hot spots"; the nearest finance
  evidence for Koopman methods (see RK219). (Abstract.)
* **No study found** of this application.

## Against, and failure modes

* A finite Koopman dictionary linearises only approximately; MPC on weak
  forecasts optimises noise.

## Fit with volatility-ai

Options are outside the owner's instrument rule (long-only stocks and
ETFs), and the engine has no options data or pricing.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Mann, J., Kutz, J. N. (2016). *Quantitative Finance* 16(11),
  1643–1655. <https://arxiv.org/abs/1508.04487>. Abstract.
