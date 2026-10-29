# Fractional Order Vector AutoRegressive (VAR) Macro Allocator

**Ledger ID RK392** · rank 392 of 14,225 in the
[ranked algorithm list](../algorithm_ledger.md#8c-the-ranked-algorithm-list-csv-import) ·
researched 2026-10-28

| | |
|---|---|
| Family | Fractional time series / Vector autoregression / Macro strategy |
| Potential effectiveness rank | 392 (1 = strongest) |
| AI implementability rank | 231 (1 = easiest) |
| Retail advantage rank | 34 (1 = strongest) |
| Fit with this project | ⛔ (no evidence) |
| Implemented in volatility-ai | **No.** |
| Related ledger entries | RK340, RK239, RK41 |

## In one paragraph

Model macro series with a fractionally integrated VAR, so each can have
long memory, and allocate across asset classes from its forecasts.
Fractional VARs are established; I found no allocation study, and the
CSV's reference, arXiv 1809.02345, looks like a placeholder ID
(sequential digits, like arXiv 1908.01234 on RK97) and could not be
identified.

## Evidence

* **Johansen & Nielsen (2012):** the fractionally cointegrated VAR (see
  RK239).
* **No allocation study found.**

## Against, and failure modes

* Long-memory estimates on short macro samples are imprecise.

## Fit with volatility-ai

An allocator for a multi-asset book; the engine trades one symbol and
the allocator in ledger §11 is not built. Without published evidence, it
is not a candidate.

## References

Full texts could not be opened from the research environment; each item
says what was checked.

* Johansen, S., Nielsen, M. Ø. (2012). *Econometrica* 80(6). Not
  re-checked.
