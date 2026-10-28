# Fractional Order Vector Error Correction Neural Network Portfolio Allocator

**Ledger ID RK239** · rank 239 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-27

| | |
|---|---|
| Family | Fractional time series / Neural networks / Portfolio allocation |
| Potential effectiveness rank | 239 (1 = strongest) |
| AI implementability rank | 269 (1 = easiest) |
| Retail advantage rank | 153 (1 = strongest) |
| Fit with this project | ⛔ (no evidence; basket trading) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK36, RK93, RK297 |

## In one paragraph

Keep the fractional integration orders of a fractionally cointegrated
VAR (FCVAR) but replace the linear error-correction term with a neural
network, and allocate across the cointegrated basket. The FCVAR model is
established econometrics; I found no study of the neural variant. The
CSV's reference, arXiv 1809.02345, looks like a placeholder ID (like
arXiv 1908.01234 on RK97) and could not be identified.

## Evidence

* **Johansen & Nielsen (2012), *Econometrica* 80(6):** likelihood
  inference for the fractionally cointegrated VAR. (Standard reference;
  not re-checked here.)
* **No study found** of the neural variant.

## Against, and failure modes

* A neural error-correction term on a few cointegrated series overfits
  easily.

## Fit with volatility-ai

Basket trading with short weights (see RK36); out of scope.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Johansen, S., Nielsen, M. Ø. (2012). "Likelihood inference for a
  fractionally cointegrated vector autoregressive model." *Econometrica*
  80(6). Not re-checked.
