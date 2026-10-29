# Wasserstein Distributionally Robust Koopman Model Predictive Control

**Ledger ID RK409** · rank 409 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-29

| | |
|---|---|
| Family | Robust statistics / Operator theory / Model predictive control |
| Potential effectiveness rank | 409 (1 = strongest) |
| AI implementability rank | 232 (1 = easiest) |
| Retail advantage rank | 152 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **Research code** in `research.catalog.koopman`: `robust_koopman_mpc`; tested on synthetic data, not wired into the engine. |
| Related ledger entries | RK206, RK225, RK415 |

## In one paragraph

Run Koopman-linearised model predictive control for multi-period
portfolio decisions inside a Wasserstein ambiguity set to guard against
model error. The Koopman/MPC entries in the list have no trading
evidence (RK201, RK206); the nearest finance paper tuned its DMD windows
in sample. The CSV's reference, arXiv 2004.05678, is a
mathematical-physics paper ("Stable polynomials and crystalline
measures"), unrelated to trading.

## Evidence

* **Mann & Kutz (2016), *Quantitative Finance* 16(11):** DMD trading
  whose windows were tuned on in-sample "hot spots"; the nearest finance
  evidence for Koopman methods (see RK219). (Abstract.)
* **Blanchet, Chen & Zhou (2022), *Management Science* 68(9):**
  Wasserstein-robust mean-variance portfolios reduce to regularised
  variance minimisation (see RK225).
* **No study found** of this application.

## Against, and failure modes

* A finite Koopman dictionary linearises only approximately; MPC on weak
  forecasts optimises noise.
* The ambiguity radius drives the answer; robust schedules mostly behave
  like higher risk aversion.

## Fit with volatility-ai

An allocator for a multi-asset book; the engine trades one symbol and
the allocator in ledger §11 is not built. Without published evidence, it
is not a candidate.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Mann, J., Kutz, J. N. (2016). *Quantitative Finance* 16(11),
  1643–1655. <https://arxiv.org/abs/1508.04487>. Abstract.
* Blanchet, J., Chen, L., Zhou, X. Y. (2022). *Management Science*
  68(9), 6382–6410. Abstract.
