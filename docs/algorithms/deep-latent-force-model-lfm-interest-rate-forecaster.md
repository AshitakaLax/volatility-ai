# Deep Latent Force Model (LFM) Interest Rate Forecaster

**Ledger ID RK224** · rank 224 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Gaussian processes / Differential equations / Fixed income |
| Potential effectiveness rank | 224 (1 = strongest) |
| AI implementability rank | 161 (1 = easiest) |
| Retail advantage rank | 86 (1 = strongest) |
| Fit with this project | ⛔ (rates forecasting; no evidence) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK226, RK287 |

## In one paragraph

Latent force models put Gaussian-process priors on the unobserved
drivers of a differential-equation model; here they would drive a
term-structure model's latent macro factors. The method comes from
machine learning (Álvarez, Luengo and Lawrence); I found no
interest-rate application. The CSV's reference, arXiv 1802.04321, looks
like a placeholder ID (like arXiv 1908.01234 on RK97) and could not be
identified.

## Evidence

* **Álvarez, Luengo & Lawrence (2009), "Latent force models," AISTATS:**
  the method. (Standard reference; not re-checked here.)
* **No interest-rate study found.**

## Against, and failure modes

* A structural prior adds assumptions; yield-curve forecasting rarely
  beats simple benchmarks (see RK226).

## Fit with volatility-ai

Rates forecasting has no direct use for this book. Not a candidate.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Álvarez, M., Luengo, D., Lawrence, N. D. (2009). "Latent Force
  Models." AISTATS. Not re-checked.
