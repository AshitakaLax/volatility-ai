# Rough Heston Stochastic Volatility Calibration

**Ledger ID RK176** · rank 176 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-30

| | |
|---|---|
| Family | Econometric volatility / Mathematical finance |
| Potential effectiveness rank | 176 (1 = strongest) |
| AI implementability rank | 358 (1 = easiest) |
| Retail advantage rank | 2,119 (1 = strongest) |
| Fit with this project | ⛔ not useful |
| Useful for volatility-ai | **Not useful.** An option-pricing model; options are excluded. |
| Implemented in volatility-ai | **Research code** `research.catalog.derivatives`: `rough_heston_smile`, `NeuralCalibrator`. |
| Related ledger entries | RK303, RK240 |

## In one paragraph

Calibrate rough-volatility models (Hurst parameter below 0.5) to option
smiles, using neural-network surrogates for speed. Horvath, Muguruza and
Tomas calibrate rough models in milliseconds by learning the
parameter-to-smile map offline; rough volatility fits the term structure
of skew with few parameters.

## Evidence

* **Horvath, Muguruza & Tomas (2021), "Deep Learning Volatility" (arXiv
  1901.09647):** network surrogates of the pricing map calibrate (rough)
  models to full surfaces in milliseconds. (Abstract.)
* **This repository:** `derivatives.rough_heston_cf`,
  `rough_heston_smile` and `NeuralCalibrator`.

## Against, and failure modes

* Calibration quality is not a trading edge.

## Fit with volatility-ai

Options are outside the owner's instrument rule (long-only stocks and
ETFs), and the engine has no options data or pricing.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Horvath, B., Muguruza, A., Tomas, M. (2021). Deep learning volatility.
  *Quantitative Finance* 21(1). <https://arxiv.org/abs/1901.09647>.
  Abstract.
