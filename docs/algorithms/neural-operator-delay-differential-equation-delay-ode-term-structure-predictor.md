# Neural Operator Delay Differential Equation (Delay-ODE) Term Structure Predictor

**Ledger ID RK287** · rank 287 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Neural operators / Delay differential equations / Fixed income |
| Potential effectiveness rank | 287 (1 = strongest) |
| AI implementability rank | 310 (1 = easiest) |
| Retail advantage rank | 87 (1 = strongest) |
| Fit with this project | ⛔ (rates forecasting; no evidence) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK224, RK226, RK289 |

## In one paragraph

Combine neural delay-differential equations with Fourier neural
operators to model time-lagged propagation across the term structure. I
found no study of this for interest rates. The CSV's reference, arXiv
2106.09876, is a general graph anomaly-detection paper ("Anomaly
Detection in Dynamic Graphs via Transformer"), not a finance one.

## Evidence

* **Li et al. (2021), Fourier neural operators, ICLR:** the operator
  class. (Not re-checked.)
* **No term-structure study found.**

## Against, and failure modes

* Heavy model for a low-dimensional, slowly moving curve; simple
  benchmarks are hard to beat (RK226).

## Fit with volatility-ai

Rates forecasting has no direct use for this book.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Li, Z., et al. (2021). Fourier Neural Operator. ICLR. Not re-checked.
